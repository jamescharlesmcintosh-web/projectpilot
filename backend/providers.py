"""Local generation only. External models use the copy/import workflow."""
import json
import os
import time
from urllib.parse import urlparse
import httpx
from models import ImportChanges

TIER_META = {
 'auto':{'label':'Auto','model_name':'manual or configured local model','price_in':None,'price_out':None},
 'local':{'label':'Local','model_name':'Ollama on your computer','price_in':0,'price_out':0},
 'cheap':{'label':'External · standard','model_name':'copy prompt / import result','price_in':None,'price_out':None},
 'expensive':{'label':'External · advanced','model_name':'copy prompt / import result','price_in':None,'price_out':None},
 'human_review':{'label':'Human review','model_name':'manual review','price_in':0,'price_out':0},
}

def ollama_url():
    url=os.environ.get('PP_OLLAMA_URL','http://127.0.0.1:11434').rstrip('/')
    parsed=urlparse(url)
    if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost','::1') or parsed.username or parsed.password:
        raise ValueError('Only a loopback Ollama server is supported. Cloud endpoints are disabled.')
    return url

async def models_available():
    try:
        async with httpx.AsyncClient(timeout=3,trust_env=False) as client:
            r=await client.get(ollama_url()+'/api/tags');r.raise_for_status()
            # Exclude zero-size remote/cloud entries. No model downloads are triggered here.
            models=[{'name':m['name'],'size':m.get('size',0)} for m in r.json().get('models',[]) if m.get('size',0)>0 and 'cloud' not in m['name'].lower()]
            return {'connected':True,'models':models,'error':None}
    except Exception:
        return {'connected':False,'models':[],'error':'Ollama is not reachable. Copy/import mode works without it.'}

async def generate(prompt, settings):
    model=settings.get('ollama_model','')
    available=await models_available()
    if model not in [m['name'] for m in available['models']]:
        raise ValueError('Select an installed local Ollama model in Settings, or use Copy task prompt and Import result.')
    started=time.monotonic()
    async with httpx.AsyncClient(timeout=httpx.Timeout(180,connect=5),trust_env=False) as client:
        async with client.stream('POST',ollama_url()+'/api/chat',json={'model':model,'stream':False,'format':ImportChanges.model_json_schema(),'messages':[{'role':'system','content':'Return only the requested JSON file changes. Respect every task boundary. Never include credentials.'},{'role':'user','content':prompt}],'options':{'num_predict':settings['max_output_tokens'],'temperature':0.15}}) as response:
            response.raise_for_status();raw=bytearray()
            async for chunk in response.aiter_bytes():
                raw.extend(chunk)
                if len(raw)>2_000_000: raise ValueError('Model output exceeded the safety limit')
    data=json.loads(raw)
    if data.get('done_reason')=='length': raise ValueError('Model output limit reached. Use a smaller task or raise the output limit.')
    changes=ImportChanges.model_validate_json(data['message']['content'])
    return changes, {'model_name':model,'tokens_in':data.get('prompt_eval_count',0),'tokens_out':data.get('eval_count',0),'latency_ms':int((time.monotonic()-started)*1000),'cost':0,'cost_status':'local_api_only','compute_cost':None}

# Cloud requests are opt-in and always preceded by a single-use quote.
_catalog={'at':0,'models':[]}
SYSTEM='Return only JSON containing summary and files with path and complete content (null for deletion). Respect scope and acceptance criteria. Never include credentials.'
class ProviderFailure(ValueError):
    def __init__(self,message,meter=None): super().__init__(message);self.meter=meter

async def cloud_models():
    if time.monotonic()-_catalog['at']<900 and _catalog['models']: return _catalog['models']
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r=await client.get('https://openrouter.ai/api/v1/models');r.raise_for_status();data=r.json()['data']
        result=[]
        for m in data:
            p=m.get('pricing',{});arch=m.get('architecture',{})
            if 'text' not in arch.get('output_modalities',[]) or 'response_format' not in m.get('supported_parameters',[]): continue
            # Restrict to text-only token billing; don't estimate image/search/request fees.
            if any(float(p.get(k) or 0)>0 for k in ('request','image','web_search','internal_reasoning')): continue
            inp=float(p['prompt']);out=float(p['completion'])
            if not all(__import__('math').isfinite(x) and x>=0 for x in (inp,out)): continue
            result.append({'id':m['id'],'name':m.get('name',m['id']),'context_length':int(m.get('context_length') or 0),'max_output_tokens':int((m.get('top_provider') or {}).get('max_completion_tokens') or 16384),'prompt_price':inp,'completion_price':out})
        _catalog.update(at=time.monotonic(),models=sorted(result,key=lambda m:(m['prompt_price']+m['completion_price'],m['id'])))
        return _catalog['models']
    except Exception as e: raise ValueError('Model catalog unavailable. Copy/import and local generation still work.') from e

async def generate_cloud(prompt,settings,quote):
    key=os.environ.get('OPENROUTER_API_KEY')
    if not key or not settings['paid_enabled']: raise ProviderFailure('Paid generation is not configured.')
    started=time.monotonic();price=quote['pricing']
    payload={'model':quote['model'],'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':prompt}],'stream':False,'max_tokens':settings['max_output_tokens'],'response_format':{'type':'json_object'},'provider':{'allow_fallbacks':False,'require_parameters':True,'sort':'price','max_price':{'prompt':price['prompt_price']*1e6,'completion':price['completion_price']*1e6,'request':0}}}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(180,connect=10)) as client:
            async with client.stream('POST','https://openrouter.ai/api/v1/chat/completions',headers={'Authorization':'Bearer '+key,'X-OpenRouter-Title':'ProjectPilot'},json=payload) as response:
                if response.status_code>=400: raise ProviderFailure(f'Provider returned HTTP {response.status_code}. No automatic retry. Review provider activity before retrying.')
                raw=bytearray()
                async for chunk in response.aiter_bytes():
                    raw.extend(chunk)
                    if len(raw)>2_000_000: raise ProviderFailure('Provider output exceeded 2 MB; usage may be unknown.')
        data=json.loads(raw);u=data.get('usage') or {};cost=u.get('cost')
        if not isinstance(cost,(float,int)) or not __import__('math').isfinite(cost) or cost<0: cost=None
        meter={'model_name':data.get('model',quote['model']),'tier':quote['tier'],'tokens_in':u.get('prompt_tokens') or 0,'tokens_out':u.get('completion_tokens') or 0,'cost':cost,'cost_status':'provider_reported' if cost is not None else 'provider_usage_unknown','provider_generation_id':data.get('id'),'latency_ms':int((time.monotonic()-started)*1000)}
        try:
            choice=data['choices'][0]
            if choice.get('finish_reason')=='length': raise ValueError('Output limit reached. Split the task or increase the output limit.')
            body=ImportChanges.model_validate_json(choice['message']['content'])
        except Exception as e: raise ProviderFailure('Model result was incomplete or invalid JSON. No repair request was made automatically.',meter) from e
        return body,meter
    except (ProviderFailure, __import__('asyncio').CancelledError): raise
    except Exception as e: raise ProviderFailure('Provider connection or response failed. Usage may be unknown; review provider activity before retrying.') from e

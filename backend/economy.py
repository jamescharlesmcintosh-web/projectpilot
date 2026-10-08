"""Transparent routing and conservative reservations; never an autonomous retry loop."""
import math
import time
import os
import planning
import providers
from models import new_id, now_iso


def route(task, settings):
    tier=task['tier']
    if tier=='human_review': return {'kind':'manual','model':'Human review','reason':'Human judgment is required.'}
    if tier=='auto':
        difficult=task.get('attempts',0)>=2 or any(word in (task['title']+' '+task['description']).lower() for word in ['security','migration','architecture','concurrency','authentication'])
        if difficult and settings['paid_enabled'] and settings['advanced_model']:
            tier='expensive';reason='Complexity or repeated attempts suggests advanced reasoning. This is a routing heuristic, not a quality guarantee.'
        elif settings['ollama_model']:
            tier='local';reason='Try the installed local model for this bounded task.'
        else:
            tier='cheap';reason='Use the configured standard model for everyday implementation.'
    else: reason='You selected this tier.'
    if tier=='local' and settings['ollama_model']: return {'kind':'local','tier':tier,'model':settings['ollama_model'],'reason':reason}
    model=settings['advanced_model' if tier=='expensive' else 'standard_model']
    if tier in ('cheap','expensive') and settings['paid_enabled'] and model and os.environ.get('OPENROUTER_API_KEY'):
        return {'kind':'cloud','tier':tier,'model':model,'reason':reason}
    return {'kind':'manual','tier':tier,'model':'Copy / import','reason':'Copy this task into a tool you already use, then import its JSON response. Configure a model in Settings for integrated runs.'}


def reserved(store, month):
    return sum(b['reserved_usd'] for b in store.list('billing') if b['created_at'].startswith(month) and b['status']!='settled')


def spent(store, month):
    return sum(r.get('cost') or 0 for r in store.list('model_runs') if r['created_at'].startswith(month))


def assert_budget(store, settings, amount):
    if amount>settings['max_run_cost_usd']: raise ValueError('Estimate exceeds the per-run cap. Split the task, reduce context/output, choose a cheaper model, or deliberately raise the cap.')
    if settings['monthly_budget_usd']<=0: raise ValueError('Set a positive monthly API budget in Settings to enable paid requests.')
    remaining=settings['monthly_budget_usd']-spent(store,now_iso()[:7])-reserved(store,now_iso()[:7])
    if amount>remaining: raise ValueError('Monthly budget is insufficient after known usage and unresolved reservations.')
    return max(0,remaining)


async def quote(task, settings, data, baseline, store):
    r=route(task,settings)
    q={'id':new_id(),'task_id':task['id'],'project_id':task['project_id'],'created_at':now_iso(),'expires_at':time.time()+300,'consumed':False,'context_hash':data['context_hash'],'settings_hash':planning.digest(settings),'baseline':baseline,**r,'estimated_usd':0 if r['kind']=='local' else None}
    if r['kind']=='cloud':
        models=await providers.cloud_models()
        model=next((m for m in models if m['id']==r['model']),None)
        if not model: raise ValueError('Selected model is unavailable in the current supported catalog. Refresh models in Settings.')
        # One token per UTF-8 byte plus generous message overhead is a conservative estimate,
        # not an exact tokenizer. Provider rates and output limit are also sent in the request.
        input_bound=len(data['prompt'].encode())+4096
        output=settings['max_output_tokens']
        if input_bound+output>model['context_length']: raise ValueError('Context estimate exceeds the model context window. Split the task or reduce context.')
        if output>model['max_output_tokens']: raise ValueError('Output limit exceeds this model capability. Lower it in Settings.')
        amount=math.ceil((input_bound*model['prompt_price']+output*model['completion_price'])*1.1*1e6)/1e6
        remaining=assert_budget(store,settings,amount)
        q.update(estimated_usd=amount,remaining_usd=remaining,projected_remaining_usd=remaining-amount,input_token_bound=input_bound,output_token_limit=output,pricing=model,estimate_note='Conservative reservation with 10% margin. Actual provider usage replaces it when reported; it is not an invoice guarantee.')
    store.save('quotes',q)
    return q

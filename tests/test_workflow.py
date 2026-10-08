import io
import json
import time
import zipfile
import asyncio
import pytest
import server as S
import models as M
import providers
import economy
from workspaces import files_at,git,check_source

def post(c,path,data={}):
    r=c.post('/api'+path,json=data)
    assert r.status_code==200,r.text
    return r.json()
def project(c,brief='Build a timer. Preserve session history.'):
    return post(c,'/projects',{'name':'Independent project','brief':brief})['id']
def task(c,p,**kw): return post(c,f'/projects/{p}/tasks',{'title':'Implement timer',**kw})['id']
def candidate(c,t,content='<!doctype html>\n<html><body><h1>Timer</h1></body></html>\n',path='index.html'):
    return post(c,f'/tasks/{t}/import',{'files':[{'path':path,'content':content}]})
def approve(c,t):
    d=c.get(f'/api/tasks/{t}/diff').json();v=c.get(f'/api/tasks/{t}/verifications').json()[0];tdata=c.get(f'/api/tasks/{t}').json()
    return post(c,f'/tasks/{t}/approve',{'candidate_hash':d['candidate_hash'],'verification_id':v['id'],'checked_criteria':list(range(len(tdata['acceptance_criteria'])))})

def test_real_workflow_exact_bytes_commit_export_and_preview(client):
    c=client;p=project(c);t=task(c,p)
    content='  <!doctype html>\n<html><body><h1>Timer</h1></body></html>\n\n'
    out=candidate(c,t,content)
    assert S.ws.head(p)=='EMPTY'
    assert files_at(S.ws.candidate(p,out['run']['id']))['index.html']==content.encode()
    v=c.get(f'/api/tasks/{t}/verifications').json()[0];assert v['status']=='passed'
    assert 'Timer' in out['diff']['files'][0]['hunk']
    preview=post(c,f'/projects/{p}/previews/launch?task_id={t}')
    r=c.get(preview['url']);assert r.text==content
    assert 'sandbox allow-scripts' in r.headers['content-security-policy']
    assert 'allow-same-origin' not in r.headers['content-security-policy']
    done=approve(c,t);assert len(done['commit_hash'])==40
    assert git(S.ws.repo(p),'show','HEAD:index.html',raw=True)==content
    assert len(c.get(f'/api/projects/{p}/history').json())==1
    z=zipfile.ZipFile(io.BytesIO(c.get(f'/api/projects/{p}/export').content));assert z.read('index.html')==content.encode()
    assert c.post(f'/api/tasks/{t}/approve',json={}).status_code==422
    assert c.get('/api/projects').json()[0]['id']==p

def test_contract_cannot_bypass_human_gate(client):
    p=project(client);t=task(client,p)
    for body in [{'status':'merged'},{'project_id':'other'},{'latest_verification_id':'fake'},{'requires_human_approval':False}]:
        assert client.patch(f'/api/tasks/{t}',json=body).status_code==422
    assert client.patch('/api/settings',json={'require_approval_before_merge':False}).status_code==422
    d=candidate(client,t)['diff'];v=client.get(f'/api/tasks/{t}/verifications').json()[0]
    assert client.post(f'/api/tasks/{t}/approve',json={'candidate_hash':d['candidate_hash'],'verification_id':v['id'],'checked_criteria':[]}).status_code==400
    assert S.ws.head(p)=='EMPTY'

def test_current_evidence_and_source_required(client):
    p=project(client);t=task(client,p);d=candidate(client,t)['diff'];v=client.get(f'/api/tasks/{t}/verifications').json()[0]
    candidate(client,t,'<!doctype html><h1>Updated</h1>')
    assert client.post(f'/api/tasks/{t}/approve',json={'candidate_hash':d['candidate_hash'],'verification_id':v['id'],'checked_criteria':[0]}).status_code==400
    other=task(client,p);candidate(client,other,'<!doctype html><h1>Other approved task</h1>');approve(client,other)
    assert client.post(f'/api/tasks/{t}/verify',json={}).status_code==400

def test_candidate_tamper_rejected(client):
    p=project(client);t=task(client,p);r=candidate(client,t)['run']
    (S.ws.candidate(p,r['id'])/'index.html').write_text('Tampered')
    assert client.post(f'/api/tasks/{t}/verify',json={}).status_code==400

def test_syntax_failure_and_no_host_execution(client,tmp_path):
    p=project(client);t=task(client,p);candidate(client,t,'const broken = ;','main.js')
    v=client.get(f'/api/tasks/{t}/verifications').json()[0];assert v['status']=='failed'
    t2=task(client,p,verification_commands=[f'touch {tmp_path}/should-not-exist'])
    candidate(client,t2)
    v=client.get(f'/api/tasks/{t2}/verifications').json()[0]
    assert v['status']=='failed' and any(c['status']=='blocked' for c in v['checks'])
    assert not (tmp_path/'should-not-exist').exists()
    t3=task(client,p);candidate(client,t3,'raise RuntimeError("Do not execute")\n','app.py')
    assert client.get(f'/api/tasks/{t3}/verifications').json()[0]['status']=='passed'

@pytest.mark.parametrize('path',['../escape','/tmp/escape','.env','.git/config','src/../../bad','a\\b','node_modules/x','.ssh/id_rsa'])
def test_path_boundaries(client,path):
    p=project(client);t=task(client,p)
    assert client.post(f'/api/tasks/{t}/import',json={'files':[{'path':path,'content':'x'}]}).status_code==400

def test_scope_dependencies_and_project_ownership(client):
    p=project(client);other=project(client);dep=task(client,p);t=task(client,p,dependencies=[dep],allowed_files=['src/**'],blocked_files=['src/private.js'])
    assert client.post(f'/api/tasks/{t}/import',json={'files':[{'path':'src/a.js','content':'const x=1'}]}).status_code==400
    candidate(client,dep);approve(client,dep)
    for path in ['index.html','src/private.js']:
        assert client.post(f'/api/tasks/{t}/import',json={'files':[{'path':path,'content':'const x=1'}]}).status_code==400
    candidate(client,t,'const x=1;\n','src/a.js')
    assert client.post(f'/api/projects/{other}/previews/launch?task_id={t}').status_code==404
    assert client.post(f'/api/projects/{other}/tasks',json={'title':'Wrong','dependencies':[dep]}).status_code==400

def test_brief_specific_versioned_plans_and_idempotent_delegation(client):
    p=project(client,'Create a book inventory. Track ISBN and shelf location.')
    plan=post(client,f'/projects/{p}/master-plan/generate')
    assert 'ISBN' in json.dumps(plan)
    assert client.post(f'/api/projects/{p}/delegation-plan/generate').status_code==400
    post(client,f'/projects/{p}/master-plan/{plan["id"]}/adopt')
    delegation=post(client,f'/projects/{p}/delegation-plan/generate')
    n=post(client,f'/projects/{p}/delegation-plan/materialize')['created'];assert n==len(delegation['tasks'])
    assert post(client,f'/projects/{p}/delegation-plan/materialize')['created']==0
    tasks=client.get(f'/api/projects/{p}/tasks').json();assert tasks[1]['dependencies']==[tasks[0]['id']]
    assert tasks[1]['model_prompt'] and tasks[1]['acceptance_criteria']==delegation['tasks'][1]['acceptance_criteria']
    client.patch(f'/api/projects/{p}',json={'brief':'Make an appointment calendar.'})
    assert client.post(f'/api/tasks/{tasks[0]["id"]}/estimate',json={}).status_code==400
    plan2=post(client,f'/projects/{p}/master-plan/generate');assert plan2['source_hash']!=plan['source_hash']
    post(client,f'/projects/{p}/master-plan/{plan2["id"]}/adopt');post(client,f'/projects/{p}/delegation-plan/generate');post(client,f'/projects/{p}/delegation-plan/materialize')
    assert client.get(f'/api/tasks/{tasks[0]["id"]}').json()['status']=='superseded'
    assert len(client.get(f'/api/projects/{p}/plan-versions').json())==2

def test_cycle_and_duplicate_plan_rejected(client):
    p=project(client)
    body={'summary':'x','roadmap':[{'number':1,'title':'A','objective':'A','dependencies':['1'],'acceptance_criteria':['a']}]}
    assert client.post(f'/api/projects/{p}/master-plan/import',json=body).status_code==400

def test_manual_review_and_backup_restore(client):
    p=project(client);t=task(client,p);original='<!doctype html>\n<h1>Original</h1>\n\n';candidate(client,t,original);sha=approve(client,t)['commit_hash']
    t2=task(client,p);candidate(client,t2,'<!doctype html><h1>New</h1>');approve(client,t2)
    restored=post(client,f'/projects/{p}/restore',{'commit_hash':sha});approve(client,restored['run']['task_id'])
    assert files_at(S.ws.repo(p))['index.html']==original.encode()
    review=task(client,p,tier='human_review',dependencies=[t2])
    post(client,f'/tasks/{review}/review',{'checked_criteria':[0],'note':'Exercised the intended user flow.'})
    r=client.get('/api/backup');z=zipfile.ZipFile(io.BytesIO(r.content));assert 'data/projectpilot.sqlite3' in z.namelist()
    assert any('/.git/' in n for n in z.namelist())
    assert client.delete(f'/api/projects/{p}').json()['archived'] is True
    assert files_at(S.ws.repo(p))
    assert client.post('/api/seed',json={'force':True}).status_code in (404,405)

def test_zip_import_review_and_traversal(client):
    p=project(client);out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z: z.writestr('example/index.html','<!doctype html><h1>ZIP source</h1>');z.writestr('example/node_modules/foo.js','ignored')
    r=client.post(f'/api/projects/{p}/import-source',content=out.getvalue(),headers={'content-type':'application/zip'})
    assert r.status_code==200,r.text
    assert S.ws.head(p)=='EMPTY' and r.json()['skipped_files']==['node_modules/foo.js']
    approve(client,r.json()['task_id'])
    bad=io.BytesIO()
    with zipfile.ZipFile(bad,'w') as z:z.writestr('root/../escape.txt','bad')
    assert client.post(f'/api/projects/{p}/import-source',content=bad.getvalue()).status_code==400

def test_local_access_headers_and_origin(client):
    assert client.post('/api/projects',json={'name':'x'},headers={'x-projectpilot-client':''}).status_code==403
    assert client.get('/api/projects',headers={'origin':'https://attacker.example'}).status_code==403
    assert client.get('/api/projects',headers={'host':'attacker.example'}).status_code==403
    S.TOKEN='test-token'
    assert client.get('/api/projects').status_code==401
    assert client.get('/api/projects',headers={'x-projectpilot-token':'test-token'}).status_code==200

def cloud_setup(c,monkeypatch,budget=1):
    monkeypatch.setenv('OPENROUTER_API_KEY','test-never-sent')
    async def catalog():return [{'id':'test/model','name':'Test','context_length':200000,'max_output_tokens':20000,'prompt_price':.000001,'completion_price':.000002}]
    monkeypatch.setattr(providers,'cloud_models',catalog)
    s=M.SettingsUpdate(paid_enabled=True,standard_model='test/model',advanced_model='test/model',monthly_budget_usd=budget).model_dump()
    assert c.patch('/api/settings',json=s).status_code==200
    p=project(c);t=task(c,p,tier='cheap');return p,t

def wait_finished(c,t):
    for _ in range(100):
        d=c.get(f'/api/tasks/{t}').json()
        if d['status']!='running':return d
        time.sleep(.01)
    pytest.fail('Job failed to finish')

def test_paid_single_use_quote_and_actual_meter(client,monkeypatch):
    p,t=cloud_setup(client,monkeypatch);calls=[]
    async def generate(prompt,s,q):
        calls.append(q['id']);return M.ImportChanges(files=[{'path':'index.html','content':'<!doctype html><h1>Paid test fixture</h1>'}]),{'model_name':'test/model','tier':'cheap','cost':.007,'cost_status':'provider_reported','tokens_in':100,'tokens_out':40,'latency_ms':1}
    monkeypatch.setattr(providers,'generate_cloud',generate)
    assert client.post(f'/api/tasks/{t}/run-edit',json={}).status_code==400
    q=post(client,f'/tasks/{t}/estimate');assert q['kind']=='cloud' and q['estimated_usd']>0
    post(client,f'/tasks/{t}/run-edit',{'quote_id':q['id']});assert wait_finished(client,t)['status']=='pending_approval'
    assert len(calls)==1
    assert client.post(f'/api/tasks/{t}/run-edit',json={'quote_id':q['id']}).status_code==400
    u=client.get(f'/api/projects/{p}/usage').json();assert u['total_cost']==.007 and u['reserved_usd']==0 and u['total_runs']==1
    assert S.ws.head(p)=='EMPTY'

def test_budget_blocks_and_quote_invalidates(client,monkeypatch):
    p,t=cloud_setup(client,monkeypatch,budget=0)
    assert client.post(f'/api/tasks/{t}/estimate',json={}).status_code==400
    s=S.settings();s.pop('id');s.pop('updated_at');s['monthly_budget_usd']=1;client.patch('/api/settings',json=s)
    q=post(client,f'/tasks/{t}/estimate')
    client.patch(f'/api/tasks/{t}',json={'description':'Changed requirements'})
    assert client.post(f'/api/tasks/{t}/run-edit',json={'quote_id':q['id']}).status_code==400
    q=post(client,f'/tasks/{t}/estimate');s['max_output_tokens']=1024;client.patch('/api/settings',json=s)
    assert client.post(f'/api/tasks/{t}/run-edit',json={'quote_id':q['id']}).status_code==400
    assert not S.store.list('billing')

def test_invalid_cloud_output_still_metered_no_retry(client,monkeypatch):
    p,t=cloud_setup(client,monkeypatch);calls=[]
    async def fail(*args):
        calls.append(1);raise providers.ProviderFailure('Invalid output',{'cost':.012,'model_name':'test/model','tier':'cheap','tokens_in':100,'tokens_out':80,'latency_ms':1,'cost_status':'provider_reported'})
    monkeypatch.setattr(providers,'generate_cloud',fail)
    q=post(client,f'/tasks/{t}/estimate');post(client,f'/tasks/{t}/run-edit',{'quote_id':q['id']});assert wait_finished(client,t)['status']=='failed'
    u=client.get('/api/usage').json();assert u['total_cost']==.012 and u['reserved_usd']==0 and len(calls)==1

def test_unknown_cloud_failure_holds_reservation(client,monkeypatch):
    p,t=cloud_setup(client,monkeypatch)
    async def fail(*args):raise providers.ProviderFailure('Connection interrupted')
    monkeypatch.setattr(providers,'generate_cloud',fail)
    q=post(client,f'/tasks/{t}/estimate');post(client,f'/tasks/{t}/run-edit',{'quote_id':q['id']});wait_finished(client,t)
    u=client.get('/api/usage').json();assert u['total_cost']==0 and u['reserved_usd']==q['estimated_usd'] and u['unknown_cost_runs']==1

def test_monthly_meter_does_not_count_previous_month(client):
    S.store.save('model_runs',{'id':'old','created_at':'2001-01-01','tier':'cheap','cost':99})
    assert client.get('/api/usage').json()['total_cost']==0

def test_auto_chooses_advanced_for_difficult_work(client,monkeypatch):
    p,t=cloud_setup(client,monkeypatch)
    s=S.settings();s['ollama_model']='local-model'
    ordinary={'tier':'auto','title':'Button color','description':'','attempts':0}
    assert economy.route(ordinary,s)['kind']=='local'
    hard={**ordinary,'title':'Review authentication security'}
    assert economy.route(hard,s)['tier']=='expensive'
    retry={**ordinary,'attempts':2}
    assert economy.route(retry,s)['tier']=='expensive'

def test_inline_script_syntax_is_checked(client):
    p=project(client);t=task(client,p);candidate(client,t,'<!doctype html><script>const broken = ;</script>')
    assert client.get(f'/api/tasks/{t}/verifications').json()[0]['status']=='failed'

@pytest.mark.parametrize('path',['.GIT/config','src/.ENV','index.html.','AUX.txt'])
def test_portable_path_boundaries(client,path):
    p=project(client);t=task(client,p)
    assert client.post(f'/api/tasks/{t}/import',json={'files':[{'path':path,'content':'bad'}]}).status_code==400

def test_cloud_wire_contract_with_fake_http(monkeypatch):
    import httpx
    original=httpx.AsyncClient;seen=[]
    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200,json={'id':'receipt-fixture','model':'test/model','choices':[{'finish_reason':'stop','message':{'content':json.dumps({'files':[{'path':'index.html','content':'  hello\n'}]})}}],'usage':{'prompt_tokens':100,'completion_tokens':20,'cost':.001}})
    monkeypatch.setenv('OPENROUTER_API_KEY','test-only')
    monkeypatch.setattr(providers.httpx,'AsyncClient',lambda **kwargs: original(transport=httpx.MockTransport(handler)))
    q={'model':'test/model','tier':'cheap','pricing':{'prompt_price':.000001,'completion_price':.000002}}
    body,meter=asyncio.run(providers.generate_cloud('small prompt',M.SettingsUpdate(paid_enabled=True).model_dump(),q))
    assert body.files[0].content=='  hello\n' and meter['cost']==.001
    assert seen[0]['provider']['allow_fallbacks'] is False
    assert seen[0]['provider']['max_price']=={'prompt':1,'completion':2,'request':0}
    assert seen[0]['max_tokens']==4096

def test_paid_cancellation_and_global_generation_limit(client,monkeypatch):
    p,t=cloud_setup(client,monkeypatch)
    async def hold(*args): await asyncio.Event().wait()
    monkeypatch.setattr(providers,'generate_cloud',hold)
    q=post(client,f'/tasks/{t}/estimate');post(client,f'/tasks/{t}/run-edit',{'quote_id':q['id']})
    t2=task(client,project(client),tier='cheap');q2=post(client,f'/tasks/{t2}/estimate')
    assert client.post(f'/api/tasks/{t2}/run-edit',json={'quote_id':q2['id']}).status_code==409
    post(client,f'/tasks/{t}/cancel');assert wait_finished(client,t)['status']=='failed'
    assert client.get('/api/usage').json()['reserved_usd']==q['estimated_usd']

def test_changed_file_scope_rechecks_candidate(client):
    p=project(client);t=task(client,p);candidate(client,t)
    post(client,f'/tasks/{t}/reject')
    r=client.patch(f'/api/tasks/{t}',json={'allowed_files':['src/**']});assert r.status_code==200
    assert client.post(f'/api/tasks/{t}/verify',json={}).status_code==400

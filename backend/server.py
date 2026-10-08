"""ProjectPilot local workbench. Single owner, one Uvicorn worker, explicit opt-in paid requests."""
import asyncio
import io
import json
import mimetypes
import os
import secrets
import shutil
import tempfile
import zipfile
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
import models as M
import planning
import providers
import economy
import time
from storage import Store
from workspaces import Workspaces, files_at, fingerprint, check_source, safe_path, check_scope, git

ROOT=Path(__file__).resolve().parent
load_dotenv(ROOT/'.env')
DATA=Path(os.environ.get('PP_DATA_DIR',ROOT.parent/'data')).resolve()
DATA.mkdir(parents=True,exist_ok=True)
store=Store(DATA/'projectpilot.sqlite3')
ws=Workspaces(DATA/'projects')
locks=defaultdict(asyncio.Lock)
jobs={}
dispatch_lock=asyncio.Lock()
TOKEN=os.environ.get('PP_ACCESS_TOKEN','')


def get(kind,id):
    doc=store.get(kind,id)
    if not doc: raise HTTPException(404,f'{kind} not found')
    return doc

def settings():
    return store.get('settings','global') or {'id':'global',**M.SettingsUpdate().model_dump()}

def activity(pid,kind,message,meta=None):
    store.save('activity',{'id':M.new_id(),'project_id':pid,'kind':kind,'message':message,'meta':meta or {},'created_at':M.now_iso()})

def update_project(pid,**values):
    p=get('projects',pid);p.update(values,updated_at=M.now_iso());store.save('projects',p);return p

def latest(kind,pid):
    return next(iter(sorted(store.list(kind,pid),key=lambda d:d['created_at'],reverse=True)),None)

def task_ready(task):
    p=get('projects',task['project_id'])
    if p['status']=='archived': raise ValueError('Restore this archived project first')
    if task['status'] in ('merged','superseded'): raise ValueError('Create a new task to change completed or superseded work')
    if task.get('plan_id') and task['plan_id']!=p.get('approved_plan_id'): raise ValueError('This task belongs to an older plan. Materialize the adopted plan.')
    if task.get('plan_id'):
        plan=get('master_plans',task['plan_id'])
        if plan['source_hash']!=planning.source_hash(p): raise ValueError('The brief changed. Adopt a current plan first.')
    for dep in task.get('dependencies',[]):
        d=get('tasks',dep)
        if d['project_id']!=task['project_id'] or d['status']!='merged': raise ValueError(f"Dependency is not completed: {d['title']}")
    return p

def make_task(pid,body,**extra):
    d=body.model_dump();existing=store.list('tasks',pid)
    d.update(id=M.new_id(),project_id=pid,number=d.get('number') or max([t.get('number') or 0 for t in existing]+[0])+1,status='queued',branch=None,diff_id=None,latest_verification_id=None,commit_hash=None,run_id=None,created_at=M.now_iso(),updated_at=M.now_iso(),attempts=0)
    d.update(extra);store.save('tasks',d);return d

def candidate_for(task):
    if not task.get('run_id'): raise ValueError('Create or import a real candidate first')
    run=get('runs',task['run_id'])
    if run['task_id']!=task['id'] or run['project_id']!=task['project_id']: raise ValueError('Candidate does not belong to this task')
    ws.assert_current(run)
    for change in run["files"]: check_scope(change["path"],task)
    return run

def task_prompt(task,override=None):
    p=get('projects',task['project_id']);s=settings();limit=s['max_context_chars']
    instruction=(task.get('model_prompt') or f"Project: {p['name']}\nFull brief:\n{p['brief']}\nTask: {task['title']}\n{task['description']}")
    instruction+='\nAcceptance criteria:\n'+'\n'.join(task['acceptance_criteria'])
    instruction+='\nAllowed paths: '+json.dumps(task['allowed_files'])+'\nBlocked paths: '+json.dumps(task['blocked_files'])
    if override: instruction+='\nRequested revision:\n'+override
    instruction+='\nReturn ONLY JSON: {"summary":"what changed","files":[{"path":"relative/file","content":"complete new content"}]}. Use content:null to delete. Return changed files only. Preserve working behavior and never invent business facts. No credentials or dependency folders.'
    if len(instruction)>limit-1000: raise ValueError('Instructions exceed the context budget. Split the task or increase the context limit in Settings.')
    root=ws.candidate(p['id'],task['run_id']) if task.get('run_id') else ws.ensure(p['id'])
    files=files_at(root);remaining=limit-len(instruction);included=[];omitted=[]
    # Favor files named in task text and exact scopes; retain complete file contents.
    ordered=sorted(files,key=lambda x:(0 if x in instruction or x in task['allowed_files'] else 1,len(files[x]),x))
    for name in ordered:
        from workspaces import match
        if any(match(name,b) for b in task['blocked_files']): omitted.append(name);continue
        try: block='\nFILE '+name+'\n'+files[name].decode()+'\nEND FILE\n'
        except UnicodeDecodeError: omitted.append(name);continue
        if len(block)>remaining: omitted.append(name);continue
        instruction+=block;remaining-=len(block);included.append(name)
    note='\nSome source files were omitted by the context budget. Request missing files before changing assumptions.' if omitted else ''
    return {'prompt':instruction+note,'included_files':included,'omitted_files':omitted,'characters':len(instruction+note),'context_hash':planning.digest(instruction),'route':economy.route(task,s),'paid_calls_enabled':s['paid_enabled']}

@asynccontextmanager
async def lifespan(app):
    # A recorded run is never silently restarted (avoids duplicate inference).
    for run in store.list('runs'):
        if run['status']=='generating':
            run.update(status='interrupted',error='Server restarted. Review the task before retrying.');store.save('runs',run)
            bill=store.get('billing',run['id'])
            if bill: bill['status']='unresolved';store.save('billing',bill)
            t=store.get('tasks',run['task_id'])
            if t and t['status']=='running': t['status']='failed';store.save('tasks',t)
    # Recover a filesystem swap interrupted between the two directory renames.
    for p in store.list('projects'):
        parent=ws.project_root(p['id'])
        if not ws.repo(p['id']).exists() and parent.exists():
            backups=sorted(parent.glob('previous-*'),key=lambda f:f.stat().st_mtime,reverse=True)
            if backups: backups[0].rename(ws.repo(p['id']))
    # Reconcile a successfully committed operation if the process ended before DB finalization.
    for op in store.list('approvals'):
        if op.get('status')=='committing':
            t=store.get('tasks',op['task_id']);run=store.get('runs',op['run_id'])
            if t and run and fingerprint(files_at(ws.repo(t['project_id'])))==run['candidate_hash'] and ws.head(t['project_id'])!=run['base_sha']:
                t.update(status='merged',commit_hash=ws.head(t['project_id']));op.update(status='committed',commit_hash=t['commit_hash']);store.save_many([('tasks',t),('approvals',op)])
    yield
    for job in list(jobs.values()): job.cancel()
    if jobs: await asyncio.gather(*list(jobs.values()),return_exceptions=True)

app=FastAPI(title='ProjectPilot',version='0.2.0',lifespan=lifespan)
api=APIRouter(prefix='/api')

@app.middleware('http')
async def protect(request,call_next):
    path=request.url.path
    if path.startswith('/api'):
        origin=request.headers.get('origin')
        allowed={'localhost','127.0.0.1','::1','testserver'}
        if request.url.hostname not in allowed: return JSONResponse({'detail':'Local access only. Use a localhost tunnel for remote access.'},status_code=403)
        if origin and urlparse(origin).hostname not in allowed: return JSONResponse({'detail':'Untrusted origin'},status_code=403)
        if TOKEN and not secrets.compare_digest(request.headers.get('x-projectpilot-token',''),TOKEN): return JSONResponse({'detail':'Enter your workspace access token.'},status_code=401)
        if request.method not in ('GET','HEAD','OPTIONS') and request.headers.get('x-projectpilot-client')!='workspace': return JSONResponse({'detail':'Workspace client header required'},status_code=403)
        try: size=int(request.headers.get('content-length','0'))
        except ValueError: return JSONResponse({'detail':'Invalid content length'},status_code=400)
        if size>5_000_000: return JSONResponse({'detail':'Request exceeds 5 MB'},status_code=413)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    if path.startswith('/api'): response.headers['Cache-Control']='no-store'
    return response

@app.exception_handler(ValueError)
async def invalid(request,exc): return JSONResponse({'detail':str(exc)},status_code=400)

@api.get('/')
async def health(): return {'message':'ProjectPilot API','status':'ok','mode':'local','paid_calls_enabled':settings()['paid_enabled']}
@api.get('/capabilities')
async def capabilities(): return {'mode':'local','storage':'SQLite','generation':'copy/import, local Ollama, or opt-in OpenRouter','paid_calls_enabled':settings()['paid_enabled'],'cloud_key_configured':bool(os.environ.get('OPENROUTER_API_KEY')),'git':bool(shutil.which('git')),'docker':bool(shutil.which('docker')),'sandbox_image':os.environ.get('PP_SANDBOX_IMAGE',''),'ollama':await providers.models_available()}
@api.get('/projects')
async def list_projects(): return sorted(store.list('projects'),key=lambda d:d['created_at'],reverse=True)
@api.post('/projects')
async def create_project(body:M.ProjectCreate):
    d=body.model_dump();d.update(id=M.new_id(),default_branch='main',current_branch='main',orchestration_status='idle',has_master_plan=False,has_delegation_plan=False,approved_plan_id=None,created_at=M.now_iso(),updated_at=M.now_iso(),mode='local')
    ws.ensure(d['id']);store.save('projects',d);activity(d['id'],'info','Project created in its own managed workspace');return d
@api.get('/projects/{pid}')
async def project(pid:str): return get('projects',pid)
@api.patch('/projects/{pid}')
async def patch_project(pid:str,body:M.ProjectUpdate):
    async with locks[pid]: return update_project(pid,**body.model_dump(exclude_none=True))
@api.delete('/projects/{pid}')
async def archive_project(pid:str):
    async with locks[pid]:
        update_project(pid,status='archived');activity(pid,'info','Project archived; source and history retained');return {'ok':True,'archived':True}

@api.get('/projects/{pid}/master-plan')
async def master(pid:str): get('projects',pid);return latest('master_plans',pid)
@api.get('/projects/{pid}/plan-versions')
async def versions(pid:str): get('projects',pid);return sorted(store.list('master_plans',pid),key=lambda x:x['created_at'],reverse=True)
@api.post('/projects/{pid}/master-plan/generate')
async def generate_master(pid:str):
    async with locks[pid]:
        p=get('projects',pid);d=planning.build_plan(p);store.save('master_plans',d);update_project(pid,has_master_plan=True);activity(pid,'plan','Created a brief-based draft; no model call');return d
@api.post('/projects/{pid}/master-plan/import')
async def import_master(pid:str,body:M.PlanImport):
    async with locks[pid]:
        d=planning.build_plan(get('projects',pid),body.model_dump());store.save('master_plans',d);update_project(pid,has_master_plan=True);activity(pid,'plan','Imported a new draft plan');return d
@api.post('/projects/{pid}/master-plan/{plan_id}/adopt')
async def adopt(pid:str,plan_id:str):
    async with locks[pid]:
        p=get('projects',pid);plan=get('master_plans',plan_id)
        if plan['project_id']!=pid: raise HTTPException(404,'Plan not found')
        if plan['source_hash']!=planning.source_hash(p): raise ValueError('Brief changed since this draft. Create a current draft.')
        if any(t['status']=='running' for t in store.list('tasks',pid)): raise ValueError('Stop the running task before adopting a plan.')
        plan.update(status='adopted',adopted_at=M.now_iso());p.update(approved_plan_id=plan_id,has_master_plan=True,has_delegation_plan=False,updated_at=M.now_iso())
        store.save_many([('master_plans',plan),('projects',p)]);activity(pid,'plan','Adopted plan version '+plan_id[:8]);return plan
@api.get('/projects/{pid}/planning-prompt')
async def planning_prompt(pid:str):
    p=get('projects',pid)
    prompt=f"Create an implementation plan for {p['name']}.\nBrief:\n{p['brief']}\nStack: {p['tech_stack']}\nPreserve existing working behavior. Use small verifiable tasks, explicit acceptance criteria, and dependencies. Human approval is required before committing or publishing. Return JSON matching this schema:\n"+json.dumps(M.PlanImport.model_json_schema())
    return {'prompt':prompt}
@api.get('/projects/{pid}/delegation-plan')
async def get_delegation(pid:str): get('projects',pid);return latest('delegation_plans',pid)
@api.post('/projects/{pid}/delegation-plan/generate')
async def generate_delegation(pid:str):
    async with locks[pid]:
        p=get('projects',pid)
        if not p.get('approved_plan_id'): raise ValueError('Adopt a master plan first')
        m=get('master_plans',p['approved_plan_id'])
        if m['source_hash']!=planning.source_hash(p): raise ValueError('Adopt a plan for the current brief first')
        d=planning.delegation(p,m);store.save('delegation_plans',d);update_project(pid,has_delegation_plan=True);return d
@api.post('/projects/{pid}/delegation-plan/materialize')
async def materialize(pid:str):
    async with locks[pid]:
        p=get('projects',pid);d=latest('delegation_plans',pid)
        if not d or d['plan_id']!=p.get('approved_plan_id'): raise ValueError('Generate delegation from the adopted plan first')
        old=store.list('tasks',pid);mapping={};created=0;items=[]
        for dt in d['tasks']:
            found=next((t for t in old if t.get('plan_id')==d['plan_id'] and t.get('source_number')==dt['number']),None)
            if found: mapping[str(dt['number'])]=found['id'];continue
            body=M.TaskCreate(title=dt['name'],description=dt['description'],tier=dt['recommended_tier'],model_prompt=dt['model_prompt'],allowed_files=dt['allowed_files'],blocked_files=dt['blocked_files'],acceptance_criteria=dt['acceptance_criteria'],verification_commands=dt['verification_commands'],git_commit_message=dt['git_commit_message'])
            t=make_task(pid,body,plan_id=d['plan_id'],source_number=dt['number']);mapping[str(dt['number'])]=t['id'];items.append((t,dt));created+=1
        for t,dt in items: t['dependencies']=[mapping[x] for x in dt['dependencies']];store.save('tasks',t)
        for t in old:
            if t.get('plan_id') and t['plan_id']!=d['plan_id'] and t['status']!='merged': t['status']='superseded';store.save('tasks',t)
        activity(pid,'info',f'Added {created} tasks with full prompts, criteria and dependencies');return {'created':created}

@api.get('/projects/{pid}/tasks')
async def tasks(pid:str): get('projects',pid);return sorted(store.list('tasks',pid),key=lambda t:t['number'])
@api.post('/projects/{pid}/tasks')
async def create_task(pid:str,body:M.TaskCreate):
    async with locks[pid]:
        get('projects',pid)
        if 'tier' not in body.model_fields_set: body.tier=settings()['default_tier']
        for dep in body.dependencies:
            if get('tasks',dep)['project_id']!=pid: raise ValueError('Dependency belongs to another project')
        t=make_task(pid,body);activity(pid,'info','Task created: '+t['title']);return t
@api.get('/tasks/{tid}')
async def task(tid:str): return get('tasks',tid)
@api.patch('/tasks/{tid}')
async def patch_task(tid:str,body:M.TaskUpdate):
    t=get('tasks',tid)
    async with locks[t['project_id']]:
        t=get('tasks',tid)
        if t['status'] not in ('queued','failed','rejected'): raise ValueError('Only queued, failed or rejected tasks can be edited')
        t.update(body.model_dump(exclude_none=True),latest_verification_id=None,updated_at=M.now_iso(),status='queued');store.save('tasks',t);return t
@api.post('/tasks/{tid}/assign-tier')
async def assign(tid:str,body:M.AssignTierBody):
    t=get('tasks',tid)
    async with locks[t['project_id']]:
        t=get('tasks',tid)
        if t['status'] not in ('queued','failed','rejected'): raise ValueError('Cannot change the route for an active or completed task')
        t['tier']=body.tier;store.save('tasks',t);return t
@api.get('/tasks/{tid}/prompt')
async def prompt(tid:str): return task_prompt(get('tasks',tid))
@api.get('/tasks/{tid}/diff')
async def diff(tid:str):
    t=get('tasks',tid);return store.get('diffs',t['diff_id']) if t.get('diff_id') else None
@api.get('/tasks/{tid}/verifications')
async def task_verifications(tid:str):
    t=get('tasks',tid);return sorted([v for v in store.list('verifications',t['project_id']) if v['task_id']==tid],key=lambda v:v['created_at'],reverse=True)
@api.get('/tasks/{tid}/runs')
async def task_runs(tid:str):
    t=get('tasks',tid);return sorted([v for v in store.list('runs',t['project_id']) if v['task_id']==tid],key=lambda v:v['created_at'],reverse=True)

async def verify_impl(t):
    task_ready(t);run=candidate_for(t)
    checks=await asyncio.to_thread(check_source,ws.candidate(t['project_id'],run['id']),t['verification_commands'])
    ws.assert_current(run)
    status='passed' if all(c['status']=='passed' for c in checks) else 'failed'
    ver={'id':M.new_id(),'project_id':t['project_id'],'task_id':t['id'],'run_id':run['id'],'candidate_hash':run['candidate_hash'],'contract_hash':planning.digest({k:t[k] for k in ['acceptance_criteria','verification_commands','allowed_files','blocked_files']}),'status':status,'checks':checks,'created_at':M.now_iso()}
    t.update(status='pending_approval' if status=='passed' else 'failed',latest_verification_id=ver['id'],updated_at=M.now_iso())
    store.save_many([('verifications',ver),('tasks',t)]);activity(t['project_id'],'verify',f"Verification {status}: {t['title']}");update_project(t['project_id'],orchestration_status='awaiting_approval' if status=='passed' else 'idle');return ver

async def apply_impl(t,body,usage=None,meter_id=None):
    task_ready(t)
    if t['tier']=='human_review': raise ValueError('Human-review tasks use Complete review, not code changes')
    # Revisions are cumulative: merge the provided changed files into the current candidate.
    changes=[f.model_dump() for f in body.files]
    if t.get('run_id'):
        previous=get('runs',t['run_id']);ws.assert_current(previous)
        baseline=files_at(ws.repo(t['project_id']));current=files_at(ws.candidate(t['project_id'],previous['id']))
        carried={p: {'path':p,'content':data.decode()} for p,data in current.items() if baseline.get(p)!=data}
        for p in baseline.keys()-current.keys(): carried[p]={'path':p,'content':None}
        for f in changes: carried[f['path']]=f
        changes=list(carried.values())
    run=await asyncio.to_thread(ws.changes,t['project_id'],t,changes)
    run.update(summary=body.summary,usage=usage or {'model_name':'manual import','tokens_in':0,'tokens_out':0,'cost':None,'cost_status':'external_unknown'})
    d={'id':M.new_id(),'project_id':t['project_id'],'task_id':t['id'],'run_id':run['id'],'branch':run['branch'],'files':run['files'],'summary':body.summary,'created_at':M.now_iso(),'candidate_hash':run['candidate_hash']}
    t.update(run_id=run['id'],diff_id=d['id'],branch=run['branch'],status='ready',latest_verification_id=None,updated_at=M.now_iso())
    meter={'id':meter_id or M.new_id(),'project_id':t['project_id'],'task_id':t['id'],'task_title':t['title'],'tier':(usage or {}).get('tier','local') if usage else t['tier'],'created_at':M.now_iso(),'latency_ms':0,'status':'success',**run['usage']}
    store.save_many([('runs',run),('diffs',d),('tasks',t),('model_runs',meter)])
    update_project(t['project_id'],current_branch=run['branch'],orchestration_status='executing');activity(t['project_id'],'edit',body.summary,{'task_id':t['id'],'run_id':run['id']})
    if settings()['auto_verify']: await verify_impl(t)
    return {'diff':d,'model_run':meter,'content':body.summary,'run':run}

@api.post('/tasks/{tid}/import')
async def import_changes(tid:str,body:M.ImportChanges):
    t=get('tasks',tid)
    async with locks[t['project_id']]:
        t=get('tasks',tid)
        if t['status']=='running': raise ValueError('Stop the running generation before importing a result')
        return await apply_impl(t,body)

def save_receipt(t,jobid,meter,status):
    record={'id':jobid,'project_id':t['project_id'],'task_id':t['id'],'task_title':t['title'],'created_at':get('runs',jobid)['created_at'],'status':status,**meter}
    store.save('model_runs',record)
    bill=store.get('billing',jobid)
    if bill and meter.get('cost') is not None:
        bill.update(status='settled',actual_usd=meter['cost']);store.save('billing',bill)
    return record

async def generation_job(tid,jobid,prompt_data,s,q):
    t=get('tasks',tid);pid=t['project_id'];meter=None
    try:
        body,meter=await (providers.generate_cloud(prompt_data['prompt'],s,q) if q['kind']=='cloud' else providers.generate(prompt_data['prompt'],s))
        save_receipt(t,jobid,meter,'received')
        async with locks[pid]:
            t=get('tasks',tid)
            if t.get('job_id')!=jobid or t['status']!='running': return
            await apply_impl(t,body,meter,meter_id=jobid)
        job=get('runs',jobid);job.update(status='completed',usage=meter);store.save('runs',job)
    except (Exception,asyncio.CancelledError) as e:
        cancelled=isinstance(e,asyncio.CancelledError)
        message='Generation cancelled. A provider request already sent may still be billed.' if cancelled else str(e)[:1000]
        meter=meter or getattr(e,'meter',None) or {'model_name':q['model'],'tier':q.get('tier','local'),'tokens_in':0,'tokens_out':0,'cost':None,'cost_status':'failed_usage_unknown','latency_ms':0}
        save_receipt(t,jobid,meter,'cancelled' if cancelled else 'failed')
        job=get('runs',jobid);job.update(status='cancelled' if cancelled else 'failed',error=message);store.save('runs',job)
        t=get('tasks',tid)
        if t.get('job_id')==jobid: t.update(status='failed',latest_verification_id=None);store.save('tasks',t)
        activity(pid,'error',message)
    finally: jobs.pop(jobid,None)

@api.get('/models/cloud')
async def cloud_models(): return await providers.cloud_models()

@api.post('/tasks/{tid}/estimate')
async def estimate(tid:str,body:M.RunEditBody):
    t=get('tasks',tid)
    async with locks[t['project_id']]:
        t=get('tasks',tid);task_ready(t)
        if t.get('run_id'): candidate_for(t)
        return await economy.quote(t,settings(),task_prompt(t,body.prompt),fingerprint(files_at(ws.ensure(t['project_id']))),store)

@api.post('/tasks/{tid}/run-edit')
async def run_edit(tid:str,body:M.RunEditBody):
    t=get('tasks',tid)
    async with dispatch_lock,locks[t['project_id']]:
        t=get('tasks',tid);task_ready(t);s=settings()
        if t['status']=='running': raise HTTPException(409,'This task is already running')
        if t['attempts']>=s['max_attempts']: raise ValueError('Attempt limit reached. Use a focused manual repair or create a revised task.')
        if any(x['status']=='running' for x in store.list('tasks')): raise HTTPException(409,'One generation at a time keeps usage bounded.')
        if t.get('run_id'): candidate_for(t)
        data=task_prompt(t,body.prompt)
        q=get('quotes',body.quote_id) if body.quote_id else None
        if not q: raise ValueError('Get an estimate before running a model.')
        if q['task_id']!=tid or q['consumed'] or q['expires_at']<time.time() or q['context_hash']!=data['context_hash'] or q['settings_hash']!=planning.digest(s) or q['baseline']!=fingerprint(files_at(ws.ensure(t['project_id']))): raise ValueError('Estimate expired or task/source/settings changed. Get a fresh estimate.')
        if q['kind']=='manual': raise ValueError(q['reason'])
        if q['kind']=='cloud': economy.assert_budget(store,s,q['estimated_usd'])
        jobid=M.new_id();q['consumed']=True
        job={'id':jobid,'task_id':tid,'project_id':t['project_id'],'status':'generating','created_at':M.now_iso(),'context_hash':data['context_hash'],'quote_id':q['id']}
        t.update(status='running',job_id=jobid,attempts=t['attempts']+1,latest_verification_id=None)
        records=[('runs',job),('tasks',t),('quotes',q)]
        if q['kind']=='cloud': records.append(('billing',{'id':jobid,'project_id':t['project_id'],'created_at':M.now_iso(),'status':'reserved','reserved_usd':q['estimated_usd']}))
        store.save_many(records);jobs[jobid]=asyncio.create_task(generation_job(tid,jobid,data,s,q));return {'job_id':jobid,'status':'generating'}
@api.post('/tasks/{tid}/cancel')
async def cancel(tid:str):
    t=get('tasks',tid)
    async with locks[t['project_id']]:
        t=get('tasks',tid)
        if t['status']!='running': raise ValueError('No generation is running')
        job=jobs.get(t.get('job_id'))
        if job: job.cancel()
        t.update(status='failed',latest_verification_id=None);store.save('tasks',t);activity(t['project_id'],'info','Generation cancelled');return t
@api.post('/tasks/{tid}/verify')
async def verify(tid:str):
    t=get('tasks',tid)
    async with locks[t['project_id']]:
        t=get('tasks',tid)
        if t['status']=='running': raise ValueError('Wait for the generation to finish')
        return await verify_impl(t)
@api.post('/tasks/{tid}/approve')
async def approve(tid:str,body:M.Approval):
    t=get('tasks',tid)
    async with locks[t['project_id']]:
        t=get('tasks',tid);task_ready(t);run=candidate_for(t)
        if t['status']!='pending_approval': raise ValueError('The current candidate must pass verification first')
        ver=get('verifications',body.verification_id)
        contract=planning.digest({k:t[k] for k in ['acceptance_criteria','verification_commands','allowed_files','blocked_files']})
        if ver['id']!=t['latest_verification_id'] or ver['task_id']!=tid or ver['run_id']!=run['id'] or ver['status']!='passed' or ver['candidate_hash']!=run['candidate_hash'] or body.candidate_hash!=run['candidate_hash'] or ver['contract_hash']!=contract: raise ValueError('Verification does not match this candidate and task contract')
        if sorted(set(body.checked_criteria))!=list(range(len(t['acceptance_criteria']))): raise ValueError('Review every acceptance criterion before approval')
        op={'id':M.new_id(),'project_id':t['project_id'],'task_id':tid,'run_id':run['id'],'status':'committing','candidate_hash':run['candidate_hash'],'verification_id':ver['id'],'actor':settings()['developer_name'],'note':body.note,'created_at':M.now_iso()}
        store.save('approvals',op)
        sha=await asyncio.to_thread(ws.commit,run,t['git_commit_message'] or 'Apply '+t['title'])
        t.update(status='merged',commit_hash=sha,updated_at=M.now_iso());op.update(status='committed',commit_hash=sha);run['status']='committed'
        store.save_many([('tasks',t),('approvals',op),('runs',run)])
        update_project(t['project_id'],current_branch='main',orchestration_status='idle');activity(t['project_id'],'merge','Approved and committed '+sha[:10],{'task_id':tid});return t
@api.post('/tasks/{tid}/review')
async def review(tid:str,body:M.HumanReview):
    t=get('tasks',tid)
    async with locks[t['project_id']]:
        t=get('tasks',tid);task_ready(t)
        if t['tier']!='human_review': raise ValueError('This task needs candidate verification and approval')
        if sorted(set(body.checked_criteria))!=list(range(len(t['acceptance_criteria']))): raise ValueError('Review every criterion')
        t.update(status='merged',review_note=body.note,reviewed_at=M.now_iso(),reviewed_source=ws.head(t['project_id']));store.save('tasks',t);activity(t['project_id'],'approve','Human review completed: '+body.note,{'task_id':tid});return t
@api.post('/tasks/{tid}/reject')
async def reject(tid:str):
    t=get('tasks',tid)
    async with locks[t['project_id']]:
        t=get('tasks',tid)
        if t['status'] in ('running','merged','superseded'): raise ValueError('This task cannot be rejected in its current state')
        t.update(status='rejected',latest_verification_id=None);store.save('tasks',t);activity(t['project_id'],'reject','Candidate rejected; source unchanged');return t

@api.get('/projects/{pid}/diffs')
async def diffs(pid:str): get('projects',pid);return sorted(store.list('diffs',pid),key=lambda d:d['created_at'],reverse=True)
@api.get('/projects/{pid}/verifications')
async def verifications(pid:str): get('projects',pid);return sorted(store.list('verifications',pid),key=lambda d:d['created_at'],reverse=True)
@api.get('/projects/{pid}/files')
async def file_list(pid:str):
    get('projects',pid);return {'files':[{'path':p,'bytes':len(d)} for p,d in files_at(ws.ensure(pid)).items()],'head':ws.head(pid)}
@api.post('/projects/{pid}/import-source')
async def import_source(pid:str,request:Request):
    # A source ZIP becomes a reviewable candidate, never an implicit commit.
    async with locks[pid]:
        p=get('projects',pid)
        if p['status']=='archived': raise ValueError('Restore the archived project first')
        raw=bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw)>5_000_000: raise HTTPException(413,'ZIP exceeds 5 MB')
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                entries=[i for i in z.infolist() if not i.is_dir()]
                if len(entries)>3000 or sum(i.file_size for i in entries)>20_000_000: raise ValueError('ZIP expands beyond the source limit (20 MB / 3000 entries)')
                from workspaces import IGNORED
                parts=[i.filename.split('/') for i in entries]
                common=parts[0][0] if parts and all(len(x)>1 and x[0]==parts[0][0] for x in parts) else None
                changes=[];skipped=[]
                for i in entries:
                    if (i.external_attr>>16)&0o170000==0o120000: raise ValueError('ZIP symlinks are not supported')
                    name=i.filename[len(common)+1:] if common else i.filename
                    if any(x in IGNORED or x=='__MACOSX' for x in name.split('/')): skipped.append(name);continue
                    safe_path(name)
                    if i.file_size>500000: raise ValueError('Source file exceeds 500 KB: '+name)
                    try: content=z.read(i).decode('utf-8')
                    except UnicodeDecodeError: raise ValueError('This source importer supports UTF-8 text, including SVG. Remove binary assets before import: '+name)
                    changes.append({'path':name,'content':content})
                body=M.ImportChanges(summary='Import existing project source for review',files=changes)
        except zipfile.BadZipFile: raise ValueError('Upload a valid source ZIP')
        t=make_task(pid,M.TaskCreate(title='Review imported source',acceptance_criteria=['The imported files belong to this project.','Startup steps and intended behavior have been reviewed.']))
        result=await apply_impl(t,body);result.update(task_id=t['id'],skipped_files=skipped);return result

@api.get('/projects/{pid}/history')
async def history(pid:str):
    get('projects',pid)
    if ws.head(pid)=='EMPTY': return []
    return [{'hash':line.split('\t',2)[0],'date':line.split('\t',2)[1],'message':line.split('\t',2)[2]} for line in git(ws.repo(pid),'log','--format=%H%x09%aI%x09%s').splitlines()]
@api.get('/projects/{pid}/export')
async def export(pid:str): get('projects',pid);return Response(ws.export(pid),media_type='application/zip',headers={'Content-Disposition':'attachment; filename="project-source.zip"'})
@api.post('/projects/{pid}/restore')
async def restore(pid:str,body:M.RestoreBody):
    async with locks[pid]:
        get('projects',pid)
        allowed=[h['hash'] for h in await history(pid)]
        if body.commit_hash not in allowed: raise ValueError('Commit not in this project history')
        data={}
        for name in git(ws.repo(pid),'ls-tree','-r','--name-only',body.commit_hash).splitlines():
            safe_path(name)
            data[name]=git(ws.repo(pid),'show',body.commit_hash+':'+name,raw=True)
        current=files_at(ws.repo(pid));changes=[{'path':p,'content':data.get(p)} for p in set(current)|set(data)]
        t=make_task(pid,M.TaskCreate(title='Restore '+body.commit_hash[:10],acceptance_criteria=['This earlier version is the intended restoration.']))
        return await apply_impl(t,M.ImportChanges(summary='Restore earlier version as a reviewable candidate',files=changes))

@api.get('/projects/{pid}/previews')
async def previews(pid:str): get('projects',pid);return sorted(store.list('previews',pid),key=lambda d:d['created_at'],reverse=True)
@api.post('/projects/{pid}/previews/launch')
async def launch_preview(pid:str,task_id:str|None=None):
    async with locks[pid]:
        p=get('projects',pid);run=None
        if task_id:
            t=get('tasks',task_id)
            if t['project_id']!=pid: raise HTTPException(404,'Task not in this project')
            run=get('runs',t['run_id']) if t.get('run_id') else None
        root=ws.candidate(pid,run['id']) if run else ws.ensure(pid)
        if any(p.endswith(('.jsx','.tsx','.ts')) for p in files_at(root)):
            raise ValueError('Framework source needs a compiled static build. Export source and build it using its documented commands.')
        if not (root/'index.html').is_file(): raise ValueError('No static index.html in this version. Export source to run a framework app, or supply a static build.')
        id=secrets.token_urlsafe(24)
        sess={'id':id,'project_id':pid,'task_id':task_id,'run_id':run['id'] if run else None,'branch':run['branch'] if run else 'main','status':'running','url':'/render/'+id+'/index.html','created_at':M.now_iso(),'candidate_hash':fingerprint(files_at(root))}
        store.save('previews',sess);activity(pid,'preview','Opened actual static candidate preview');return sess
@api.post('/previews/{id}/stop')
async def stop_preview(id:str): p=get('previews',id);p['status']='stopped';store.save('previews',p);return p
@app.get('/render/{id}/{path:path}')
async def render(id:str,path:str):
    s=get('previews',id)
    if s['status']!='running': raise HTTPException(410,'Preview stopped')
    try: safe_path(path)
    except ValueError: raise HTTPException(404,'File not found')
    root=ws.candidate(s['project_id'],s['run_id']) if s['run_id'] else ws.repo(s['project_id'])
    if fingerprint(files_at(root))!=s['candidate_hash']: raise HTTPException(409,'Source changed. Launch a new preview.')
    p=root/path
    if not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(root.resolve()): raise HTTPException(404,'File not found')
    headers={'Content-Security-Policy':"sandbox allow-scripts; default-src 'none'; script-src 'unsafe-inline' 'unsafe-eval' http://127.0.0.1:* http://localhost:*; style-src 'unsafe-inline' http://127.0.0.1:* http://localhost:*; img-src data: blob: http://127.0.0.1:* http://localhost:*; font-src data: http://127.0.0.1:* http://localhost:*; connect-src 'none'; form-action 'none'",'Access-Control-Allow-Origin':'*','Cache-Control':'no-store'}
    return FileResponse(p,headers=headers)

@api.get('/settings')
async def get_settings(): return settings()
@api.patch('/settings')
async def save_settings(body:M.SettingsUpdate):
    d={'id':'global',**body.model_dump(),'updated_at':M.now_iso()};store.save('settings',d);return d
@api.get('/tiers')
async def tiers(): return {k:{**v,'tier':k} for k,v in providers.TIER_META.items()}

def usage_summary(pid=None):
    all_runs=store.list('model_runs',pid);month=M.now_iso()[:7];runs=[r for r in all_runs if r['created_at'].startswith(month)]
    by={}
    for r in runs:
        entry=by.setdefault(r['tier'],{'tier':r['tier'],'runs':0,'cost':0,'tokens':0})
        entry['runs']+=1;entry['cost']+=r.get('cost') or 0;entry['tokens']+=r.get('tokens_in',0)+r.get('tokens_out',0)
    return {'period':month,'total_runs':len(runs),'total_cost':sum(r.get('cost') or 0 for r in runs),'total_tokens':sum(r.get('tokens_in',0)+r.get('tokens_out',0) for r in runs),'unknown_cost_runs':sum(r.get('cost') is None for r in runs),'by_tier':list(by.values()),'recent_runs':sorted(all_runs,key=lambda r:r['created_at'],reverse=True)[:50],'paid_calls_enabled':settings()['paid_enabled'],'reserved_usd':economy.reserved(store,month),'monthly_budget_usd':settings()['monthly_budget_usd'],'global_known_cost':economy.spent(store,month),'cost_note':'Known API charges only. Manual tool charges and local compute costs are unknown. Unresolved paid requests retain a conservative reservation.'}
@api.get('/usage')
async def usage(): return usage_summary()
@api.get('/projects/{pid}/usage')
async def project_usage(pid:str): get('projects',pid);return usage_summary(pid)
@api.get('/projects/{pid}/activity')
async def project_activity(pid:str): get('projects',pid);return sorted(store.list('activity',pid),key=lambda a:a['created_at'],reverse=True)
@api.get('/activity')
async def all_activity(): return sorted(store.list('activity'),key=lambda a:a['created_at'],reverse=True)
@api.get('/dashboard')
async def dashboard(project_id:str|None=None):
    projs=[p for p in await list_projects() if p['status']!='archived'];p=next((p for p in projs if p['id']==project_id),projs[0] if projs else None)
    ts=[t for t in store.list('tasks',p['id']) if t['status']!='superseded'] if p else [];by_status={};by_tier={}
    for t in ts: by_status[t['status']]=by_status.get(t['status'],0)+1;by_tier[t['tier']]=by_tier.get(t['tier'],0)+1
    u=usage_summary(p['id']) if p else usage_summary()
    return {'active_projects':[p for p in projs if p['status']=='active'],'current_project':p,'current_task':next((t for t in ts if t['status'] in ('running','ready','pending_approval')),None),'tasks_by_status':by_status,'tasks_by_tier':by_tier,'total_tasks':len(ts),'pending_approvals':[t for t in ts if t['status']=='pending_approval'],'recent_runs':u['recent_runs'][:8],'verification_failures':[v for v in store.list('verifications',p['id']) if v['status']=='failed'] if p else [],'estimated_cost':0,'actual_cost':u['total_cost'],'preview_sessions':[v for v in store.list('previews',p['id']) if v['status']=='running'] if p else [],'recent_activity':(await project_activity(p['id']))[:12] if p else []}
@api.get('/backup')
async def backup():
    # Single worker snapshot: don't interleave a candidate mutation with backup.
    if jobs or any(lock.locked() for lock in locks.values()): raise HTTPException(409,'Wait for the active operation before backing up')
    with tempfile.TemporaryDirectory() as tmp:
        dbfile=Path(tmp)/'projectpilot.sqlite3';store.backup(dbfile);out=io.BytesIO()
        with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
            z.write(dbfile,'data/projectpilot.sqlite3')
            for p in (DATA/'projects').rglob('*'):
                if p.is_file() and not p.is_symlink(): z.write(p,'data/projects/'+p.relative_to(DATA/'projects').as_posix())
        return Response(out.getvalue(),media_type='application/zip',headers={'Content-Disposition':'attachment; filename="projectpilot-backup.zip"'})

app.include_router(api)
DIST=ROOT.parent/'frontend'/'dist'
if DIST.exists():
    app.mount('/assets',StaticFiles(directory=DIST/'assets'),name='assets')
    @app.get('/{path:path}')
    async def frontend(path:str):
        if path.startswith(('api/','render/')): raise HTTPException(404)
        return FileResponse(DIST/'index.html')

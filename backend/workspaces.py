"""Managed source candidates, real diffs and approved local Git commits.

No arbitrary source code executes on the host. Optional build commands use Docker.
"""
import ast
import difflib
import fnmatch
import hashlib
from html.parser import HTMLParser
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path, PurePosixPath
from models import new_id, now_iso

IGNORED = {'.git','node_modules','.venv','venv','__pycache__','.cache','dist','build'}
PROTECTED = {'.git','.env','.ssh','.aws','.npmrc','.pypirc','credentials.json'}
MAX_SOURCE = 20_000_000

def safe_path(path):
    p=PurePosixPath(path)
    if not path or '\\' in path or '\x00' in path or ':' in path or p.is_absolute() or any(x in ('','..','.') for x in path.split('/')):
        raise ValueError('Only relative project file paths are allowed')
    parts=[x.casefold() for x in p.parts]
    if any(x.endswith((' ','.')) or x.split('.')[0] in {'con','prn','aux','nul',*[f'com{i}' for i in range(1,10)],*[f'lpt{i}' for i in range(1,10)]} for x in parts):
        raise ValueError('Ambiguous or reserved filesystem path')
    if any(x in PROTECTED or x.startswith('.env.') or x.endswith(('.pem','.key')) for x in parts):
        raise ValueError(f'Protected path: {path}')
    if any(x in IGNORED for x in parts): raise ValueError(f'Generated/dependency folder is not source: {path}')
    return p.as_posix()

def match(path, pattern):
    return pattern in ('**','*') or fnmatch.fnmatchcase(path,pattern) or (pattern.startswith('**/') and fnmatch.fnmatchcase(path,pattern[3:]))

def check_scope(path, task):
    safe_path(path)
    if any(match(path,p) for p in task.get('blocked_files',[])): raise ValueError(f'Blocked file: {path}')
    if not any(match(path,p) for p in task.get('allowed_files',[])): raise ValueError(f'File outside task scope: {path}')

def files_at(root):
    result={}; size=0
    if not root.exists(): return result
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:]=[d for d in dirs if d not in IGNORED]
        for d in dirs:
            if (Path(directory)/d).is_symlink(): raise ValueError('Symlink directories are not supported')
        for name in files:
            p=Path(directory)/name
            if p.is_symlink(): raise ValueError('Symlink files are not supported')
            rel=p.relative_to(root).as_posix(); safe_path(rel)
            size+=p.stat().st_size
            if size>MAX_SOURCE: raise ValueError('Project source exceeds the 20 MB local limit')
            result[rel]=p.read_bytes()
    return result

def fingerprint(files):
    h=hashlib.sha256()
    for path, data in sorted(files.items()):
        h.update(path.encode());h.update(b'\0');h.update(hashlib.sha256(data).digest())
    return h.hexdigest()

def write_files(root, files):
    root.mkdir(parents=True,exist_ok=True)
    for path, data in files.items():
        safe_path(path); p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)

def git(root, *args, check=True, raw=False):
    env={k:v for k,v in os.environ.items() if k in ('PATH','SYSTEMROOT','TMPDIR','TEMP')}
    env.update({'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':os.devnull,'GIT_TERMINAL_PROMPT':'0'})
    r=subprocess.run(['git','-c','core.hooksPath='+os.devnull,'-c','commit.gpgsign=false','-c','user.name=ProjectPilot','-c','user.email=local@projectpilot.invalid','-C',str(root),*args],capture_output=True,text=True,timeout=30,env=env)
    if check and r.returncode: raise ValueError(r.stderr.strip() or 'Git operation failed')
    return r.stdout if raw else r.stdout.strip()

class Workspaces:
    def __init__(self, root): self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
    def project_root(self,pid): return self.root/pid
    def repo(self,pid): return self.project_root(pid)/'source'
    def candidate(self,pid,rid): return self.project_root(pid)/'candidates'/rid
    def ensure(self,pid):
        repo=self.repo(pid);repo.mkdir(parents=True,exist_ok=True)
        if not (repo/'.git').exists(): git(repo,'init','-b','main')
        return repo
    def head(self,pid): return git(self.ensure(pid),'rev-parse','--verify','HEAD',check=False) or 'EMPTY'
    def changes(self,pid,task,changes):
        base=files_at(self.ensure(pid)); new=dict(base)
        seen=set()
        for f in changes:
            p=f['path'];check_scope(p,task)
            if p in seen: raise ValueError(f'Duplicate path: {p}')
            seen.add(p)
            if f['content'] is None: new.pop(p,None)
            else: new[p]=f['content'].encode()
        if sum(map(len,new.values()))>MAX_SOURCE: raise ValueError('Project exceeds 20 MB')
        diff=self.diff(base,new)
        if not diff: raise ValueError('No source changes were supplied')
        rid=new_id();root=self.candidate(pid,rid);write_files(root,new)
        return {'id':rid,'project_id':pid,'task_id':task['id'],'created_at':now_iso(),'status':'ready','base_sha':self.head(pid),'base_hash':fingerprint(base),'candidate_hash':fingerprint(new),'branch':'candidate/'+rid[:8],'files':diff}
    @staticmethod
    def diff(old,new):
        result=[]
        for p in sorted(set(old)|set(new)):
            if old.get(p)==new.get(p): continue
            try:
                a=old.get(p,b'').decode().splitlines(keepends=True);b=new.get(p,b'').decode().splitlines(keepends=True)
                lines=list(difflib.unified_diff(a,b,fromfile='a/'+p,tofile='b/'+p))
                adds=sum(x.startswith('+') and not x.startswith('+++') for x in lines)
                dels=sum(x.startswith('-') and not x.startswith('---') for x in lines)
                hunk=''.join(lines)
            except UnicodeDecodeError:
                adds=dels=0;hunk='Binary asset changed'
            result.append({'path':p,'additions':adds,'deletions':dels,'hunk':hunk})
        return result
    def assert_current(self,run):
        if self.head(run['project_id'])!=run['base_sha'] or fingerprint(files_at(self.repo(run['project_id'])))!=run['base_hash']:
            raise ValueError('Approved source changed. Create a new candidate from the latest source.')
        if fingerprint(files_at(self.candidate(run['project_id'],run['id'])))!=run['candidate_hash']:
            raise ValueError('Candidate changed since it was recorded. Import and verify it again.')
    def commit(self,run,message):
        self.assert_current(run)
        pid=run['project_id']; parent=self.project_root(pid)
        staging=parent/('commit-'+run['id']);backup=parent/('previous-'+run['id'])
        if staging.exists(): shutil.rmtree(staging)
        shutil.copytree(self.repo(pid),staging)
        for child in staging.iterdir():
            if child.name!='.git':
                if child.is_dir(): shutil.rmtree(child)
                else: child.unlink()
        write_files(staging,files_at(self.candidate(pid,run['id'])))
        git(staging,'add','--all');git(staging,'commit','-m',message or 'Apply reviewed ProjectPilot task')
        sha=git(staging,'rev-parse','HEAD')
        self.repo(pid).rename(backup)
        try: staging.rename(self.repo(pid))
        except BaseException:
            backup.rename(self.repo(pid));raise
        # Keep previous repository snapshot for crash recovery and backup.
        return sha
    def export(self,pid,run=None):
        root=self.candidate(pid,run['id']) if run else self.repo(pid)
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
            for p,data in files_at(root).items(): z.writestr(p,data)
        return out.getvalue()

def check_source(root, commands):
    """Parse-only host checks; optional commands run in an explicit Docker sandbox."""
    result=[];files=files_at(root)
    def add(name,status,output,command=None,duration=0): result.append({'name':name,'status':status,'output':output,'command':command or name,'duration_ms':duration})
    add('source','passed' if files else 'failed',f'{len(files)} source files; no protected paths or symlinks.')
    for path,data in files.items():
        if path.endswith(('.json','.py','.js','.mjs','.cjs')):
            start=time.monotonic()
            try:
                text=data.decode()
                if path.endswith('.json'): json.loads(text)
                elif path.endswith('.py'): ast.parse(text,filename=path)
                elif shutil.which('node'):
                    # stdin module parsing supports ESM .js without executing imports or code.
                    r=subprocess.run(['node','--input-type='+('commonjs' if path.endswith('.cjs') else 'module'),'--check'],input=text,capture_output=True,text=True,timeout=15)
                    if r.returncode: raise ValueError(r.stderr[:5000])
                else:
                    add('syntax:'+path,'blocked','Install Node.js to check JavaScript syntax.');continue
                add('syntax:'+path,'passed','Syntax parsed; this does not prove runtime behavior.',duration=int((time.monotonic()-start)*1000))
            except Exception as e: add('syntax:'+path,'failed',str(e)[:5000])
    class Scripts(HTMLParser):
        def __init__(self): super().__init__();self.script=None;self.blocks=[]
        def handle_starttag(self,tag,attrs):
            attrs=dict(attrs)
            if tag=='script' and not attrs.get('src') and attrs.get('type','').lower() in ('','module','text/javascript','application/javascript'): self.script=''
        def handle_data(self,data):
            if self.script is not None:self.script+=data
        def handle_endtag(self,tag):
            if tag=='script' and self.script is not None:self.blocks.append(self.script);self.script=None
    for path,data in files.items():
        if path.endswith('.html'):
            try:
                parser=Scripts();parser.feed(data.decode())
                if parser.script is not None: raise ValueError('Unclosed script element')
                for i,script in enumerate(parser.blocks):
                    if not shutil.which('node'): add('inline-script:'+path,'blocked','Install Node.js for inline JavaScript checks.');continue
                    r=subprocess.run(['node','--input-type=module','--check'],input=script,capture_output=True,text=True,timeout=15)
                    add('inline-script:'+path+':'+str(i+1),'passed' if r.returncode==0 else 'failed',r.stderr[:5000] or 'Inline script syntax parsed; behavior still needs review.')
            except Exception as e:add('html:'+path,'failed',str(e)[:5000])
    requires_build=any(p.endswith(('.jsx','.tsx','.ts')) for p in files) or 'package.json' in files
    if requires_build and not commands: add('runtime','blocked','This project needs a real build command. Add verification_commands and enable Docker checks, or supply a static HTML/CSS/JS project.')
    for command in commands:
        image=os.environ.get('PP_SANDBOX_IMAGE','')
        if not image or not shutil.which('docker'):
            add('build','blocked','Docker checks are not configured. See README: PP_SANDBOX_IMAGE.',command);continue
        if len(command)>500: add('build','failed','Command exceeds maximum length.',command);continue
        name='pp-check-'+new_id()[:12];started=time.monotonic()
        try:
            with tempfile.TemporaryDirectory(prefix='pp-check-') as tmp:
                work=Path(tmp)/'workspace';write_files(work,files)
                r=subprocess.run(['docker','run','--name',name,'--rm','--pull=never','--network=none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--pids-limit=128','--memory=1g','--cpus=1','--tmpfs','/tmp:rw,nosuid,size=256m','--mount',f'type=bind,src={work.resolve()},dst=/workspace','-w','/workspace',image,'sh','-lc',command],capture_output=True,text=True,timeout=120)
                add('build','passed' if r.returncode==0 else 'failed',(r.stdout+r.stderr)[-16000:],command,int((time.monotonic()-started)*1000))
        except Exception as e: add('build','failed',str(e),command)
        finally: subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=10)
    if not any(p.endswith('.html') for p in files) and not requires_build:
        add('preview','passed','No HTML entry point. Source checks only; review the intended runtime separately.')
    return result

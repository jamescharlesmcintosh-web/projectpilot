"""Transparent brief scaffolding and complete, versioned task contracts."""
import hashlib
import json
import re
from models import now_iso, new_id, PlanImport

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def requirements(project):
    return [s.strip(' -•\t') for s in re.split(r'\n+|(?<=[.!?])\s+', project['brief']) if s.strip(' -•\t')]

def validate_graph(tasks):
    nums = [str(t['number']) for t in tasks]
    if len(set(nums)) != len(nums): raise ValueError('Roadmap numbers must be unique')
    graph = {str(t['number']):t.get('dependencies',[]) for t in tasks}
    visiting, done = set(), set()
    def visit(n):
        if n not in graph: raise ValueError(f'Dependency #{n} does not exist')
        if n in visiting: raise ValueError('Dependency cycle detected')
        if n in done: return
        visiting.add(n)
        for d in graph[n]: visit(d)
        visiting.remove(n); done.add(n)
    for n in graph: visit(n)

def source_hash(project):
    return digest({k:project.get(k) for k in ['brief','tech_stack','project_type']})

def build_plan(project, imported=None):
    req = requirements(project)
    if not req: raise ValueError('Write a project brief before creating a plan')
    if imported:
        content = PlanImport.model_validate(imported).model_dump()
        roadmap = content['roadmap']
    else:
        roadmap = [{'number':1,'title':'Establish the project foundation','objective':f"Create the smallest working foundation for {project['name']} using {project['tech_stack'] or 'the chosen stack'}. Preserve existing working code. Read the complete brief before choosing structure.",'files':['**'],'dependencies':[],'acceptance_criteria':['The project has a runnable entry point and documented startup steps.'],'recommended_tier':'auto','verification_commands':[]}]
        groups = [req[i:i+3] for i in range(0,len(req),3)]
        for group in groups[:45]:
            n=len(roadmap)+1
            roadmap.append({'number':n,'title':group[0][:110],'objective':'Implement or honor these source requirements:\n'+'\n'.join(group),'files':['**'],'dependencies':[str(n-1)],'acceptance_criteria':group,'recommended_tier':'auto','verification_commands':[]})
        if len(groups)>45:
            roadmap[-1]['objective']+='\n'+'\n'.join(s for g in groups[45:] for s in g)
            roadmap[-1]['acceptance_criteria']=['All remaining requirements in the full brief are explicitly covered and reviewed.']
        n=len(roadmap)+1
        roadmap.append({'number':n,'title':'Review the complete result','objective':'Review every requirement against the actual result. Record unresolved limits and decide whether it is ready to export.','files':[],'dependencies':[str(n-1)],'acceptance_criteria':['The requirements are satisfied or unresolved gaps are documented.','The intended user workflow has been manually exercised.'],'recommended_tier':'human_review','verification_commands':[]})
        content={'summary':f"Structured draft for {project['name']}. Requirements below are taken from your brief. This free scaffold is not an AI architecture review; edit or import a tailored plan before adoption.",'roadmap':roadmap}
    validate_graph(roadmap)
    return {'id':new_id(),'project_id':project['id'],'status':'draft','created_at':now_iso(),'source_hash':source_hash(project),'generator':'imported' if imported else 'brief-scaffold',
      'summary':content['summary'],'recommended_stack':[s.strip() for s in project.get('tech_stack','').split(',') if s.strip()],
      'folder_structure':'Chosen after inspecting the existing source.',
      'component_architecture':['Preserve reusable components and approved design decisions.'],
      'page_structure':[],'data_model':[],'animation_architecture':[],'scroll_chapter_pattern':'',
      'responsive_strategy':'Review at mobile and desktop sizes where applicable.',
      'image_performance_strategy':'Use project-provided assets; avoid unnecessary regeneration.',
      'accessibility_requirements':['Keyboard access, descriptive labels, and readable contrast.'],
      'form_strategy':'Only implement forms and persistence required by the brief.',
      'seo_requirements':[], 'git_checkpoint_strategy':'Work on a separate candidate. Commit only after checks and your explicit approval.',
      'testing_strategy':'Run actual available checks. Missing runtime checks are reported, not fabricated.',
      'deployment_strategy':'Export reviewed source. Publishing is a separate explicit action.', 'roadmap':roadmap}

def delegation(project, plan):
    tasks=[]
    for r in plan['roadmap']:
        tasks.append({'number':r['number'],'name':r['title'],'description':r['objective'],
          'recommended_tier':r['recommended_tier'],'model_prompt':f"Project: {project['name']}\nFull brief:\n{project['brief']}\n\nTask: {r['title']}\nObjective: {r['objective']}\nAcceptance criteria:\n"+'\n'.join('- '+a for a in r['acceptance_criteria']),
          'allowed_files':r['files'],'blocked_files':['.git/**','.env','.env.*','**/.env','**/.env.*'],
          'expected_output':'JSON object with summary and files: [{path, content}]. content=null deletes a file.',
          'verification_commands':r.get('verification_commands',[]),'git_commit_message':f"feat: {r['title']}"[:240],
          'dependencies':r['dependencies'],'acceptance_criteria':r['acceptance_criteria'],'requires_human_approval':True})
    return {'id':new_id(),'project_id':project['id'],'plan_id':plan['id'],'created_at':now_iso(),'tasks':tasks}

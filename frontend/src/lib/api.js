import axios from 'axios';
export const API='/api';
const client=axios.create({baseURL:API,timeout:150000,headers:{'X-ProjectPilot-Client':'workspace'}});
client.interceptors.request.use(config=>{const token=sessionStorage.getItem('pp_access_token');if(token)config.headers['X-ProjectPilot-Token']=token;return config;});
const get=(path)=>client.get(path).then(r=>r.data);
const post=(path,body={})=>client.post(path,body).then(r=>r.data);
export const api={
 dashboard:id=>get('/dashboard'+(id?'?project_id='+id:'')),tiers:()=>get('/tiers'),capabilities:()=>get('/capabilities'),cloudModels:()=>get('/models/cloud'),
 listProjects:()=>get('/projects'),getProject:id=>get('/projects/'+id),createProject:body=>post('/projects',body),
 updateProject:(id,body)=>client.patch('/projects/'+id,body).then(r=>r.data),deleteProject:id=>client.delete('/projects/'+id).then(r=>r.data),
 importSource:(id,file)=>client.post(`/projects/${id}/import-source`,file,{headers:{'Content-Type':'application/zip'}}).then(r=>r.data),
 getMasterPlan:id=>get(`/projects/${id}/master-plan`),generateMasterPlan:id=>post(`/projects/${id}/master-plan/generate`),
 planVersions:id=>get(`/projects/${id}/plan-versions`),adoptPlan:(id,plan)=>post(`/projects/${id}/master-plan/${plan}/adopt`),
 importPlan:(id,body)=>post(`/projects/${id}/master-plan/import`,body),planningPrompt:id=>get(`/projects/${id}/planning-prompt`),
 getDelegationPlan:id=>get(`/projects/${id}/delegation-plan`),generateDelegationPlan:id=>post(`/projects/${id}/delegation-plan/generate`),materializeTasks:id=>post(`/projects/${id}/delegation-plan/materialize`),
 listTasks:id=>get(`/projects/${id}/tasks`),getTask:id=>get('/tasks/'+id),createTask:(id,body)=>post(`/projects/${id}/tasks`,body),updateTask:(id,body)=>client.patch('/tasks/'+id,body).then(r=>r.data),
 assignTier:(id,tier)=>post(`/tasks/${id}/assign-tier`,{tier}),taskPrompt:id=>get(`/tasks/${id}/prompt`),estimate:(id,prompt)=>post(`/tasks/${id}/estimate`,{prompt:prompt||null}),
 runEdit:(id,prompt,quote_id)=>post(`/tasks/${id}/run-edit`,{prompt:prompt||null,quote_id}),importChanges:(id,body)=>post(`/tasks/${id}/import`,body),cancel:id=>post(`/tasks/${id}/cancel`),
 verify:id=>post(`/tasks/${id}/verify`),approve:(id,body)=>post(`/tasks/${id}/approve`,body),completeReview:(id,body)=>post(`/tasks/${id}/review`,body),reject:id=>post(`/tasks/${id}/reject`),
 getDiff:id=>get(`/tasks/${id}/diff`),taskVerifications:id=>get(`/tasks/${id}/verifications`),taskRuns:id=>get(`/tasks/${id}/runs`),
 projectDiffs:id=>get(`/projects/${id}/diffs`),projectVerifications:id=>get(`/projects/${id}/verifications`),previews:id=>get(`/projects/${id}/previews`),
 launchPreview:(id,taskId)=>post(`/projects/${id}/previews/launch`+(taskId?'?task_id='+taskId:'')),stopPreview:id=>post('/previews/'+id+'/stop'),usage:id=>get(`/projects/${id}/usage`),activity:id=>get(`/projects/${id}/activity`),
 getSettings:()=>get('/settings'),updateSettings:body=>client.patch('/settings',body).then(r=>r.data),files:id=>get(`/projects/${id}/files`),history:id=>get(`/projects/${id}/history`),restore:(id,sha)=>post(`/projects/${id}/restore`,{commit_hash:sha}),
 download:async(path,name)=>{const r=await client.get(path,{responseType:'blob'});const url=URL.createObjectURL(r.data);const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);},
};
export const errorMessage=e=>{const d=e?.response?.data?.detail;return typeof d==='string'?d:Array.isArray(d)?d.map(x=>x.msg).join('; '):e.message||'Something went wrong';};
export default api;

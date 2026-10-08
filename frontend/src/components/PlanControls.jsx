import React,{useEffect,useState} from 'react';
import {toast} from 'sonner';
import api,{errorMessage} from '../lib/api';
import {useProjects} from '../lib/store';
import {copyMarkdown} from '../lib/markdown';
export default function PlanControls({plan,onChange}){
 const{current,refreshCurrent}=useProjects();const[history,setHistory]=useState([]),[open,setOpen]=useState(false),[input,setInput]=useState(''),[busy,setBusy]=useState(false);
 useEffect(()=>{if(current)api.planVersions(current.id).then(setHistory).catch(()=>{});},[current?.id,plan?.id]);
 if(!current)return null;
 const act=async(fn)=>{setBusy(true);try{await fn();await refreshCurrent();}catch(e){toast.error(errorMessage(e));}finally{setBusy(false);}};
 return <div className="space-y-3 rounded-lg border border-sky-900/70 bg-sky-950/10 p-4">
 <div className="flex flex-wrap items-center justify-between gap-3"><div><div className="text-sm font-semibold">A plan you control</div><p className="text-xs text-slate-400">Drafts preserve earlier versions. Adopt the version you want the task queue to use.</p></div><span className="rounded border border-slate-700 px-2 py-1 text-xs">{current.approved_plan_id===plan?.id?'Adopted':plan?'Draft':'No draft yet'}</span></div>
 <div className="flex flex-wrap gap-2"><button className="pp-btn" onClick={()=>act(async()=>copyMarkdown((await api.planningPrompt(current.id)).prompt,'Planning prompt'))}>Copy planning prompt</button><button className="pp-btn" onClick={()=>setOpen(!open)}>Import tailored plan</button>{plan&&current.approved_plan_id!==plan.id&&<button disabled={busy} className="pp-btn pp-primary" onClick={()=>act(async()=>{await api.adoptPlan(current.id,plan.id);toast.success('Plan adopted');})}>Adopt this version</button>}
 {history.length>1&&<select aria-label="Plan version" className="pp-input max-w-xs" value={plan?.id||''} onChange={e=>onChange(history.find(x=>x.id===e.target.value))}>{history.map((p,i)=><option key={p.id} value={p.id}>{p.generator} · {new Date(p.created_at).toLocaleString()} {p.id===current.approved_plan_id?'· adopted':''}</option>)}</select>}</div>
 {open&&<div className="space-y-2"><p className="text-xs text-slate-400">Use the planning prompt in your chosen tool, then paste its JSON plan here. External usage is billed by that tool.</p><textarea className="pp-input w-full font-mono text-xs" rows={8} value={input} onChange={e=>setInput(e.target.value)} placeholder={'{"summary":"...","roadmap":[...]}'} aria-label="Import plan JSON"/><button disabled={busy} className="pp-btn pp-primary" onClick={()=>act(async()=>{const p=await api.importPlan(current.id,JSON.parse(input));onChange(p);setOpen(false);toast.success('Draft imported');})}>Save as new draft</button></div>}
 </div>;
}

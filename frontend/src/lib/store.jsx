import React,{createContext,useContext,useEffect,useState,useCallback} from 'react';
import api,{errorMessage} from './api';
const ProjectContext=createContext(null);
export function ProjectProvider({children}){
 const[projects,setProjects]=useState([]),[currentId,setCurrentId]=useState(()=>localStorage.getItem('pp_current_project')),[loading,setLoading]=useState(true),[error,setError]=useState(null),[token,setToken]=useState('');
 const refresh=useCallback(async()=>{try{const list=await api.listProjects();setProjects(list);setCurrentId(prev=>list.some(p=>p.id===prev)?prev:list.find(p=>p.status!=='archived')?.id||null);setError(null);return list;}catch(e){setError(errorMessage(e));throw e;}finally{setLoading(false);}},[]);
 useEffect(()=>{refresh().catch(()=>{});},[refresh]);
 useEffect(()=>{if(currentId)localStorage.setItem('pp_current_project',currentId);else localStorage.removeItem('pp_current_project');},[currentId]);
 const current=projects.find(p=>p.id===currentId)||null;
 if(error)return <div className="mx-auto mt-24 max-w-lg rounded-xl border border-slate-700 bg-[#14171D] p-8"><h1 className="text-xl font-semibold">Connect to your workspace</h1><p className="my-4 text-slate-400">{error}</p><p className="mb-4 text-sm text-slate-400">Start ProjectPilot with python run.py. If you configured an access token, enter it below.</p><input aria-label="Workspace access token" type="password" className="w-full rounded bg-slate-900 p-3" value={token} onChange={e=>setToken(e.target.value)} placeholder="Access token (if configured)"/><button className="mt-4 rounded bg-sky-400 px-4 py-2 text-slate-950" onClick={()=>{if(token)sessionStorage.setItem('pp_access_token',token);refresh().catch(()=>{});}}>Reconnect</button></div>;
 return <ProjectContext.Provider value={{projects,current,currentId,loading,setCurrentId,refresh,refreshCurrent:async()=>{if(!currentId)return;const p=await api.getProject(currentId);setProjects(prev=>prev.map(x=>x.id===p.id?p:x));}}}>{children}</ProjectContext.Provider>;
}
export function useProjects(){return useContext(ProjectContext);}

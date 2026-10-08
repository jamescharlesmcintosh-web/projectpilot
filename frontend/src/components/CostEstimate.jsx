import React from 'react';
import {Coins} from 'lucide-react';
export default function CostEstimate({kind,className=''}){
 return <div className={`flex items-center gap-2 rounded-md border border-[#282E3A] bg-[#0D0F12] px-3 py-2 text-xs text-slate-400 ${className}`}><Coins size={14} className="text-sky-400"/>{kind==='regenerate'?'Brief scaffold and exports use no model calls.':kind==='build'?'Checks use your computer. No AI call is needed.':'Choose a route and review its estimate before generation.'}</div>;
}

import React from 'react';
import { Handle, Position } from 'reactflow';

export default function CustomNode({ data }) {
  const risk = data.risk || 0;
  
  let borderColor = 'border-emerald-500';
  let shadowColor = 'shadow-emerald-500/20';
  let riskTextColor = 'text-emerald-400';
  
  if (risk >= 0.4 && risk <= 0.7) {
    borderColor = 'border-amber-500';
    shadowColor = 'shadow-amber-500/20';
    riskTextColor = 'text-amber-400';
  } else if (risk > 0.7) {
    borderColor = 'border-red-500';
    shadowColor = 'shadow-red-500/20';
    riskTextColor = 'text-red-400';
  }

  return (
    <div className={`bg-slate-800 rounded-xl shadow-lg border-2 ${borderColor} ${shadowColor} p-5 min-w-[160px] text-center transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl`}>
      <Handle type="target" position={Position.Top} className="!bg-slate-500 w-3 h-3" />
      <div className="font-bold text-white text-xl tracking-wide">{data.id}</div>
      <div className={`text-sm mt-2 font-semibold ${riskTextColor}`}>
        Risk: {risk.toFixed(2)}
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-slate-500 w-3 h-3" />
    </div>
  );
}

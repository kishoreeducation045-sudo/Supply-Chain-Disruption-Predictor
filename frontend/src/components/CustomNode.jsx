import { Handle, Position } from 'reactflow';

export default function CustomNode({ data }) {
  const risk = data.fullData.total_risk;
  let borderColor = 'border-secondary/50';
  let textColor = 'text-secondary';
  if (risk > 0.4) { borderColor = 'border-amber-500/80'; textColor = 'text-amber-500'; }
  if (risk > 0.7) { borderColor = 'border-error/90'; textColor = 'text-error'; }

  return (
    <div className={`bg-surface-container-high px-6 py-4 rounded-xl border-2 ${borderColor} shadow-lg backdrop-blur-md w-48`}>
      <Handle type="target" position={Position.Top} className="w-3 h-3 bg-white" />
      <div className="text-center">
        <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">{data.fullData.tier}</div>
        <div className="text-md font-black text-white mb-2">{data.fullData.id}</div>
        <div className={`text-xl font-black ${textColor}`}>{(risk * 100).toFixed(1)}% RISK</div>
      </div>
      <Handle type="source" position={Position.Bottom} className="w-3 h-3 bg-white" />
    </div>
  );
}
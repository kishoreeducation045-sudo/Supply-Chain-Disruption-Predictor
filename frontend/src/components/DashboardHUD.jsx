import React from 'react';

const DashboardHUD = ({ globalMetrics }) => {
  return (
    <div className="col-span-9 row-span-1 flex justify-end gap-6 pointer-events-auto items-start">
      <div className="bg-slate-900/50 backdrop-blur-xl rounded-full border border-slate-700/50 px-8 py-4 shadow-2xl flex gap-10">
        <div className="flex flex-col items-center">
            <span className="text-slate-400 text-[10px] font-bold uppercase tracking-[0.2em] opacity-80 mb-1">Global Health</span>
            <span className="text-xl font-black text-emerald-400 drop-shadow-md">
                {(globalMetrics.global_health || 1.0).toFixed(2)}
            </span>
        </div>
        <div className="w-px bg-slate-700/50"></div>
        <div className="flex flex-col items-center">
            <span className="text-slate-400 text-[10px] font-bold uppercase tracking-[0.2em] opacity-80 mb-1">Network Risk</span>
            <span className="text-xl font-black text-amber-400 drop-shadow-md">
                {(globalMetrics.avg_risk_percentage || 0).toFixed(2)}%
            </span>
        </div>
        <div className="w-px bg-slate-700/50"></div>
        <div className="flex flex-col items-center">
            <span className="text-slate-400 text-[10px] font-bold uppercase tracking-[0.2em] opacity-80 mb-1">Threat Streams</span>
            <span className="text-xl font-black text-red-400 drop-shadow-md">
                {globalMetrics.threat_streams || 0}
            </span>
        </div>
      </div>
    </div>
  );
};

export default DashboardHUD;

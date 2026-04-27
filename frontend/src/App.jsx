import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, { Background, Controls, applyNodeChanges, applyEdgeChanges } from 'reactflow';
import 'reactflow/dist/style.css';
import { getNetwork, runSimulation, getMitigation } from './api/client';
import { Activity, AlertTriangle, Send, Network } from 'lucide-react';
import CustomNode from './CustomNode';

const nodeTypes = {
  customNode: CustomNode
};

const getColorForRisk = (risk) => {
  if (risk < 0.4) return '#10b981'; // Emerald
  if (risk <= 0.7) return '#f59e0b'; // Amber
  return '#ef4444'; // Crimson
};

export default function App() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [scenarioText, setScenarioText] = useState('');
  const [isSimulating, setIsSimulating] = useState(false);
  const [mitigationDraft, setMitigationDraft] = useState('');
  const [isDeploying, setIsDeploying] = useState(false);
  const [globalMetrics, setGlobalMetrics] = useState({ global_health: 1.0, threat_streams: 0, avg_risk_percentage: 0 });

  // Apply layout
  const layoutNodes = (graphNodes) => {
    const total = graphNodes.length;
    const radius = 400;
    const cx = window.innerWidth / 2 + 150; // offset slightly right due to sidebar
    const cy = window.innerHeight / 2;

    return graphNodes.map((node, i) => {
      const angle = (2 * Math.PI * i) / total;
      const x = cx + radius * Math.cos(angle);
      const y = cy + radius * Math.sin(angle);

      return {
        id: node.id,
        type: 'customNode',
        position: { x, y },
        data: { id: node.id, risk: node.total_risk },
        payload: node // save original data
      };
    });
  };

  const layoutEdges = (graphEdges) => {
    return graphEdges.map((edge, i) => ({
      id: `e-${edge.source}-${edge.target}-${i}`,
      source: edge.source,
      target: edge.target,
      animated: true,
      style: { stroke: 'rgba(255,255,255,0.2)', strokeWidth: Math.max(1, edge.risk_weight) },
    }));
  };

  const fetchNetwork = async () => {
    try {
      const data = await getNetwork();
      setNodes(layoutNodes(data.nodes));
      setEdges(layoutEdges(data.edges));
      if (data.metrics) {
        setGlobalMetrics(data.metrics);
      }
      
      // Update selected node if applicable
      if (selectedNode) {
        const updated = data.nodes.find(n => n.id === selectedNode.payload.id);
        if (updated) setSelectedNode({ ...selectedNode, payload: updated });
      }
    } catch (error) {
      console.error("Failed to fetch network:", error);
    }
  };

  useEffect(() => {
    fetchNetwork();
    // eslint-disable-next-line
  }, []);

  useEffect(() => {
    if (selectedNode && selectedNode.payload.total_risk > 0.7) {
      // Fetch mitigation automatically
      getMitigation(selectedNode.payload.id)
        .then(res => setMitigationDraft(res.drafted_email))
        .catch(console.error);
    } else {
      setMitigationDraft('');
    }
  }, [selectedNode]);

  const handleSimulate = async () => {
    if (!scenarioText.trim()) return;
    setIsSimulating(true);
    try {
      await runSimulation(scenarioText);
      await fetchNetwork();
    } catch (error) {
      console.error("Simulation failed:", error);
    } finally {
      setIsSimulating(false);
    }
  };

  const onNodeClick = (_, node) => {
    setSelectedNode(node);
  };

  const onNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      
      {/* Background Canvas */}
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0 z-10" style={{ backgroundImage: 'radial-gradient(circle at center, transparent 0%, #020617 100%)', pointerEvents: 'none' }} />
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onNodeClick={onNodeClick}
          fitView
          minZoom={0.1}
          className="bg-slate-950"
        >
          <Background color="#334155" size={1.5} />
          <Controls className="bottom-8 right-8 z-50 bg-slate-800 border-slate-700" />
        </ReactFlow>
      </div>

      {/* UI Overlay */}
      <div className="absolute inset-0 z-10 pointer-events-none p-6 grid grid-cols-12 gap-6 grid-rows-6">
        
        {/* Sidebar / Left Glass Panel */}
        <div className="col-span-3 row-span-6 flex flex-col bg-slate-900/50 backdrop-blur-xl border border-slate-700/50 rounded-3xl p-6 shadow-2xl pointer-events-auto h-full overflow-hidden">
          
          {/* Header */}
          <div className="flex items-center justify-between mb-8 pb-4 border-b border-slate-700/50">
            <h1 className="text-xl font-black tracking-wider text-white flex items-center gap-3">
              <Network className="text-emerald-400" size={24} />
              SCDP Command
            </h1>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-emerald-400">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
              </span>
              Live
            </div>
          </div>

          {/* Simulation Box */}
          <div className="mb-6">
            <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-3">Disaster Simulator</label>
            <textarea
              className="w-full bg-slate-950/60 border border-slate-700/60 rounded-xl p-4 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500/80 focus:ring-1 focus:ring-emerald-500/50 transition-all resize-none h-28 mb-4 shadow-inner"
              placeholder="Inject threat simulation... e.g., 'Typhoon approaching Shanghai port'"
              value={scenarioText}
              onChange={(e) => setScenarioText(e.target.value)}
            />
            <button
              onClick={handleSimulate}
              disabled={isSimulating || !scenarioText.trim()}
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-xl transition-all duration-300 shadow-[0_0_15px_rgba(16,185,129,0.2)] hover:shadow-[0_0_25px_rgba(16,185,129,0.4)] border border-emerald-400/50"
            >
              {isSimulating ? (
                 <div className="h-5 w-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                'Run AI Simulation'
              )}
            </button>
          </div>

          {/* Node Details Card */}
          {selectedNode ? (
            <div className="flex flex-col flex-grow overflow-y-auto pr-2 custom-scrollbar animate-in slide-in-from-left-4 fade-in duration-300 pb-4">
              <h2 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-3">Node Telemetry</h2>
              
              <div className="bg-slate-950/60 border border-slate-700/60 rounded-2xl p-5 mb-5 relative overflow-hidden group hover:border-slate-500/50 transition-colors shadow-lg">
                <div className="flex justify-between items-start mb-5">
                  <h3 className="text-xl font-black text-white">{selectedNode.payload.id}</h3>
                  <span className="px-3 py-1 rounded-lg text-xs font-bold tracking-wider bg-slate-800 border border-slate-600/50 text-slate-300 shadow-sm">
                    {selectedNode.payload.tier}
                  </span>
                </div>
                
                <div className="space-y-4 text-sm mb-6">
                  <div className="flex justify-between border-b border-slate-800 pb-3">
                    <span className="text-slate-500 font-medium tracking-wide">Weather</span>
                    <span className="font-semibold text-slate-200 drop-shadow-sm">{selectedNode.payload.weather_condition}</span>
                  </div>
                  <div className="flex justify-between border-b border-slate-800 pb-3">
                    <span className="text-slate-500 font-medium tracking-wide">Geo Risk</span>
                    <span className="font-mono font-medium text-slate-200">{(selectedNode.payload.geopolitical_risk || 0).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between border-b border-slate-800 pb-3">
                    <span className="text-slate-500 font-medium tracking-wide">Reliability</span>
                    <span className="font-mono font-medium text-slate-200">{(selectedNode.payload.base_reliability || 0).toFixed(2)}</span>
                  </div>
                </div>

                {/* Risk Score */}
                <div className="mt-2 p-4 rounded-xl bg-slate-900 border border-slate-700/50 flex items-center justify-between shadow-inner">
                  <div>
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1.5 opacity-80">Total Risk Index</div>
                    <div className="text-3xl font-black drop-shadow-lg" style={{ color: getColorForRisk(selectedNode.payload.total_risk)}}>
                      {selectedNode.payload.total_risk.toFixed(2)}
                    </div>
                  </div>
                  <Activity size={32} style={{ color: getColorForRisk(selectedNode.payload.total_risk), opacity: 0.15 }} />
                </div>
              </div>

              {/* Mitigation Alert */}
              {selectedNode.payload.total_risk > 0.7 && (
                <div className="mt-auto animate-in slide-in-from-bottom-4 fade-in duration-500">
                  <div className="border border-red-500/50 bg-red-950/30 rounded-2xl p-5 shadow-[0_0_30px_rgba(239,68,68,0.1)] relative overflow-hidden flex flex-col h-full">
                    <div className="absolute top-0 left-0 w-1.5 h-full bg-gradient-to-b from-red-500 to-red-600" />
                    
                    <div className="flex items-center gap-2 text-red-400 font-black tracking-widest text-[11px] uppercase mb-4 drop-shadow-md">
                      <AlertTriangle size={14} className="animate-pulse" />
                      Critical Disruption Detected
                    </div>
                    
                    <div className="bg-slate-950/80 rounded-xl p-3 text-[11px] text-slate-300 font-mono mb-4 border border-red-900/30 flex-grow overflow-y-auto whitespace-pre-wrap leading-relaxed shadow-inner">
                      {mitigationDraft ? mitigationDraft : "Synthesizing AI mitigation strategy..."}
                    </div>

                    <button
                      onClick={() => setIsDeploying(true)}
                      disabled={!mitigationDraft || isDeploying}
                      className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 disabled:opacity-50 disabled:grayscale text-white font-bold py-2.5 px-4 rounded-xl transition-all border border-red-400/50 shadow-[0_0_20px_rgba(239,68,68,0.25)] hover:shadow-[0_0_30px_rgba(239,68,68,0.4)]"
                    >
                      {isDeploying ? 'Deploying...' : (
                        <>
                          Deploy Mitigation <Send size={16} />
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex-grow flex items-center justify-center text-slate-600 text-sm border-2 border-dashed border-slate-700/50 rounded-2xl opacity-60 bg-slate-900/30">
              Select node to activate telemetry
            </div>
          )}
        </div>
        
        {/* Top KPIs (Right side) */}
        <div className="col-span-9 row-span-1 flex justify-end gap-6 pointer-events-auto items-start">
           <div className="bg-slate-900/50 backdrop-blur-xl rounded-full border border-slate-700/50 px-8 py-4 shadow-2xl flex gap-10">
              <div className="flex flex-col items-center">
                 <span className="text-slate-400 text-[10px] font-bold uppercase tracking-[0.2em] opacity-80 mb-1">Global Health</span>
                 <span className="text-xl font-black text-emerald-400 drop-shadow-md">{globalMetrics.global_health.toFixed(2)}</span>
              </div>
              <div className="w-px bg-slate-700/50"></div>
              <div className="flex flex-col items-center">
                 <span className="text-slate-400 text-[10px] font-bold uppercase tracking-[0.2em] opacity-80 mb-1">Network Risk</span>
                 <span className="text-xl font-black text-amber-400 drop-shadow-md">{globalMetrics.avg_risk_percentage}%</span>
              </div>
              <div className="w-px bg-slate-700/50"></div>
              <div className="flex flex-col items-center">
                 <span className="text-slate-400 text-[10px] font-bold uppercase tracking-[0.2em] opacity-80 mb-1">Threat Streams</span>
                 <span className="text-xl font-black text-red-400 drop-shadow-md">{globalMetrics.threat_streams}</span>
              </div>
           </div>
        </div>

      </div>
    </div>
  );
}

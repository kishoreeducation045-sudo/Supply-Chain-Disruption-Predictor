import React, { useState, useEffect } from 'react';
import ReactFlow, { Background, Controls, MarkerType, ReactFlowProvider, useReactFlow, Panel } from 'reactflow';
import 'reactflow/dist/style.css';
import { getNetwork, runSimulation, getMitigation } from './api/client';
import CustomNode from './components/CustomNode';

const nodeTypes = { custom: CustomNode };

function FlowCanvas() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [simText, setSimText] = useState("");
  const [selectedNode, setSelectedNode] = useState(null);
  const [mitigationDraft, setMitigationDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [reportData, setReportData] = useState("");
  const { fitView } = useReactFlow();

  const getCircularLayout = (rfNodes, rfEdges) => {
    const radius = 350;
    const n = rfNodes.length;
    return rfNodes.map((node, i) => {
      const angle = (i / n) * 2 * Math.PI;
      return {
        ...node,
        position: {
          x: radius * Math.cos(angle),
          y: radius * Math.sin(angle)
        }
      };
    });
  };

  const fetchGraph = async () => {
    const res = await getNetwork();
    setMetrics(res.data.metrics);

    let rfNodes = res.data.nodes.map(n => ({
      id: n.id,
      type: 'custom',
      data: { fullData: n },
      position: { x: 0, y: 0 }
    }));

    const generateColor = (str) => {
      let hash = 0;
      for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
      }
      const hue = Math.abs(hash) % 360;
      return `hsl(${hue}, 80%, 60%)`;
    };

    let rfEdges = res.data.edges.map(e => {
      const color = generateColor(e.source);
      return {
        id: `e-${e.source}-${e.target}`, source: e.source, target: e.target,
        animated: true, style: { stroke: color, strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: color }
      };
    });

    setNodes(getCircularLayout(rfNodes, rfEdges));
    setEdges(rfEdges);
  };

  useEffect(() => { fetchGraph(); }, []);

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const res = await runSimulation(simText);
      await fetchGraph();
      if (res && res.data && res.data.data && res.data.data.markdown_report) {
        setReportData(res.data.data.markdown_report);
        setIsModalOpen(true);
      }
    } catch (err) {
      console.error("Simulation failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleNodeClick = async (e, node) => {
    setSelectedNode(node.data.fullData);
    if (node.data.fullData.total_risk > 0.7) {
      const res = await getMitigation(node.data.fullData.id);
      setMitigationDraft(res.data.drafted_action_plan);
    } else {
      setMitigationDraft("");
    }
  };

  return (
    <div className="relative w-screen h-screen bg-[#0b1326] text-white font-inter overflow-hidden">

      {/* LAYER 0: React Flow Canvas (Interactive background) */}
      <div className="absolute inset-0 z-0">
        <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} onNodeClick={handleNodeClick} fitView>
          <Background color="#3e4850" gap={30} size={1} />
          <Panel position="bottom-center">
            <button 
              onClick={() => fitView({ duration: 800, padding: 0.2 })}
              className="bg-[#171f33]/90 text-primary font-bold border border-primary px-4 py-2 rounded shadow-lg tracking-widest text-xs uppercase hover:bg-primary hover:text-black transition-colors mb-4"
            >
              Recenter Network
            </button>
          </Panel>
        </ReactFlow>
      </div>

      {/* LAYER 10: Stitch UI HUD (pointer-events-none to let clicks pass through to graph) */}
      <div className="absolute inset-0 z-10 pointer-events-none flex">

        {/* Left Sidebar (pointer-events-auto makes buttons clickable) */}
        <aside className="w-80 h-full bg-[#171f33]/90 backdrop-blur-md border-r border-slate-700/50 p-6 pointer-events-auto flex flex-col shadow-2xl overflow-y-auto">
          <div className="mb-8">
            <h1 className="text-2xl font-black text-primary tracking-widest uppercase">CHAIN IQ</h1>
            <p className="text-xs text-secondary flex items-center gap-2 mt-1"><span className="w-2 h-2 rounded-full bg-secondary animate-pulse"></span> LIVE V3.0</p>
          </div>

          <div className="bg-surface-container-high rounded-xl p-5 mb-6 border border-slate-700">
            <label className="text-xs font-bold text-primary tracking-widest uppercase mb-3 block">Threat Injection Engine</label>
            <textarea
              value={simText} onChange={(e) => setSimText(e.target.value)}
              className="w-full bg-surface border-none rounded-lg p-3 text-sm text-white focus:ring-1 focus:ring-primary min-h-[100px]"
              placeholder="E.g. Category 5 hurricane in East Asia..."
            />
            <button onClick={handleSimulate} className="w-full mt-4 bg-primary text-black font-black py-3 rounded-lg text-xs tracking-widest hover:bg-white transition-all">
              {loading ? "PROCESSING..." : "ANALYZE THREAT IMPACT"}
            </button>
          </div>

          {selectedNode && (
            <div className="bg-surface-container-high rounded-xl p-5 border border-slate-700 relative">
              {selectedNode.total_risk > 0.7 && <div className="absolute top-3 right-3 text-[10px] font-bold bg-error text-white px-2 py-1 rounded-md">CRITICAL</div>}
              <p className="text-xs text-slate-400 font-bold uppercase mb-1">Node Identity</p>
              <h3 className="text-lg font-bold mb-2">{selectedNode.id}</h3>
              <p className="text-xs text-slate-400">Weather: <span className="text-white">{selectedNode.weather_condition}</span></p>
              <p className="text-xs text-slate-400 mt-1">News: <span className="text-white">{selectedNode.latest_news}</span></p>

              <div className="mt-4 pt-4 border-t border-slate-700 flex justify-between items-end">
                <div className="text-xs text-slate-400 font-bold uppercase">Risk Score</div>
                <div className={`text-3xl font-black ${selectedNode.total_risk > 0.7 ? 'text-error' : 'text-secondary'}`}>{(selectedNode.total_risk * 100).toFixed(1)}</div>
              </div>
            </div>
          )}

          {mitigationDraft && (
            <div className="mt-6 bg-red-950/40 border border-error/50 rounded-xl p-4">
              <p className="text-xs text-error font-bold tracking-widest uppercase mb-2">AI Mitigation Draft</p>
              <p className="text-xs text-slate-300 italic mb-4">{mitigationDraft}</p>
              <button className="w-full bg-error text-white font-bold py-2 rounded text-xs uppercase">Deploy Action</button>
            </div>
          )}
        </aside>

        {/* Right Side HUD Bento Box */}
        <div className="flex-1 p-8 flex flex-col items-end pointer-events-none">
          {metrics && (
            <div className="w-80 space-y-6 pointer-events-auto">

              {/* Intelligence Stream */}
              <div className="bg-[#171f33]/90 backdrop-blur-md rounded-2xl p-6 border border-slate-700 shadow-xl">
                <h3 className="text-xs font-black tracking-widest text-white uppercase mb-4 flex justify-between">Stream <span className="w-2 h-2 rounded-full bg-primary animate-ping"></span></h3>
                <div className="space-y-4">
                  {metrics.intelligence_stream.map((log, i) => (
                    <div key={i} className="text-xs text-slate-300 border-l-2 border-primary pl-3 py-1">{log}</div>
                  ))}
                </div>
              </div>

              {/* Global Health */}
              <div className="bg-[#171f33]/90 backdrop-blur-md rounded-2xl p-6 border border-slate-700 shadow-xl flex justify-between items-center">
                <div>
                  <p className="text-[10px] font-black text-primary tracking-widest uppercase mb-1">Global Health</p>
                  <h4 className="text-3xl font-black text-white">{metrics.global_health}%</h4>
                </div>
                <div className="w-10 h-10 rounded-full border-4 border-slate-600 border-t-primary animate-spin"></div>
              </div>

              {/* Delta Cost */}
              <div className="bg-[#171f33]/90 backdrop-blur-md rounded-2xl p-6 border border-slate-700 shadow-xl">
                <p className="text-[10px] font-black text-slate-400 tracking-widest uppercase mb-2">Projected Network Loss</p>
                <h4 className="text-2xl font-black text-error mb-1">{metrics.simulated_delta_cost} <span className="text-xs text-slate-400">/day</span></h4>
                <p className="text-[10px] text-slate-500 italic">Projected network loss based on current topology risk.</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-[768px] h-[80vh] bg-surface-container-high rounded-2xl border border-slate-600 shadow-2xl p-8 flex flex-col relative pointer-events-auto">
            <button 
              className="absolute top-4 right-4 text-slate-400 hover:text-white font-bold text-lg"
              onClick={() => setIsModalOpen(false)}
            >
              ✕
            </button>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-black text-white uppercase tracking-widest">Threat Analysis Report</h2>
              <button 
                onClick={() => {
                  const blob = new Blob([reportData], { type: 'text/markdown' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = "ChainIQ_Threat_Report.md";
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                className="bg-primary text-black hover:bg-white font-bold px-4 py-2 rounded text-xs uppercase tracking-widest transition-colors"
              >
                Download Report (.md)
              </button>
            </div>
            <pre className="whitespace-pre-wrap font-sans text-sm text-slate-300 overflow-y-auto flex-1 p-4 bg-[#0b1326]/50 rounded-lg border border-slate-700">
              {reportData}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default function App() {
  return (
    <ReactFlowProvider>
      <FlowCanvas />
    </ReactFlowProvider>
  );
}
import React, { useCallback, useMemo } from 'react';
import ReactFlow, { Background, Controls, applyNodeChanges } from 'reactflow';
import 'reactflow/dist/style.css';
import CustomNode from './CustomNode';

const NetworkCanvas = ({ nodes, edges, setNodes, onNodeClick }) => {
  const nodeTypes = useMemo(() => ({ customNode: CustomNode }), []);

  const onNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    [setNodes]
  );

  return (
    <div className="absolute inset-0 z-0 bg-slate-950">
      <div 
        className="absolute inset-0 z-10 pointer-events-none" 
        style={{ backgroundImage: 'radial-gradient(circle at center, transparent 0%, #020617 100%)' }} 
      />
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onNodeClick={onNodeClick}
        fitView
        minZoom={0.1}
      >
        <Background color="#334155" size={1.5} />
        <Controls className="bottom-8 right-8 z-[60] bg-slate-800 border-slate-700 pointer-events-auto" />
      </ReactFlow>
    </div>
  );
};

export default NetworkCanvas;

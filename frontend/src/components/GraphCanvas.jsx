import React, { useEffect, useState, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { fetchGraphTopology } from '../services/api';

export default function GraphCanvas({ onSelectNode }) {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [summary, setSummary] = useState(null);
  const containerRef = useRef();
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  useEffect(() => {
    fetchGraphTopology().then((res) => {
      if (res && res.nodes) {
        setGraphData({ nodes: res.nodes, links: res.links });
        setSummary(res.summary);
      }
    });

    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.offsetWidth,
        height: containerRef.current.offsetHeight,
      });
    }
  }, []);

  // Node color by role
  const getNodeColor = (node) => {
    switch (node.role_id) {
      case 1: return '#ef4444'; // Red: Ghost Kingpin
      case 3: return '#f59e0b'; // Amber: Tech Enabler / SIM Box
      case 2: return '#06b6d4'; // Cyan: Caller
      case 4: return '#3b82f6'; // Blue: Money Mule
      case 5: return '#a855f7'; // Purple: Field Cashier
      default: return '#64748b'; // Slate: Civilian
    }
  };

  return (
    <div ref={containerRef} className="flex-1 h-full bg-slate-950 relative overflow-hidden">
      {/* Top Banner Stats */}
      {summary && (
        <div className="absolute top-3 left-3 z-10 flex gap-3 text-xs font-mono bg-slate-900/90 border border-slate-800 p-2.5 rounded-lg shadow-lg">
          <div><span className="text-slate-400">Total Entities:</span> <span className="text-white font-bold">{summary.total_entities}</span></div>
          <div><span className="text-slate-400">Tactical Links:</span> <span className="text-indigo-400 font-bold">{summary.total_relationships}</span></div>
          <div><span className="text-slate-400">Ghost Kingpins:</span> <span className="text-red-400 font-bold">{summary.kingpins_unmasked}</span></div>
        </div>
      )}

      {/* Force Graph */}
      <ForceGraph2D
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}
        nodeId="id"
        nodeLabel={(n) => `${n.label} | ${n.role} (Degree: ${n.degree}, KingpinScore: ${n.kingpin_score})`}
        nodeColor={getNodeColor}
        nodeRelSize={6}
        linkColor={(link) => link.color || '#475569'}
        linkWidth={(link) => (link.weight ? link.weight * 2.5 : 1.5)}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
        onNodeClick={(node) => onSelectNode(node)}
      />

      {/* Legend */}
      <div className="absolute bottom-3 left-3 bg-slate-900/90 border border-slate-800 p-3 rounded-lg text-[11px] text-slate-300 font-mono grid grid-cols-2 gap-x-4 gap-y-1 z-10 shadow-lg">
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-red-500"></span> Ghost Kingpin</span>
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Tech Enabler</span>
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-cyan-500"></span> Vishing Caller</span>
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span> Money Mule</span>
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span> Cashier / Collector</span>
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-slate-500"></span> Civilian Node</span>
      </div>
    </div>
  );
}
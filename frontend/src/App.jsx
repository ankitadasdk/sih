import React, { useState, useEffect } from 'react';
import GraphCanvas from './components/GraphCanvas';
import FileIngestionSidebar from './components/FileIngestionSidebar';
import NodeInspector from './components/NodeInspector';
import { fetchGraphTopology } from './services/api';
import { Shield, ShieldAlert, Activity, RefreshCw } from 'lucide-react';

export default function App() {
  const [selectedNode, setSelectedNode] = useState(null);
  const [masterGraphData, setMasterGraphData] = useState(null);
  const [customGraphData, setCustomGraphData] = useState(null);
  const [loadingMaster, setLoadingMaster] = useState(false);

  const loadMasterGraph = async () => {
    setLoadingMaster(true);
    const data = await fetchGraphTopology();
    if (data && data.nodes) {
      setMasterGraphData(data);
    }
    setLoadingMaster(false);
  };

  useEffect(() => {
    loadMasterGraph();
  }, []);

  const handleAnalysisComplete = (extractedData) => {
    const incomingGraph = 
      extractedData?.graph_data || 
      extractedData?.data?.graph_data || 
      extractedData;

    if (incomingGraph?.nodes && incomingGraph.nodes.length > 0) {
      setCustomGraphData(incomingGraph);
    }
  };

  const activeGraph = customGraphData || masterGraphData;

  return (
    <div className="w-screen h-screen flex flex-col bg-[#0b0f17] text-slate-100 overflow-hidden font-sans">
      {/* Header Bar */}
      <header className="h-14 border-b border-slate-800/80 px-6 flex items-center justify-between bg-[#0f172a]/95 shrink-0 z-20 shadow-md">
        <div className="flex items-center gap-3">
          <div className="p-1.5 bg-indigo-950/80 rounded border border-indigo-700/50">
            <Shield className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-xs font-bold tracking-wider uppercase text-slate-100 font-mono flex items-center gap-2">
              <span>Anti-Fraud Entity & Device Trail Intelligence</span>
              <span className="text-[10px] bg-emerald-950/80 text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded font-mono">LIVE API</span>
            </h1>
            <p className="text-[10px] text-slate-400 font-mono">Hub-and-Spoke Topology Analysis • User / Device / Account / Transaction</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {customGraphData && (
            <button
              onClick={() => setCustomGraphData(null)}
              className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded border border-slate-700 font-mono transition-colors flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reset to Master Graph</span>
            </button>
          )}

          <div className="flex items-center gap-2 text-xs font-mono bg-slate-900/90 px-3 py-1.5 rounded border border-slate-800 text-slate-300">
            <Activity className="w-3.5 h-3.5 text-amber-400" />
            <span>Target: <strong className="text-amber-400">DEV-174Q</strong></span>
          </div>
        </div>
      </header>

      {/* Main Viewport */}
      <main className="flex-1 flex overflow-hidden relative">
        {/* Left Document & FIR Ingestion Sidebar */}
        <FileIngestionSidebar onAnalysisComplete={handleAnalysisComplete} />
        
        {/* Center Force Graph Viewport */}
        <div className="flex-1 h-full relative overflow-hidden">
          <GraphCanvas
            initialData={activeGraph}
            customGraphData={activeGraph}
            onSelectNode={(node) => setSelectedNode(node)}
            onNodeSelect={(node) => setSelectedNode(node)}
          />
        </div>

        {/* Right Node Inspector Slide-out */}
        {selectedNode && (
          <NodeInspector
            selectedNode={selectedNode}
            onClose={() => setSelectedNode(null)}
          />
        )}
      </main>
    </div>
  );
}
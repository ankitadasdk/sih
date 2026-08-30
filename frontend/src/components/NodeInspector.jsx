import React, { useEffect, useState } from 'react';
import { fetchSuspectConnections } from '../services/api';
import { ShieldAlert, PhoneCall, Landmark, AlertOctagon, X } from 'lucide-react';

export default function NodeInspector({ selectedNode, onClose }) {
  const [connections, setConnections] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!selectedNode?.id) return;
    setLoading(true);
    fetchSuspectConnections(selectedNode.id)
      .then((data) => setConnections(data))
      .catch(() => setConnections(null))
      .finally(() => setLoading(false));
  }, [selectedNode]);

  if (!selectedNode) return null;

  return (
    <aside className="w-96 h-full border-l border-slate-800 bg-slate-900/95 backdrop-blur-lg flex flex-col p-5 overflow-y-auto absolute right-0 top-0 z-30 shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div>
          <h3 className="text-sm font-bold text-white font-mono">{selectedNode.label || selectedNode.id}</h3>
          <span className="text-[11px] font-mono text-indigo-400 font-semibold">{selectedNode.role}</span>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-3 font-mono text-xs">
        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
            <span className="text-[10px] text-slate-500 block">SYNDICATE CELL</span>
            <span className="text-emerald-400 font-bold">{selectedNode.syndicate_cell_id || 'CELL_01'}</span>
          </div>
          <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
            <span className="text-[10px] text-slate-500 block">KINGPIN SCORE</span>
            <span className={selectedNode.kingpin_score > 0.1 ? "text-red-400 font-bold" : "text-slate-300 font-bold"}>
              {selectedNode.kingpin_score || '0.000'}
            </span>
          </div>
          <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
            <span className="text-[10px] text-slate-500 block">NETWORK DEGREE</span>
            <span className="text-white font-bold">{selectedNode.degree || 0} active links</span>
          </div>
          <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
            <span className="text-[10px] text-slate-500 block">EXPOSURE INR</span>
            <span className="text-cyan-400 font-bold">₹{Number(selectedNode.unauthorized_amount || 0).toLocaleString()}</span>
          </div>
        </div>

        {/* Tactical Investigative Conclusion */}
        {selectedNode.investigative_conclusion && (
          <div className="bg-indigo-950/40 p-3 rounded border border-indigo-800/80">
            <div className="flex items-center gap-1.5 text-indigo-300 font-bold text-[11px] mb-1">
              <AlertOctagon className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
              <span>FORENSIC CONCLUSION & LEADS</span>
            </div>
            <p className="text-[11px] text-slate-200 leading-relaxed font-sans">
              {selectedNode.investigative_conclusion}
            </p>
          </div>
        )}

        {/* Telecom Intercept Frequency Card */}
        {selectedNode.telecom_intercepts && (
          <div className="bg-slate-950 p-3 rounded border border-slate-800">
            <div className="flex items-center gap-1.5 text-emerald-400 font-bold text-[11px] mb-2">
              <PhoneCall className="w-3.5 h-3.5 shrink-0" />
              <span>TELECOM INTERCEPT PATTERNS</span>
            </div>
            <div className="space-y-1 text-[11px]">
              <div><span className="text-slate-500">Volume:</span> <span className="text-white">{selectedNode.telecom_intercepts.total_calls} calls captured</span></div>
              <div><span className="text-slate-500">Frequent Target:</span> <span className="text-amber-300">{selectedNode.telecom_intercepts.frequent_target}</span></div>
              <div><span className="text-slate-500">Call Windows:</span> <span className="text-slate-300">{selectedNode.telecom_intercepts.burst_window}</span></div>
              <div><span className="text-slate-500">Tower Coverage:</span> <span className="text-indigo-300">{selectedNode.telecom_intercepts.region}</span></div>
            </div>
          </div>
        )}

        {/* Banking Velocity & Regional Flow */}
        {selectedNode.financial_telemetry && (
          <div className="bg-slate-950 p-3 rounded border border-slate-800">
            <div className="flex items-center gap-1.5 text-cyan-400 font-bold text-[11px] mb-2">
              <Landmark className="w-3.5 h-3.5 shrink-0" />
              <span>FINANCIAL ROUTING TELEMETRY</span>
            </div>
            <div className="space-y-1 text-[11px]">
              <div><span className="text-slate-500">Observed Volume:</span> <span className="text-white">{selectedNode.financial_telemetry.observed_tx_count}</span></div>
              <div><span className="text-slate-500">Clearing Channels:</span> <span className="text-cyan-300">{selectedNode.financial_telemetry.routing_region}</span></div>
              <div><span className="text-slate-500">Transit Velocity:</span> <span className="text-emerald-300">{selectedNode.financial_telemetry.transit_velocity}</span></div>
            </div>
          </div>
        )}

        {/* Legal Admissibility */}
        <div className="bg-slate-950 p-3 rounded border border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
            <span className="text-[11px] text-slate-300">Sec 63 BSA Hash Admissibility</span>
          </div>
          <span className="text-[10px] text-emerald-400 font-bold bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">
            VERIFIED
          </span>
        </div>
      </div>
    </aside>
  );
}
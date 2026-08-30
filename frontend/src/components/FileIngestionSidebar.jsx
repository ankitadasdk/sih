import React, { useState } from 'react';
import { analyzeDocumentFile } from '../services/api';
import { UploadCloud, FileText, ShieldAlert } from 'lucide-react';

export default function FileIngestionSidebar({ onAnalysisComplete }) {
  const [loading, setLoading] = useState(false);
  const [extractedData, setExtractedData] = useState(null);
  const [fileName, setFileName] = useState('');

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileName(file.name);
    setLoading(true);
    const result = await analyzeDocumentFile(file);
    setLoading(false);

    if (result && result.data) {
      setExtractedData(result.data);
      if (onAnalysisComplete) {
        onAnalysisComplete(result.data);
      }
    }
  };

  // Safe extraction fallbacks for both nested and flat schemas
  const charges = extractedData?.statutory_charges || [];
  const phones = extractedData?.tactical_entities?.phone_numbers || extractedData?.phone_numbers || [];
  const imeis = extractedData?.tactical_entities?.imei_numbers || extractedData?.imeis || [];
  const accounts = extractedData?.tactical_entities?.bank_accounts || extractedData?.bank_accounts || [];
  const milestones = extractedData?.judicial_milestones || {};

  return (
    <aside className="w-80 h-full border-r border-slate-800 bg-slate-900/60 flex flex-col p-4 overflow-y-auto shrink-0 z-20">
      <h2 className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-3 font-mono">
        Evidence & FIR Ingestion
      </h2>

      <label className="border-2 border-dashed border-slate-700 hover:border-indigo-500 transition-colors rounded-lg p-5 flex flex-col items-center justify-center cursor-pointer bg-slate-950/40 text-center mb-4">
        <UploadCloud className="w-8 h-8 text-indigo-400 mb-2" />
        <span className="text-xs text-slate-200 font-medium">Upload FIR / Case Document</span>
        <span className="text-[10px] text-slate-500 mt-1">Accepts .PDF or .TXT</span>
        <input
          type="file"
          accept=".pdf,.txt"
          className="hidden"
          onChange={handleFileUpload}
        />
      </label>

      {loading && (
        <div className="text-xs font-mono text-indigo-300 animate-pulse text-center my-2">
          Extracting tactical entities...
        </div>
      )}

      {extractedData && (
        <div className="space-y-3 font-mono text-xs mt-2">
          {fileName && (
            <div className="text-[10px] text-slate-400 truncate flex items-center gap-1">
              <FileText className="w-3 h-3 text-indigo-400" />
              <span>{fileName}</span>
            </div>
          )}

          {/* Charges */}
          <div className="bg-slate-950 p-3 rounded border border-slate-800">
            <span className="text-slate-400 block text-[10px]">CHARGES DETECTED</span>
            <div className="flex flex-wrap gap-1 mt-1.5">
              {charges.length > 0 ? (
                charges.map((sec, i) => (
                  <span key={i} className="bg-red-950/80 text-red-400 px-2 py-0.5 rounded text-[10px] border border-red-800">
                    {sec}
                  </span>
                ))
              ) : (
                <span className="text-slate-500 text-[10px]">None identified</span>
              )}
            </div>
          </div>

          {/* Telephony / Identifiers */}
          <div className="bg-slate-950 p-3 rounded border border-slate-800">
            <span className="text-slate-400 block text-[10px]">PHONE & IMEI IDENTIFIERS</span>
            <div className="mt-1 space-y-1">
              {phones.length > 0 && (
                <p className="text-slate-200 text-[11px] break-all">
                  <span className="text-slate-500">SIM:</span> {phones.join(', ')}
                </p>
              )}
              {imeis.length > 0 && (
                <p className="text-amber-300 text-[11px] break-all">
                  <span className="text-slate-500">IMEI:</span> {imeis.join(', ')}
                </p>
              )}
              {phones.length === 0 && imeis.length === 0 && (
                <span className="text-slate-500 text-[10px]">None detected</span>
              )}
            </div>
          </div>

          {/* Financial Routing */}
          <div className="bg-slate-950 p-3 rounded border border-slate-800">
            <span className="text-slate-400 block text-[10px]">FINANCIAL ACCOUNTS</span>
            <p className="text-cyan-400 text-[11px] mt-1 break-all">
              {accounts.length > 0 ? accounts.join(', ') : <span className="text-slate-500 text-[10px]">None detected</span>}
            </p>
          </div>

          {/* Section 63 BSA Hash & Milestones */}
          {extractedData.section_63_bsa_compliant !== undefined && (
            <div className="bg-slate-950 p-3 rounded border border-slate-800 flex items-center justify-between">
              <span className="text-[10px] text-slate-400">SEC 63 BSA COMPLIANCE</span>
              <span className={extractedData.section_63_bsa_compliant ? "text-emerald-400 text-[10px] font-bold" : "text-amber-400 text-[10px]"}>
                {extractedData.section_63_bsa_compliant ? "VALID HASH CERT" : "MISSING 65B/63 CERT"}
              </span>
            </div>
          )}
        </div>
      )}
    </aside>
  );
}
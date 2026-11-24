import React, { useState } from 'react';
import { 
  FileCheck2, 
  Sparkles, 
  FileText, 
  Bookmark, 
  CheckCircle2, 
  RefreshCw,
  AlertCircle,
  Hash,
  Layers
} from 'lucide-react';
import { api } from '../api';

export default function DocumentSummarizer({ documents = [] }) {
  const [selectedDocId, setSelectedDocId] = useState(documents[0]?.id || '');
  const [summaryFocus, setSummaryFocus] = useState('executive');
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [loadingFacts, setLoadingFacts] = useState(false);
  const [summaryData, setSummaryData] = useState(null);
  const [factsData, setFactsData] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSummarize = async () => {
    if (!selectedDocId) {
      setErrorMsg('Please select a document.');
      return;
    }
    setLoadingSummary(true);
    setErrorMsg('');
    try {
      const res = await api.summarizeDocument({
        document_id: selectedDocId,
        focus: summaryFocus
      });
      setSummaryData(res);
    } catch (err) {
      setErrorMsg(err.message || 'Summarization failed');
    } finally {
      setLoadingSummary(false);
    }
  };

  const handleExtractFacts = async () => {
    setLoadingFacts(true);
    setErrorMsg('');
    try {
      const res = await api.extractFacts({
        document_ids: selectedDocId ? [selectedDocId] : null,
        categories: ["Key Metrics", "Methodology Claims", "Datasets Used", "Quantitative Results"]
      });
      setFactsData(res);
    } catch (err) {
      setErrorMsg(err.message || 'Fact extraction failed');
    } finally {
      setLoadingFacts(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 lg:p-8 space-y-8 bg-slate-950">
      <div>
        <h2 className="text-2xl font-bold text-slate-100 flex items-center space-x-2">
          <FileCheck2 className="w-6 h-6 text-indigo-400" />
          <span>Automated Summarization & Fact Extraction</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Generate structured executive summaries and extract verified numerical metrics, experimental findings, and datasets with page citations.
        </p>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Control Panel */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div>
            <label className="text-slate-400 block mb-1 font-medium">Target Document</label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 font-semibold focus:outline-none min-w-[200px]"
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id} className="bg-slate-900">
                  {d.filename}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-slate-400 block mb-1 font-medium">Summary Focus</label>
            <select
              value={summaryFocus}
              onChange={(e) => setSummaryFocus(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 font-semibold focus:outline-none"
            >
              <option value="executive">Executive Overview</option>
              <option value="methodology">Methodology & Architecture</option>
              <option value="findings">Empirical Results & Findings</option>
            </select>
          </div>
        </div>

        <div className="flex items-center space-x-2 pt-4 sm:pt-0">
          <button
            onClick={handleSummarize}
            disabled={!selectedDocId || loadingSummary}
            className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-xs transition flex items-center space-x-2 shadow-lg shadow-indigo-600/20 cursor-pointer"
          >
            {loadingSummary ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            <span>Summarize Document</span>
          </button>

          <button
            onClick={handleExtractFacts}
            disabled={loadingFacts}
            className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 font-medium text-xs transition flex items-center space-x-2 cursor-pointer"
          >
            {loadingFacts ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Hash className="w-4 h-4 text-indigo-400" />}
            <span>Extract Key Facts</span>
          </button>
        </div>
      </div>

      {/* Summary View */}
      {summaryData && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 animate-fadeIn">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
              <FileText className="w-4 h-4 text-indigo-400" />
              <span>Executive Summary: {summaryData.document_name}</span>
            </h3>
            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
              Grounded
            </span>
          </div>

          <div className="text-sm text-slate-200 leading-relaxed font-serif whitespace-pre-wrap">
            {summaryData.summary}
          </div>

          {/* Key Findings Bullets */}
          {summaryData.key_findings && summaryData.key_findings.length > 0 && (
            <div className="pt-4 border-t border-slate-800 space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Key Empirical Findings
              </h4>
              <div className="space-y-1.5 text-xs">
                {summaryData.key_findings.map((f, i) => (
                  <div key={i} className="flex items-start space-x-2 p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    <span className="text-slate-300">{f}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Facts View */}
      {factsData && (
        <div className="space-y-6 animate-fadeIn">
          <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
            <Hash className="w-5 h-5 text-indigo-400" />
            <span>Extracted Quantitative Facts & Methodological Claims</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(factsData.facts_by_category).map(([cat, facts], idx) => (
              <div key={idx} className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center justify-between">
                  <span>{cat}</span>
                  <span className="text-slate-500 font-mono">({facts.length})</span>
                </h4>
                <div className="space-y-2">
                  {facts.map((f, i) => (
                    <div key={i} className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 text-xs space-y-1">
                      <p className="text-slate-200 font-medium">{f.fact}</p>
                      <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-1">
                        <span>{f.document_name}</span>
                        <span className="text-indigo-400 font-semibold">P.{f.page_number}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useState } from 'react';
import { 
  Scale, 
  Sparkles, 
  CheckSquare, 
  Square, 
  FileText, 
  Bookmark, 
  ArrowRight, 
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { api } from '../api';

export default function ResearchComparison({ documents = [] }) {
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [aspects, setAspects] = useState([
    "Objectives & Problem Statement",
    "Methodology & Architecture",
    "Key Findings & Results",
    "Limitations & Future Work"
  ]);
  const [loading, setLoading] = useState(false);
  const [comparisonResult, setComparisonResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const toggleDoc = (id) => {
    setSelectedDocs(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleCompare = async () => {
    if (selectedDocs.length < 2) {
      setErrorMsg('Please select at least 2 research documents to compare.');
      return;
    }
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await api.compareDocuments({
        document_ids: selectedDocs,
        aspects
      });
      setComparisonResult(res);
    } catch (err) {
      setErrorMsg(err.message || 'Comparison failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 lg:p-8 space-y-8 bg-slate-950">
      <div>
        <h2 className="text-2xl font-bold text-slate-100 flex items-center space-x-2">
          <Scale className="w-6 h-6 text-indigo-400" />
          <span>Multi-Document Research Paper Comparison</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Perform side-by-side comparative analysis of research methodologies, experimental findings, and architectures with cross-document citations.
        </p>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Document Selection Checklist */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200">
            Select Documents for Comparison (Selected: {selectedDocs.length})
          </h3>
          <button
            onClick={() => setSelectedDocs(documents.map(d => d.id))}
            className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
          >
            Select All
          </button>
        </div>

        {documents.length < 2 ? (
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-400 text-center">
            Upload at least 2 research papers or load the benchmark papers to run comparative analysis.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {documents.map((doc) => {
              const isSelected = selectedDocs.includes(doc.id);
              return (
                <div
                  key={doc.id}
                  onClick={() => toggleDoc(doc.id)}
                  className={`p-3.5 rounded-xl border text-xs cursor-pointer flex items-center justify-between transition ${
                    isSelected
                      ? 'bg-indigo-600/20 border-indigo-500/50 text-indigo-200 font-medium'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center space-x-2 truncate pr-2">
                    <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
                    <span className="truncate">{doc.filename}</span>
                  </div>
                  {isSelected ? (
                    <CheckSquare className="w-4 h-4 text-indigo-400 shrink-0" />
                  ) : (
                    <Square className="w-4 h-4 text-slate-600 shrink-0" />
                  )}
                </div>
              );
            })}
          </div>
        )}

        <div className="pt-2">
          <button
            onClick={handleCompare}
            disabled={selectedDocs.length < 2 || loading}
            className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-xs transition flex items-center space-x-2 shadow-lg shadow-indigo-600/20 cursor-pointer"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            <span>{loading ? 'Synthesizing Multi-Paper Comparison...' : 'Generate Side-by-Side Comparison'}</span>
          </button>
        </div>
      </div>

      {/* Comparison Results */}
      {comparisonResult && (
        <div className="space-y-6 animate-fadeIn">
          {/* Executive Summary */}
          <div className="p-6 rounded-2xl bg-indigo-950/30 border border-indigo-500/30 text-xs space-y-2">
            <h4 className="text-sm font-bold text-indigo-200 flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              <span>Comparative Synthesis</span>
            </h4>
            <p className="text-slate-300 leading-relaxed">
              {comparisonResult.executive_summary}
            </p>
          </div>

          {/* Matrix Table */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-950 text-slate-300 uppercase font-bold border-b border-slate-800">
                  <tr>
                    <th className="p-4 w-48 bg-slate-900/90 border-r border-slate-800">Aspect</th>
                    {comparisonResult.document_names.map((name, i) => (
                      <th key={i} className="p-4 border-r border-slate-800 min-w-[280px]">
                        {name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {Object.entries(comparisonResult.comparison_matrix).map(([aspect, docMap], idx) => (
                    <tr key={idx} className="hover:bg-slate-800/20 transition">
                      <td className="p-4 font-bold text-indigo-300 bg-slate-950/40 border-r border-slate-800 align-top">
                        {aspect}
                      </td>
                      {comparisonResult.document_names.map((name, i) => (
                        <td key={i} className="p-4 border-r border-slate-800 align-top leading-relaxed text-[11px]">
                          {docMap[name] || 'Not specified.'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useState } from 'react';
import { 
  FileText, 
  Bookmark, 
  ExternalLink, 
  CheckCircle2, 
  Layers, 
  Hash, 
  ArrowUpRight,
  Sparkles,
  Info
} from 'lucide-react';

export default function CitationPanel({
  citations = [],
  retrievedPassages = [],
  selectedCitation,
  onSelectCitation,
  onClose
}) {
  const [activeView, setActiveView] = useState('citations'); // 'citations' | 'passages'

  return (
    <aside className="w-80 md:w-96 border-l border-slate-800 bg-slate-900/80 backdrop-blur flex flex-col h-full shadow-2xl">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Bookmark className="w-4 h-4 text-indigo-400" />
          <h2 className="text-sm font-bold text-slate-200">Evidence & Citations</h2>
        </div>
        <div className="flex items-center space-x-1 bg-slate-950 p-0.5 rounded-lg border border-slate-800 text-xs">
          <button
            onClick={() => setActiveView('citations')}
            className={`px-2 py-1 rounded font-medium transition ${
              activeView === 'citations' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Citations ({citations.length})
          </button>
          <button
            onClick={() => setActiveView('passages')}
            className={`px-2 py-1 rounded font-medium transition ${
              activeView === 'passages' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Passages ({retrievedPassages.length})
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {activeView === 'citations' ? (
          citations.length === 0 ? (
            <div className="text-center py-12 px-4 text-xs text-slate-500">
              <Info className="w-8 h-8 text-slate-600 mx-auto mb-2 opacity-50" />
              Ask a question to view extracted source citations with exact page numbers.
            </div>
          ) : (
            citations.map((cite, index) => {
              const isSelected = selectedCitation?.id === cite.id;
              return (
                <div
                  key={cite.id || index}
                  onClick={() => onSelectCitation(cite)}
                  className={`p-3.5 rounded-xl border text-xs cursor-pointer transition ${
                    isSelected
                      ? 'bg-indigo-950/40 border-indigo-500/60 shadow-lg shadow-indigo-500/10'
                      : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-slate-200 flex items-center space-x-1.5 truncate">
                      <FileText className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                      <span className="truncate">{cite.document_name}</span>
                    </span>
                    <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 font-mono text-[10px] border border-indigo-500/20 shrink-0">
                      Page {cite.page_number}
                    </span>
                  </div>

                  <p className="text-slate-300 leading-relaxed italic bg-slate-900/80 p-2.5 rounded-lg border border-slate-800/50 mb-2 font-serif text-[11px]">
                    "{cite.excerpt}"
                  </p>

                  <div className="flex items-center justify-between text-[10px] text-slate-400">
                    <span className="flex items-center space-x-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      <span>Chunk #{cite.chunk_index}</span>
                    </span>
                    {cite.score && (
                      <span className="font-mono text-indigo-400 font-semibold">
                        Score: {(cite.score * 100).toFixed(1)}%
                      </span>
                    )}
                  </div>
                </div>
              );
            })
          )
        ) : (
          retrievedPassages.length === 0 ? (
            <div className="text-center py-12 px-4 text-xs text-slate-500">
              No retrieved passages available.
            </div>
          ) : (
            retrievedPassages.map((p, index) => (
              <div
                key={p.id || index}
                className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs space-y-2"
              >
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-semibold text-slate-200 flex items-center space-x-1.5 truncate">
                    <span className="w-4 h-4 rounded-full bg-indigo-600/30 text-indigo-300 font-bold flex items-center justify-center text-[10px]">
                      {index + 1}
                    </span>
                    <span className="truncate">{p.document_name}</span>
                  </span>
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">
                    P.{p.page_number}
                  </span>
                </div>

                <div className="text-slate-300 text-[11px] leading-relaxed bg-slate-900/70 p-2 rounded border border-slate-800/40 font-mono">
                  {p.text}
                </div>

                {/* Score breakdown badge */}
                <div className="grid grid-cols-2 gap-1 text-[10px] font-mono pt-1 border-t border-slate-800/60">
                  <div className="text-slate-400">
                    Dense: <span className="text-cyan-400 font-semibold">{p.dense_score !== null ? (p.dense_score * 100).toFixed(1) + '%' : 'N/A'}</span>
                  </div>
                  <div className="text-slate-400">
                    BM25: <span className="text-amber-400 font-semibold">{p.bm25_score !== null ? (p.bm25_score * 100).toFixed(1) + '%' : 'N/A'}</span>
                  </div>
                  <div className="text-slate-400">
                    Hybrid: <span className="text-indigo-400 font-semibold">{p.hybrid_score !== null ? (p.hybrid_score * 100).toFixed(1) + '%' : 'N/A'}</span>
                  </div>
                  <div className="text-slate-400">
                    Rerank: <span className="text-emerald-400 font-bold">{p.rerank_score !== null ? (p.rerank_score * 100).toFixed(1) + '%' : 'N/A'}</span>
                  </div>
                </div>
              </div>
            ))
          )
        )}
      </div>

      <div className="p-3 border-t border-slate-800 text-[11px] text-slate-500 bg-slate-950/60 flex items-center justify-between">
        <span>Grounded Citation Protocol</span>
        <span className="text-indigo-400 font-semibold">Strict Attribution</span>
      </div>
    </aside>
  );
}

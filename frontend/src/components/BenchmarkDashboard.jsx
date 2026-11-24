import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  Play, 
  Sparkles, 
  Layers, 
  CheckCircle2, 
  TrendingUp, 
  Award,
  RefreshCw,
  HelpCircle,
  Database
} from 'lucide-react';
import { api } from '../api';

export default function BenchmarkDashboard() {
  const [running, setRunning] = useState(false);
  const [report, setReport] = useState(null);
  const [dataset, setDataset] = useState([]);
  const [runs, setRuns] = useState([]);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    loadHistoricalRuns();
    loadDataset();
  }, []);

  const loadHistoricalRuns = async () => {
    try {
      const data = await api.getEvaluationRuns();
      setRuns(data);
    } catch (e) {
      console.error(e);
    }
  };

  const loadDataset = async () => {
    try {
      const data = await api.getBenchmarkDataset();
      setDataset(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleRunBenchmark = async () => {
    setRunning(true);
    setErrorMsg('');
    try {
      const res = await api.runBenchmark({
        chunk_strategies: ["recursive", "page_based"],
        retrieval_modes: ["semantic", "bm25", "hybrid", "hybrid_rerank"]
      });
      setReport(res);
      await loadHistoricalRuns();
    } catch (err) {
      setErrorMsg(err.message || 'Benchmark execution failed');
    } finally {
      setRunning(false);
    }
  };

  const activeRuns = report?.runs || runs;

  return (
    <div className="flex-1 overflow-y-auto p-6 lg:p-8 space-y-8 bg-slate-950">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center space-x-2">
            <BarChart3 className="w-6 h-6 text-indigo-400" />
            <span>Empirical RAG Evaluation & Benchmarking</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Evaluates Recall@K, Mean Reciprocal Rank (MRR), Faithfulness, and Answer Relevance across chunking and retrieval ablations.
          </p>
        </div>

        <button
          onClick={handleRunBenchmark}
          disabled={running}
          className="inline-flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-semibold text-xs shadow-lg shadow-indigo-600/30 transition disabled:opacity-50 cursor-pointer"
        >
          {running ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-white" />}
          <span>{running ? 'Running Grid Benchmark Evaluation...' : 'Run Live Benchmark Grid'}</span>
        </button>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
          {errorMsg}
        </div>
      )}

      {/* Benchmark Summary Pill if report exists */}
      {report?.best_configuration && (
        <div className="p-5 rounded-2xl bg-gradient-to-r from-indigo-950/60 via-slate-900 to-slate-900 border border-indigo-500/30 flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 flex items-center space-x-1">
              <Award className="w-3.5 h-3.5" />
              <span>Optimal Empirical Configuration</span>
            </span>
            <div className="text-sm font-bold text-slate-100">{report.best_configuration}</div>
          </div>
          <span className="text-xs text-emerald-400 font-mono font-semibold px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
            Validated Groundedness
          </span>
        </div>
      )}

      {/* Benchmark Comparison Table */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-indigo-400" />
            <span>Retrieval & Generation Ablation Results</span>
          </h3>
          <span className="text-xs text-slate-400 font-mono">
            Evaluated on {dataset.length} Curated Research Queries
          </span>
        </div>

        {activeRuns.length === 0 ? (
          <div className="text-center py-16 px-4 text-slate-500 text-xs">
            No benchmark runs recorded. Click "Run Live Benchmark Grid" to evaluate all retrieval modes and chunking strategies.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Retrieval Mode</th>
                  <th className="px-4 py-3">Chunk Strategy</th>
                  <th className="px-4 py-3">Recall@1</th>
                  <th className="px-4 py-3">Recall@3</th>
                  <th className="px-4 py-3">Recall@5</th>
                  <th className="px-4 py-3">MRR</th>
                  <th className="px-4 py-3">Faithfulness</th>
                  <th className="px-4 py-3">Answer Relevance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300 font-mono">
                {activeRuns.map((r, i) => {
                  const isTop = r.retrieval_mode.includes('rerank');
                  return (
                    <tr key={r.id || i} className={`hover:bg-slate-800/30 transition ${isTop ? 'bg-indigo-950/20' : ''}`}>
                      <td className="px-4 py-3 font-bold text-slate-200">
                        {r.retrieval_mode.toUpperCase()}
                      </td>
                      <td className="px-4 py-3 text-slate-400 font-sans">{r.chunk_strategy}</td>
                      <td className="px-4 py-3 text-cyan-400 font-bold">{(r.recall_at_1 * 100).toFixed(1)}%</td>
                      <td className="px-4 py-3 text-cyan-400 font-bold">{(r.recall_at_3 * 100).toFixed(1)}%</td>
                      <td className="px-4 py-3 text-cyan-400 font-bold">{(r.recall_at_5 * 100).toFixed(1)}%</td>
                      <td className="px-4 py-3 text-indigo-400 font-bold">{r.mrr.toFixed(3)}</td>
                      <td className="px-4 py-3 text-emerald-400 font-bold">{(r.faithfulness * 100).toFixed(1)}%</td>
                      <td className="px-4 py-3 text-amber-400 font-bold">{(r.answer_relevance * 100).toFixed(1)}%</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Dataset Explorer */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4">
        <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
          <Database className="w-4 h-4 text-indigo-400" />
          <span>Evaluation Test Dataset ({dataset.length} Queries)</span>
        </h3>
        <p className="text-xs text-slate-400">
          Curated ground-truth test collection used to evaluate ranking quality, passage attribution, and answer faithfulness without synthetic hallucination.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          {dataset.map((q) => (
            <div key={q.id} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 space-y-2">
              <div className="font-semibold text-slate-200">{q.query}</div>
              <p className="text-[11px] text-slate-400 leading-relaxed font-serif bg-slate-900/50 p-2 rounded">
                Expected: {q.expected_answer}
              </p>
              <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
                <span>Targets: {q.relevant_doc_names.join(', ')}</span>
                <span className="text-indigo-400">Pages: {q.relevant_pages.join(', ')}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

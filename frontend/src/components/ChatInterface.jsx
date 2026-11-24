import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Sparkles, 
  Layers, 
  Sliders, 
  Clock, 
  CheckCircle2, 
  AlertTriangle, 
  FileText, 
  ChevronDown, 
  Bookmark,
  RefreshCw,
  ExternalLink,
  HelpCircle,
  Cpu
} from 'lucide-react';

export default function ChatInterface({
  conversation,
  documents = [],
  onSendMessage,
  loading,
  selectedCitation,
  onSelectCitation,
  onOpenCitationPanel
}) {
  const [input, setInput] = useState('');
  const [searchMode, setSearchMode] = useState('hybrid_rerank');
  const [selectedDocId, setSelectedDocId] = useState('');
  const [temperature, setTemperature] = useState(0.1);
  const [showSettings, setShowSettings] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation?.messages, loading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    onSendMessage({
      query: input.trim(),
      search_mode: searchMode,
      document_ids: selectedDocId ? [selectedDocId] : null,
      temperature,
    });
    setInput('');
  };

  const sampleQueries = [
    "What is the computational complexity of self-attention in Transformers?",
    "How does hybrid search combine dense vectors and sparse BM25?",
    "What role does the Cross-Encoder reranker play in two-stage retrieval?",
    "How does page-level chunking prevent cross-page citation errors?"
  ];

  const renderMessageContent = (msg) => {
    if (msg.role === 'user') {
      return <div className="text-sm font-medium text-slate-100">{msg.content}</div>;
    }

    // Format inline citations like [Doc, p.X] into clickable pills
    const parts = msg.content.split(/(\[[^\]]+,\s*p\.\d+\])/g);
    return (
      <div className="space-y-3">
        <div className="text-sm text-slate-200 leading-relaxed font-normal whitespace-pre-wrap">
          {parts.map((part, i) => {
            if (/^\[[^\]]+,\s*p\.\d+\]$/.test(part)) {
              return (
                <button
                  key={i}
                  onClick={() => {
                    // Find matching citation or construct
                    const cite = (msg.citations || []).find(c => part.includes(c.document_name) || part.includes(`p.${c.page_number}`));
                    onSelectCitation(cite || { document_name: part, page_number: '', excerpt: part });
                    onOpenCitationPanel?.();
                  }}
                  className="inline-flex items-center mx-1 px-1.5 py-0.5 rounded text-[11px] font-mono font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 hover:bg-indigo-600 hover:text-white transition cursor-pointer"
                  title="View verified source passage"
                >
                  <Bookmark className="w-2.5 h-2.5 mr-0.5" />
                  {part}
                </button>
              );
            }
            return part;
          })}
        </div>

        {/* Message Metadata Footer */}
        <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center justify-between text-[11px] text-slate-400 gap-2">
          <div className="flex items-center space-x-2">
            {msg.content.includes("insufficient information") || msg.unavailable_info ? (
              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
                <AlertTriangle className="w-3 h-3" />
                <span>Information Unavailable</span>
              </span>
            ) : (
              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                <CheckCircle2 className="w-3 h-3" />
                <span>Grounded with Citations</span>
              </span>
            )}

            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">
              {msg.search_mode?.replace('_', ' ').toUpperCase() || 'HYBRID'}
            </span>
          </div>

          {msg.citations && msg.citations.length > 0 && (
            <button
              onClick={() => {
                onSelectCitation(msg.citations[0]);
                onOpenCitationPanel?.();
              }}
              className="text-indigo-400 hover:text-indigo-300 font-medium flex items-center space-x-1"
            >
              <span>{msg.citations.length} Sources Cited</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 overflow-hidden">
      {/* Control Bar */}
      <div className="px-6 py-3 border-b border-slate-800/80 bg-slate-900/40 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-3">
          {/* Search Mode Selector */}
          <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-slate-400">Mode:</span>
            <select
              value={searchMode}
              onChange={(e) => setSearchMode(e.target.value)}
              className="bg-transparent text-slate-200 font-semibold focus:outline-none cursor-pointer"
            >
              <option value="hybrid_rerank" className="bg-slate-900">Hybrid + Reranker (Best)</option>
              <option value="hybrid" className="bg-slate-900">Hybrid (RRF Dense+BM25)</option>
              <option value="semantic" className="bg-slate-900">Semantic Dense Only</option>
              <option value="bm25" className="bg-slate-900">BM25 Keyword Only</option>
            </select>
          </div>

          {/* Document Filter */}
          <div className="hidden sm:flex items-center space-x-2 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5">
            <FileText className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-slate-400">Scope:</span>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="bg-transparent text-slate-200 font-semibold focus:outline-none cursor-pointer max-w-[140px] truncate"
            >
              <option value="" className="bg-slate-900">All Documents ({documents.length})</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id} className="bg-slate-900 truncate">
                  {d.filename}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Settings Toggle */}
        <button
          onClick={() => setShowSettings(!showSettings)}
          className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg border transition ${
            showSettings ? 'bg-indigo-600/20 border-indigo-500/40 text-indigo-300' : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          <span className="hidden md:inline">RAG Parameters</span>
        </button>
      </div>

      {/* Advanced Drawer */}
      {showSettings && (
        <div className="px-6 py-3 border-b border-slate-800 bg-slate-900/90 text-xs flex items-center space-x-6 animate-fadeIn">
          <div className="flex items-center space-x-2">
            <span className="text-slate-400">Temperature:</span>
            <input
              type="range"
              min="0"
              max="0.8"
              step="0.05"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              className="w-24 accent-indigo-500"
            />
            <span className="font-mono text-indigo-400 font-semibold">{temperature}</span>
          </div>
          <div className="text-slate-400 text-[11px]">
            Lower temperature yields strictly grounded and reproducible scientific citations.
          </div>
        </div>
      )}

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-8 py-6 space-y-6">
        {(!conversation?.messages || conversation.messages.length === 0) ? (
          <div className="max-w-2xl mx-auto py-12 text-center space-y-6">
            <div className="w-16 h-16 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center mx-auto text-indigo-400 shadow-xl shadow-indigo-500/10">
              <Sparkles className="w-8 h-8" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-100">Enterprise AI Research Assistant</h3>
              <p className="text-xs text-slate-400 mt-2 max-w-md mx-auto">
                Ask multi-document research questions. Every response is strictly grounded in retrieved evidence with physical page-level source citations.
              </p>
            </div>

            {/* Quick Prompts */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-left pt-4">
              {sampleQueries.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => setInput(q)}
                  className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-indigo-500/40 text-xs text-slate-300 hover:text-white transition flex items-start space-x-2"
                >
                  <HelpCircle className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                  <span>{q}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          conversation.messages.map((msg, index) => {
            const isUser = msg.role === 'user';
            return (
              <div
                key={msg.id || index}
                className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-3xl rounded-2xl p-4 shadow-sm ${
                    isUser
                      ? 'bg-indigo-600 text-white rounded-br-none'
                      : 'bg-slate-900/90 border border-slate-800 rounded-bl-none'
                  }`}
                >
                  {renderMessageContent(msg)}
                </div>
              </div>
            );
          })
        )}

        {loading && (
          <div className="flex justify-start">
            <div className="max-w-xl rounded-2xl rounded-bl-none p-4 bg-slate-900 border border-slate-800 flex items-center space-x-3 text-xs text-indigo-400">
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Synthesizing cross-document evidence & verifying citations...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/60">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto flex items-center space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a technical or empirical research question (e.g. self-attention complexity, hybrid search...)"
            className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition shadow-inner"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-sm transition flex items-center space-x-2 shadow-lg shadow-indigo-600/30 cursor-pointer"
          >
            <span>Ask</span>
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}

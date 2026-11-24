import React from 'react';
import { 
  Cpu, 
  Layers, 
  MessageSquare, 
  FileText, 
  Scale, 
  FileCheck2, 
  BarChart3,
  Sparkles,
  ShieldCheck,
  Activity
} from 'lucide-react';

export default function Header({ 
  activeTab, 
  setActiveTab, 
  health, 
  provider, 
  setProvider,
  availableProviders = ['mock', 'openai', 'gemini', 'anthropic', 'ollama']
}) {
  const tabs = [
    { id: 'chat', label: 'Research Chat', icon: MessageSquare },
    { id: 'documents', label: 'Documents & Chunks', icon: FileText },
    { id: 'compare', label: 'Paper Comparison', icon: Scale },
    { id: 'summarize', label: 'Summaries & Facts', icon: FileCheck2 },
    { id: 'benchmark', label: 'RAG Benchmarks', icon: BarChart3 },
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-0.5 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Cpu className="w-5 h-5 text-indigo-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-indigo-300 bg-clip-text text-transparent">
                  NeuralSearch
                </span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300">
                  Enterprise RAG
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">AI Knowledge & Research Assistant</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex space-x-1 sm:space-x-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30 font-semibold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden md:inline">{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Status & Model Provider Config */}
          <div className="flex items-center space-x-3">
            {/* LLM Provider Selector */}
            <div className="hidden lg:flex items-center space-x-2 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              <span className="text-slate-400">LLM:</span>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="bg-transparent text-slate-200 font-semibold focus:outline-none cursor-pointer"
              >
                {availableProviders.map((p) => (
                  <option key={p} value={p} className="bg-slate-900 text-slate-200">
                    {p.toUpperCase()} {p === 'mock' ? '(Hermetic / Zero-Cost)' : ''}
                  </option>
                ))}
              </select>
            </div>

            {/* Health Indicator */}
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="font-medium hidden sm:inline">Engine Active</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

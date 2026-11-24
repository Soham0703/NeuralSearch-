import React, { useState } from 'react';
import { 
  Upload, 
  FileText, 
  Trash2, 
  RefreshCw, 
  Layers, 
  Sliders, 
  CheckCircle, 
  AlertCircle,
  FileDown,
  Sparkles,
  BookOpen,
  Eye,
  X
} from 'lucide-react';
import { api } from '../api';

export default function DocumentManager({
  documents = [],
  onRefresh,
  loading
}) {
  const [uploading, setUploading] = useState(false);
  const [chunkStrategy, setChunkStrategy] = useState('recursive');
  const [chunkSize, setChunkSize] = useState(500);
  const [chunkOverlap, setChunkOverlap] = useState(100);
  const [inspectChunks, setInspectChunks] = useState(null);
  const [selectedDocChunks, setSelectedDocChunks] = useState([]);
  const [chunksLoading, setChunksLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setErrorMsg('');
    setSuccessMsg('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('chunk_strategy', chunkStrategy);
    formData.append('chunk_size', chunkSize.toString());
    formData.append('chunk_overlap', chunkOverlap.toString());

    try {
      const res = await api.uploadDocument(formData);
      setSuccessMsg(`Successfully uploaded & indexed ${res.filename} (${res.chunk_count} chunks, ${res.page_count} pages)`);
      onRefresh();
    } catch (err) {
      setErrorMsg(err.message || 'Upload failed');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleLoadSamples = async () => {
    setUploading(true);
    setErrorMsg('');
    try {
      const res = await api.loadSampleDocuments();
      setSuccessMsg(res.message);
      onRefresh();
    } catch (err) {
      setErrorMsg(err.message || 'Failed to load sample papers');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId, filename) => {
    if (!confirm(`Are you sure you want to delete ${filename}?`)) return;
    try {
      await api.deleteDocument(docId);
      setSuccessMsg(`Deleted ${filename}`);
      onRefresh();
    } catch (err) {
      setErrorMsg(err.message || 'Delete failed');
    }
  };

  const handleReindex = async (docId) => {
    try {
      await api.reindexDocument(docId, {
        chunk_strategy: chunkStrategy,
        chunk_size: chunkSize,
        chunk_overlap: chunkOverlap
      });
      setSuccessMsg('Document successfully re-indexed with new chunking settings.');
      onRefresh();
    } catch (err) {
      setErrorMsg(err.message || 'Re-index failed');
    }
  };

  const handleInspect = async (doc) => {
    setInspectChunks(doc);
    setChunksLoading(true);
    try {
      const chunks = await api.getDocumentChunks(doc.id);
      setSelectedDocChunks(chunks);
    } catch (err) {
      setSelectedDocChunks([]);
    } finally {
      setChunksLoading(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 lg:p-8 space-y-8 bg-slate-950">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center space-x-2">
            <BookOpen className="w-6 h-6 text-indigo-400" />
            <span>Document Processing & Ingestion Engine</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Upload scientific PDFs, DOCX, and TXT files. Automatic page extraction, recursive chunking, and dual vector/keyword indexing.
          </p>
        </div>

        <button
          onClick={handleLoadSamples}
          disabled={uploading}
          className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-600 hover:text-white transition text-xs font-semibold shadow-lg shadow-indigo-600/10 cursor-pointer"
        >
          <Sparkles className="w-4 h-4" />
          <span>Load Curated Benchmark Papers</span>
        </button>
      </div>

      {/* Notifications */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}
      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center space-x-2">
          <CheckCircle className="w-4 h-4 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Ingestion & Chunking Strategy Settings */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Upload Zone */}
        <div className="md:col-span-2 p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-200 mb-1">Upload New Document</h3>
            <p className="text-xs text-slate-400 mb-4">
              Extracts text preserving page numbers, generates dense SentenceTransformer embeddings and BM25 tokens.
            </p>

            <label className="border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer transition bg-slate-950/40 group">
              <Upload className="w-8 h-8 text-slate-400 group-hover:text-indigo-400 mb-2 transition" />
              <span className="text-xs font-semibold text-slate-200">
                {uploading ? 'Processing & Indexing Document...' : 'Click or drag PDF, DOCX, or TXT file'}
              </span>
              <span className="text-[11px] text-slate-500 mt-1">Supports PDF (with page metadata), DOCX, TXT</span>
              <input
                type="file"
                accept=".pdf,.docx,.doc,.txt,.md"
                onChange={handleFileUpload}
                disabled={uploading}
                className="hidden"
              />
            </label>
          </div>
        </div>

        {/* Chunking Config */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-indigo-400" />
            <span>Chunking Strategy</span>
          </h3>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-400 block mb-1 font-medium">Strategy</label>
              <select
                value={chunkStrategy}
                onChange={(e) => setChunkStrategy(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 font-semibold focus:outline-none focus:border-indigo-500"
              >
                <option value="recursive">Recursive Character (Hierarchical)</option>
                <option value="page_based">Page-Preserving (Exact Attribution)</option>
                <option value="semantic">Semantic Paragraph (Topic Breaks)</option>
              </select>
            </div>

            <div>
              <div className="flex justify-between text-slate-400 mb-1">
                <span>Target Chunk Size</span>
                <span className="font-mono text-indigo-400 font-semibold">{chunkSize} chars</span>
              </div>
              <input
                type="range"
                min="200"
                max="1200"
                step="50"
                value={chunkSize}
                onChange={(e) => setChunkSize(parseInt(e.target.value))}
                className="w-full accent-indigo-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-slate-400 mb-1">
                <span>Chunk Overlap</span>
                <span className="font-mono text-indigo-400 font-semibold">{chunkOverlap} chars</span>
              </div>
              <input
                type="range"
                min="0"
                max="300"
                step="25"
                value={chunkOverlap}
                onChange={(e) => setChunkOverlap(parseInt(e.target.value))}
                className="w-full accent-indigo-500"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Document Library Table */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
            <FileText className="w-4 h-4 text-indigo-400" />
            <span>Indexed Document Repository ({documents.length})</span>
          </h3>
          <button
            onClick={onRefresh}
            className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white transition"
            title="Refresh documents"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {documents.length === 0 ? (
          <div className="text-center py-16 px-4 text-slate-500 text-xs">
            No research documents uploaded yet. Upload a document or click "Load Curated Benchmark Papers" above.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 uppercase font-semibold border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Document Name</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Pages</th>
                  <th className="px-4 py-3">Chunks</th>
                  <th className="px-4 py-3">Strategy</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-800/30 transition">
                    <td className="px-4 py-3 font-medium text-slate-200 flex items-center space-x-2">
                      <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
                      <span className="truncate max-w-xs">{doc.filename}</span>
                    </td>
                    <td className="px-4 py-3 uppercase font-mono text-[10px] text-slate-400">{doc.file_type}</td>
                    <td className="px-4 py-3 font-mono">{doc.page_count}</td>
                    <td className="px-4 py-3 font-mono text-indigo-400 font-semibold">{doc.chunk_count}</td>
                    <td className="px-4 py-3 text-slate-400">{doc.chunk_strategy}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {doc.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right space-x-2">
                      <button
                        onClick={() => handleInspect(doc)}
                        className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition text-[11px]"
                      >
                        Inspect Chunks
                      </button>
                      <button
                        onClick={() => handleReindex(doc.id)}
                        className="px-2.5 py-1 rounded-lg bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white transition text-[11px]"
                        title="Re-chunk with current settings"
                      >
                        Re-Index
                      </button>
                      <button
                        onClick={() => handleDelete(doc.id, doc.filename)}
                        className="p-1 rounded-lg hover:bg-red-500/20 text-slate-500 hover:text-red-400 transition"
                        title="Delete Document"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Inspect Chunks Modal */}
      {inspectChunks && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-3xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl flex flex-col max-h-[85vh] overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-100 flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-indigo-400" />
                  <span>Chunk Inspector: {inspectChunks.filename}</span>
                </h3>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Total Chunks: {selectedDocChunks.length} | Strategy: {inspectChunks.chunk_strategy}
                </p>
              </div>
              <button
                onClick={() => setInspectChunks(null)}
                className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4 overflow-y-auto space-y-3 flex-1">
              {chunksLoading ? (
                <div className="text-center py-12 text-slate-400 text-xs">Loading chunks...</div>
              ) : selectedDocChunks.length === 0 ? (
                <div className="text-center py-12 text-slate-500 text-xs">No chunks found.</div>
              ) : (
                selectedDocChunks.map((c) => (
                  <div key={c.id} className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 text-xs space-y-2">
                    <div className="flex items-center justify-between text-[11px] text-slate-400">
                      <span className="font-semibold text-indigo-400">Chunk #{c.chunk_index}</span>
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">
                        Page {c.page_number}
                      </span>
                    </div>
                    <p className="text-slate-300 font-mono text-[11px] leading-relaxed bg-slate-900/60 p-2.5 rounded border border-slate-800/40">
                      {c.text}
                    </p>
                    <div className="flex items-center space-x-4 text-[10px] text-slate-500">
                      <span>Chars: {c.start_char} - {c.end_char}</span>
                      <span>Est. Tokens: {c.token_count}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

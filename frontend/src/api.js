const API_BASE = '/api';

export const api = {
  // Health & Config
  getHealth: async () => {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Failed to fetch health');
    return res.json();
  },
  getConfig: async () => {
    const res = await fetch(`${API_BASE}/config`);
    if (!res.ok) throw new Error('Failed to fetch config');
    return res.json();
  },

  // Documents
  getDocuments: async () => {
    const res = await fetch(`${API_BASE}/documents`);
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
  },
  uploadDocument: async (formData) => {
    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },
  getDocumentChunks: async (documentId) => {
    const res = await fetch(`${API_BASE}/documents/${documentId}/chunks`);
    if (!res.ok) throw new Error('Failed to fetch chunks');
    return res.json();
  },
  deleteDocument: async (documentId) => {
    const res = await fetch(`${API_BASE}/documents/${documentId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Delete failed');
    return res.json();
  },
  reindexDocument: async (documentId, data) => {
    const res = await fetch(`${API_BASE}/documents/${documentId}/reindex`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Reindex failed');
    return res.json();
  },
  loadSampleDocuments: async () => {
    const res = await fetch(`${API_BASE}/documents/load-samples`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to load sample documents');
    return res.json();
  },
  rebuildIndices: async () => {
    const res = await fetch(`${API_BASE}/documents/index/rebuild`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to rebuild indices');
    return res.json();
  },

  // RAG & Chat
  sendChat: async (payload) => {
    const res = await fetch(`${API_BASE}/rag/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Chat query failed');
    }
    return res.json();
  },
  compareDocuments: async (payload) => {
    const res = await fetch(`${API_BASE}/rag/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Comparison failed');
    return res.json();
  },
  summarizeDocument: async (payload) => {
    const res = await fetch(`${API_BASE}/rag/summarize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Summarization failed');
    return res.json();
  },
  extractFacts: async (payload) => {
    const res = await fetch(`${API_BASE}/rag/extract-facts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Fact extraction failed');
    return res.json();
  },

  // Conversations
  getConversations: async () => {
    const res = await fetch(`${API_BASE}/conversations`);
    if (!res.ok) throw new Error('Failed to fetch conversations');
    return res.json();
  },
  createConversation: async (title = 'New Research Session') => {
    const res = await fetch(`${API_BASE}/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    });
    if (!res.ok) throw new Error('Failed to create conversation');
    return res.json();
  },
  getConversation: async (id) => {
    const res = await fetch(`${API_BASE}/conversations/${id}`);
    if (!res.ok) throw new Error('Failed to fetch conversation');
    return res.json();
  },
  deleteConversation: async (id) => {
    const res = await fetch(`${API_BASE}/conversations/${id}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete conversation');
    return res.json();
  },

  // Evaluation & Benchmark
  runBenchmark: async (config) => {
    const res = await fetch(`${API_BASE}/eval/benchmark`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config || {}),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Benchmark failed');
    }
    return res.json();
  },
  getEvaluationRuns: async () => {
    const res = await fetch(`${API_BASE}/eval/runs`);
    if (!res.ok) throw new Error('Failed to fetch evaluation runs');
    return res.json();
  },
  getBenchmarkDataset: async () => {
    const res = await fetch(`${API_BASE}/eval/dataset`);
    if (!res.ok) throw new Error('Failed to fetch dataset');
    return res.json();
  },
};

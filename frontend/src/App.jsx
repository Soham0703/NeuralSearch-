import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import ConversationSidebar from './components/ConversationSidebar';
import ChatInterface from './components/ChatInterface';
import CitationPanel from './components/CitationPanel';
import DocumentManager from './components/DocumentManager';
import ResearchComparison from './components/ResearchComparison';
import DocumentSummarizer from './components/DocumentSummarizer';
import BenchmarkDashboard from './components/BenchmarkDashboard';
import { api } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' | 'documents' | 'compare' | 'summarize' | 'benchmark'
  const [documents, setDocuments] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [showCitationPanel, setShowCitationPanel] = useState(true);
  const [loading, setLoading] = useState(false);
  const [provider, setProvider] = useState('mock');
  const [health, setHealth] = useState(null);

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      const [healthData, docsData, convsData] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getDocuments().catch(() => ({ documents: [] })),
        api.getConversations().catch(() => ({ conversations: [] }))
      ]);

      setHealth(healthData);
      setDocuments(docsData.documents || []);
      setConversations(convsData.conversations || []);

      if (convsData.conversations && convsData.conversations.length > 0) {
        loadConversation(convsData.conversations[0].id);
      } else {
        handleNewConversation();
      }
    } catch (err) {
      console.error('Error initializing app:', err);
    }
  };

  const loadConversation = async (id) => {
    try {
      const conv = await api.getConversation(id);
      setCurrentConversation(conv);
      // Auto select first citation if available in latest message
      const lastMsg = conv.messages?.[conv.messages.length - 1];
      if (lastMsg?.citations?.[0]) {
        setSelectedCitation(lastMsg.citations[0]);
      }
    } catch (err) {
      console.error('Failed to load conversation:', err);
    }
  };

  const handleNewConversation = async () => {
    try {
      const newConv = await api.createConversation('New Research Session');
      setConversations(prev => [newConv, ...prev]);
      setCurrentConversation(newConv);
      setSelectedCitation(null);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteConversation = async (id) => {
    try {
      await api.deleteConversation(id);
      setConversations(prev => prev.filter(c => c.id !== id));
      if (currentConversation?.id === id) {
        const remaining = conversations.filter(c => c.id !== id);
        if (remaining.length > 0) {
          loadConversation(remaining[0].id);
        } else {
          handleNewConversation();
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSendMessage = async ({ query, search_mode, document_ids, temperature }) => {
    setLoading(true);
    try {
      const res = await api.sendChat({
        query,
        conversation_id: currentConversation?.id,
        search_mode,
        document_ids,
        temperature,
        llm_provider: provider
      });

      // Reload updated conversation
      await loadConversation(res.conversation_id);
      if (res.citations && res.citations.length > 0) {
        setSelectedCitation(res.citations[0]);
      }
    } catch (err) {
      console.error('Chat error:', err);
      alert('Error querying RAG assistant: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const refreshDocuments = async () => {
    try {
      const data = await api.getDocuments();
      setDocuments(data.documents || []);
    } catch (err) {
      console.error(err);
    }
  };

  // Extract latest citations and retrieved passages from current conversation
  const latestMessage = currentConversation?.messages?.filter(m => m.role === 'assistant')?.slice(-1)?.[0];
  const activeCitations = latestMessage?.citations || [];
  const activePassages = latestMessage?.retrieved_chunks || [];

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 overflow-hidden">
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        health={health}
        provider={provider}
        setProvider={setProvider}
      />

      <div className="flex-1 flex overflow-hidden">
        {activeTab === 'chat' && (
          <>
            <ConversationSidebar
              conversations={conversations}
              currentConversationId={currentConversation?.id}
              onSelectConversation={loadConversation}
              onNewConversation={handleNewConversation}
              onDeleteConversation={handleDeleteConversation}
            />

            <ChatInterface
              conversation={currentConversation}
              documents={documents}
              onSendMessage={handleSendMessage}
              loading={loading}
              selectedCitation={selectedCitation}
              onSelectCitation={setSelectedCitation}
              onOpenCitationPanel={() => setShowCitationPanel(true)}
            />

            {showCitationPanel && (
              <CitationPanel
                citations={activeCitations}
                retrievedPassages={activePassages}
                selectedCitation={selectedCitation}
                onSelectCitation={setSelectedCitation}
                onClose={() => setShowCitationPanel(false)}
              />
            )}
          </>
        )}

        {activeTab === 'documents' && (
          <DocumentManager
            documents={documents}
            onRefresh={refreshDocuments}
            loading={loading}
          />
        )}

        {activeTab === 'compare' && (
          <ResearchComparison
            documents={documents}
          />
        )}

        {activeTab === 'summarize' && (
          <DocumentSummarizer
            documents={documents}
          />
        )}

        {activeTab === 'benchmark' && (
          <BenchmarkDashboard />
        )}
      </div>
    </div>
  );
}

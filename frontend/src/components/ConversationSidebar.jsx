import React from 'react';
import { Plus, MessageSquare, Trash2, Calendar, FileText } from 'lucide-react';

export default function ConversationSidebar({
  conversations = [],
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
}) {
  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/60 flex flex-col h-full select-none">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-2">
          <MessageSquare className="w-3.5 h-3.5 text-indigo-400" />
          <span>Research Sessions</span>
        </h2>
        <button
          onClick={onNewConversation}
          title="New Research Session"
          className="p-1.5 rounded-lg bg-indigo-600/20 border border-indigo-500/30 text-indigo-400 hover:bg-indigo-600 hover:text-white transition"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {conversations.length === 0 ? (
          <div className="text-center py-8 px-4 text-xs text-slate-500">
            No previous sessions. Start a new research query!
          </div>
        ) : (
          conversations.map((conv) => {
            const isSelected = conv.id === currentConversationId;
            return (
              <div
                key={conv.id}
                onClick={() => onSelectConversation(conv.id)}
                className={`group flex items-center justify-between px-3 py-2.5 rounded-lg text-xs cursor-pointer transition ${
                  isSelected
                    ? 'bg-indigo-600/20 border border-indigo-500/40 text-indigo-200 font-medium'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                }`}
              >
                <div className="truncate flex-1 pr-2">
                  <div className="truncate text-slate-200 font-medium">
                    {conv.title || 'Untitled Session'}
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    {new Date(conv.created_at).toLocaleDateString()}
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteConversation(conv.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-500/20 text-slate-500 hover:text-red-400 transition"
                  title="Delete Session"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>

      <div className="p-3 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
        <span>Sessions: {conversations.length}</span>
        <span className="text-indigo-400 font-medium">Persistent DB</span>
      </div>
    </aside>
  );
}

import React, { memo, useCallback } from 'react';
import {
  Plus,
  MessageSquare,
  Trash2,
  X
} from 'lucide-react';
import relanceLogo from '../assets/reliance-logo.svg'; // Import the logo

// Helper function to group sessions by date
function groupSessionsByDate(sessions) {
  const groups = {
    'Today': [],
    'Yesterday': [],
    'Previous 7 Days': [],
    'Previous 30 Days': [],
    'Older': [],
  };

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const weekAgo = new Date(today);
  weekAgo.setDate(weekAgo.getDate() - 7);
  const monthAgo = new Date(today);
  monthAgo.setDate(monthAgo.getDate() - 30);

  sessions.forEach(session => {
    const sessionDate = new Date(session.updated_at || session.created_at);

    if (sessionDate >= today) {
      groups['Today'].push(session);
    } else if (sessionDate >= yesterday) {
      groups['Yesterday'].push(session);
    } else if (sessionDate >= weekAgo) {
      groups['Previous 7 Days'].push(session);
    } else if (sessionDate >= monthAgo) {
      groups['Previous 30 Days'].push(session);
    } else {
      groups['Older'].push(session);
    }
  });

  return groups;
}

function Sidebar({
  isOpen,
  sessions,
  currentSessionId,
  stats,
  onNewChat,
  onSelectSession,
  onDeleteSession,
  onClearHistory,
  onClose
}) {
  const groupedSessions = groupSessionsByDate(sessions);

  return (
    <aside
      className={`
        fixed lg:relative inset-y-0 left-0 z-40
        w-72 flex flex-col
        bg-gray-50 dark:bg-dark-surface/95
        border-r border-gray-200 dark:border-dark-border/50
        dark:shadow-[1px_0_20px_rgba(0,0,0,0.3)]
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-0 lg:overflow-hidden'}
      `}
    >
      {/* Header with Logo */}
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-3">
          {/* Company Logo */}
          <img
            src={relanceLogo}
            alt="Reliance Logo"
            className="h-10 w-auto object-contain transition-all duration-300"
            style={{
              filter: 'var(--logo-filter, none)'
            }}
          />
        </div>
        {/* Close button for mobile */}
        <button
          onClick={onClose}
          className="lg:hidden btn-icon text-charcoal-600 dark:text-gray-400"
        >
          <X size={20} />
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl
            border-2 border-dashed border-gray-300 dark:border-dark-border
            text-charcoal-700 dark:text-gray-300
            hover:border-blue-500 hover:text-blue-600 dark:hover:text-blue-400 hover:shadow-[0_0_15px_rgba(59,130,246,0.25)]
            hover:bg-blue-500/5
            transition-smooth"
        >
          <Plus size={18} strokeWidth={2.5} />
          <span className="font-medium">New Chat</span>
        </button>
      </div>

      {/* Chat History */}
      <nav className="flex-1 overflow-y-auto scrollbar-thin px-3 py-2">
        {Object.entries(groupedSessions).map(([group, groupSessions]) => (
          groupSessions.length > 0 && (
            <div key={group} className="mb-4">
              <h3 className="px-3 py-2 text-xs font-semibold uppercase tracking-wider text-charcoal-500 dark:text-gray-500">
                {group}
              </h3>
              <ul className="space-y-1">
                {groupSessions.map((session) => (
                  <li key={session.id}>
                    <div
                      onClick={() => onSelectSession(session)}
                      className={`sidebar-item group ${currentSessionId === session.id ? 'active' : ''}`}
                    >
                      <MessageSquare size={16} className="flex-shrink-0" />
                      <span className="flex-1 truncate text-sm">
                        {session.title?.substring(0, 28) || 'New Chat'}
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteSession(session.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 rounded-lg
                          hover:bg-red-500/10 text-charcoal-500 hover:text-red-500
                          transition-smooth"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )
        ))}

        {sessions.length === 0 && (
          <div className="text-center py-8 text-charcoal-500 dark:text-gray-500">
            <MessageSquare size={32} className="mx-auto mb-2 opacity-50" />
            <p className="text-sm">No conversations yet</p>
          </div>
        )}
      </nav>

      {/* Footer */}
      <div className="border-t border-gray-200 dark:border-dark-border p-3 space-y-3">
        {/* Clear History */}
        <button
          onClick={onClearHistory}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl
            text-sm text-charcoal-600 dark:text-gray-400
            hover:bg-red-500/10 hover:text-red-500
            transition-smooth"
        >
          <Trash2 size={16} />
          <span>Clear All History</span>
        </button>
      </div>
    </aside>
  );
}

export default memo(Sidebar);
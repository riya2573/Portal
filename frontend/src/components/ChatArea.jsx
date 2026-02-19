import React, { useRef, useEffect, memo, useCallback } from 'react';
import { Menu, Sun, Moon, AlertCircle } from 'lucide-react';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';

function ChatArea({
  messages,
  loading,
  apiConnected,
  darkMode,
  availableTopics = [],
  selectedTopics = [],
  onSendMessage,
  onRegenerate,
  onToggleDarkMode,
  onToggleSidebar,
  onToggleTopic,
  onClearTopics
}) {
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 flex flex-col min-w-0">
      {/* Top Bar */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-dark-border/50 bg-white dark:bg-dark-surface/80 dark:backdrop-blur-sm">
        <div className="flex items-center gap-3">
          {/* Menu toggle */}
          <button
            onClick={onToggleSidebar}
            className="btn-icon text-charcoal-600 dark:text-gray-400"
          >
            <Menu size={20} />
          </button>

          {/* Logo and Model name */}
          <div className="flex items-center gap-3">
            <div className="logo-circle">
              <span className="text-xs font-bold">KM</span>
            </div>
            <div className="hidden sm:block">
              <h1 className="text-sm font-semibold text-charcoal-800 dark:text-gray-100">
                RPMG KM ChatBot
              </h1>
              <p className="text-xs text-charcoal-500 dark:text-gray-500">
                Document Assistant
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Connection status */}
          {!apiConnected && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500/10 text-red-600 dark:text-red-400 text-xs">
              <AlertCircle size={14} />
              <span className="hidden sm:inline">Disconnected</span>
            </div>
          )}

          {/* Dark mode toggle */}
          <button
            onClick={onToggleDarkMode}
            className="btn-icon text-charcoal-600 dark:text-gray-400"
            title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {darkMode ? <Sun size={20} /> : <Moon size={20} />}
          </button>
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {messages.length === 0 ? (
          <WelcomeScreen onSendMessage={onSendMessage} />
        ) : (
          <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onRegenerate={message.type === 'assistant' ? onRegenerate : null}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="bg-white dark:bg-dark-surface/80 dark:backdrop-blur-sm">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <ChatInput
            onSendMessage={onSendMessage}
            loading={loading}
            disabled={!apiConnected}
            availableTopics={availableTopics}
            selectedTopics={selectedTopics}
            onToggleTopic={onToggleTopic}
            onClearTopics={onClearTopics}
          />

          {/* Disclaimer */}
          <p className="text-center text-xs text-charcoal-500 dark:text-gray-500 mt-3">
            KM ChatBot can make mistakes. Verify important information.
          </p>
        </div>
      </div>
    </div>
  );
}

// Welcome Screen Component
function WelcomeScreen({ onSendMessage }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 py-12">
      {/* Logo with enhanced dark mode glow */}
      <div className="w-16 h-16 rounded-full border-4 border-blue-500
        shadow-[0_0_30px_rgba(59,130,246,0.3)]
        hover:shadow-[0_0_40px_rgba(59,130,246,0.5)]
        dark:shadow-[0_0_40px_rgba(59,130,246,0.4)]
        dark:hover:shadow-[0_0_60px_rgba(59,130,246,0.6)]
        transition-all duration-300 flex items-center justify-center mb-6
        dark:bg-blue-500/10">
        <span className="text-2xl font-bold text-blue-500 dark:text-blue-400">KM</span>
      </div>

      <h1 className="text-2xl font-semibold text-charcoal-800 dark:text-gray-50 mb-2">
        How can I help you today?
      </h1>
      <p className="text-charcoal-500 dark:text-gray-400 mb-8 text-center max-w-md">
        Ask questions about your documents or request specific diagrams and images.
      </p>
    </div>
  );
}

export default memo(ChatArea);
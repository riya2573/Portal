import React, { useEffect, useRef, useState } from 'react';
import '../styles/Chat.css';
import MessageItem from './MessageItem';

function ChatWindow({ messages, loading, onSendMessage, apiConnected, onCopyMessage, onRegenerate }) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  }, [inputValue]);

  const handleSendMessage = () => {
    if (inputValue.trim() && !loading && apiConnected) {
      onSendMessage(inputValue);
      setInputValue('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="chat-container">
      {/* Messages Area */}
      <div className="messages-area">
        {messages.length === 0 ? (
          <div className="welcome-screen">
            <div className="welcome-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
            </div>
            <h2 className="welcome-title">How can I help you today?</h2>
            <p className="welcome-subtitle">Ask questions about your documents and get AI-powered answers</p>

            <div className="suggestion-chips">
              <button className="suggestion-chip" onClick={() => onSendMessage("What topics are covered in the documents?")}>
                What topics are covered?
              </button>
              <button className="suggestion-chip" onClick={() => onSendMessage("Summarize the main concepts")}>
                Summarize main concepts
              </button>
              <button className="suggestion-chip" onClick={() => onSendMessage("Show me diagrams or images")}>
                Show me diagrams
              </button>
            </div>
          </div>
        ) : (
          <div className="messages-list">
            {messages.map((message) => (
              <MessageItem
                key={message.id}
                message={message}
                onCopy={onCopyMessage}
                onRegenerate={onRegenerate}
              />
            ))}
            {loading && (
              <div className="message assistant">
                <div className="message-avatar assistant">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M12 6v6l4 2"></path>
                  </svg>
                </div>
                <div className="message-content">
                  <div className="message-bubble assistant">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="input-area">
        <div className="input-container">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={apiConnected ? "Type your message..." : "Backend not connected..."}
            disabled={!apiConnected || loading}
            rows={1}
            className="message-input"
          />
          <button
            className="send-button"
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || !apiConnected || loading}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
        <p className="input-hint">
          Press <kbd>Enter</kbd> to send, <kbd>Shift + Enter</kbd> for new line
        </p>
      </div>
    </div>
  );
}

export default ChatWindow;

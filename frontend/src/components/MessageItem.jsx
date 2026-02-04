import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import '../styles/Chat.css';
import ImageDisplay from './ImageDisplay';
import { documentAPI } from '../services/api';

function MessageItem({ message, onCopy, onRegenerate }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    onCopy(message.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Open document at specific page
  const handleSourceClick = (source) => {
    const filename = source.document_name;
    const pageNumber = source.page_number || 1;

    // Open document in new tab with page reference
    const url = documentAPI.getDocumentUrl(filename, pageNumber);
    window.open(url, '_blank');
  };

  // Get images if available
  const images = message.images && message.images.length > 0 ? message.images : [];

  // Debug logging - ALWAYS log for assistant messages
  if (message.type === 'assistant') {
    console.log('[MessageItem] message.images =', message.images);
    console.log('[MessageItem] images array length =', images.length);
  }

  return (
    <div className={`message ${message.type}`}>
      {/* Avatar */}
      <div className={`message-avatar ${message.type}`}>
        {message.type === 'user' ? (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
        ) : (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M12 6v6l4 2"></path>
          </svg>
        )}
      </div>

      {/* Content */}
      <div className="message-content">
        <div className={`message-bubble ${message.type} ${message.isError ? 'error' : ''}`}>
          <div className="message-text">
            {message.type === 'assistant' && !message.isError ? (
              <ReactMarkdown
                components={{
                  // Custom heading styles
                  h1: ({ children }) => <h1 className="md-h1">{children}</h1>,
                  h2: ({ children }) => <h2 className="md-h2">{children}</h2>,
                  h3: ({ children }) => <h3 className="md-h3">{children}</h3>,
                  h4: ({ children }) => <h4 className="md-h4">{children}</h4>,
                  // Custom paragraph
                  p: ({ children }) => <p className="md-p">{children}</p>,
                  // Custom list styles
                  ul: ({ children }) => <ul className="md-ul">{children}</ul>,
                  ol: ({ children }) => <ol className="md-ol">{children}</ol>,
                  li: ({ children }) => <li className="md-li">{children}</li>,
                  // Code blocks
                  code: ({ inline, className, children, ...props }) => {
                    if (inline) {
                      return <code className="md-inline-code" {...props}>{children}</code>;
                    }
                    return (
                      <pre className="md-code-block">
                        <code className={className} {...props}>{children}</code>
                      </pre>
                    );
                  },
                  // Bold and emphasis
                  strong: ({ children }) => <strong className="md-strong">{children}</strong>,
                  em: ({ children }) => <em className="md-em">{children}</em>,
                  // Blockquote
                  blockquote: ({ children }) => <blockquote className="md-blockquote">{children}</blockquote>,
                  // Tables
                  table: ({ children }) => <table className="md-table">{children}</table>,
                  thead: ({ children }) => <thead className="md-thead">{children}</thead>,
                  tbody: ({ children }) => <tbody className="md-tbody">{children}</tbody>,
                  tr: ({ children }) => <tr className="md-tr">{children}</tr>,
                  th: ({ children }) => <th className="md-th">{children}</th>,
                  td: ({ children }) => <td className="md-td">{children}</td>,
                }}
              >
                {message.text || ''}
              </ReactMarkdown>
            ) : (
              // User messages or errors - simple text display
              message.text?.split('\n').map((line, idx) => (
                <p key={idx}>{line || '\u00A0'}</p>
              ))
            )}
            {/* Streaming indicator */}
            {message.isStreaming && (
              <span className="streaming-cursor">|</span>
            )}
          </div>
        </div>

        {/* Action buttons for assistant messages */}
        {message.type === 'assistant' && !message.isError && !message.isStreaming && (
          <div className="message-actions">
            <button
              className={`action-btn ${copied ? 'copied' : ''}`}
              onClick={handleCopy}
              title="Copy"
            >
              {copied ? (
                <>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                  Copied
                </>
              ) : (
                <>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                  </svg>
                  Copy
                </>
              )}
            </button>
            <button className="action-btn" onClick={onRegenerate} title="Regenerate">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="23 4 23 10 17 10"></polyline>
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
              </svg>
              Regenerate
            </button>
          </div>
        )}

        {/* Sources - clickable chips that open document at page */}
        {message.sources && message.sources.length > 0 && !message.isStreaming && (
          <div className="sources-section">
            <div className="sources-header">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
              </svg>
              <span>Sources (click to open):</span>
            </div>
            <div className="sources-list">
              {message.sources.map((source, idx) => (
                <button
                  key={idx}
                  className="source-chip clickable"
                  onClick={() => handleSourceClick(source)}
                  title={`Open ${source.document_name} at ${source.page_label || 'Page ' + (source.page_number || 1)}`}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                    <polyline points="15 3 21 3 21 9"></polyline>
                    <line x1="10" y1="14" x2="21" y2="3"></line>
                  </svg>
                  <span className="source-name">
                    {(source.document_name || 'Document').substring(0, 25)}
                    {(source.document_name || '').length > 25 ? '...' : ''}
                  </span>
                  {source.page_number && (
                    <span className="source-page">
                      {source.page_label || `p.${source.page_number}`}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Images section - at the bottom, after sources */}
        {images.length > 0 && (
          <div className="images-section-bottom">
            <div className="images-header">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <circle cx="8.5" cy="8.5" r="1.5"></circle>
                <polyline points="21 15 16 10 5 21"></polyline>
              </svg>
              <span>Related Images:</span>
            </div>
            <div className="images-grid-bottom">
              {images.map((img, idx) => (
                <ImageDisplay key={idx} imageData={img} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default MessageItem;

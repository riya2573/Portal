import React from 'react';
import '../styles/Modal.css';

function SettingsModal({ isOpen, onClose, stats }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Settings</h2>
          <button className="modal-close" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div className="modal-body">
          <section className="settings-section">
            <h3>System Information</h3>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">Documents Indexed</span>
                <span className="info-value">{stats.indexed_documents}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Images Indexed</span>
                <span className="info-value">{stats.indexed_images}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Chat Messages</span>
                <span className="info-value">{stats.chat_messages}</span>
              </div>
            </div>
          </section>

          <section className="settings-section">
            <h3>About</h3>
            <p className="about-text">
              KM Portal is a document-based Q&A system powered by local LLM (Ollama)
              and vector search (ChromaDB). Ask questions about your documents and
              get AI-powered answers with source references.
            </p>
          </section>

          <section className="settings-section">
            <h3>Keyboard Shortcuts</h3>
            <div className="shortcuts-list">
              <div className="shortcut-item">
                <span className="shortcut-key">Enter</span>
                <span className="shortcut-desc">Send message</span>
              </div>
              <div className="shortcut-item">
                <span className="shortcut-key">Shift + Enter</span>
                <span className="shortcut-desc">New line</span>
              </div>
              <div className="shortcut-item">
                <span className="shortcut-key">Esc</span>
                <span className="shortcut-desc">Close modal / image viewer</span>
              </div>
            </div>
          </section>

          <section className="settings-section">
            <h3>Backend Status</h3>
            <div className="backend-info">
              <div className="backend-item">
                <span>API URL:</span>
                <code>http://localhost:8000</code>
              </div>
              <div className="backend-item">
                <span>Model:</span>
                <code>tinyllama (1.1B)</code>
              </div>
            </div>
          </section>
        </div>

        <div className="modal-footer">
          <button className="btn btn-primary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default SettingsModal;

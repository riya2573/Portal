import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import '../styles/Chat.css';
import { documentAPI } from '../services/api';

function ImageDisplay({ imageData }) {
  const [error, setError] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);

  // Get the correct image ID from the data
  const imageId = imageData.image_id || imageData.id;
  const imageSrc = imageId ? `http://localhost:8000/images/${imageId}` : null;

  // Get document URL for the source link
  const documentUrl = imageData.document_name
    ? documentAPI.getDocumentUrl(imageData.document_name, imageData.page_number || 1)
    : null;

  // Open document at the specific page
  const openSourceDocument = (e) => {
    e.stopPropagation();
    if (documentUrl) {
      window.open(documentUrl, '_blank');
    }
  };

  const openModal = () => {
    if (!error && imageSrc) {
      setIsModalOpen(true);
    }
  };

  const closeModal = () => {
    setIsModalOpen(false);
  };

  // Handle ESC key and body scroll
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        closeModal();
      }
    };

    if (isModalOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'auto';
    };
  }, [isModalOpen]);

  if (!imageSrc) {
    return (
      <div className="image-item">
        <div className="image-error">No image available</div>
      </div>
    );
  }

  // Modal component rendered via Portal
  const Modal = () => {
    if (!isModalOpen) return null;

    return ReactDOM.createPortal(
      <div className="image-modal-overlay" onClick={closeModal}>
        <div className="image-modal-container" onClick={(e) => e.stopPropagation()}>
          <button className="image-modal-close" onClick={closeModal}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
          <div className="image-modal-header">
            <span className="image-modal-title">
              {imageData.document_name || 'Document'} - Page {imageData.page_number || '?'}
            </span>
            {documentUrl && (
              <button className="image-modal-source-link" onClick={openSourceDocument} title="Open source document">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                  <polyline points="15 3 21 3 21 9"></polyline>
                  <line x1="10" y1="14" x2="21" y2="3"></line>
                </svg>
                <span>Open Source</span>
              </button>
            )}
          </div>
          <div className="image-modal-body">
            <img
              src={imageSrc}
              alt={`Page ${imageData.page_number}`}
              className="image-modal-img"
            />
          </div>
        </div>
      </div>,
      document.body
    );
  };

  return (
    <>
      <div className="image-item" onClick={openModal}>
        <div className="image-preview">
          {!imageLoaded && !error && (
            <div className="image-loading">
              <div className="image-loading-spinner"></div>
            </div>
          )}
          <img
            src={imageSrc}
            alt={`Page ${imageData.page_number}`}
            onLoad={() => setImageLoaded(true)}
            onError={() => setError(true)}
            style={{ opacity: imageLoaded ? 1 : 0 }}
          />
          {error && <div className="image-error">Failed to load</div>}
          <div className="image-overlay">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              <line x1="11" y1="8" x2="11" y2="14"></line>
              <line x1="8" y1="11" x2="14" y2="11"></line>
            </svg>
            <span>Click to enlarge</span>
          </div>
        </div>
        <div className="image-info">
          <span className="image-page">Page {imageData.page_number || '?'}</span>
          <span className="image-doc">{(imageData.document_name || 'Document').substring(0, 30)}</span>
        </div>
      </div>

      <Modal />
    </>
  );
}

export default ImageDisplay;

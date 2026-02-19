import React, { useEffect, memo, useCallback } from 'react';
import { X, ExternalLink, Download } from 'lucide-react';
import { imageAPI, documentAPI } from '../services/api';

function ImageModal({ image, onClose }) {
  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'auto';
    };
  }, []);

  const imageUrl = imageAPI.getImageUrl(image.image_id);
  const documentUrl = documentAPI.getDocumentUrl(image.document_name, image.page_number);

  const handleDownload = async () => {
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `figure_page_${image.page_number}.png`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading image:', error);
    }
  };

  return (
    <div
      className="image-modal-backdrop"
      onClick={onClose}
    >
      <div
        className="image-modal-content"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-dark-border/30 dark:bg-dark-surface/50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-blue-500/10 border-2 border-blue-500/30 flex items-center justify-center">
              <span className="text-xs font-bold text-blue-600 dark:text-blue-400">KM</span>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-charcoal-800 dark:text-gray-100">
                {image.document_name}
              </h3>
              <p className="text-xs text-charcoal-500 dark:text-gray-500">
                Page {image.page_number}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Open Source Button */}
            <a
              href={documentUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg
                bg-gradient-to-r from-blue-500 to-blue-600 text-white text-sm font-medium
                hover:from-blue-400 hover:to-blue-500 hover:shadow-[0_0_20px_rgba(59,130,246,0.5)] transition-all duration-300"
            >
              <ExternalLink size={14} />
              <span>Open Source</span>
            </a>

            {/* Download Button */}
            <button
              onClick={handleDownload}
              className="p-2 rounded-lg text-charcoal-600 dark:text-gray-300
                hover:bg-gray-100 dark:hover:bg-dark-hover
                dark:hover:text-blue-400 dark:hover:shadow-[0_0_10px_rgba(59,130,246,0.2)]
                transition-smooth"
              title="Download"
            >
              <Download size={18} />
            </button>

            {/* Close Button */}
            <button
              onClick={onClose}
              className="p-2 rounded-lg text-charcoal-600 dark:text-gray-300
                hover:bg-gray-100 dark:hover:bg-dark-hover
                dark:hover:text-red-400 dark:hover:shadow-[0_0_10px_rgba(239,68,68,0.2)]
                transition-smooth"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Image */}
        <div className="p-4 bg-gray-50 dark:bg-dark-bg/80 overflow-auto max-h-[calc(90vh-100px)]">
          <img
            src={imageUrl}
            alt={`Figure from ${image.document_name} page ${image.page_number}`}
            className="max-w-full h-auto mx-auto rounded-lg shadow-lg dark:shadow-[0_8px_30px_rgba(0,0,0,0.5)]"
            style={{ maxHeight: 'calc(90vh - 140px)' }}
          />
        </div>

        {/* Footer with caption if available */}
        {image.figure_caption && (
          <div className="px-4 py-3 border-t border-gray-200 dark:border-dark-border/30 dark:bg-dark-surface/30">
            <p className="text-sm text-charcoal-700 dark:text-gray-300 italic">
              {image.figure_caption}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default memo(ImageModal);

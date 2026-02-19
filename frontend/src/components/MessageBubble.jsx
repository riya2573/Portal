import React, { useState, memo, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { User, Copy, Check, RefreshCw, FileText } from 'lucide-react';
import ImageModal from './ImageModal';
import { imageAPI, documentAPI } from '../services/api';

// Helper to get short document name (without extension, truncated)
function getShortDocName(filename, maxLength = 20) {
  if (!filename) return 'Document';
  // Remove extension
  const name = filename.replace(/\.[^/.]+$/, '');
  // Truncate if too long
  if (name.length > maxLength) {
    return name.substring(0, maxLength) + '...';
  }
  return name;
}

// Helper to get file type icon indicator
function getFileType(filename) {
  if (!filename) return 'doc';
  const ext = filename.split('.').pop()?.toLowerCase();
  if (ext === 'pdf') return 'PDF';
  if (ext === 'pptx' || ext === 'ppt') return 'PPT';
  if (ext === 'docx' || ext === 'doc') return 'DOC';
  return 'DOC';
}

function MessageBubble({ message, onRegenerate }) {
  const [copied, setCopied] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);

  const isUser = message.type === 'user';
  const isStreaming = message.isStreaming;
  const isError = message.isError;

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(message.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [message.text]);

  const handleImageClick = useCallback((image) => {
    setSelectedImage(image);
  }, []);

  const handleCloseModal = useCallback(() => {
    setSelectedImage(null);
  }, []);

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}>
      {/* Avatar for Assistant */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500/10 border-2 border-blue-500/30 flex items-center justify-center">
          <span className="text-xs font-bold text-blue-600 dark:text-blue-400">KM</span>
        </div>
      )}

      {/* Message Content */}
      <div className={`flex flex-col max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Message Bubble - User only, Assistant has no box */}
        {isUser ? (
          <div className="rounded-2xl px-4 py-3 shadow-soft bg-gradient-to-br from-blue-500 via-blue-600 to-blue-700 text-white rounded-br-md shadow-[0_2px_15px_rgba(59,130,246,0.3)] dark:shadow-[0_4px_20px_rgba(59,130,246,0.4)]">
            <p className="text-sm whitespace-pre-wrap">{message.text}</p>
          </div>
        ) : (
          <div className={`${isError ? 'text-red-600 dark:text-red-400' : 'text-charcoal-800 dark:text-gray-100'}`}>
            <div className="markdown-content text-base leading-relaxed">
              {isStreaming && !message.text ? (
                <TypingIndicator />
              ) : (
                <ReactMarkdown>{message.text}</ReactMarkdown>
              )}
              {isStreaming && message.text && (
                <span className="inline-block w-2 h-4 bg-blue-500 animate-pulse ml-1" />
              )}
            </div>
          </div>
        )}

        {/* Sources - only show after streaming is complete */}
        {!isUser && !isStreaming && message.sources && message.sources.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {message.sources.slice(0, 5).map((source, idx) => (
              <a
                key={idx}
                href={documentAPI.getDocumentUrl(source.document_name, source.page_number)}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg
                  bg-white dark:bg-dark-elevated
                  border border-gray-200 dark:border-dark-border/50
                  text-xs text-charcoal-600 dark:text-gray-300
                  hover:border-blue-500 hover:text-blue-600 dark:hover:text-blue-400
                  hover:shadow-[0_0_15px_rgba(59,130,246,0.25)] dark:hover:shadow-[0_0_20px_rgba(59,130,246,0.3)]
                  hover:-translate-y-0.5
                  transition-smooth group"
                title={`${source.document_name} - ${source.page_label || `Page ${source.page_number}`}`}
              >
                <FileText size={14} className="text-blue-500 flex-shrink-0" />
                <div className="flex flex-col items-start">
                  <span className="font-medium truncate max-w-40">
                    {getShortDocName(source.document_name)}
                  </span>
                  <span className="text-[10px] text-charcoal-500 dark:text-gray-500 group-hover:text-blue-500">
                    {getFileType(source.document_name)} • {source.page_label || `Page ${source.page_number}`}
                  </span>
                </div>
              </a>
            ))}
          </div>
        )}

        {/* Images - only show after streaming is complete */}
        {!isUser && !isStreaming && message.images && message.images.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {message.images.map((image, idx) => (
              <button
                key={idx}
                onClick={() => handleImageClick(image)}
                className="relative group overflow-hidden rounded-xl
                  border-2 border-gray-200 dark:border-dark-border/50
                  hover:border-blue-500 hover:shadow-[0_0_20px_rgba(59,130,246,0.3)]
                  dark:hover:shadow-[0_0_25px_rgba(59,130,246,0.4)]
                  dark:shadow-[0_4px_12px_rgba(0,0,0,0.3)]
                  transition-all duration-300"
                title={`${image.document_name} - Page ${image.page_number}`}
              >
                <img
                  src={imageAPI.getImageUrl(image.image_id)}
                  alt={`Figure from ${image.document_name} page ${image.page_number}`}
                  className="w-28 h-28 object-cover"
                  loading="lazy"
                />
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-all flex items-center justify-center">
                  <span className="opacity-0 group-hover:opacity-100 text-white text-xs font-medium transition-opacity">
                    View
                  </span>
                </div>
                <div className="absolute bottom-0 left-0 right-0 px-1.5 py-1 bg-gradient-to-t from-black/80 to-transparent">
                  <p className="text-white text-[10px] truncate font-medium">
                    {getShortDocName(image.document_name, 15)}
                  </p>
                  <p className="text-white/80 text-[9px]">
                    {getFileType(image.document_name)} • Page {image.page_number}
                  </p>
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Actions */}
        {!isUser && !isStreaming && message.text && (
          <div className="flex items-center gap-1 mt-2">
            <button
              onClick={handleCopy}
              className="p-1.5 rounded-lg text-charcoal-500 dark:text-gray-500
                hover:bg-gray-100 dark:hover:bg-dark-hover
                transition-smooth"
              title="Copy"
            >
              {copied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
            </button>
            {onRegenerate && (
              <button
                onClick={onRegenerate}
                className="p-1.5 rounded-lg text-charcoal-500 dark:text-gray-500
                  hover:bg-gray-100 dark:hover:bg-dark-hover
                  transition-smooth"
                title="Regenerate"
              >
                <RefreshCw size={14} />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Avatar for User */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-[0_0_15px_rgba(59,130,246,0.4)]">
          <User size={16} className="text-white" />
        </div>
      )}

      {/* Image Modal */}
      {selectedImage && (
        <ImageModal
          image={selectedImage}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
}

// Typing Indicator
function TypingIndicator() {
  return (
    <div className="typing-indicator">
      <span></span>
      <span></span>
      <span></span>
    </div>
  );
}

export default memo(MessageBubble);

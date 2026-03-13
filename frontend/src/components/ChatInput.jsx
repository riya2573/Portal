import React, { useState, useRef, useEffect, memo, useCallback } from 'react';
import { Plus, Mic, MicOff, Send, Check, X, Filter, Square } from 'lucide-react';

// Check if browser supports speech recognition
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const speechSupported = !!SpeechRecognition;

function ChatInput({
  onSendMessage,
  loading,
  disabled,
  availableTopics = [],
  selectedTopics = [],
  onToggleTopic,
  onClearTopics,
  onStopGeneration
}) {
  const [inputValue, setInputValue] = useState('');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [speechError, setSpeechError] = useState(null);

  const textareaRef = useRef(null);
  const dropdownRef = useRef(null);
  const recognitionRef = useRef(null);

  // Initialize speech recognition
  useEffect(() => {
    if (speechSupported) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        if (finalTranscript) {
          setInputValue(prev => {
            const newValue = prev + (prev ? ' ' : '') + finalTranscript;
            return newValue;
          });
        }
      };

      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setSpeechError(event.error);
        setIsListening(false);

        // Clear error after 3 seconds
        setTimeout(() => setSpeechError(null), 3000);
      };

      recognition.onend = () => {
        // Only set listening to false if we didn't manually stop
        if (isListening) {
          setIsListening(false);
        }
      };

      recognitionRef.current = recognition;
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, [inputValue]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Listen for edit message events
  useEffect(() => {
    const handleEditMessage = (event) => {
      const { text } = event.detail;
      setInputValue(text);
      // Focus the textarea
      setTimeout(() => {
        textareaRef.current?.focus();
        // Move cursor to end
        textareaRef.current?.setSelectionRange(text.length, text.length);
      }, 100);
    };

    window.addEventListener('editMessage', handleEditMessage);
    return () => window.removeEventListener('editMessage', handleEditMessage);
  }, []);

  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    if (inputValue.trim() && !loading && !disabled) {
      // Stop listening if active
      if (isListening && recognitionRef.current) {
        recognitionRef.current.stop();
        setIsListening(false);
      }
      onSendMessage(inputValue.trim());
      setInputValue('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  }, [inputValue, loading, disabled, onSendMessage, isListening]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }, [handleSubmit]);

  const handleTopicClick = useCallback((topic) => {
    if (onToggleTopic) {
      onToggleTopic(topic);
    }
  }, [onToggleTopic]);

  const toggleListening = useCallback(() => {
    if (!speechSupported) {
      setSpeechError('Speech recognition not supported in this browser');
      setTimeout(() => setSpeechError(null), 3000);
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else {
      setSpeechError(null);
      try {
        recognitionRef.current?.start();
        setIsListening(true);
      } catch (error) {
        console.error('Failed to start speech recognition:', error);
        setSpeechError('Failed to start voice input');
        setTimeout(() => setSpeechError(null), 3000);
      }
    }
  }, [isListening]);

  // Format topic name for display (capitalize, replace underscores)
  const formatTopicName = (topic) => {
    return topic
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const hasFilters = selectedTopics.length > 0;
  const hasTopics = availableTopics.length > 0;

  return (
    <form onSubmit={handleSubmit} className="relative">
      {/* Active filter chips */}
      {hasFilters && (
        <div className="absolute -top-10 left-0 right-0 flex items-center gap-2 flex-wrap">
          <Filter size={14} className="text-blue-500" />
          {selectedTopics.map((topic) => (
            <span
              key={topic}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs
                bg-blue-500/10 border border-blue-500/30 text-blue-600 dark:text-blue-400
                shadow-[0_0_10px_rgba(59,130,246,0.15)]"
            >
              {formatTopicName(topic)}
              <button
                type="button"
                onClick={() => handleTopicClick(topic)}
                className="hover:text-blue-800 dark:hover:text-blue-200"
              >
                <X size={12} />
              </button>
            </span>
          ))}
          {selectedTopics.length > 1 && (
            <button
              type="button"
              onClick={onClearTopics}
              className="text-xs text-charcoal-500 dark:text-gray-500 hover:text-blue-500"
            >
              Clear all
            </button>
          )}
        </div>
      )}

      {/* Speech error message */}
      {speechError && (
        <div className="absolute -top-10 left-1/2 -translate-x-1/2 px-3 py-1 rounded-lg
          bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400 text-xs
          animate-fade-in">
          {speechError === 'not-allowed' ? 'Microphone access denied' : speechError}
        </div>
      )}

      <div
        className={`
          flex items-end gap-2 p-2 rounded-2xl
          bg-white dark:bg-dark-card
          border-2 border-gray-200 dark:border-dark-border/50
          dark:shadow-[0_4px_12px_rgba(0,0,0,0.25),inset_0_1px_0_rgba(255,255,255,0.03)]
          transition-all duration-200
          ${disabled ? 'opacity-50' : ''}
          ${isListening
            ? 'border-red-500 shadow-[0_0_20px_rgba(239,68,68,0.3)] dark:shadow-[0_0_25px_rgba(239,68,68,0.4)]'
            : 'focus-within:border-blue-500 focus-within:shadow-[0_0_20px_rgba(59,130,246,0.2)] dark:focus-within:shadow-[0_0_25px_rgba(59,130,246,0.3)]'}
        `}
      >
        {/* Plus Button with Topic Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className={`
              p-2.5 rounded-xl transition-smooth relative
              ${dropdownOpen || hasFilters
                ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-[0_0_15px_rgba(59,130,246,0.4)]'
                : 'text-charcoal-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-hover'
              }
            `}
            disabled={disabled}
            title={hasTopics ? "Filter by topic" : "No topics available"}
          >
            <Plus size={20} strokeWidth={2.5} />
            {/* Badge for active filters */}
            {hasFilters && !dropdownOpen && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-blue-600 text-white text-[10px] rounded-full flex items-center justify-center">
                {selectedTopics.length}
              </span>
            )}
          </button>

          {/* Dropdown Menu */}
          {dropdownOpen && (
            <div className="dropdown-menu bottom-full left-0 mb-2 w-56 max-h-64 overflow-y-auto scrollbar-thin
              dark:bg-dark-elevated dark:border-dark-border/50">
              {/* Header */}
              <div className="px-4 py-2 border-b border-gray-200 dark:border-dark-border/30">
                <p className="text-xs font-semibold text-charcoal-500 dark:text-gray-500 uppercase tracking-wider">
                  Filter by Topic
                </p>
              </div>

              {hasTopics ? (
                <>
                  {availableTopics.map((topic) => {
                    const isSelected = selectedTopics.includes(topic);
                    return (
                      <div
                        key={topic}
                        onClick={() => handleTopicClick(topic)}
                        className="dropdown-item"
                      >
                        <span className="font-medium">{formatTopicName(topic)}</span>
                        <div className="relative">
                          <div
                            className={`
                              w-5 h-5 rounded-md border-2 flex items-center justify-center
                              transition-all duration-200
                              ${isSelected
                                ? 'bg-blue-500 border-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.4)]'
                                : 'border-gray-300 dark:border-dark-border hover:border-blue-400'
                              }
                            `}
                          >
                            {isSelected && <Check size={14} className="text-white" strokeWidth={3} />}
                          </div>
                        </div>
                      </div>
                    );
                  })}

                  {/* Clear all option */}
                  {hasFilters && (
                    <div className="border-t border-gray-200 dark:border-dark-border mt-1 pt-1">
                      <div
                        onClick={onClearTopics}
                        className="dropdown-item text-red-500 hover:bg-red-500/10"
                      >
                        <span className="font-medium">Clear all filters</span>
                        <X size={16} />
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="px-4 py-6 text-center text-charcoal-500 dark:text-gray-500">
                  <p className="text-sm">No topics available</p>
                  <p className="text-xs mt-1">
                    Create subfolders in<br />
                    <code className="text-blue-500">data/documents/</code><br />
                    to add topics
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Text Input */}
        <textarea
          ref={textareaRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            disabled
              ? "Connecting to server..."
              : isListening
                ? "Listening... speak now"
                : "Message KM Portal..."
          }
          disabled={disabled || loading}
          rows={1}
          className={`flex-1 resize-none bg-transparent border-none outline-none
            text-charcoal-800 dark:text-gray-100 text-sm
            placeholder-gray-400 dark:placeholder-gray-500
            py-2.5 px-1
            max-h-[200px] scrollbar-thin
            ${isListening ? 'placeholder-red-400 dark:placeholder-red-400' : ''}`}
        />

        {/* Microphone Button */}
        <button
          type="button"
          onClick={toggleListening}
          className={`
            p-2.5 rounded-xl transition-all duration-200
            ${isListening
              ? 'bg-red-500 text-white shadow-[0_0_15px_rgba(239,68,68,0.5)] animate-pulse'
              : 'text-charcoal-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-hover hover:text-blue-500'
            }
          `}
          disabled={disabled}
          title={
            !speechSupported
              ? "Voice input not supported in this browser"
              : isListening
                ? "Stop listening"
                : "Start voice input"
          }
        >
          {isListening ? <MicOff size={20} /> : <Mic size={20} />}
        </button>

        {/* Send / Stop Button */}
        {loading ? (
          <button
            type="button"
            onClick={onStopGeneration}
            className="p-2.5 rounded-xl transition-smooth
              bg-gradient-to-r from-red-500 to-red-600 text-white
              shadow-[0_0_15px_rgba(239,68,68,0.4)]
              hover:from-red-400 hover:to-red-500
              hover:shadow-[0_0_20px_rgba(239,68,68,0.5)]
              active:from-red-600 active:to-red-700"
            title="Stop generating"
          >
            <Square size={18} fill="currentColor" />
          </button>
        ) : (
          <button
            type="submit"
            disabled={!inputValue.trim() || disabled}
            className={`
              p-2.5 rounded-xl transition-smooth
              ${inputValue.trim() && !disabled
                ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-[0_0_15px_rgba(59,130,246,0.4)] hover:from-blue-400 hover:to-blue-500 hover:shadow-[0_0_20px_rgba(59,130,246,0.5)] active:from-blue-600 active:to-blue-700'
                : 'bg-gray-200 dark:bg-dark-hover text-gray-400 dark:text-gray-600 cursor-not-allowed'
              }
            `}
          >
            <Send size={20} />
          </button>
        )}
      </div>

      {/* Listening indicator */}
      {isListening && (
        <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-2 text-xs text-red-500">
          <span className="flex gap-1">
            <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
            <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
            <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
          </span>
          <span>Listening...</span>
        </div>
      )}
    </form>
  );
}

export default memo(ChatInput);

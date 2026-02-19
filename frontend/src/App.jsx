import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import { chatAPI, sessionAPI, topicAPI } from './services/api';

// Memoized Sidebar wrapper
const MemoizedSidebar = React.memo(Sidebar);
const MemoizedChatArea = React.memo(ChatArea);

function App() {
  // Theme state
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    if (saved !== null) return JSON.parse(saved);
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  // Sidebar state
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Chat state
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [apiConnected, setApiConnected] = useState(false);

  // Topic filter state (dynamic from backend)
  const [availableTopics, setAvailableTopics] = useState([]);
  const [selectedTopics, setSelectedTopics] = useState([]);

  // Stats
  const [stats, setStats] = useState({
    indexed_documents: 0,
    indexed_images: 0,
    chat_messages: 0,
    sessions: 0,
  });

  // Refs for streaming
  const streamingMessageRef = useRef(null);
  const pendingImagesRef = useRef([]);
  const pendingSourcesRef = useRef([]);

  // Apply dark mode
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
  }, [darkMode]);

  // Initialize - load all data in parallel
  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = useCallback(async () => {
    try {
      // Load health, stats, sessions, and topics in parallel
      const [healthResult, statsResult, sessionsResult, topicsResult] = await Promise.allSettled([
        chatAPI.checkHealth(),
        chatAPI.getStatistics(),
        sessionAPI.listSessions(50),
        topicAPI.listTopics(),
      ]);

      // Process health
      if (healthResult.status === 'fulfilled' && healthResult.value.status === 'healthy') {
        setApiConnected(true);
      } else {
        setApiConnected(false);
      }

      // Process stats
      if (statsResult.status === 'fulfilled') {
        setStats(statsResult.value);
      }

      // Process sessions
      if (sessionsResult.status === 'fulfilled') {
        setSessions(sessionsResult.value.sessions || []);
      }

      // Process topics (auto-discovered from document folders)
      if (topicsResult.status === 'fulfilled') {
        setAvailableTopics(topicsResult.value.topics || []);
        console.log('[TOPICS] Available topics:', topicsResult.value.topics);
      }
    } catch (error) {
      console.error('Error initializing app:', error);
      setApiConnected(false);
    }
  }, []);

  const loadStats = useCallback(async () => {
    try {
      const newStats = await chatAPI.getStatistics();
      setStats(newStats);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  }, []);

  const loadSessions = useCallback(async () => {
    try {
      const result = await sessionAPI.listSessions(50);
      setSessions(result.sessions || []);
    } catch (error) {
      console.error('Error loading sessions:', error);
    }
  }, []);

  const handleNewChat = async () => {
    try {
      const session = await sessionAPI.createSession();
      setCurrentSessionId(session.id);
      setMessages([]);
      loadSessions();
    } catch (error) {
      console.error('Error creating session:', error);
      setMessages([]);
      setCurrentSessionId(null);
    }
  };

  const handleSelectSession = async (session) => {
    try {
      setCurrentSessionId(session.id);
      const sessionData = await sessionAPI.getSession(session.id);

      const loadedMessages = [];
      for (const msg of sessionData.messages) {
        loadedMessages.push({
          id: msg.id * 2,
          type: 'user',
          text: msg.user,
          timestamp: msg.timestamp,
        });
        loadedMessages.push({
          id: msg.id * 2 + 1,
          type: 'assistant',
          text: msg.assistant,
          sources: msg.sources || [],
          images: msg.images || [],
          timestamp: msg.timestamp,
        });
      }
      setMessages(loadedMessages);
    } catch (error) {
      console.error('Error loading session:', error);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await sessionAPI.deleteSession(sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (currentSessionId === sessionId) {
        setMessages([]);
        setCurrentSessionId(null);
      }
    } catch (error) {
      console.error('Error deleting session:', error);
    }
  };

  const handleClearHistory = async () => {
    if (window.confirm('Are you sure you want to clear all chat history?')) {
      try {
        await chatAPI.clearChatHistory();
        setMessages([]);
        setSessions([]);
        setCurrentSessionId(null);
        loadStats();
      } catch (error) {
        console.error('Error clearing history:', error);
      }
    }
  };

  const handleSendMessage = async (text) => {
    if (!text.trim() || !apiConnected) return;

    // Create session if none exists
    let sessionId = currentSessionId;
    if (!sessionId) {
      try {
        const session = await sessionAPI.createSession();
        sessionId = session.id;
        setCurrentSessionId(sessionId);
      } catch (error) {
        console.error('Error creating session:', error);
      }
    }

    const userMessage = {
      id: Date.now(),
      type: 'user',
      text,
      timestamp: new Date().toISOString(),
    };

    const assistantPlaceholder = {
      id: Date.now() + 1,
      type: 'assistant',
      text: '',
      sources: [],
      images: [],
      isStreaming: true,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage, assistantPlaceholder]);
    setLoading(true);
    streamingMessageRef.current = assistantPlaceholder.id;

    try {
      // Pass selected topics to filter the search
      const topicsFilter = selectedTopics.length > 0 ? selectedTopics : null;

      await chatAPI.sendMessageStream(
        text,
        sessionId,
        topicsFilter,
        // onToken
        (token) => {
          setMessages(prev =>
            prev.map(msg =>
              msg.id === streamingMessageRef.current
                ? { ...msg, text: msg.text + token }
                : msg
            )
          );
        },
        // onSources
        (sources) => {
          pendingSourcesRef.current = sources;
          setMessages(prev =>
            prev.map(msg =>
              msg.id === streamingMessageRef.current
                ? { ...msg, sources }
                : msg
            )
          );
        },
        // onImages
        (images) => {
          pendingImagesRef.current = images;
        },
        // onDone
        () => {
          const finalImages = [...pendingImagesRef.current];
          const finalSources = [...pendingSourcesRef.current];
          const targetId = streamingMessageRef.current;

          setMessages(prev =>
            prev.map(msg =>
              msg.id === targetId
                ? { ...msg, isStreaming: false, images: finalImages, sources: finalSources }
                : msg
            )
          );

          setLoading(false);
          setTimeout(() => {
            pendingImagesRef.current = [];
            pendingSourcesRef.current = [];
            streamingMessageRef.current = null;
          }, 100);

          // Update session in list without full reload (optimization)
          if (sessionId) {
            setSessions(prev => {
              const updated = prev.map(s =>
                s.id === sessionId
                  ? { ...s, updated_at: new Date().toISOString(), message_count: (s.message_count || 0) + 1 }
                  : s
              );
              // Move updated session to top
              const session = updated.find(s => s.id === sessionId);
              if (session) {
                return [session, ...updated.filter(s => s.id !== sessionId)];
              }
              return updated;
            });
          }
          // Only reload stats (lightweight)
          loadStats();
        },
        // onError
        (error) => {
          setMessages(prev =>
            prev.map(msg =>
              msg.id === streamingMessageRef.current
                ? { ...msg, text: `Error: ${error}`, isError: true, isStreaming: false }
                : msg
            )
          );
          setLoading(false);
          streamingMessageRef.current = null;
        }
      );
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev =>
        prev.map(msg =>
          msg.id === streamingMessageRef.current
            ? {
                ...msg,
                text: msg.text || `Error: ${error.message || 'Unable to process your message.'}`,
                isError: !msg.text,
                isStreaming: false,
              }
            : msg
        )
      );
      streamingMessageRef.current = null;
      setLoading(false);
    }
  };

  const handleRegenerateResponse = async () => {
    if (messages.length < 2 || loading) return;

    const lastUserMsg = [...messages].reverse().find(m => m.type === 'user');
    if (!lastUserMsg) return;

    setMessages(prev => prev.slice(0, -1));

    const assistantPlaceholder = {
      id: Date.now(),
      type: 'assistant',
      text: '',
      sources: [],
      images: [],
      isStreaming: true,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, assistantPlaceholder]);
    setLoading(true);
    streamingMessageRef.current = assistantPlaceholder.id;

    try {
      const topicsFilter = selectedTopics.length > 0 ? selectedTopics : null;

      await chatAPI.sendMessageStream(
        lastUserMsg.text,
        currentSessionId,
        topicsFilter,
        (token) => {
          setMessages(prev =>
            prev.map(msg =>
              msg.id === streamingMessageRef.current
                ? { ...msg, text: msg.text + token }
                : msg
            )
          );
        },
        (sources) => {
          pendingSourcesRef.current = sources;
          setMessages(prev =>
            prev.map(msg =>
              msg.id === streamingMessageRef.current
                ? { ...msg, sources }
                : msg
            )
          );
        },
        (images) => {
          pendingImagesRef.current = images;
        },
        () => {
          const finalImages = [...pendingImagesRef.current];
          const finalSources = [...pendingSourcesRef.current];
          const targetId = streamingMessageRef.current;

          setMessages(prev =>
            prev.map(msg =>
              msg.id === targetId
                ? { ...msg, isStreaming: false, images: finalImages, sources: finalSources }
                : msg
            )
          );
          setLoading(false);
          loadStats(); // Only reload stats, not sessions
          setTimeout(() => {
            pendingImagesRef.current = [];
            pendingSourcesRef.current = [];
            streamingMessageRef.current = null;
          }, 100);
        },
        (error) => {
          setMessages(prev =>
            prev.map(msg =>
              msg.id === streamingMessageRef.current
                ? { ...msg, text: `Error: ${error}`, isError: true, isStreaming: false }
                : msg
            )
          );
          setLoading(false);
          streamingMessageRef.current = null;
        }
      );
    } catch (error) {
      setMessages(prev =>
        prev.map(msg =>
          msg.id === streamingMessageRef.current
            ? { ...msg, text: msg.text || `Error: ${error.message}`, isError: !msg.text, isStreaming: false }
            : msg
        )
      );
      setLoading(false);
      streamingMessageRef.current = null;
    }
  };

  const toggleDarkMode = () => setDarkMode(prev => !prev);
  const toggleSidebar = () => setSidebarOpen(prev => !prev);

  // Memoize callbacks to prevent unnecessary re-renders
  const handleCloseSidebar = useCallback(() => setSidebarOpen(false), []);

  // Handle topic selection (multi-select support)
  const handleToggleTopic = useCallback((topic) => {
    setSelectedTopics(prev => {
      if (prev.includes(topic)) {
        return prev.filter(t => t !== topic);
      } else {
        return [...prev, topic];
      }
    });
  }, []);

  const handleClearTopics = useCallback(() => {
    setSelectedTopics([]);
  }, []);

  return (
    <div className="h-screen flex overflow-hidden bg-white dark:bg-dark-bg transition-colors duration-300">
      {/* Sidebar */}
      <MemoizedSidebar
        isOpen={sidebarOpen}
        sessions={sessions}
        currentSessionId={currentSessionId}
        stats={stats}
        onNewChat={handleNewChat}
        onSelectSession={handleSelectSession}
        onDeleteSession={handleDeleteSession}
        onClearHistory={handleClearHistory}
        onClose={handleCloseSidebar}
      />

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 dark:bg-black/70 backdrop-blur-sm z-30 lg:hidden"
          onClick={handleCloseSidebar}
        />
      )}

      {/* Main Chat Area */}
      <MemoizedChatArea
        messages={messages}
        loading={loading}
        apiConnected={apiConnected}
        darkMode={darkMode}
        availableTopics={availableTopics}
        selectedTopics={selectedTopics}
        onSendMessage={handleSendMessage}
        onRegenerate={handleRegenerateResponse}
        onToggleDarkMode={toggleDarkMode}
        onToggleSidebar={toggleSidebar}
        onToggleTopic={handleToggleTopic}
        onClearTopics={handleClearTopics}
      />
    </div>
  );
}

export default App;

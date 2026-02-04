import React, { useState, useEffect, useCallback, useRef } from 'react';
import './styles/App.css';
import ChatWindow from './components/ChatWindow';
import SettingsModal from './components/SettingsModal';
import { chatAPI, sessionAPI } from './services/api';

function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [apiConnected, setApiConnected] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [theme, setTheme] = useState(() => {
    // Initialize theme from localStorage or system preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) return savedTheme;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });
  const [stats, setStats] = useState({
    indexed_documents: 0,
    indexed_images: 0,
    chat_messages: 0,
    sessions: 0,
  });
  const streamingMessageRef = useRef(null);
  const pendingImagesRef = useRef([]);
  const pendingSourcesRef = useRef([]);

  // Apply theme to document
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  // Check API connection on mount
  useEffect(() => {
    checkAPIHealth();
    loadSessions();
  }, []);

  const checkAPIHealth = async () => {
    try {
      const health = await chatAPI.checkHealth();
      setApiConnected(health.status === 'healthy');
      if (health.status === 'healthy') {
        loadStats();
      }
    } catch (error) {
      console.error('API not reachable:', error);
      setApiConnected(false);
    }
  };

  const loadStats = async () => {
    try {
      const newStats = await chatAPI.getStatistics();
      setStats(newStats);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const loadSessions = async () => {
    try {
      const result = await sessionAPI.listSessions(50);
      setSessions(result.sessions || []);
    } catch (error) {
      console.error('Error loading sessions:', error);
    }
  };

  const startNewChat = async () => {
    try {
      // Create a new session on the backend
      const session = await sessionAPI.createSession();
      setCurrentSessionId(session.id);
      setMessages([]);
      loadSessions(); // Refresh session list
    } catch (error) {
      console.error('Error creating session:', error);
      // Fallback: just clear messages locally
      setMessages([]);
      setCurrentSessionId(null);
    }
  };

  const loadSession = async (session) => {
    try {
      setCurrentSessionId(session.id);
      const sessionData = await sessionAPI.getSession(session.id);

      // Convert messages to the format expected by the chat window
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

  const handleDeleteSession = async (sessionId, e) => {
    e.stopPropagation();
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

    // Create placeholder for assistant message
    const assistantPlaceholder = {
      id: Date.now() + 1,
      type: 'assistant',
      text: '',
      sources: [],
      images: [],
      isStreaming: true,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage, assistantPlaceholder]);
    setLoading(true);
    streamingMessageRef.current = assistantPlaceholder.id;

    try {
      // Use streaming API
      await chatAPI.sendMessageStream(
        text,
        sessionId,
        // onToken
        (token) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === streamingMessageRef.current
                ? { ...msg, text: msg.text + token }
                : msg
            )
          );
        },
        // onSources
        (sources) => {
          pendingSourcesRef.current = sources;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === streamingMessageRef.current
                ? { ...msg, sources }
                : msg
            )
          );
        },
        // onImages
        (images) => {
          console.log('[App] Received images, storing in ref:', images);
          pendingImagesRef.current = images;
        },
        // onDone
        () => {
          const finalImages = [...pendingImagesRef.current]; // Copy arrays
          const finalSources = [...pendingSourcesRef.current];
          const targetId = streamingMessageRef.current; // Capture ID before any async ops

          console.log('[App] Stream done - targetId:', targetId, 'images:', finalImages);

          setMessages((prev) => {
            console.log('[App] Inside setMessages, looking for ID:', targetId);
            return prev.map((msg) => {
              if (msg.id === targetId) {
                console.log('[App] MATCH! Applying images:', finalImages.length);
                return {
                  ...msg,
                  isStreaming: false,
                  images: finalImages,
                  sources: finalSources
                };
              }
              return msg;
            });
          });

          // Clear refs AFTER state update is queued
          setTimeout(() => {
            pendingImagesRef.current = [];
            pendingSourcesRef.current = [];
            streamingMessageRef.current = null;
          }, 100);

          loadSessions();
          loadStats();
        },
        // onError
        (error) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === streamingMessageRef.current
                ? { ...msg, text: `Error: ${error}`, isError: true, isStreaming: false }
                : msg
            )
          );
          streamingMessageRef.current = null;
        }
      );
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === streamingMessageRef.current
            ? {
                ...msg,
                text: `Error: ${error.message || 'Unable to process your message.'}`,
                isError: true,
                isStreaming: false,
              }
            : msg
        )
      );
      streamingMessageRef.current = null;
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerateResponse = async () => {
    if (messages.length < 2 || loading) return;

    // Get the last user message
    const lastUserMsg = [...messages].reverse().find(m => m.type === 'user');
    if (!lastUserMsg) return;

    // Remove the last assistant message
    setMessages(prev => prev.slice(0, -1));

    // Create new placeholder
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
      await chatAPI.sendMessageStream(
        lastUserMsg.text,
        currentSessionId,
        (token) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === streamingMessageRef.current
                ? { ...msg, text: msg.text + token }
                : msg
            )
          );
        },
        (sources) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === streamingMessageRef.current
                ? { ...msg, sources }
                : msg
            )
          );
        },
        (images) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === streamingMessageRef.current
                ? { ...msg, images }
                : msg
            )
          );
        },
        () => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === streamingMessageRef.current
                ? { ...msg, isStreaming: false }
                : msg
            )
          );
          streamingMessageRef.current = null;
        },
        (error) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === streamingMessageRef.current
                ? { ...msg, text: `Error: ${error}`, isError: true, isStreaming: false }
                : msg
            )
          );
          streamingMessageRef.current = null;
        }
      );
    } catch (error) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === streamingMessageRef.current
            ? { ...msg, text: `Error: ${error.message}`, isError: true, isStreaming: false }
            : msg
        )
      );
      streamingMessageRef.current = null;
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = async () => {
    if (window.confirm('Are you sure you want to clear all chat history and sessions?')) {
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

  const handleCopyMessage = (text) => {
    navigator.clipboard.writeText(text);
  };

  const handleShareChat = () => {
    const chatText = messages.map(m =>
      `${m.type === 'user' ? 'You' : 'Assistant'}: ${m.text}`
    ).join('\n\n');
    navigator.clipboard.writeText(chatText);
    alert('Chat copied to clipboard!');
  };

  // Group sessions by date
  const groupedSessions = groupSessionsByDate(sessions);

  return (
    <div className="app-container">
      {/* SIDEBAR */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <button className="new-chat-btn" onClick={startNewChat}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            New Chat
          </button>
        </div>

        <nav className="sidebar-nav">
          {Object.entries(groupedSessions).map(([group, groupSessions]) => (
            groupSessions.length > 0 && (
              <div key={group} className="chat-group">
                <h3 className="chat-group-title">{group}</h3>
                <ul className="chat-list">
                  {groupSessions.map((session) => (
                    <li
                      key={session.id}
                      className={`chat-item ${currentSessionId === session.id ? 'active' : ''}`}
                      onClick={() => loadSession(session)}
                    >
                      <svg className="chat-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                      </svg>
                      <span className="chat-title">{session.title?.substring(0, 30) || 'Chat'}...</span>
                      <div className="chat-actions">
                        <button
                          className="chat-action-btn"
                          onClick={(e) => handleDeleteSession(session.id, e)}
                          title="Delete"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                          </svg>
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="stats-bar">
            <div className="stat-item" title="Documents">
              <span className="stat-icon">D</span>
              <span>{stats.indexed_documents}</span>
            </div>
            <div className="stat-item" title="Images">
              <span className="stat-icon">I</span>
              <span>{stats.indexed_images}</span>
            </div>
            <div className="stat-item" title="Messages">
              <span className="stat-icon">M</span>
              <span>{stats.chat_messages}</span>
            </div>
          </div>

          <button className="sidebar-btn" onClick={handleClearHistory}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
            Clear All
          </button>

          <div className="user-profile">
            <div className="user-avatar">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
            </div>
            <span className="user-name">User</span>
            <div className={`status-dot ${apiConnected ? 'connected' : 'disconnected'}`}></div>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT */}
      <main className="main-content">
        <header className="chat-header">
          <div className="header-left">
            <button className="menu-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="3" y1="12" x2="21" y2="12"></line>
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <line x1="3" y1="18" x2="21" y2="18"></line>
              </svg>
            </button>
            <h1 className="header-title">KM Portal</h1>
            <span className="header-model">Document Assistant</span>
          </div>
          <div className="header-right">
            <button className="theme-toggle" onClick={toggleTheme} title={theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}>
              {theme === 'light' ? (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="5"></circle>
                  <line x1="12" y1="1" x2="12" y2="3"></line>
                  <line x1="12" y1="21" x2="12" y2="23"></line>
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                  <line x1="1" y1="12" x2="3" y2="12"></line>
                  <line x1="21" y1="12" x2="23" y2="12"></line>
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                  <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
                </svg>
              )}
            </button>
            <button className="header-btn" onClick={handleShareChat} title="Share">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="18" cy="5" r="3"></circle>
                <circle cx="6" cy="12" r="3"></circle>
                <circle cx="18" cy="19" r="3"></circle>
                <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
                <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
              </svg>
            </button>
            <button className="header-btn" onClick={() => setSettingsOpen(true)} title="Settings">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
              </svg>
            </button>
          </div>
        </header>

        <ChatWindow
          messages={messages}
          loading={loading}
          onSendMessage={handleSendMessage}
          apiConnected={apiConnected}
          onCopyMessage={handleCopyMessage}
          onRegenerate={handleRegenerateResponse}
        />

        {!apiConnected && (
          <div className="connection-warning">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            Backend not connected. Run: <code>uvicorn main:app --reload</code>
          </div>
        )}
      </main>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        stats={stats}
      />
    </div>
  );
}

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

export default App;

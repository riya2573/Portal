import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Session services
export const sessionAPI = {
  // Create a new session
  createSession: async (title = null) => {
    try {
      const response = await api.post('/sessions', { title });
      return response.data;
    } catch (error) {
      console.error('Error creating session:', error);
      throw error;
    }
  },

  // List all sessions
  listSessions: async (limit = 50) => {
    try {
      const response = await api.get('/sessions', { params: { limit } });
      return response.data;
    } catch (error) {
      console.error('Error listing sessions:', error);
      throw error;
    }
  },

  // Get a session with all messages
  getSession: async (sessionId) => {
    try {
      const response = await api.get(`/sessions/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching session:', error);
      throw error;
    }
  },

  // Update session title
  updateSession: async (sessionId, title) => {
    try {
      const response = await api.put(`/sessions/${sessionId}`, { title });
      return response.data;
    } catch (error) {
      console.error('Error updating session:', error);
      throw error;
    }
  },

  // Delete a session
  deleteSession: async (sessionId) => {
    try {
      const response = await api.delete(`/sessions/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting session:', error);
      throw error;
    }
  },
};

// Chat services
export const chatAPI = {
  // Send a message and get response (non-streaming)
  sendMessage: async (text, sessionId = null) => {
    try {
      const response = await api.post('/chat', { text, session_id: sessionId });
      return response.data;
    } catch (error) {
      console.error('Chat error:', error);
      throw error;
    }
  },

  // Send message with streaming response
  sendMessageStream: async (text, sessionId = null, onToken, onSources, onImages, onDone, onError) => {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text, session_id: sessionId }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (data.type) {
                case 'token':
                  if (onToken) onToken(data.token);
                  break;
                case 'sources':
                  console.log('[API] Received sources:', data.sources);
                  if (onSources) onSources(data.sources);
                  break;
                case 'images':
                  console.log('[API] Received images:', data.images);
                  if (onImages) onImages(data.images);
                  break;
                case 'done':
                  console.log('[API] Stream done');
                  if (onDone) onDone(data.session_id);
                  break;
                case 'error':
                  console.error('[API] Stream error:', data.error);
                  if (onError) onError(data.error);
                  break;
                default:
                  console.log('[API] Unknown type:', data.type);
                  break;
              }
            } catch (e) {
              // Ignore JSON parse errors for incomplete data
            }
          }
        }
      }
    } catch (error) {
      console.error('Streaming error:', error);
      if (onError) onError(error.message);
      throw error;
    }
  },

  // Send message with explicit intent
  sendMessageWithIntent: async (text, showImages = false) => {
    try {
      const response = await api.post('/chat/with-intent', {
        text,
        show_images: showImages,
      });
      return response.data;
    } catch (error) {
      console.error('Chat error:', error);
      throw error;
    }
  },

  // Get chat history (legacy)
  getChatHistory: async (limit = 50) => {
    try {
      const response = await api.get('/chat-history', {
        params: { limit },
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching history:', error);
      throw error;
    }
  },

  // Clear chat history
  clearChatHistory: async () => {
    try {
      const response = await api.delete('/chat-history');
      return response.data;
    } catch (error) {
      console.error('Error clearing history:', error);
      throw error;
    }
  },

  // Delete specific chat
  deleteChat: async (chatId) => {
    try {
      const response = await api.delete(`/chat-history/${chatId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting chat:', error);
      throw error;
    }
  },

  // Get system statistics
  getStatistics: async () => {
    try {
      const response = await api.get('/stats');
      return response.data;
    } catch (error) {
      console.error('Error fetching stats:', error);
      throw error;
    }
  },

  // Check health
  checkHealth: async () => {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      console.error('Health check error:', error);
      throw error;
    }
  },
};

// Image services
export const imageAPI = {
  // Get image URL
  getImageUrl: (imageId) => {
    return `${API_BASE_URL}/images/${imageId}`;
  },

  // Get image by ID
  getImage: async (imageId) => {
    try {
      const response = await api.get(`/images/${imageId}`, {
        responseType: 'blob',
      });
      return response;
    } catch (error) {
      console.error('Error fetching image:', error);
      throw error;
    }
  },

  // List all images
  listImages: async () => {
    try {
      const response = await api.get('/images');
      return response.data;
    } catch (error) {
      console.error('Error listing images:', error);
      throw error;
    }
  },
};

// Document services
export const documentAPI = {
  // Get document URL with page number
  getDocumentUrl: (filename, pageNumber = null) => {
    let url = `${API_BASE_URL}/documents/${encodeURIComponent(filename)}`;
    if (pageNumber) {
      url += `#page=${pageNumber}`;
    }
    return url;
  },
};

export default api;

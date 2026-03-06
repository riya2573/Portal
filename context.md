# KM Portal Project Context

## Project Overview

A **Document-Based Knowledge Management Chatbot System** that enables local, privacy-friendly Q&A interactions with uploaded documents using semantic search and a local LLM. The system extracts text and images from documents (PDF, PPTX, DOCX, TXT), creates vector embeddings for semantic search, and uses a local Ollama LLM to generate answers with source citations and relevant images.

**Version:** 2.0.0 (Frontend) / 4.1 (Backend - Optimized)

---

## Key Features

- **Multi-format Document Support**: PDF, PPTX, DOCX, TXT
- **Layout-Aware Image Extraction**: Extracts figures with captions and spatial context from PDFs and PPTX
- **Semantic Search**: Uses Ollama nomic-embed-text for intelligent document retrieval (768 dimensions)
- **Source Citations**: Shows document name + page/slide numbers with clickable links
- **Intent Detection**: Distinguishes between image requests and questions
- **Multiple Images**: Returns up to 3 relevant images per query (only if relevant)
- **Session Management**: Persistent chat sessions with history grouped by date
- **Streaming Responses**: Real-time token-by-token response display via Server-Sent Events
- **Dark/Light Mode**: Full theme support with localStorage persistence
- **Topic-Based Filtering**: Auto-discovered from folder structure, multi-select support
- **Voice Input**: Speech recognition support in the chat input
- **Local & Private**: All processing happens locally using Ollama
- **Interactive Chat Formatting**: Bold highlights, emojis, tables for comparisons
- **Performance Optimized**: 3-5x faster ingestion with parallel processing, caching, and progress bars

---

## Tech Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.2.0 | UI library |
| Tailwind CSS | 3.4.0 | Utility-first CSS framework |
| Lucide React | 0.294.0 | Icon library (blue stroke icons) |
| Axios | 1.6.2 | HTTP client |
| React Markdown | 9.0.0 | Markdown rendering |
| PostCSS | 8.4.32 | CSS processing |
| Autoprefixer | 10.4.16 | CSS vendor prefixing |
| Inter Font | - | Typography (Google Fonts) |

**Port:** `http://localhost:3000`

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.109.0 | Web framework |
| Uvicorn | 0.27.0 | ASGI server |
| Pydantic | 2.9.0 | Data validation |
| SQLAlchemy | 2.0.25 | SQL toolkit |
| Qdrant | 1.9.0 | Vector database (local file storage) |
| PyMuPDF | 1.23.8 | PDF image extraction with layout-aware context |
| python-pptx | 0.6.23 | PPTX text and image extraction |
| python-docx | 0.8.11 | DOCX text extraction |
| PyPDF2 | 3.0.1 | PDF text extraction |
| Pillow | 10.1.0 | Image processing |
| Requests | 2.31.0 | HTTP client for Ollama API (with connection pooling) |
| NumPy | 1.26.0 | Numerical operations |
| tqdm | 4.66.0 | Progress bars for ingestion pipeline |

**Port:** `http://localhost:8000`

### AI/ML (Ollama)
| Component | Model | Purpose |
|-----------|-------|---------|
| LLM | llama3.1:8b | Chat response generation |
| Embeddings | nomic-embed-text | Text embeddings (768 dimensions) |

**Port:** `http://localhost:11434`

### Database
| Type | Purpose | Location |
|------|---------|----------|
| SQLite | Chat history, sessions, image metadata | `backend/data/chat_history.db` |
| Qdrant | Vector storage for text & image embeddings | `backend/data/qdrant_db/` |
| Embedding Cache | Disk-based cache for computed embeddings | `backend/data/embedding_cache/` |

---

## Project Structure

```
KM_Portal/
├── frontend/
│   ├── public/
│   │   └── index.html              # HTML template with dark mode init script
│   ├── src/
│   │   ├── App.jsx                 # Main app with state management
│   │   ├── index.js                # React entry point
│   │   ├── index.css               # Tailwind + custom styles (scrollbar, markdown, modals)
│   │   ├── assets/
│   │   │   ├── logo.svg            # App logo
│   │   │   └── reliance-logo.svg   # Company logo for sidebar
│   │   ├── components/
│   │   │   ├── Sidebar.jsx         # Collapsible left sidebar with sessions
│   │   │   ├── ChatArea.jsx        # Main chat area with welcome screen
│   │   │   ├── ChatInput.jsx       # Input with +, mic, send buttons + topic filter
│   │   │   ├── MessageBubble.jsx   # Message display with sources/images
│   │   │   └── ImageModal.jsx      # Image preview modal with download
│   │   └── services/
│   │       └── api.js              # API client (session, chat, image, topic APIs)
│   ├── tailwind.config.js          # Tailwind configuration (blue theme, dark mode)
│   ├── postcss.config.js           # PostCSS configuration
│   └── package.json                # Dependencies and scripts
│
├── backend/
│   ├── main.py                     # FastAPI app with all endpoints
│   ├── config.py                   # Configuration settings (models, paths, prompts, parallelism)
│   ├── embeddings.py               # Ollama embedding service (parallel, cached, connection pooling)
│   ├── vector_store.py             # Qdrant interface (text + images collections, batch processing)
│   ├── llm_service.py              # Ollama LLM integration (streaming + non-streaming)
│   ├── image_extractor.py          # Layout-aware image extraction (parallel PDF processing)
│   ├── ingest.py                   # Document ingestion pipeline (4-phase with progress)
│   ├── requirement.txt             # Python dependencies
│   └── data/
│       ├── documents/              # Input documents (with topic subfolders)
│       │   ├── piping/             # Topic: piping
│       │   ├── heat_exchanger/     # Topic: heat_exchanger
│       │   └── *.pdf               # Topic: general (root folder)
│       ├── extracted_images/       # Images extracted from documents
│       ├── qdrant_db/              # Vector database storage
│       ├── embedding_cache/        # Cached embeddings (hash-based pickle files)
│       └── chat_history.db         # SQLite database
│
└── context.md                      # This documentation file
```

---

## How to Run

### Prerequisites
1. **Python 3.8+** installed
2. **Node.js 16+** installed
3. **Ollama** installed from https://ollama.ai

### Step 1: Start Ollama (Terminal 1)
```bash
# Start Ollama server
ollama serve

# Pull required models (in another terminal)
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### Step 2: Setup & Run Backend (Terminal 2)
```powershell
cd backend

# Create virtual environment (first time)
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# OR for cmd.exe
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirement.txt

# Place documents in data/documents/ folder (or subfolders for topics)
# Then ingest them
python ingest.py --clear

# Start server
uvicorn main:app --reload --port 8000
```

### Step 3: Setup & Run Frontend (Terminal 3)
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm start
```

### Access Points
| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Ollama | http://localhost:11434 |

---

## API Endpoints

### Chat
| Method | Endpoint | Description | Body |
|--------|----------|-------------|------|
| POST | `/chat` | Send message, get AI response | `{text, session_id?, topics?[]}` |
| POST | `/chat/stream` | Streaming chat with SSE | `{text, session_id?, topics?[]}` |

### Sessions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sessions` | Create new chat session |
| GET | `/sessions` | List all sessions with message counts |
| GET | `/sessions/{id}` | Get session with all messages |
| PUT | `/sessions/{id}` | Update session title |
| DELETE | `/sessions/{id}` | Delete session and its messages |

### Documents & Images
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents/{filename}` | Serve document file (supports #page=N) |
| GET | `/images/{id}` | Get specific image by ID |
| GET | `/images` | List all extracted images |

### Topics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/topics` | List available topics (auto-discovered from folders) |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (Ollama status, indexed counts) |
| GET | `/stats` | System statistics (documents, images, sessions, messages) |
| GET | `/chat-history` | Legacy: Get flat chat history |
| DELETE | `/chat-history` | Clear all history and sessions |
| DELETE | `/chat-history/{id}` | Delete specific chat entry |

---

## Configuration

### Backend Configuration (`backend/config.py`)

```python
# LLM Configuration
OLLAMA_MODEL = "llama3.1:8b"           # LLM model for chat
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_TIMEOUT = 300                   # 5 minutes timeout

# Embedding Configuration
EMBEDDINGS_MODEL = "nomic-embed-text"  # 768 dimensions

# Vector Search Configuration
TOP_K_DOCUMENTS = 5                    # Text chunks per query
TOP_K_IMAGES = 3                       # Max images per query
SIMILARITY_THRESHOLD = 0.3             # Min similarity score

# Document Processing
MAX_CHUNK_SIZE = 1000                  # Characters per chunk
CHUNK_OVERLAP = 200                    # Overlap between chunks

# Supported File Types
SUPPORTED_FORMATS = {".pdf", ".docx", ".pptx", ".txt"}

# ============================================================================
# PARALLEL PROCESSING CONFIGURATION (NEW)
# ============================================================================
EMBEDDING_MAX_WORKERS = 4              # Concurrent Ollama embedding requests
DOCUMENT_MAX_WORKERS = 2               # Concurrent document processing threads
IMAGE_EXTRACTION_MAX_WORKERS = 4       # Concurrent PDF page extraction threads

# ============================================================================
# EMBEDDING CACHE CONFIGURATION (NEW)
# ============================================================================
ENABLE_EMBEDDING_CACHE = True          # Enable disk-based embedding cache
EMBEDDING_CACHE_DIR = DATA_DIR / "embedding_cache"  # Cache directory

# ============================================================================
# PROGRESS REPORTING CONFIGURATION (NEW)
# ============================================================================
SHOW_PROGRESS_BAR = True               # Enable tqdm progress bars
```

### Recommended Models by RAM
| RAM | LLM Model | Commands |
|-----|-----------|----------|
| 8GB | `llama3.2:3b` | `ollama pull llama3.2:3b && ollama pull nomic-embed-text` |
| 16GB+ | `llama3.1:8b` (default) | `ollama pull llama3.1:8b && ollama pull nomic-embed-text` |

---

## Performance Optimizations

### Ingestion Pipeline (3-5x Faster)

The document ingestion pipeline has been optimized for significantly faster processing:

#### 1. Parallel Embedding Generation (`embeddings.py`)
- **ThreadPoolExecutor**: Generate multiple embeddings concurrently (4 workers default)
- **Connection Pooling**: `requests.Session` with `HTTPAdapter` for reusing HTTP connections
- **Retry Strategy**: Automatic retry on transient failures (500, 502, 503, 504)

```python
# Before: Sequential (50-100s for 100 texts)
for text in texts:
    embedding = get_embedding(text)

# After: Parallel (15-25s for 100 texts) - 3-4x faster
with ThreadPoolExecutor(max_workers=4) as executor:
    embeddings = list(executor.map(get_embedding, texts))
```

#### 2. Embedding Cache (`embeddings.py`)
- **Hash-based Disk Cache**: SHA256 hash of text → pickle file
- **Atomic Writes**: Write to temp file, then rename (prevents corruption)
- **Cache Statistics**: Track hits, misses, hit rate, cache size

```python
# Cache location: backend/data/embedding_cache/
# File naming: {sha256_hash}.pkl
# Re-ingestion speedup: 5-10x (only compute new embeddings)
```

#### 3. Parallel PDF Processing (`image_extractor.py`)
- **Page-Level Parallelism**: Process multiple PDF pages simultaneously
- **Thread-Safe SQLite**: `threading.Lock` for database operations
- **Isolated Page Processing**: Each thread opens its own PDF handle

```python
# Before: Sequential page processing (5-10 min for 500 pages)
for page_num in range(total_pages):
    process_page(page_num)

# After: Parallel page processing (1-3 min for 500 pages) - 3-5x faster
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(process_page, p) for p in range(total_pages)]
```

#### 4. Progress Reporting (`ingest.py`)
- **4-Phase Pipeline**: Discovery → Extraction → Indexing → Summary
- **tqdm Progress Bars**: Visual progress for all long operations
- **Timing Estimates**: Per-phase and total timing with human-readable format
- **Cache Statistics**: Shows cache hits/misses and hit rate at completion

```
[PHASE 1/4] Document Discovery
[PHASE 2/4] Text Extraction
  Processing pages: 100%|████████████████| 500/500 [01:23<00:00]
[PHASE 3/4] Vector Store Indexing
  Generating embeddings: 100%|███████████| 1200/1200 [00:45<00:00]
[PHASE 4/4] Summary & Statistics

[TIMING]
  Phase 1 (Discovery):  0.5s
  Phase 2 (Extraction): 1m 23s
  Phase 3 (Indexing):   45s
  Total time:           2m 8s

[EMBEDDING CACHE]
  Cache hits: 850
  Cache misses: 350
  Hit rate: 70.8%
```

#### Performance Comparison
| Operation | Before | After | Speedup |
|-----------|--------|-------|---------|
| 100 text embeddings | 50-100s | 15-25s | **3-4x** |
| 500-page PDF extraction | 5-10 min | 1-3 min | **3-5x** |
| 100 image embeddings | 50-100s | 15-25s | **3-4x** |
| Re-ingestion (cached) | Full time | 10-30% time | **5-10x** |

### Frontend Optimizations
- `React.memo` on all components
- `useCallback` for all event handlers
- Parallel API calls on startup (health + stats + sessions + topics)
- Smart session list updates (no full reload after each message)
- Lazy loading for images

### Backend Optimizations
- Caching headers for documents (24 hours) and images (7 days)
- Accept-Ranges header for PDF streaming
- Accurate page number tracking during ingestion
- Singleton pattern for services
- Batch upsert for Qdrant (100 points per batch)

---

## Chat Response Formatting

The LLM generates interactive, well-formatted responses:

### Style Guidelines (configured in `SYSTEM_PROMPT`)
- **Bold** for important terms, key values, and critical points
- Bullet points (•) for lists of features, steps, or characteristics
- Markdown tables for comparisons
- Emojis used sparingly (1-3 per response max):
  - ✅ for advantages/benefits
  - ⚠️ for warnings/cautions
  - 💡 for tips or key insights
  - 📌 for important notes
- Short paragraphs (2-3 sentences max)
- Headers (##) for distinct sections in longer answers
- NO inline citations or document references in the answer text

### Example Response Format
```markdown
## Butterfly Valve Characteristics

💡 **Key Design Features:**
- Consists of a **tubular shaped diaphragm** with T-cross section
- Can be fitted with **metal-to-polymer** or **metal-to-metal** seatings
- Supports **bi-directional flow**

✅ **Advantages:**
- High capacity at low cost
- Small body mass and lightweight
- Easy to install

| Type | Use Case |
|------|----------|
| Nominal-leakage | Throttling/flow control |
| Tight shut-off | Isolation duty |

⚠️ **Caution:** May stick in closed position unless eccentric disks are used.
```

---

## UI Design

### Color Theme (Royal Blue)
| Element | Light Mode | Dark Mode |
|---------|------------|-----------|
| Background | `#FFFFFF` | `#0f1419` |
| Surface | `#F9FAFB` | `#1a1f2e` |
| Card | `#FFFFFF` | `#232a3b` |
| Primary Accent | `#3B82F6` | `#3B82F6` |
| Text Primary | `#1A1A1A` | `#F3F4F6` |
| Border | `#E5E7EB` | `#2d3748` |

### Layout (ChatGPT-style)
- **Left Sidebar**: Collapsible, company logo, new chat button, session history grouped by date
- **Top Bar**: Menu toggle, KM logo, title, dark mode toggle
- **Chat Area**: Centered conversation with messages, welcome screen when empty
- **Input Area**: Rounded input with + (topic filter), mic (voice input), send buttons

### Message Styles
- **User Messages**: Blue gradient background (`#3B82F6` to `#1D4ED8`), right-aligned, rounded-br-md
- **Assistant Messages**: No box (clean text), KM avatar on left, markdown rendered with bold/tables/emojis

---

## Topic-Based Filtering

### Folder Structure
```
data/documents/
├── piping/              # topic="piping"
│   ├── valves.pdf
│   └── pumps.pdf
├── heat_exchanger/      # topic="heat_exchanger"
│   └── design.pdf
└── general_doc.pdf      # topic="general" (root folder)
```

### How It Works
1. **Auto-Discovery**: On startup and ingestion, scans `data/documents/` for subfolders
2. **Metadata Storage**: Each text chunk and image includes `"topic"` in metadata
3. **UI Integration**: Topics appear as checkboxes in the "+" dropdown menu
4. **Query Filtering**: When topics selected, uses Qdrant's `MatchAny` filter for multi-topic search
5. **Multi-Select**: Multiple topics can be selected simultaneously

### API Usage
```javascript
// Get available topics
GET /topics
// Response: { topics: ["piping", "heat_exchanger"], total: 2 }

// Send message with topic filter
POST /chat/stream
{
  "text": "What is a ball valve?",
  "session_id": "uuid",
  "topics": ["piping"]  // Only search in piping documents
}
```

---

## Intent Detection

The system automatically detects user intent in `main.py:_is_image_only_request()`:

### Image-Only Requests (returns only images, no text)
- "show me the valve diagram"
- "display the pump figure"
- "image of ball valve"
- "valve diagram"
- "picture of the assembly"

### Questions (returns text answer + relevant images)
- "what is a ball valve?"
- "how does a pump work?"
- "explain the valve operation"

### Detection Logic
```python
# Image-only triggers:
- Starts with: show, display, image, picture, diagram, figure
- Contains: "show me the diagram", "image of", "picture of"
- Ends with: diagram, image, picture, figure

# Excluded if contains question indicators:
- ?, what is, how does, why, explain, describe, tell me about
```

---

## Image Search (Layout-Aware)

The system uses **layout-aware extraction** to find relevant images without requiring LLaVA:

### Extraction Process (during ingestion)
1. **Bounding Box Detection**: Get image positions on each page
2. **Figure Caption Detection**: Use patterns like "Fig. 1", "Figure 2-3", "FIGURE 4"
3. **Spatial Context**: Extract text blocks above/below/beside images within ~0.7 inches
4. **Section Headings**: Associate images with nearby section headers

### Retrieval Strategy (during query)
1. **Figure Captions** (Priority 1): Match query against detected captions
2. **Layout Context** (Priority 2): Match query against nearby text context
3. **Figure References** (Priority 3): Detect "see Figure 3" in retrieved text chunks
4. **Minimum Threshold**: Score must be >= 5 to be returned (no false positives)

### Configuration
```python
# In image_extractor.py
VERTICAL_PROXIMITY_THRESHOLD = 50  # ~0.7 inches for nearby text
FIGURE_CAPTION_PATTERNS = [
    r'(Fig\.?\s*\d+[-.]?\d*[.:]\s*[^\n]{5,150})',
    r'(Figure\s+\d+[-.]?\d*[.:]\s*[^\n]{5,150})',
    # ... more patterns
]
```

---

## Frontend Components

### App.jsx
- Main state management (messages, sessions, topics, dark mode)
- Parallel initialization (health + stats + sessions + topics)
- Streaming message handling with refs
- Memoized child components

### Sidebar.jsx
- Company logo (reliance-logo.svg) with dark mode filter
- "New Chat" button with dashed border
- Session history grouped by date (Today, Yesterday, Previous 7 Days, etc.)
- Delete session on hover
- "Clear All History" button

### ChatArea.jsx
- Top bar with menu toggle, KM logo circle, title, dark mode toggle
- Connection status indicator
- Welcome screen with prompt suggestion
- Scrollable message list
- Input area wrapper

### ChatInput.jsx
- Topic filter dropdown (+ button)
- Active filter chips display
- Auto-resizing textarea
- Speech recognition (Web Speech API)
- Listening indicator animation
- Send button with loading spinner

### MessageBubble.jsx
- User/Assistant message differentiation
- Markdown rendering for assistant messages (supports bold, tables, emojis)
- Source chips with file type badges (PDF, PPT, DOC)
- Image thumbnails with overlay info
- Copy and regenerate buttons
- Typing indicator during streaming

### ImageModal.jsx
- Full-screen backdrop with blur
- Document name and page header
- "Open Source" button (opens document at page)
- Download button
- Figure caption footer

---

## Database Schema

### SQLite Tables

```sql
-- Sessions table
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat history table
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    user_message TEXT,
    assistant_response TEXT,
    source_documents TEXT,  -- JSON array
    images TEXT,            -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Images table
CREATE TABLE images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_hash TEXT UNIQUE,
    image_path TEXT,
    document_name TEXT,
    page_number INTEGER,
    context_text TEXT,
    image_description TEXT,
    figure_caption TEXT,
    bbox_x0 REAL, bbox_y0 REAL, bbox_x1 REAL, bbox_y1 REAL,
    topic TEXT,
    embedding BLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Qdrant Collections

```python
# Text documents collection
COLLECTION_NAME_TEXT = "documents_text"
# Payload: document_name, source, topic, chunk_index, page_number, file_type, text

# Images collection
COLLECTION_NAME_IMAGES = "documents_images"
# Payload: image_path, document_name, page_number, image_id, figure_caption, text
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" localhost:11434 | Run `ollama serve` in a terminal |
| "Model not found" | Run `ollama pull llama3.1:8b && ollama pull nomic-embed-text` |
| Slow responses | Close other apps, restart Ollama, or use smaller model |
| Out of memory | Change `OLLAMA_MODEL` to `"llama3.2:3b"` in config.py |
| No documents indexed | Place files in `data/documents/`, run `python ingest.py --clear` |
| Wrong page numbers | Re-run `python ingest.py --clear` to rebuild index |
| Images not showing | Check `data/extracted_images/`, re-run ingest |
| Tailwind styles not loading | Run `npm install` in frontend folder |
| Qdrant errors | Delete `data/qdrant_db/` folder and re-run ingest |
| CORS errors | Ensure backend is running on port 8000 |
| Speech recognition not working | Use Chrome/Edge, allow microphone permission |
| Inline citations in answers | Restart backend after config.py changes |
| Progress bars not showing | Install tqdm: `pip install tqdm` |

---

## Ingestion Commands

```bash
# Normal ingestion (add new documents)
python ingest.py

# Clear and re-ingest everything (clears cache too)
python ingest.py --clear

# Show image extraction and cache statistics
python ingest.py --stats
```

---

## Architecture Overview

```
+---------------------------------------------------------------+
|                    FRONTEND (React + Tailwind)                  |
|  +------------+  +--------------+  +--------------------------+ |
|  |  Sidebar   |  |  ChatArea    |  |     MessageBubble        | |
|  | - Logo     |  | - Messages   |  | - Sources (doc + page)   | |
|  | - Sessions |  | - Welcome    |  | - Images (with captions) | |
|  | - History  |  | - Input      |  | - Markdown (bold/tables) | |
|  +------------+  +--------------+  +--------------------------+ |
|                     Blue Theme (#3B82F6) + Dark Mode            |
+---------------------------------------------------------------+
                              |
                              v HTTP/SSE
+---------------------------------------------------------------+
|                        BACKEND (FastAPI)                        |
|  +-----------------------------------------------------------+ |
|  |                      main.py                               | |
|  |  - Intent Detection (image-only vs question)              | |
|  |  - Topic Filtering (multi-select)                         | |
|  |  - /chat, /chat/stream, /sessions, /documents, /images    | |
|  +-----------------------------------------------------------+ |
|         |              |              |              |          |
|         v              v              v              v          |
|  +-----------+  +-----------+  +-----------+  +-----------+    |
|  | vector_   |  | llm_      |  | image_    |  | ingest.py |    |
|  | store.py  |  | service.py|  | extractor |  |           |    |
|  | (Qdrant)  |  | (Ollama)  |  | (Parallel)|  | (4-Phase) |    |
|  | (Batch)   |  | (Stream)  |  | (Layout)  |  | (Progress)|    |
|  +-----------+  +-----------+  +-----------+  +-----------+    |
|         |                                                       |
|         v                                                       |
|  +-----------+                                                  |
|  |embeddings |  - Parallel (ThreadPoolExecutor)                |
|  |  .py      |  - Cached (SHA256 → pickle)                     |
|  |           |  - Connection Pooling (HTTPAdapter)             |
|  +-----------+                                                  |
+---------------------------------------------------------------+
                              |
              +---------------+---------------+
              v               v               v
       +-----------+   +-----------+   +-----------+
       |  Qdrant   |   |  SQLite   |   |  Ollama   |
       |  (Vectors)|   | (History) |   |  (LLM)    |
       +-----------+   +-----------+   +-----------+
              |
              v
       +-----------+
       | Embedding |
       |   Cache   |
       | (Pickle)  |
       +-----------+
```

---

## Data Flow

### Query Processing (`/chat/stream`)

```
User Query + Topics Filter
    |
    v
+-----------------------------+
| Intent Detection             |
| - Image request? -> Images   |
| - Question? -> Text + Images |
+-----------------------------+
    |
    v
+-----------------------------+
| Semantic Search (Qdrant)     |
| - Generate query embedding   |
| - Filter by topics (if any)  |
| - Get Top-K similar chunks   |
| - Extract page numbers       |
+-----------------------------+
    |
    v
+-----------------------------+
| LLM Generation (if question) |
| - Build context from chunks  |
| - Generate answer via Ollama |
| - Stream tokens via SSE      |
| - Format: bold, tables, emoji|
+-----------------------------+
    |
    v
+--------------------------------------+
| Layout-Aware Image Retrieval          |
| 1. Match by figure captions          |
| 2. Match by layout context           |
| 3. Match by figure references        |
| - Min relevance threshold required   |
| - Empty list if no good match        |
+--------------------------------------+
    |
    v
+-----------------------------+
| SSE Response Events          |
| - sources: [...]            |
| - token: "..."              |
| - images: [...]             |
| - done: {session_id}        |
+-----------------------------+
```

### Ingestion Pipeline (`python ingest.py`)

```
[PHASE 1] Document Discovery
    |
    v
+-----------------------------+
| Scan folders for documents   |
| - Root folder (general)     |
| - Subfolders (topics)       |
| - Separate PDFs from others |
+-----------------------------+
    |
    v
[PHASE 2] Text & Image Extraction
    |
    v
+-----------------------------+
| Non-PDF Documents            |
| - DOCX, PPTX, TXT           |
| - Sequential processing     |
+-----------------------------+
    |
    v
+-----------------------------+
| PDF Documents                |
| - Text extraction           |
| - Parallel image extraction |
| - Layout-aware context      |
+-----------------------------+
    |
    v
[PHASE 3] Vector Store Indexing
    |
    v
+-----------------------------+
| Generate Embeddings          |
| - Check cache first         |
| - Parallel for cache misses |
| - Save new to cache         |
+-----------------------------+
    |
    v
+-----------------------------+
| Upsert to Qdrant             |
| - Batch upsert (100/batch)  |
| - Text + Image collections  |
+-----------------------------+
    |
    v
[PHASE 4] Summary & Statistics
    |
    v
+-----------------------------+
| Report Results               |
| - Documents indexed         |
| - Images indexed            |
| - Phase timings             |
| - Cache hit rate            |
+-----------------------------+
```

---

## Session History

### Session 1-4
- Initial project setup, bug fixes, and feature additions
- Vector database setup, dependency fixes
- Image extraction from PDF and PPTX
- Layout-aware context extraction

### Session 5
- Complete frontend redesign (ChatGPT-style UI)
- Tailwind CSS integration
- Dark/Light mode support
- Intent detection implementation

### Session 6
- Blue theme redesign (from gold to #3B82F6)
- Artistic hover effects and glow animations
- Performance optimizations (memoization, parallel loading)
- Dynamic topic filtering with multi-select
- Voice input support
- Fixed source page number tracking

### Session 7
- Dependency cleanup and optimizations
- Migrated from ChromaDB to Qdrant vector database
- Local file-based Qdrant storage (no server required)
- Improved vector search performance

### Session 8
- **Major Performance Optimization (3-5x faster ingestion)**
  - Parallel embedding generation with ThreadPoolExecutor
  - Connection pooling with requests.Session + HTTPAdapter
  - Hash-based disk cache for embeddings
  - Parallel PDF page processing for image extraction
  - Thread-safe SQLite operations
  - tqdm progress bars for all long operations
  - 4-phase ingestion pipeline with timing reports
- **Interactive Chat Formatting**
  - Bold highlights for important terms
  - Markdown tables for comparisons
  - Sparingly used emojis (✅ ⚠️ 💡 📌)
  - Removed inline citations from answers
  - Cleaner context format for LLM

### Session 9 (Current - v2.0 Release)
- **Dependency Fixes**
  - Changed PyPDF2 to pypdf (actively maintained fork)
  - Updated .gitignore to include embedding_cache folder
- **Cross-System Compatibility Review**
  - Verified Python 3.12.7 compatibility
  - Documented hardware requirements (8GB+ RAM)
  - Confirmed auto-creation of data folders
- **Version Management**
  - Tagged v1.0 for original ChromaDB implementation
  - Tagged v2.0 for Qdrant + optimizations release
  - Created v1-chromadb branch for legacy support

---

## Version History

| Version | Description | Key Features |
|---------|-------------|--------------|
| v1.0 | Initial Release | ChromaDB, basic ingestion, React UI |
| v2.0 | Performance Release | Qdrant, parallel processing, embedding cache, layout-aware extraction |

---

## Current Dependencies

### Backend (`requirement.txt`)
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
pydantic==2.9.0
pydantic-settings==2.2.1
qdrant-client==1.9.0
sqlalchemy==2.0.25
python-dotenv==1.0.0
pillow==10.1.0
pypdf>=3.0.0
python-docx==0.8.11
python-pptx==0.6.23
PyMuPDF==1.23.8
requests==2.31.0
numpy==1.26.0
tqdm==4.66.0
```

### Frontend (`package.json`)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.2",
    "react-markdown": "^9.0.0",
    "lucide-react": "^0.294.0"
  },
  "devDependencies": {
    "react-scripts": "5.0.1",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32"
  }
}
```

**Note:** No LLaVA, PyTorch, sentence-transformers, pdf2image, or ollama library needed. Embeddings use Ollama's nomic-embed-text model via direct HTTP requests with connection pooling.

---

*Last Updated: March 2026 (Session 9 - v2.0 Release & Cross-System Compatibility)*

# KM_Portal Project Context

## Project Overview
A **Document-Based Chatbot System** that enables local, privacy-friendly Q&A interactions with uploaded documents using semantic search and a local LLM. The system extracts text and images from documents (PDF, PPTX, DOCX, TXT), creates vector embeddings for semantic search, and uses a local Ollama LLM to generate answers with source citations and relevant images.

---

## Key Features

- **Multi-format Document Support**: PDF, PPTX, DOCX, TXT
- **Image Extraction**: Automatically extracts figures/diagrams from PDFs and PPTX
- **Semantic Search**: Uses sentence transformers for intelligent document retrieval
- **Source Citations**: Shows exact page/slide numbers with clickable links
- **Multiple Images**: Returns up to 3 relevant images per query
- **Session Management**: Persistent chat sessions with history
- **Streaming Responses**: Real-time token-by-token response display
- **Local & Private**: All processing happens locally using Ollama

---

## Tech Stack

### Frontend
- **React 18.2.0** - UI library
- **Axios 1.6.2** - HTTP client
- **React Markdown** - Markdown rendering
- **ReactDOM Portals** - Modal rendering
- **Port**: `http://localhost:3000`

### Backend
- **FastAPI 0.109.0** - Web framework
- **Uvicorn** - ASGI server
- **Python 3.x**
- **Port**: `http://localhost:8000`

### AI/ML
- **Ollama** - Local LLM runtime (using `llama3.2:3b` model)
- **Sentence Transformers 2.2.2** - Text embeddings (all-MiniLM-L6-v2)
- **ChromaDB 0.4.22** - Vector database
- **PyTorch 2.1.2** - ML framework (CPU-only)
- **PyMuPDF 1.23.8** - PDF image extraction
- **python-pptx 0.6.23** - PPTX text and image extraction

### Database
- **SQLite** - Chat history, sessions & image metadata
- **ChromaDB** - Vector storage for text embeddings

---

## Project Structure

```
KM_Portal/
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # Main app component
│   │   ├── index.js               # React entry point
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx     # Chat interface with streaming
│   │   │   ├── MessageItem.jsx    # Message display with sources
│   │   │   ├── ImageDisplay.jsx   # Image preview & modal with source link
│   │   │   └── SettingsModal.jsx  # Settings configuration
│   │   ├── services/
│   │   │   └── api.js             # API client (chat, sessions, images, documents)
│   │   └── styles/
│   │       ├── App.css            # Global styles
│   │       └── Chat.css           # Chat & image modal styles
│   └── package.json
│
├── backend/
│   ├── main.py              # FastAPI app with all endpoints
│   ├── config.py            # Configuration settings
│   ├── embeddings.py        # Embedding generation service
│   ├── vector_store.py      # ChromaDB interface
│   ├── llm_service.py       # Ollama LLM integration
│   ├── image_extractor.py   # Image extraction (PDF & PPTX)
│   ├── ingest.py            # Document ingestion pipeline
│   ├── requirement.txt      # Python dependencies
│   └── data/
│       ├── documents/           # Input documents (PDF, DOCX, PPTX, TXT)
│       ├── extracted_images/    # Images extracted from documents
│       ├── chroma_db/           # Vector database storage
│       └── chat_history.db      # SQLite database
│
└── context.md               # This file
```

---

## How to Run

### Prerequisites
1. **Python 3.8+** installed
2. **Node.js 16+** installed
3. **Ollama** installed from https://ollama.ai

### Step 1: Start Ollama (Terminal 1)
```bash
ollama serve
```
Then pull the model:
```bash
ollama pull llama3.2:3b
```

### Step 2: Setup & Run Backend (Terminal 2)
```powershell
cd backend

# Create virtual environment (first time)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirement.txt

# Place documents in data/documents/ folder, then ingest
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
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Ollama**: http://localhost:11434

---

## API Endpoints

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Send message, get AI response with sources & images |
| POST | `/chat/stream` | Streaming chat with Server-Sent Events |

### Sessions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sessions` | Create new chat session |
| GET | `/sessions` | List all sessions |
| GET | `/sessions/{id}` | Get session with messages |
| PUT | `/sessions/{id}` | Update session title |
| DELETE | `/sessions/{id}` | Delete session |

### Documents & Images
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents/{filename}` | Serve document file (supports #page=N) |
| GET | `/images/{id}` | Get specific image by ID |
| GET | `/images` | List all extracted images |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (Ollama status, indexed counts) |
| GET | `/stats` | System statistics |
| GET | `/chat-history` | Legacy: Get flat chat history |
| DELETE | `/chat-history` | Clear all history and sessions |

---

## Document Support Matrix

| Feature | PDF | PPTX | DOCX | TXT |
|---------|-----|------|------|-----|
| Text Extraction | Yes | Yes | Yes | Yes |
| Image Extraction | Yes | Yes | No | N/A |
| Page/Slide Tracking | Yes | Yes | No | No |
| Figure Caption Detection | Yes | Yes | N/A | N/A |

---

## Configuration

Key settings in `backend/config.py`:

```python
OLLAMA_MODEL = "llama3.2:3b"      # LLM model
TOP_K_DOCUMENTS = 5               # Text chunks per query
TOP_K_IMAGES = 3                  # Max images per query
MAX_CHUNK_SIZE = 1000             # Characters per chunk
CHUNK_OVERLAP = 200               # Overlap between chunks
SIMILARITY_THRESHOLD = 0.3        # Min similarity score
```

### Recommended Models by RAM:
| RAM | Model | Command |
|-----|-------|---------|
| 8GB | `tinyllama` | `ollama pull tinyllama` |
| 16GB | `llama3.2:3b` (default) | `ollama pull llama3.2:3b` |
| 16GB+ | `llama3.1:8b` (better quality) | `ollama pull llama3.1:8b` |

---

## Session History

### Session 1
- Initial project exploration
- Fixed configuration errors and code bugs
- Updated ChromaDB API usage
- Added missing Python dependencies
- Created context.md

### Session 2
- Fixed critical package compatibility issues for Windows
- Resolved PyTorch/transformers version conflicts
- Fixed DLL loading errors (PyTorch 2.2+ incompatible)
- Added PyMuPDF for PDF image extraction

### Session 3 (Current)
- **Added PPTX image extraction support**
- **Improved source tracking with accurate page/slide numbers**
- **Multiple images support (up to 3 per query)**
- **Source deduplication**
- **Added "Open Source" button in image modal**

---

## Fixes Applied (Session 3)

### 1. PPTX Image Extraction

Added new method `extract_images_from_pptx()` in `image_extractor.py`:
- Extracts images from PowerPoint slides using python-pptx
- Filters out small icons and decorative images
- Captures slide text as context for better search
- Handles images in group shapes
- Deduplicates using MD5 hash

Updated `ingest.py` to call PPTX image extraction:
```python
elif doc_file.suffix.lower() == ".pptx":
    extracted = self.image_extractor.extract_images_from_pptx(
        str(doc_file), doc_file.name
    )
```

### 2. Accurate Page/Slide Number Tracking

Updated `ingest.py` to store page numbers in metadata during ingestion:
```python
metadatas.append({
    "document_name": file_path.name,
    "file_path": str(file_path),
    "chunk_index": i,
    "page_number": page_number,  # NEW: Extracted from [Page X] or [Slide X]
    "file_type": ext,            # NEW: .pdf, .pptx, .docx, .txt
})
```

Updated `_enrich_sources_with_pages()` in `main.py`:
- Uses stored `page_number` from metadata (primary)
- Falls back to text extraction if needed
- Handles both `[Page X]` (PDF) and `[Slide X]` (PPTX) formats
- Adds `page_label` field ("Page 5" or "Slide 3")
- **Deduplicates sources** by document+page combination

### 3. Multiple Images Support (Up to 3)

Added new method `find_relevant_images()` in `image_extractor.py`:
- Returns up to 3 relevant images (configurable via `max_images`)
- Uses 3 strategies:
  1. **Figure references** - Finds "Figure 3-1", "Fig. 5.2" in text
  2. **Context/caption match** - Scores by search term matches
  3. **Page-based matching** - Gets images from relevant pages
- Deduplicates to avoid showing same image twice

Updated both `/chat` and `/chat/stream` endpoints to use new method.

### 4. "Open Source" Button in Image Modal

Updated `ImageDisplay.jsx`:
- Added document URL generation using `documentAPI`
- Added "Open Source" button in modal header
- Clicking opens the source document at the exact page

Added CSS styling in `Chat.css`:
```css
.image-modal-source-link {
  /* Blue button with hover effects */
  background: rgba(37, 99, 235, 0.8);
  /* ... */
}
```

---

## Frontend Components

### MessageItem.jsx
- Displays user and assistant messages
- Renders markdown with custom styling
- Shows clickable source chips with page numbers
- Displays up to 3 related images
- Copy and regenerate actions

### ImageDisplay.jsx
- Thumbnail preview with loading state
- Click to enlarge in modal
- Modal shows:
  - Document name and page number
  - "Open Source" button to open document
  - Full-size image

### ChatWindow.jsx
- Streaming response display
- Session management
- Welcome screen with suggestions
- Input with send button

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" localhost:11434 | Run `ollama serve` |
| "Model not found" | Run `ollama pull llama3.2:3b` |
| Slow responses | Close other apps, restart Ollama |
| Out of memory | Reduce `TOP_K_DOCUMENTS` to 3 |
| No documents indexed | Place files in `data/documents/`, run `python ingest.py --clear` |
| `register_pytree_node` error | Use `torch==2.1.2`, `transformers==4.36.2` |
| DLL load failed (Windows) | Use `torch==2.1.2` (not 2.2+) |
| `cached_download` import error | Use `huggingface_hub==0.20.3` |
| `no such column: collections.topic` | Delete `data/chroma_db/` folder and re-run ingest |
| PPTX images not showing | Re-run `python ingest.py --clear` to re-extract |
| Wrong page numbers in sources | Re-run `python ingest.py --clear` to rebuild index |

---

## Clean Install Instructions (Windows)

If you encounter dependency issues, do a clean install:

```powershell
cd backend

# Remove old venv
Remove-Item -Recurse -Force venv -ErrorAction SilentlyContinue

# Create fresh venv
python -m venv venv

# Activate
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirement.txt

# Clear old data and re-ingest
Remove-Item -Recurse -Force data\chroma_db -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force data\extracted_images\* -ErrorAction SilentlyContinue
python ingest.py --clear
```

---

## Current requirement.txt

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
pydantic==2.9.0
pydantic-settings==2.2.1
chromadb==0.4.22
onnxruntime==1.16.3
torch==2.1.2
sentence-transformers==2.2.2
transformers==4.36.2
huggingface_hub==0.20.3
ollama==0.6.1
sqlalchemy==2.0.25
python-dotenv==1.0.0
pillow==10.1.0
PyPDF2==3.0.1
python-docx==0.8.11
python-pptx==0.6.23
pdf2image==1.17.0
PyMuPDF==1.23.8
requests==2.31.0
numpy==1.26.0
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ ChatWindow  │  │ MessageItem │  │     ImageDisplay        │ │
│  │ - Input     │  │ - Markdown  │  │ - Preview + Modal       │ │
│  │ - Streaming │  │ - Sources   │  │ - "Open Source" button  │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP/SSE
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                      main.py                              │  │
│  │  /chat, /chat/stream, /sessions, /documents, /images      │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │              │              │              │          │
│         ▼              ▼              ▼              ▼          │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐   │
│  │ vector_   │  │ llm_      │  │ image_    │  │ ingest.py │   │
│  │ store.py  │  │ service.py│  │ extractor │  │           │   │
│  │ (ChromaDB)│  │ (Ollama)  │  │ (PDF/PPTX)│  │ (Pipeline)│   │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ┌───────────┐   ┌───────────┐   ┌───────────┐
       │  ChromaDB │   │  SQLite   │   │  Ollama   │
       │  (Vectors)│   │ (History) │   │  (LLM)    │
       └───────────┘   └───────────┘   └───────────┘
```

---

## Data Flow

### Document Ingestion (`python ingest.py`)
```
Documents (PDF/PPTX/DOCX/TXT)
    │
    ▼
┌─────────────────────────────┐
│ Text Extraction              │
│ - PDF: PyPDF2 with [Page X] │
│ - PPTX: python-pptx [Slide] │
│ - DOCX: python-docx         │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ Image Extraction             │
│ - PDF: PyMuPDF (figures)    │
│ - PPTX: python-pptx shapes  │
│ - Filter: size, aspect ratio│
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ Chunking & Embedding         │
│ - 1000 char chunks          │
│ - 200 char overlap          │
│ - Sentence Transformers     │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ Storage                      │
│ - ChromaDB: text vectors    │
│ - SQLite: image metadata    │
│ - Filesystem: image files   │
└─────────────────────────────┘
```

### Query Processing (`/chat`)
```
User Question
    │
    ▼
┌─────────────────────────────┐
│ Semantic Search (ChromaDB)   │
│ - Query embedding           │
│ - Top-K similar chunks      │
│ - Extract page numbers      │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ LLM Generation (Ollama)      │
│ - Context from chunks       │
│ - Generate answer           │
│ - Stream tokens             │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ Image Retrieval              │
│ - Figure references         │
│ - Context matching          │
│ - Page-based fallback       │
│ - Up to 3 images            │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ Response                     │
│ - Answer text               │
│ - Sources (deduplicated)    │
│ - Images with page links    │
└─────────────────────────────┘
```

---

*Last Updated: February 2026 (Session 3)*

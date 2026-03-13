# KM Portal - Project Context

## Overview

A **local, privacy-focused Knowledge Management chatbot** that lets you chat with your documents. Upload PDFs, DOCX, PPTX files and ask questions - the system finds relevant content and generates answers using a local LLM.

**Key Point**: Everything runs locally on your machine. No data leaves your computer.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│                      http://localhost:3000                       │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│                      http://localhost:8000                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Embeddings  │  │  LLM Model  │  │     Vector Store        │  │
│  │ (nomic)     │  │  (LLaMA)    │  │     (Qdrant)            │  │
│  │ CPU only    │  │  CPU only   │  │     Local files         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**No external servers or APIs** - everything runs in-process.

---

## Tech Stack

### Backend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Framework | FastAPI | REST API + streaming |
| LLM | llama-cpp-python | Local LLaMA 3.1 8B (GGUF) |
| Embeddings | sentence-transformers | nomic-embed-text-v1 (768 dim) |
| Vector DB | Qdrant | Semantic search |
| Document Processing | PyMuPDF, python-docx, python-pptx | Extract text/images |

### Frontend
| Component | Technology |
|-----------|------------|
| Framework | React 18 |
| Styling | Tailwind CSS |
| HTTP Client | Axios |
| Markdown | react-markdown |

---

## How It Works

### 1. Document Ingestion (`ingest.py`)
```
Documents (PDF/DOCX/PPTX)
        │
        ▼
┌───────────────────┐
│ Extract Text      │ → Split into chunks (1000 chars, 200 overlap)
│ Extract Images    │ → Save to extracted_images/
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Generate          │ → nomic-embed-text-v1 (768 dimensions)
│ Embeddings        │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Store in Qdrant   │ → Local file-based vector database
└───────────────────┘
```

### 2. Query Processing (`main.py`)
```
User Question
        │
        ▼
┌───────────────────┐
│ Embed Question    │ → Same embedding model
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Vector Search     │ → Find top 5 similar chunks
│ (Qdrant)          │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ LLM Generation    │ → LLaMA 3.1 generates answer
│ (llama-cpp)       │   using retrieved context
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Find Images       │ → Match relevant figures
└───────────────────┘
        │
        ▼
Response (text + sources + images)
```

---

## File Structure

```
KM_Portal/
├── backend/
│   ├── config.py           # All configuration settings
│   ├── main.py             # FastAPI app, API endpoints
│   ├── embeddings.py       # Embedding service (sentence-transformers)
│   ├── llm_service.py      # LLM service (llama-cpp-python)
│   ├── vector_store.py     # Qdrant vector database
│   ├── image_extractor.py  # Image extraction and matching
│   ├── ingest.py           # Document ingestion script
│   ├── requirements.txt    # Python dependencies
│   │
│   ├── models/             # LLM model (GGUF file)
│   │   └── Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf (~4.6GB)
│   │
│   ├── hf_cache/           # HuggingFace embedding models (~523MB)
│   │   └── hub/
│   │       └── models--nomic-ai--nomic-embed-text-v1/
│   │
│   ├── data/
│   │   ├── documents/      # Your source documents (organized by topic)
│   │   ├── extracted_images/
│   │   ├── qdrant_db/      # Vector database files
│   │   ├── embedding_cache/
│   │   └── chat_history.db # SQLite chat history
│   │
│   └── venv/               # Python virtual environment
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Main app component
│   │   ├── components/
│   │   │   ├── ChatArea.jsx
│   │   │   ├── ChatInput.jsx
│   │   │   ├── MessageBubble.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   └── ImageModal.jsx
│   │   ├── services/
│   │   │   └── api.js      # API client
│   │   └── index.css       # Tailwind styles
│   ├── public/
│   ├── package.json
│   └── tailwind.config.js
│
├── .gitignore
├── SETUP.md                # Setup instructions
└── context.md              # This file
```

---

## Configuration (`config.py`)

### LLM Settings
```python
LLAMA_MODEL_PATH = "models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
LLM_TEMPERATURE = 0.5
LLM_MAX_TOKENS = 1024
LLM_CONTEXT_SIZE = 4096
LLM_GPU_LAYERS = 0          # CPU only
```

### Embedding Settings
```python
EMBEDDING_MODEL_NAME = "nomic-ai/nomic-embed-text-v1"
EMBEDDING_DIMENSION = 768
EMBEDDING_BATCH_SIZE = 32
```

### Search Settings
```python
TOP_K_DOCUMENTS = 5         # Chunks to retrieve
TOP_K_IMAGES = 3            # Images to return
SIMILARITY_THRESHOLD = 0.3
```

### Chunking Settings
```python
MAX_CHUNK_SIZE = 1000       # Characters per chunk
CHUNK_OVERLAP = 200         # Overlap for context
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/topics` | List document topics |
| POST | `/chat` | Send message (non-streaming) |
| POST | `/chat/stream` | Send message (streaming) |
| GET | `/sessions` | List chat sessions |
| POST | `/sessions` | Create new session |
| GET | `/sessions/{id}` | Get session with messages |
| DELETE | `/sessions/{id}` | Delete session |
| GET | `/images/{id}` | Get image by ID |
| GET | `/documents/{filename}` | Serve document file |

---

## Key Features

### 1. Topic-Based Filtering
Documents organized in subfolders become filterable topics:
```
data/documents/
├── piping/          → Topic: "piping"
├── valves/          → Topic: "valves"
└── general/         → Topic: "general"
```

### 2. Streaming Responses
Real-time token-by-token display via Server-Sent Events.

### 3. Image Extraction
Extracts figures from PDFs/PPTX with captions and returns relevant images with answers.

### 4. Follow-up Questions
Resolves pronouns ("its", "this") using conversation context.

### 5. Session Management
Persistent chat sessions with history.

### 6. Source Citations
Shows document name + page/slide numbers.

---

## Running the Project

### Terminal 1: Backend
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

### Terminal 2: Frontend
```bash
cd frontend
npm start
```

### Ingest Documents
```bash
cd backend
venv\Scripts\activate
python ingest.py
```

---

## Models (Auto-Download)

Both models **auto-download on first run** if not present.

### LLM: Meta-LLaMA 3.1 8B Instruct
- **File**: `Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf`
- **Repo**: `bartowski/Meta-Llama-3.1-8B-Instruct-GGUF`
- **Size**: ~4.6GB
- **Quantization**: Q4_K_M (4-bit)
- **RAM Required**: ~6GB
- **Auto-downloads** to `backend/models/`

### Embeddings: Nomic Embed Text v1
- **Model**: `nomic-ai/nomic-embed-text-v1`
- **Size**: ~523MB
- **Dimensions**: 768
- **Auto-downloads** to `backend/hf_cache/`

### Manual Download (if needed)
```python
# LLM model
from huggingface_hub import hf_hub_download
hf_hub_download(
    repo_id='bartowski/Meta-Llama-3.1-8B-Instruct-GGUF',
    filename='Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf',
    local_dir='./models'
)
```

---

## System Requirements

- **RAM**: 16GB recommended (8GB minimum)
- **Storage**: ~6GB for models
- **CPU**: Any modern multi-core
- **OS**: Windows/Linux/macOS
- **Python**: 3.10+
- **Node.js**: 18+

---

## Version

- **Version**: 6.0
- **Last Updated**: March 2026
- **Architecture**: llama-cpp-python (direct) + sentence-transformers + Qdrant

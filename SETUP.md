# KM Portal - Setup Guide

## Architecture

- LLM runs directly inside Python (llama-cpp-python, CPU only)
- Embeddings run directly (sentence-transformers, CPU only)
- No separate servers needed

## Project Structure

```
KM_Portal/
├── backend/
│   ├── hf_cache/          # HuggingFace models (~523MB)
│   ├── models/            # LLM model GGUF (~4.6GB)
│   ├── data/              # Documents, vector DB
│   ├── venv/              # Python virtual environment
│   └── *.py               # Source code
├── frontend/
│   ├── node_modules/
│   └── src/
└── SETUP.md
```

## Quick Start

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

## First-Time Setup

### 1. Prerequisites
- Python 3.10+
- Node.js 18+

### 2. Model Files (auto-download)

Both models **auto-download** on first run:

| Model | Size | Location |
|-------|------|----------|
| LLaMA 3.1 8B (GGUF) | ~4.6GB | `backend/models/` |
| Nomic Embeddings | ~523MB | `backend/hf_cache/` |

First startup will download ~5GB. Be patient.

### 3. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Frontend Setup
```bash
cd frontend
npm install
```

### 5. Add Documents
```
backend/data/documents/
├── piping/
│   └── document.pdf
├── valves/
│   └── valve_guide.pptx
└── general/
    └── overview.pdf
```

### 6. Ingest Documents
```bash
cd backend
venv\Scripts\activate
python ingest.py
```

## Troubleshooting

**Out of memory**: Use smaller model (Q3_K_M) or reduce `LLM_CONTEXT_SIZE` in config.py

**Qdrant errors**: Delete `backend/data/qdrant_db/` and re-run `python ingest.py`

## URLs

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

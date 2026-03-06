# Configuration file for Document Chatbot System

import os
from pathlib import Path

# ============================================================================
# OLLAMA MODEL CONFIGURATION
# ============================================================================

# Using llama3.1:8b for better quality responses
# Requires 16GB+ RAM for optimal performance

OLLAMA_MODEL = "llama3.1:8b"  # Better quality model

# Alternative models:
# OLLAMA_MODEL = "llama3.2:3b"    # Lighter, faster (good for 8GB RAM)
# OLLAMA_MODEL = "llama3.2:1b"    # Smallest, fastest

OLLAMA_BASE_URL = "http://localhost:11434"  # Ollama server address
OLLAMA_API_URL = OLLAMA_BASE_URL  # Alias for compatibility
OLLAMA_TIMEOUT = 300  # Timeout in seconds (5 minutes for larger models like llama3.1:8b)

# ============================================================================
# VECTOR SEARCH CONFIGURATION
# ============================================================================

# Embedding model (using Ollama's nomic-embed-text)
EMBEDDINGS_MODEL = "nomic-embed-text"  # 768 dims, better quality than MiniLM
EMBEDDING_DIMENSION = 768  # Dimension for nomic-embed-text

# Qdrant collection names
COLLECTION_NAME_TEXT = "documents_text"
COLLECTION_NAME_IMAGES = "documents_images"

# Qdrant configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_PATH = None  # Set to a path for local file-based storage, or None for in-memory/server

# Vector search parameters (unchanged - optimal for your setup)
TOP_K_DOCUMENTS = 5  # Number of text chunks to retrieve
TOP_K_IMAGES = 3  # Number of images to retrieve
SIMILARITY_THRESHOLD = 0.3  # Minimum similarity score (0.0-1.0)

# ============================================================================
# DOCUMENT PROCESSING CONFIGURATION
# ============================================================================

# Text chunking settings (unchanged - optimal)
MAX_CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks for context

# File paths (unchanged)
DATA_DIR = Path(__file__).parent / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
IMAGES_DIR = DATA_DIR / "extracted_images"
CHAT_HISTORY_DB = DATA_DIR / "chat_history.db"

# Aliases for compatibility
DB_PATH = CHAT_HISTORY_DB
QDRANT_DB_DIR = DATA_DIR / "qdrant_db"

# Create directories if they don't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
QDRANT_DB_DIR.mkdir(parents=True, exist_ok=True)

# Supported file types (unchanged)
SUPPORTED_FORMATS = {".pdf", ".docx", ".pptx", ".txt"}
SUPPORTED_EXTENSIONS = SUPPORTED_FORMATS  # Alias for compatibility

# ============================================================================
# TOPIC-BASED FILTERING CONFIGURATION
# ============================================================================

# Topics are auto-discovered from subfolders in DOCUMENTS_DIR
# e.g., data/documents/piping/ → topic="piping"
# e.g., data/documents/heat_exchanger/ → topic="heat_exchanger"

def get_available_topics():
    """Scan documents directory for topic subfolders"""
    topics = []
    if DOCUMENTS_DIR.exists():
        for item in DOCUMENTS_DIR.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                topics.append(item.name)
    return sorted(topics)

# Reserved topic name for files in root documents folder (no subfolder)
DEFAULT_TOPIC = "general"

# ============================================================================
# LLM PROMPT CONFIGURATION
# ============================================================================

# System prompt for the model
SYSTEM_PROMPT = """Answer the question using the documents below.

IMPORTANT FORMATTING RULES:
- Do NOT include inline citations or references like "(Section X of document.pdf)" in your answer
- Do NOT mention document names, page numbers, or section numbers in the answer text
- Just provide the information directly and clearly
- Images are handled separately by the system, so do not say you cannot show images

STYLE GUIDELINES (make responses engaging and easy to read):
- Use **bold** for important terms, key values, and critical points
- Use bullet points (•) for lists of features, steps, or characteristics
- When comparing items, use a markdown table format like:
  | Feature | Option A | Option B |
  |---------|----------|----------|
  | Cost    | Low      | High     |
- Use emojis sparingly for visual cues (1-3 per response max):
  • ✅ for advantages/benefits
  • ⚠️ for warnings/cautions
  • 💡 for tips or key insights
  • 📌 for important notes
- Keep paragraphs short (2-3 sentences max)
- Use headers (##) for distinct sections in longer answers

Documents:
{context}

Question: {question}

Answer:"""

# Intent detection prompt (for determining if user wants images)
IMAGE_SEARCH_PROMPT = """Based on the user's query, determine if they want to see images/diagrams/visual content.
Respond with ONLY: "SHOW_IMAGE" or "TEXT_ONLY"

User query: {question}

Response:"""

# ============================================================================
# PERFORMANCE TUNING
# ============================================================================

INFERENCE_TIMEOUT = 120  # Max seconds to wait for model response
CHUNK_PROCESSING_BATCH_SIZE = 50  # Process embeddings in batches

# Response settings
MIN_RESPONSE_LENGTH = 50  # Minimum characters in response
MAX_RESPONSE_LENGTH = 4000  # Maximum characters in response

# ============================================================================
# PARALLEL PROCESSING CONFIGURATION
# ============================================================================

# Number of concurrent Ollama embedding requests (conservative to avoid overload)
EMBEDDING_MAX_WORKERS = 4

# Number of concurrent document processing threads
DOCUMENT_MAX_WORKERS = 2

# Number of concurrent PDF page extraction threads
IMAGE_EXTRACTION_MAX_WORKERS = 4

# ============================================================================
# EMBEDDING CACHE CONFIGURATION
# ============================================================================

# Enable disk-based embedding cache to avoid recomputing identical embeddings
ENABLE_EMBEDDING_CACHE = True

# Directory for embedding cache files
EMBEDDING_CACHE_DIR = DATA_DIR / "embedding_cache"

# Create cache directory if enabled
if ENABLE_EMBEDDING_CACHE:
    EMBEDDING_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# PROGRESS REPORTING CONFIGURATION
# ============================================================================

# Enable tqdm progress bars (gracefully degrades if tqdm not installed)
SHOW_PROGRESS_BAR = True

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# SQLite chat history database
SQLALCHEMY_DATABASE_URL = f"sqlite:///{CHAT_HISTORY_DB}"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# ============================================================================
# API CONFIGURATION
# ============================================================================

# FastAPI settings
API_HOST = "0.0.0.0"
API_PORT = 8000
API_TITLE = "Document Chatbot API"
API_DESCRIPTION = "Local document-based Q&A system with Ollama"

# CORS settings (for local development)
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
]

# Frontend URL for CORS
FRONTEND_URL = "http://localhost:3000"

# ============================================================================
# 📋 LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = "INFO"
LOG_FILE = DATA_DIR / "chatbot.log"

# ============================================================================
# NOTES
# ============================================================================

"""
CURRENT CONFIGURATION:
- LLM Model: llama3.1:8b (8B parameters, needs ~5-6GB RAM)
- Embedding Model: nomic-embed-text (via Ollama, 768 dimensions)
- Vector Database: Qdrant (local file storage, no server required)

REQUIREMENTS:
- RAM: 16GB+ recommended for llama3.1:8b
- If you have less RAM, change OLLAMA_MODEL to "llama3.2:3b"

SETUP COMMANDS:
ollama pull llama3.1:8b
ollama pull nomic-embed-text

TROUBLESHOOTING:
Issue: "Connection refused" at localhost:11434
→ Run: ollama serve (keep running)

Issue: "Model not found"
→ Run: ollama pull llama3.1:8b && ollama pull nomic-embed-text

Issue: "Out of memory" error
→ Change OLLAMA_MODEL to "llama3.2:3b"
→ Reduce TOP_K_DOCUMENTS to 3

Issue: Qdrant errors
→ Delete data/qdrant_db/ folder and re-run ingest

EMBEDDING MODEL BENEFITS (nomic-embed-text):
- 768 dimensions (vs 384 for all-MiniLM-L6-v2)
- Better semantic understanding
- Runs via Ollama (no separate Python ML libs needed)
- Lower memory footprint (no PyTorch required)

QDRANT BENEFITS:
- Local file storage (no server required)
- Fast vector search with HNSW index
- Better filtering and payload support
- Production-ready with optional server mode
"""

# ============================================================================
# VERSION INFO
# ============================================================================

__version__ = "4.0"
__model_version__ = "llama3.1:8b + nomic-embed-text + Qdrant"
__last_updated__ = "March 2026"
__changes__ = """
CHANGES (v4.0):
- Vector Database: ChromaDB → Qdrant (better performance, no ONNX issues)
- Qdrant uses local file storage (no server required)
- Improved vector search with native filtering support
- Better memory efficiency and faster search

CHANGES (v3.0):
- OLLAMA_MODEL: llama3.2:3b → llama3.1:8b (better quality)
- EMBEDDINGS_MODEL: sentence-transformers → nomic-embed-text (via Ollama)
- Removed heavy dependencies (torch, sentence-transformers, transformers)
- Embeddings now use Ollama API instead of local Python models
"""

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
# 📊 VECTOR SEARCH CONFIGURATION
# ============================================================================

# Embedding model (using Ollama's nomic-embed-text)
EMBEDDINGS_MODEL = "nomic-embed-text"  # 768 dims, better quality than MiniLM
CHROMA_COLLECTION_DOCUMENTS = "documents_text"
CHROMA_COLLECTION_IMAGES = "documents_images"

# Aliases for compatibility
COLLECTION_NAME_TEXT = CHROMA_COLLECTION_DOCUMENTS
COLLECTION_NAME_IMAGES = CHROMA_COLLECTION_IMAGES

# Vector search parameters (unchanged - optimal for your setup)
TOP_K_DOCUMENTS = 5  # Number of text chunks to retrieve
TOP_K_IMAGES = 3  # Number of images to retrieve
SIMILARITY_THRESHOLD = 0.3  # Minimum similarity score (0.0-1.0)

# ============================================================================
# 📄 DOCUMENT PROCESSING CONFIGURATION
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
CHROMA_DB_DIR = DATA_DIR / "chroma_db"

# Create directories if they don't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)

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
# 🧠 LLM PROMPT CONFIGURATION
# ============================================================================

# System prompt for the model
SYSTEM_PROMPT = """Answer the question using the documents below. Do NOT say you cannot show images - images are handled separately by the system.

Documents:
{context}

Question: {question}

Answer (be detailed and use bullet points):"""

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
# 🗄️ DATABASE CONFIGURATION
# ============================================================================

# SQLite chat history database
SQLALCHEMY_DATABASE_URL = f"sqlite:///{CHAT_HISTORY_DB}"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# ============================================================================
# 🔧 API CONFIGURATION
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

EMBEDDING MODEL BENEFITS (nomic-embed-text):
- 768 dimensions (vs 384 for all-MiniLM-L6-v2)
- Better semantic understanding
- Runs via Ollama (no separate Python ML libs needed)
- Lower memory footprint (no PyTorch required)
"""

# ============================================================================
# 📊 VERSION INFO
# ============================================================================

__version__ = "3.0"
__model_version__ = "llama3.1:8b + nomic-embed-text"
__last_updated__ = "February 2026"
__changes__ = """
CHANGES (v3.0):
- OLLAMA_MODEL: llama3.2:3b → llama3.1:8b (better quality)
- EMBEDDINGS_MODEL: sentence-transformers → nomic-embed-text (via Ollama)
- Removed heavy dependencies (torch, sentence-transformers, transformers)
- Embeddings now use Ollama API instead of local Python models
"""

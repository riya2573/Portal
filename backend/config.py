# Configuration file for Document Chatbot System

import os
from pathlib import Path

# ============================================================================
# OLLAMA MODEL CONFIGURATION (UPDATED FOR YOUR 8GB RAM LAPTOP)
# ============================================================================

# MODEL CHANGED FROM: llama3:8b-instruct → tinyllama
# Reason: Your laptop has 8GB RAM, not 16GB
# tinyllama uses only 1.5-2GB RAM vs 5-6GB for llama3

OLLAMA_MODEL = "llama3.2:3b"  # ✅ OPTIMIZED FOR 8GB RAM

# If you want to try alternatives later:
# OLLAMA_MODEL = "llama3.2-1b"    # Similar speed, slightly better quality
# OLLAMA_MODEL = "llama3.2"        # 3B model (risky on 8GB, only if needed)
# ❌ DO NOT USE: mistral, llama3.1, phi4 (will crash on 8GB)

OLLAMA_BASE_URL = "http://localhost:11434"  # Ollama server address
OLLAMA_API_URL = OLLAMA_BASE_URL  # Alias for compatibility
OLLAMA_TIMEOUT = 120  # Timeout in seconds (increased for slower model)

# ============================================================================
# 📊 VECTOR SEARCH CONFIGURATION
# ============================================================================

# ChromaDB settings (unchanged - still optimal)
EMBEDDINGS_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # 384 dims
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
# ⚡ PERFORMANCE TUNING FOR 8GB RAM
# ============================================================================

# Reduced for faster responses on smaller model
INFERENCE_TIMEOUT = 60  # Max seconds to wait for model response
CHUNK_PROCESSING_BATCH_SIZE = 50  # Process embeddings in batches

# Model-specific settings for tinyllama
# tinyllama responds faster but may be less detailed
MIN_RESPONSE_LENGTH = 50  # Minimum characters in response
MAX_RESPONSE_LENGTH = 2000  # Maximum characters in response

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
# ⚠️ IMPORTANT NOTES FOR YOUR 8GB RAM LAPTOP
# ============================================================================

"""
SYSTEM SPECIFICATIONS:
- RAM: 8GB (7.74GB usable)
- Processor: Intel i3-11th Gen @ 3.00GHz
- Storage: 477GB available

RAM ALLOCATION:
- Windows/System: 1-1.5GB
- Browser/Frontend: 0.5-1GB
- FastAPI Backend: 0.5-1GB
- ChromaDB/Embeddings: 0.5-1GB
- Ollama (tinyllama): 1.5-2GB
- Free/Buffer: ~1-2GB

TINYLLAMA (1.1B) BENEFITS:
✅ Fast inference (1-2 seconds)
✅ Low RAM usage (1.5-2GB)
✅ No system lag
✅ Good for simple Q&A
✅ CPU efficient
✅ Responsive UI

PERFORMANCE TIPS:
1. Close unnecessary apps before starting
2. Don't open multiple browser tabs
3. Keep Ollama running in background (Terminal 1)
4. Restart if system becomes sluggish
5. Use smaller documents (< 50 pages)

If responses are too slow:
- Try: llama3.2-1b (slightly slower but better quality)
- Command: ollama pull llama3.2-1b
- Update OLLAMA_MODEL = "llama3.2-1b"

If you need better quality:
- Only available on 16GB+ RAM systems
- Consider upgrading RAM or using cloud-based solution

DO NOT USE THESE MODELS:
❌ llama3:8b-instruct (original - needs 5-6GB)
❌ mistral (7B - needs 5-6GB)
❌ llama3.1 (8B - needs 5-6GB)
❌ phi4 (14B - needs 7-8GB)
❌ Any model > 3B parameters

TROUBLESHOOTING:
Issue: "Connection refused" at localhost:11434
→ Run: ollama serve (keep running)

Issue: "Model not found"
→ Run: ollama pull tinyllama

Issue: Slow responses (> 5 seconds)
→ Close other apps
→ Restart Ollama
→ Clear browser cache

Issue: "Out of memory" error
→ Reduce TOP_K_DOCUMENTS to 3
→ Reduce MAX_CHUNK_SIZE to 500
→ Use smaller documents
"""

# ============================================================================
# 📊 VERSION INFO
# ============================================================================

__version__ = "2.0"
__model_version__ = "tinyllama-1.1b"
__optimization__ = "Optimized for 8GB RAM Intel i3 laptop"
__last_updated__ = "January 2026"
__changes__ = """
CHANGES FROM ORIGINAL CONFIG:
- OLLAMA_MODEL: llama3:8b-instruct → tinyllama
- OLLAMA_TIMEOUT: 60 → 120 (slower model)
- Added tinyllama-specific settings
- Optimized for 8GB RAM
- Updated documentation
- Added troubleshooting guide
"""

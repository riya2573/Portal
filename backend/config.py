# Configuration file for Document Chatbot System

import os
from pathlib import Path

# ============================================================================
# HUGGINGFACE LOCAL CACHE CONFIGURATION (for portability)
# ============================================================================
# Set HuggingFace cache to local folder so models travel with the project
HF_CACHE_DIR = Path(__file__).parent / "hf_cache"
os.environ["HF_HOME"] = str(HF_CACHE_DIR)
os.environ["TRANSFORMERS_CACHE"] = str(HF_CACHE_DIR)
os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(HF_CACHE_DIR)

# ============================================================================
# LLAMA.CPP DIRECT EXECUTION CONFIGURATION
# ============================================================================

# Model path (GGUF file)
LLAMA_MODEL_PATH = Path(__file__).parent / "models" / "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"

# Generation settings
LLM_TEMPERATURE = 0.5
LLM_MAX_TOKENS = 1024
LLM_CONTEXT_SIZE = 4096  # Context window size

# CPU only mode (no GPU)
LLM_GPU_LAYERS = 0

# ============================================================================
# SENTENCE-TRANSFORMERS CONFIGURATION
# ============================================================================

# Local embedding model using sentence-transformers
EMBEDDING_MODEL_NAME = "nomic-ai/nomic-embed-text-v1"
EMBEDDING_DIMENSION = 768  # Dimension for nomic-embed-text-v1
EMBEDDING_BATCH_SIZE = 32  # Process embeddings in batches
EMBEDDING_TRUST_REMOTE_CODE = True  # Required for nomic model

# ============================================================================
# VECTOR SEARCH CONFIGURATION
# ============================================================================

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

# System prompt for the model - OPTIMIZED for speed and document-only answers
SYSTEM_PROMPT = """You are a document-based assistant. Answer using ONLY the reference content provided below.

**CRITICAL RULES:**
1. ONLY answer if the information exists in the reference content below
2. If the question cannot be answered from the reference content, respond with:
   "I don't have information about this topic in my documents."
3. Do NOT use your general knowledge - ONLY use the reference content
4. NEVER mention "Document 1", "Document 2", "found in documents", "according to the documents", or any source references
5. Write your answer as if YOU know this information directly - do not cite or reference where it came from

**FORMATTING:**
- Use **bold** for key terms
- For comparisons: Use markdown tables
- For lists: Use dashes (-)
- For steps: Use **Step 1:**, **Step 2:** format
- Use ## headers for long answers
- ✅ for advantages, ⚠️ for disadvantages

**RESPONSE STYLE:**
- Be detailed but concise (150-400 words typical)
- Explain the "why" not just "what"
- Include specific values, percentages when available
- Write naturally without referencing sources

Reference Content:
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

# Number of concurrent embedding batch processes
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
API_DESCRIPTION = "Local document-based Q&A system with llama.cpp"

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
- LLM: llama-cpp-python (direct execution, no server needed)
- LLM Model: Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf (~4.7 GB, needs ~6GB RAM)
- Embedding Model: nomic-ai/nomic-embed-text-v1 (via sentence-transformers, 768 dimensions)
- Vector Database: Qdrant (local file storage, no server required)

REQUIREMENTS:
- RAM: 16GB+ recommended
- Python packages: llama-cpp-python, sentence-transformers, torch, transformers

SETUP COMMANDS:
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Download GGUF model to backend/models/
# From: https://huggingface.co/lmstudio-ai/Meta-Llama-3.1-8B-Instruct-GGUF

# 3. Run the backend (no separate server needed!)
python -m uvicorn main:app --reload --port 8000

TROUBLESHOOTING:
Issue: "Out of memory" error
→ Use a smaller quantized model (Q3_K_M instead of Q4_K_M)
→ Reduce LLM_CONTEXT_SIZE to 2048

Issue: Qdrant errors
→ Delete data/qdrant_db/ folder and re-run ingest

EMBEDDING MODEL BENEFITS (nomic-embed-text-v1):
- 768 dimensions (vs 384 for all-MiniLM-L6-v2)
- Better semantic understanding
- Runs locally via sentence-transformers
- No external API calls needed
"""

# ============================================================================
# VERSION INFO
# ============================================================================

__version__ = "6.0"
__model_version__ = "llama-cpp-python (direct) + sentence-transformers + Qdrant"
__last_updated__ = "March 2026"
__changes__ = """
CHANGES (v6.0):
- LLM: llama.cpp server → llama-cpp-python direct execution
- No separate server process needed - model runs inside Python
- Simpler deployment: just run uvicorn, model loads automatically
- GPU acceleration support via LLM_GPU_LAYERS config
- More portable: single process, no HTTP overhead

CHANGES (v5.0):
- LLM Server: Ollama → llama.cpp (OpenAI-compatible API)
- Embeddings: Ollama API → sentence-transformers (local Python model)

CHANGES (v4.0):
- Vector Database: ChromaDB → Qdrant
- Qdrant uses local file storage (no server required)
"""

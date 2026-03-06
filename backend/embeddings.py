import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import numpy as np
import hashlib
import pickle
import os
from pathlib import Path
from typing import List, Union, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import (
    EMBEDDINGS_MODEL,
    OLLAMA_API_URL,
    OLLAMA_TIMEOUT,
    EMBEDDING_MAX_WORKERS,
    ENABLE_EMBEDDING_CACHE,
    EMBEDDING_CACHE_DIR,
    SHOW_PROGRESS_BAR,
)

# Try to import tqdm for progress bars
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


class EmbeddingsService:
    def __init__(self):
        """Initialize the embeddings service using Ollama's nomic-embed-text"""
        self.model = EMBEDDINGS_MODEL
        self.api_url = OLLAMA_API_URL
        self._embedding_dim = None
        self.max_workers = EMBEDDING_MAX_WORKERS
        self.cache_enabled = ENABLE_EMBEDDING_CACHE
        self.cache_dir = EMBEDDING_CACHE_DIR if ENABLE_EMBEDDING_CACHE else None
        self.show_progress = SHOW_PROGRESS_BAR and TQDM_AVAILABLE

        # Statistics
        self._cache_hits = 0
        self._cache_misses = 0
        self._total_requests = 0

        # Create connection pool with retry strategy
        self._session = self._create_session()

        self._verify_model()
        print(f"[OK] Using Ollama embeddings model: {self.model}")
        print(f"     Parallel workers: {self.max_workers}")
        print(f"     Embedding cache: {'enabled' if self.cache_enabled else 'disabled'}")
        print(f"     Progress bars: {'enabled' if self.show_progress else 'disabled'}")

    def _create_session(self) -> requests.Session:
        """Create a requests session with connection pooling and retry strategy"""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
        )

        # Configure connection pool with adapter
        adapter = HTTPAdapter(
            pool_connections=self.max_workers,
            pool_maxsize=self.max_workers * 2,
            max_retries=retry_strategy,
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _verify_model(self):
        """Verify the embedding model is available in Ollama"""
        try:
            response = self._session.get(f"{self.api_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                # Check if model is available (with or without :latest tag)
                model_found = any(
                    self.model in name or name.startswith(self.model.split(":")[0])
                    for name in model_names
                )
                if not model_found:
                    print(f"[WARN] Model '{self.model}' not found in Ollama.")
                    print(f"  Available models: {model_names}")
                    print(f"  Run: ollama pull {self.model}")
        except Exception as e:
            print(f"[WARN] Could not verify model availability: {e}")

    def _get_cache_key(self, text: str) -> str:
        """Generate a cache key for a text using SHA256 hash"""
        return hashlib.sha256(f"{self.model}:{text}".encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the file path for a cached embedding"""
        return self.cache_dir / f"{cache_key}.pkl"

    def _load_from_cache(self, text: str) -> Optional[List[float]]:
        """Load embedding from disk cache if available"""
        if not self.cache_enabled:
            return None

        cache_key = self._get_cache_key(text)
        cache_path = self._get_cache_path(cache_key)

        if cache_path.exists():
            try:
                with open(cache_path, "rb") as f:
                    embedding = pickle.load(f)
                self._cache_hits += 1
                return embedding
            except Exception:
                # Cache file corrupted, ignore and recompute
                try:
                    cache_path.unlink()
                except:
                    pass

        return None

    def _save_to_cache(self, text: str, embedding: List[float]):
        """Save embedding to disk cache atomically"""
        if not self.cache_enabled or not embedding:
            return

        cache_key = self._get_cache_key(text)
        cache_path = self._get_cache_path(cache_key)
        temp_path = cache_path.with_suffix(".tmp")

        try:
            # Write to temp file first for atomic operation
            with open(temp_path, "wb") as f:
                pickle.dump(embedding, f)
            # Atomic rename
            temp_path.replace(cache_path)
        except Exception:
            # Clean up temp file if it exists
            try:
                temp_path.unlink()
            except:
                pass

    def generate_embeddings(
        self,
        texts: Union[str, List[str]],
        show_progress: Optional[bool] = None
    ) -> np.ndarray:
        """
        Generate embeddings for text or list of texts using Ollama with parallel processing

        Args:
            texts: String or list of strings to embed
            show_progress: Override for progress bar display (None = use default)

        Returns:
            Embeddings as numpy array
        """
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            return np.array([])

        self._total_requests += len(texts)
        show_progress = show_progress if show_progress is not None else self.show_progress

        # Check cache first
        embeddings = [None] * len(texts)
        texts_to_compute = []
        indices_to_compute = []

        for i, text in enumerate(texts):
            cached = self._load_from_cache(text)
            if cached is not None:
                embeddings[i] = cached
            else:
                texts_to_compute.append(text)
                indices_to_compute.append(i)
                self._cache_misses += 1

        # If all cached, return immediately
        if not texts_to_compute:
            return np.array(embeddings)

        # Generate embeddings for uncached texts in parallel
        computed_embeddings = self._generate_embeddings_parallel(
            texts_to_compute, show_progress
        )

        # Merge results and cache new embeddings
        for idx, text, embedding in zip(indices_to_compute, texts_to_compute, computed_embeddings):
            embeddings[idx] = embedding
            self._save_to_cache(text, embedding)

        return np.array(embeddings)

    def _generate_embeddings_parallel(
        self,
        texts: List[str],
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Generate embeddings in parallel using ThreadPoolExecutor

        Args:
            texts: List of texts to embed
            show_progress: Whether to show progress bar

        Returns:
            List of embeddings
        """
        if len(texts) == 1:
            # Single text, no need for parallel processing
            return [self._get_embedding(texts[0])]

        embeddings = [None] * len(texts)

        # Choose number of workers based on batch size
        num_workers = min(self.max_workers, len(texts))

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(self._get_embedding, text): i
                for i, text in enumerate(texts)
            }

            # Progress tracking
            if show_progress and TQDM_AVAILABLE:
                futures = tqdm(
                    as_completed(future_to_index),
                    total=len(texts),
                    desc="Generating embeddings",
                    unit="text"
                )
            else:
                futures = as_completed(future_to_index)

            # Collect results
            for future in futures:
                idx = future_to_index[future]
                try:
                    embeddings[idx] = future.result()
                except Exception as e:
                    print(f"[ERROR] Failed to get embedding for text {idx}: {e}")
                    dim = self._embedding_dim or 768
                    embeddings[idx] = [0.0] * dim

        return embeddings

    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text using Ollama API

        Args:
            text: Text to embed

        Returns:
            Embedding as list of floats
        """
        try:
            response = self._session.post(
                f"{self.api_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=OLLAMA_TIMEOUT,
            )
            response.raise_for_status()
            result = response.json()
            embedding = result.get("embedding", [])

            # Cache the dimension on first successful call
            if self._embedding_dim is None and embedding:
                self._embedding_dim = len(embedding)

            return embedding
        except Exception as e:
            print(f"[ERROR] Failed to get embedding: {e}")
            # Return zero vector of expected dimension (768 for nomic-embed-text)
            dim = self._embedding_dim or 768
            return [0.0] * dim

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        if self._embedding_dim is None:
            # Get a test embedding to determine dimension
            test_embedding = self._get_embedding("test")
            self._embedding_dim = len(test_embedding) if test_embedding else 768
        return self._embedding_dim

    def clear_cache(self):
        """Clear all cached embeddings"""
        if not self.cache_enabled or not self.cache_dir:
            print("[WARN] Cache not enabled")
            return

        cleared = 0
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                try:
                    cache_file.unlink()
                    cleared += 1
                except:
                    pass

            self._cache_hits = 0
            self._cache_misses = 0
            print(f"[OK] Cleared {cleared} cached embeddings")
        except Exception as e:
            print(f"[ERROR] Failed to clear cache: {e}")

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        cache_size = 0
        cache_files = 0

        if self.cache_enabled and self.cache_dir and self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_files += 1
                try:
                    cache_size += cache_file.stat().st_size
                except:
                    pass

        hit_rate = 0.0
        total = self._cache_hits + self._cache_misses
        if total > 0:
            hit_rate = self._cache_hits / total * 100

        return {
            "enabled": self.cache_enabled,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate_percent": round(hit_rate, 1),
            "cache_files": cache_files,
            "cache_size_mb": round(cache_size / (1024 * 1024), 2),
            "total_requests": self._total_requests,
        }


# Global instance
embeddings_service = None


def get_embeddings_service() -> EmbeddingsService:
    """Get or create embeddings service singleton"""
    global embeddings_service
    if embeddings_service is None:
        embeddings_service = EmbeddingsService()
    return embeddings_service

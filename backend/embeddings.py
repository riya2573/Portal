import numpy as np
import hashlib
import pickle
from pathlib import Path
from typing import List, Union, Optional, Dict

from config import (
    EMBEDDING_MODEL_NAME,
    EMBEDDING_DIMENSION,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_TRUST_REMOTE_CODE,
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
        """Initialize the embeddings service using sentence-transformers"""
        self.model_name = EMBEDDING_MODEL_NAME
        self._model = None  # Lazy-loaded
        self._embedding_dim = EMBEDDING_DIMENSION
        self.batch_size = EMBEDDING_BATCH_SIZE
        self.cache_enabled = ENABLE_EMBEDDING_CACHE
        self.cache_dir = EMBEDDING_CACHE_DIR if ENABLE_EMBEDDING_CACHE else None
        self.show_progress = SHOW_PROGRESS_BAR and TQDM_AVAILABLE

        # Statistics
        self._cache_hits = 0
        self._cache_misses = 0
        self._total_requests = 0

        print(f"[OK] Embeddings service initialized")
        print(f"     Model: {self.model_name}")
        print(f"     Batch size: {self.batch_size}")
        print(f"     Embedding cache: {'enabled' if self.cache_enabled else 'disabled'}")
        print(f"     Progress bars: {'enabled' if self.show_progress else 'disabled'}")

    def _load_model(self):
        """Lazy-load the sentence-transformer model"""
        if self._model is None:
            print(f"[INFO] Loading embedding model: {self.model_name}...")
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(
                    self.model_name,
                    trust_remote_code=EMBEDDING_TRUST_REMOTE_CODE,
                    device="cpu"  # Force CPU only
                )
                # Verify dimension
                test_embedding = self._model.encode(["test"], convert_to_numpy=True)
                actual_dim = test_embedding.shape[1]
                if actual_dim != self._embedding_dim:
                    print(f"[WARN] Model dimension {actual_dim} differs from configured {self._embedding_dim}")
                    self._embedding_dim = actual_dim
                print(f"[OK] Embedding model loaded (dimension: {self._embedding_dim})")
            except Exception as e:
                print(f"[ERROR] Failed to load embedding model: {e}")
                raise
        return self._model

    def _get_cache_key(self, text: str) -> str:
        """Generate a cache key for a text using SHA256 hash"""
        return hashlib.sha256(f"{self.model_name}:{text}".encode()).hexdigest()

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
        Generate embeddings for text or list of texts using sentence-transformers

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

        # Load model (lazy loading)
        model = self._load_model()

        # Generate embeddings in batches
        computed_embeddings = self._generate_embeddings_batch(
            model, texts_to_compute, show_progress
        )

        # Merge results and cache new embeddings
        for idx, text, embedding in zip(indices_to_compute, texts_to_compute, computed_embeddings):
            embedding_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
            embeddings[idx] = embedding_list
            self._save_to_cache(text, embedding_list)

        return np.array(embeddings)

    def _generate_embeddings_batch(
        self,
        model,
        texts: List[str],
        show_progress: bool = False
    ) -> List[np.ndarray]:
        """
        Generate embeddings in batches using sentence-transformers

        Args:
            model: SentenceTransformer model
            texts: List of texts to embed
            show_progress: Whether to show progress bar

        Returns:
            List of embeddings as numpy arrays
        """
        all_embeddings = []

        # Process in batches
        num_batches = (len(texts) + self.batch_size - 1) // self.batch_size

        if show_progress and TQDM_AVAILABLE:
            batch_iterator = tqdm(
                range(0, len(texts), self.batch_size),
                total=num_batches,
                desc="Generating embeddings",
                unit="batch"
            )
        else:
            batch_iterator = range(0, len(texts), self.batch_size)

        for batch_start in batch_iterator:
            batch_end = min(batch_start + self.batch_size, len(texts))
            batch_texts = texts[batch_start:batch_end]

            try:
                # Generate embeddings for batch
                batch_embeddings = model.encode(
                    batch_texts,
                    convert_to_numpy=True,
                    show_progress_bar=False  # We handle progress ourselves
                )
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                print(f"[ERROR] Failed to generate embeddings for batch: {e}")
                # Return zero vectors for failed batch
                for _ in batch_texts:
                    all_embeddings.append(np.zeros(self._embedding_dim))

        return all_embeddings

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
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

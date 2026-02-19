import requests
import numpy as np
from typing import List, Union
from config import EMBEDDINGS_MODEL, OLLAMA_API_URL, OLLAMA_TIMEOUT


class EmbeddingsService:
    def __init__(self):
        """Initialize the embeddings service using Ollama's nomic-embed-text"""
        self.model = EMBEDDINGS_MODEL
        self.api_url = OLLAMA_API_URL
        self._embedding_dim = None
        self._verify_model()
        print(f"[OK] Using Ollama embeddings model: {self.model}")

    def _verify_model(self):
        """Verify the embedding model is available in Ollama"""
        try:
            response = requests.get(f"{self.api_url}/api/tags")
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

    def generate_embeddings(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for text or list of texts using Ollama

        Args:
            texts: String or list of strings to embed

        Returns:
            Embeddings as numpy array
        """
        if isinstance(texts, str):
            texts = [texts]

        embeddings = []
        for text in texts:
            embedding = self._get_embedding(text)
            embeddings.append(embedding)

        return np.array(embeddings)

    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text using Ollama API

        Args:
            text: Text to embed

        Returns:
            Embedding as list of floats
        """
        try:
            response = requests.post(
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


# Global instance
embeddings_service = None


def get_embeddings_service() -> EmbeddingsService:
    """Get or create embeddings service singleton"""
    global embeddings_service
    if embeddings_service is None:
        embeddings_service = EmbeddingsService()
    return embeddings_service

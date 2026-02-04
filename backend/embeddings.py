from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
from config import EMBEDDINGS_MODEL


class EmbeddingsService:
    def __init__(self):
        """Initialize the embeddings model"""
        self.model = SentenceTransformer(EMBEDDINGS_MODEL)
        print(f"[OK] Loaded embeddings model: {EMBEDDINGS_MODEL}")

    def generate_embeddings(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for text or list of texts

        Args:
            texts: String or list of strings to embed

        Returns:
            Embeddings as numpy array
        """
        if isinstance(texts, str):
            texts = [texts]

        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        return self.model.get_sentence_embedding_dimension()


# Global instance
embeddings_service = None


def get_embeddings_service() -> EmbeddingsService:
    """Get or create embeddings service singleton"""
    global embeddings_service
    if embeddings_service is None:
        embeddings_service = EmbeddingsService()
    return embeddings_service

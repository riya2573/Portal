import os

# Suppress ChromaDB telemetry and disable default embedding function
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_DISABLE_ONNX"] = "1"

import chromadb
from chromadb.config import Settings
import sqlite3
from typing import List, Tuple
import numpy as np
import os
from config import (
    CHROMA_DB_DIR,
    COLLECTION_NAME_TEXT,
    COLLECTION_NAME_IMAGES,
    TOP_K_DOCUMENTS,
    TOP_K_IMAGES,
    DB_PATH,
)


class VectorStore:
    def __init__(self):
        """Initialize ChromaDB"""
        # Ensure the directory exists
        os.makedirs(CHROMA_DB_DIR, exist_ok=True)

        # Use PersistentClient for ChromaDB 0.4+ (works with 0.5.x)
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DB_DIR),
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collections
        self.text_collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME_TEXT, metadata={"hnsw:space": "cosine"}
        )

        self.images_collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME_IMAGES, metadata={"hnsw:space": "cosine"}
        )

        print("[OK] Initialized ChromaDB collections")

    def add_text_documents(
        self, texts: List[str], metadatas: List[dict], ids: List[str]
    ):
        """
        Add text documents to vector store

        Args:
            texts: List of text chunks
            metadatas: List of metadata dicts (doc_name, page, etc.)
            ids: Unique IDs for documents
        """
        try:
            self.text_collection.add(documents=texts, metadatas=metadatas, ids=ids)
            print(f"[OK] Added {len(texts)} text chunks to vector store")
        except Exception as e:
            print(f"[ERROR] Error adding documents: {str(e)}")

    def add_image_metadata(self, image_ids: List[int]):
        """
        Add image metadata to vector store for searching

        Args:
            image_ids: List of image IDs from SQLite
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        for img_id in image_ids:
            cursor.execute(
                "SELECT image_path, document_name, page_number FROM images WHERE id = ?",
                (img_id,),
            )
            row = cursor.fetchone()

            if row:
                image_path, doc_name, page_num = row
                # Use upsert to handle duplicates
                self.images_collection.upsert(
                    documents=[f"Image from {doc_name} page {page_num}"],
                    metadatas=[
                        {
                            "image_path": image_path,
                            "document_name": doc_name,
                            "page_number": page_num,
                            "image_id": img_id,
                        }
                    ],
                    ids=[f"image_{img_id}"],
                )

        conn.close()
        print(f"[OK] Added {len(image_ids)} images to vector store")

    def search_text(
        self, query: str, n_results: int = TOP_K_DOCUMENTS
    ) -> Tuple[List[str], List[dict]]:
        """
        Search for relevant text documents

        Args:
            query: Search query
            n_results: Number of results to return

        Returns:
            Tuple of (texts, metadatas)
        """
        try:
            results = self.text_collection.query(
                query_texts=[query], n_results=n_results
            )

            texts = results["documents"][0] if results["documents"] else []
            metadatas = results["metadatas"][0] if results["metadatas"] else []

            return texts, metadatas
        except Exception as e:
            print(f"[ERROR] Error searching documents: {str(e)}")
            return [], []

    def search_images(self, query: str, n_results: int = TOP_K_IMAGES) -> List[dict]:
        """
        Search for relevant images

        Args:
            query: Search query
            n_results: Number of results to return

        Returns:
            List of image metadata dicts
        """
        try:
            results = self.images_collection.query(
                query_texts=[query], n_results=n_results
            )

            metadatas = results["metadatas"][0] if results["metadatas"] else []
            return metadatas
        except Exception as e:
            print(f"[ERROR] Error searching images: {str(e)}")
            return []

    def get_collection_stats(self) -> dict:
        """Get statistics about collections"""
        return {
            "text_documents": self.text_collection.count(),
            "images": self.images_collection.count(),
        }

    def clear_all(self):
        """Clear all collections (use with caution)"""
        self.client.delete_collection(COLLECTION_NAME_TEXT)
        self.client.delete_collection(COLLECTION_NAME_IMAGES)
        self.text_collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME_TEXT, metadata={"hnsw:space": "cosine"}
        )
        self.images_collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME_IMAGES, metadata={"hnsw:space": "cosine"}
        )
        print("[OK] Cleared all collections")


# Global instance
vector_store = None


def get_vector_store() -> VectorStore:
    """Get or create vector store singleton"""
    global vector_store
    if vector_store is None:
        vector_store = VectorStore()
    return vector_store

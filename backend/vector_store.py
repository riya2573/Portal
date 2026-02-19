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
        Add image metadata to vector store for searching.
        Uses figure_caption and context_text for embedding-based search.

        Args:
            image_ids: List of image IDs from SQLite
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        added_count = 0
        for img_id in image_ids:
            cursor.execute(
                """SELECT image_path, document_name, page_number, figure_caption, context_text
                   FROM images WHERE id = ?""",
                (img_id,),
            )
            row = cursor.fetchone()

            if row:
                image_path, doc_name, page_num, caption, context = row

                # Build searchable document text from caption and context
                doc_parts = []
                if caption:
                    doc_parts.append(caption)
                if context:
                    doc_parts.append(context)

                # Fallback to basic description if no caption/context
                if not doc_parts:
                    doc_parts.append(f"Image from {doc_name} page {page_num}")

                doc_text = " | ".join(doc_parts)

                # Use upsert to handle duplicates
                self.images_collection.upsert(
                    documents=[doc_text],
                    metadatas=[
                        {
                            "image_path": image_path,
                            "document_name": doc_name,
                            "page_number": page_num,
                            "image_id": img_id,
                            "figure_caption": caption or "",
                        }
                    ],
                    ids=[f"image_{img_id}"],
                )
                added_count += 1

        conn.close()
        print(f"[OK] Added {added_count} images to vector store (using caption/context)")

    def search_text(
        self, query: str, n_results: int = TOP_K_DOCUMENTS, topic: str = None, topics: List[str] = None
    ) -> Tuple[List[str], List[dict]]:
        """
        Search for relevant text documents with optional topic filtering

        Args:
            query: Search query
            n_results: Number of results to return
            topic: Single topic to filter by (deprecated, use topics)
            topics: List of topics to filter by (supports multi-select)

        Returns:
            Tuple of (texts, metadatas)
        """
        try:
            # Build query parameters
            query_params = {
                "query_texts": [query],
                "n_results": n_results
            }

            # Add topic filter if specified
            if topics and len(topics) > 0:
                if len(topics) == 1:
                    # Single topic filter
                    query_params["where"] = {"topic": topics[0]}
                else:
                    # Multi-topic filter using $in operator
                    query_params["where"] = {"topic": {"$in": topics}}
            elif topic:
                # Legacy single topic support
                query_params["where"] = {"topic": topic}

            results = self.text_collection.query(**query_params)

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

import os
import sqlite3
from typing import List, Tuple, Optional
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    MatchAny,
)

from config import (
    QDRANT_DB_DIR,
    COLLECTION_NAME_TEXT,
    COLLECTION_NAME_IMAGES,
    TOP_K_DOCUMENTS,
    TOP_K_IMAGES,
    DB_PATH,
    EMBEDDING_DIMENSION,
    SHOW_PROGRESS_BAR,
)
from embeddings import get_embeddings_service

# Try to import tqdm for progress bars
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


class VectorStore:
    def __init__(self):
        """Initialize Qdrant vector store with local file storage"""
        # Ensure the directory exists
        os.makedirs(QDRANT_DB_DIR, exist_ok=True)

        # Use local file-based storage (no server required)
        self.client = QdrantClient(path=str(QDRANT_DB_DIR))

        # Get embeddings service for generating vectors
        self.embeddings_service = get_embeddings_service()

        # Progress bar settings
        self.show_progress = SHOW_PROGRESS_BAR and TQDM_AVAILABLE

        # Initialize collections
        self._init_collections()

        print("[OK] Initialized Qdrant vector store (local file storage)")

    def _init_collections(self):
        """Create collections if they don't exist"""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        # Create text documents collection
        if COLLECTION_NAME_TEXT not in collection_names:
            self.client.create_collection(
                collection_name=COLLECTION_NAME_TEXT,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIMENSION,
                    distance=Distance.COSINE
                )
            )
            print(f"[OK] Created collection: {COLLECTION_NAME_TEXT}")

        # Create images collection
        if COLLECTION_NAME_IMAGES not in collection_names:
            self.client.create_collection(
                collection_name=COLLECTION_NAME_IMAGES,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIMENSION,
                    distance=Distance.COSINE
                )
            )
            print(f"[OK] Created collection: {COLLECTION_NAME_IMAGES}")

    def add_text_documents(
        self, texts: List[str], metadatas: List[dict], ids: List[str]
    ):
        """
        Add text documents to vector store with parallel embedding generation

        Args:
            texts: List of text chunks
            metadatas: List of metadata dicts (doc_name, page, etc.)
            ids: Unique IDs for documents
        """
        try:
            print(f"[EMBED] Generating embeddings for {len(texts)} text chunks...")

            # Generate embeddings for all texts (uses parallel processing internally)
            embeddings = self.embeddings_service.generate_embeddings(
                texts,
                show_progress=self.show_progress
            )

            # Create points for Qdrant
            print(f"[DB] Creating Qdrant points...")
            points = []

            # Use progress bar for point creation if enabled
            text_iter = enumerate(zip(texts, metadatas, ids))
            if self.show_progress and TQDM_AVAILABLE:
                text_iter = tqdm(
                    text_iter,
                    total=len(texts),
                    desc="Creating points",
                    unit="chunk"
                )

            for i, (text, metadata, doc_id) in text_iter:
                # Store the text content in payload along with metadata
                payload = {**metadata, "text": text}

                points.append(PointStruct(
                    id=str(uuid.uuid4()),  # Qdrant needs UUID or int
                    vector=embeddings[i].tolist(),
                    payload=payload
                ))

            # Upsert points in batches (Qdrant handles large batches well)
            batch_size = 100
            total_batches = (len(points) + batch_size - 1) // batch_size

            print(f"[DB] Upserting {len(points)} points in {total_batches} batches...")

            batch_iter = range(0, len(points), batch_size)
            if self.show_progress and TQDM_AVAILABLE:
                batch_iter = tqdm(
                    batch_iter,
                    total=total_batches,
                    desc="Upserting batches",
                    unit="batch"
                )

            for i in batch_iter:
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=COLLECTION_NAME_TEXT,
                    points=batch
                )

            print(f"[OK] Added {len(texts)} text chunks to Qdrant vector store")
        except Exception as e:
            print(f"[ERROR] Error adding documents: {str(e)}")
            raise

    def add_image_metadata(self, image_ids: List[int]):
        """
        Add image metadata to vector store for searching.
        Uses figure_caption and context_text for embedding-based search.
        Optimized to generate all embeddings at once using parallel processing.

        Args:
            image_ids: List of image IDs from SQLite
        """
        if not image_ids:
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Fetch all image data at once
        print(f"[IMG] Loading metadata for {len(image_ids)} images...")
        image_data = []
        doc_texts = []

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
                doc_texts.append(doc_text)
                image_data.append({
                    "img_id": img_id,
                    "image_path": image_path,
                    "doc_name": doc_name,
                    "page_num": page_num,
                    "caption": caption,
                    "doc_text": doc_text,
                })

        conn.close()

        if not image_data:
            return

        # Generate all embeddings at once (parallel processing)
        print(f"[EMBED] Generating embeddings for {len(doc_texts)} images...")
        embeddings = self.embeddings_service.generate_embeddings(
            doc_texts,
            show_progress=self.show_progress
        )

        # Create points
        print(f"[DB] Creating Qdrant points for images...")
        points = []
        for i, img_info in enumerate(image_data):
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=embeddings[i].tolist(),
                payload={
                    "image_path": img_info["image_path"],
                    "document_name": img_info["doc_name"],
                    "page_number": img_info["page_num"],
                    "image_id": img_info["img_id"],
                    "figure_caption": img_info["caption"] or "",
                    "text": img_info["doc_text"],
                }
            ))

        if points:
            # Upsert points
            self.client.upsert(
                collection_name=COLLECTION_NAME_IMAGES,
                points=points
            )

        print(f"[OK] Added {len(points)} images to Qdrant vector store (using caption/context)")

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
            # Generate embedding for the query
            query_embedding = self.embeddings_service.generate_embeddings(query)[0]

            # Build filter if topics are specified
            query_filter = None
            if topics and len(topics) > 0:
                if len(topics) == 1:
                    # Single topic filter
                    query_filter = Filter(
                        must=[
                            FieldCondition(
                                key="topic",
                                match=MatchValue(value=topics[0])
                            )
                        ]
                    )
                else:
                    # Multi-topic filter using MatchAny
                    query_filter = Filter(
                        must=[
                            FieldCondition(
                                key="topic",
                                match=MatchAny(any=topics)
                            )
                        ]
                    )
            elif topic:
                # Legacy single topic support
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="topic",
                            match=MatchValue(value=topic)
                        )
                    ]
                )

            # Perform search
            results = self.client.search(
                collection_name=COLLECTION_NAME_TEXT,
                query_vector=query_embedding.tolist(),
                query_filter=query_filter,
                limit=n_results,
                with_payload=True
            )

            # Extract texts and metadatas from results
            texts = []
            metadatas = []

            for hit in results:
                payload = hit.payload
                # Extract text from payload
                text = payload.pop("text", "")
                texts.append(text)
                metadatas.append(payload)

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
            # Generate embedding for the query
            query_embedding = self.embeddings_service.generate_embeddings(query)[0]

            # Perform search
            results = self.client.search(
                collection_name=COLLECTION_NAME_IMAGES,
                query_vector=query_embedding.tolist(),
                limit=n_results,
                with_payload=True
            )

            # Extract metadatas from results
            metadatas = []
            for hit in results:
                payload = hit.payload.copy()
                payload.pop("text", None)  # Remove text field
                metadatas.append(payload)

            return metadatas
        except Exception as e:
            print(f"[ERROR] Error searching images: {str(e)}")
            return []

    def get_collection_stats(self) -> dict:
        """Get statistics about collections"""
        try:
            text_info = self.client.get_collection(COLLECTION_NAME_TEXT)
            images_info = self.client.get_collection(COLLECTION_NAME_IMAGES)

            return {
                "text_documents": text_info.points_count,
                "images": images_info.points_count,
            }
        except Exception as e:
            print(f"[ERROR] Error getting collection stats: {str(e)}")
            return {"text_documents": 0, "images": 0}

    def clear_all(self):
        """Clear all collections (use with caution)"""
        try:
            # Delete and recreate collections
            self.client.delete_collection(COLLECTION_NAME_TEXT)
            self.client.delete_collection(COLLECTION_NAME_IMAGES)

            # Recreate collections
            self.client.create_collection(
                collection_name=COLLECTION_NAME_TEXT,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIMENSION,
                    distance=Distance.COSINE
                )
            )
            self.client.create_collection(
                collection_name=COLLECTION_NAME_IMAGES,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIMENSION,
                    distance=Distance.COSINE
                )
            )
            print("[OK] Cleared all Qdrant collections")
        except Exception as e:
            print(f"[ERROR] Error clearing collections: {str(e)}")


# Global instance
vector_store = None


def get_vector_store() -> VectorStore:
    """Get or create vector store singleton"""
    global vector_store
    if vector_store is None:
        vector_store = VectorStore()
    return vector_store

#!/usr/bin/env python3
"""
Document Ingestion Pipeline
Extracts text and images from documents, generates embeddings, and stores in vector DB
Run: python ingest.py
"""

import os
import sqlite3
from pathlib import Path
from typing import List, Tuple
import uuid

# Import local modules
from config import (
    DOCUMENTS_DIR,
    IMAGES_DIR,
    DB_PATH,
    SUPPORTED_EXTENSIONS,
    MAX_CHUNK_SIZE,
    CHUNK_OVERLAP,
)
from embeddings import get_embeddings_service
from vector_store import get_vector_store
from image_extractor import get_image_extractor

try:
    from docx import Document as DocxDocument
except ImportError:
    print("Error: python-docx not installed. Run: pip install python-docx")
    exit(1)

try:
    from pptx import Presentation
except ImportError:
    print("Error: python-pptx not installed. Run: pip install python-pptx")
    exit(1)


class DocumentProcessor:
    def __init__(self):
        self.embeddings_service = get_embeddings_service()
        self.vector_store = get_vector_store()
        self.image_extractor = get_image_extractor()
        self._init_chat_db()

    def _init_chat_db(self):
        """Initialize SQLite database for chat history"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT,
                assistant_response TEXT,
                source_documents TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

    def process_all_documents(self):
        """Process all documents in the documents directory"""
        print("\n" + "=" * 60)
        print("DOCUMENT INGESTION PIPELINE")
        print("=" * 60)

        if not DOCUMENTS_DIR.exists():
            print(f"[ERROR] Documents directory not found: {DOCUMENTS_DIR}")
            return

        # Get all supported files
        document_files = []
        for ext in SUPPORTED_EXTENSIONS:
            document_files.extend(DOCUMENTS_DIR.glob(f"*{ext}"))

        if not document_files:
            print(f"[WARN] No documents found in {DOCUMENTS_DIR}")
            print(f"   Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}")
            return

        print(f"\nFound {len(document_files)} documents to process:")
        for file in document_files:
            print(f"  - {file.name}")

        # Process each document
        all_texts = []
        all_metadatas = []
        all_ids = []
        image_ids = []

        for doc_file in document_files:
            print(f"\n[FILE] Processing: {doc_file.name}")

            texts, metadatas, ids = self._process_document(doc_file)

            if texts:
                all_texts.extend(texts)
                all_metadatas.extend(metadatas)
                all_ids.extend(ids)
                print(f"  [OK] Extracted {len(texts)} text chunks")

            # Extract images from PDFs
            if doc_file.suffix.lower() == ".pdf":
                extracted = self.image_extractor.extract_images_from_pdf(
                    str(doc_file), doc_file.name
                )
                if extracted:
                    # Get image IDs from database
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT id FROM images WHERE document_name = ?",
                        (doc_file.name,),
                    )
                    for row in cursor.fetchall():
                        image_ids.append(row[0])
                    conn.close()

            # Extract images from PPTX
            elif doc_file.suffix.lower() == ".pptx":
                extracted = self.image_extractor.extract_images_from_pptx(
                    str(doc_file), doc_file.name
                )
                if extracted:
                    # Get image IDs from database
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT id FROM images WHERE document_name = ?",
                        (doc_file.name,),
                    )
                    for row in cursor.fetchall():
                        image_ids.append(row[0])
                    conn.close()

        # Add to vector store
        if all_texts:
            print(f"\n[DB] Adding {len(all_texts)} documents to vector store...")
            self.vector_store.add_text_documents(all_texts, all_metadatas, all_ids)

        # Add images to vector store
        if image_ids:
            print(f"\n[IMG] Adding {len(image_ids)} images to vector store...")
            self.vector_store.add_image_metadata(image_ids)

        # Print summary
        stats = self.vector_store.get_collection_stats()
        print("\n" + "=" * 60)
        print("INGESTION COMPLETE")
        print("=" * 60)
        print(f"Text documents indexed: {stats['text_documents']}")
        print(f"Images indexed: {stats['images']}")
        print(f"Images directory: {IMAGES_DIR}")
        print(f"Vector DB: {DB_PATH}")
        print("\n[OK] Ready to start backend server!")
        print("=" * 60 + "\n")

    def _process_document(
        self, file_path: Path
    ) -> Tuple[List[str], List[dict], List[str]]:
        """
        Process a single document and return text chunks

        Args:
            file_path: Path to document

        Returns:
            Tuple of (texts, metadatas, ids)
        """
        ext = file_path.suffix.lower()

        try:
            if ext == ".pdf":
                text = self._extract_text_from_pdf(file_path)
            elif ext == ".docx":
                text = self._extract_text_from_docx(file_path)
            elif ext == ".pptx":
                text = self._extract_text_from_pptx(file_path)
            elif ext == ".txt":
                text = self._extract_text_from_txt(file_path)
            else:
                print(f"  [ERROR] Unsupported file format: {ext}")
                return [], [], []

            if not text or text.strip() == "":
                print(f"  [X] No text extracted")
                return [], [], []

            # Split into chunks
            print(f"  Chunking {len(text)} characters with max_size={MAX_CHUNK_SIZE}, overlap={CHUNK_OVERLAP}...")
            chunks = self._chunk_text(text, MAX_CHUNK_SIZE, CHUNK_OVERLAP)
            print(f"  Created {len(chunks)} chunks")

            # Create metadata for each chunk with page/slide numbers
            import re
            metadatas = []
            for i, chunk in enumerate(chunks):
                # Extract page number (for PDFs)
                page_match = re.search(r'\[Page\s*(\d+)\]', chunk)
                # Extract slide number (for PPTX)
                slide_match = re.search(r'\[Slide\s*(\d+)\]', chunk)

                # Determine the page/slide number
                if page_match:
                    page_number = int(page_match.group(1))
                elif slide_match:
                    page_number = int(slide_match.group(1))
                else:
                    page_number = 1  # Default

                metadatas.append({
                    "document_name": file_path.name,
                    "file_path": str(file_path),
                    "chunk_index": i,
                    "page_number": page_number,
                    "file_type": ext,  # .pdf, .pptx, .docx, .txt
                })

            # Create unique IDs
            ids = [f"{file_path.stem}_{uuid.uuid4()}" for _ in chunks]

            return chunks, metadatas, ids

        except Exception as e:
            import traceback
            error_msg = str(e) or repr(e)
            print(f"  [ERROR] Error processing file: {type(e).__name__}: {error_msg}")
            traceback.print_exc()
            return [], [], []

    def _extract_text_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF - processes pages one at a time to save memory"""
        try:
            from pypdf import PdfReader
        except ImportError:
            try:
                # Fallback to PyPDF2
                from PyPDF2 import PdfReader
            except ImportError:
                print("  [ERROR] PDF library not installed. Run: pip install pypdf")
                return ""

        text = []
        try:
            pdf = PdfReader(str(file_path))
            total_pages = len(pdf.pages)
            print(f"  [READ] Extracting text from {total_pages} pages...")

            for page_num in range(total_pages):
                try:
                    page_text = pdf.pages[page_num].extract_text()
                    if page_text and page_text.strip():
                        text.append(f"[Page {page_num + 1}] {page_text}")

                    if (page_num + 1) % 100 == 0:
                        print(f"  [OK] Extracted text from {page_num + 1}/{total_pages} pages...")
                except Exception as page_error:
                    print(f"  [WARN] Skipping page {page_num + 1}: {str(page_error)}")
                    continue

            print(f"  [OK] Text extraction complete: {len(text)} pages with content")
        except Exception as e:
            print(f"  [WARN] Error reading PDF: {str(e)}")

        return "\n\n".join(text)

    def _extract_text_from_docx(self, file_path: Path) -> str:
        """Extract text from DOCX"""
        text = []
        try:
            doc = DocxDocument(str(file_path))
            for para in doc.paragraphs:
                if para.text.strip():
                    text.append(para.text)

            # Also extract from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text.append(cell.text)
        except Exception as e:
            print(f"  [WARN] Error reading DOCX: {str(e)}")

        return "\n\n".join(text)

    def _extract_text_from_pptx(self, file_path: Path) -> str:
        """Extract text from PPTX"""
        text = []
        try:
            prs = Presentation(str(file_path))
            for slide_num, slide in enumerate(prs.slides, 1):
                slide_text = [f"[Slide {slide_num}]"]
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_text.append(shape.text)
                text.append("\n".join(slide_text))
        except Exception as e:
            print(f"  [WARN] Error reading PPTX: {str(e)}")

        return "\n\n".join(text)

    def _extract_text_from_txt(self, file_path: Path) -> str:
        """Extract text from TXT"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"  [WARN] Error reading TXT: {str(e)}")
            return ""

    def _chunk_text(self, text: str, max_size: int, overlap: int) -> List[str]:
        """
        Split text into overlapping chunks

        Args:
            text: Text to chunk
            max_size: Max characters per chunk
            overlap: Character overlap between chunks

        Returns:
            List of text chunks
        """
        if not text:
            return []

        # Ensure overlap is less than max_size to avoid infinite loops
        if overlap >= max_size:
            overlap = max_size // 2

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            # Take max_size characters
            end = min(start + max_size, text_len)
            chunk = text[start:end]

            # Try to break at a sentence boundary
            if end < text_len:
                last_period = chunk.rfind(". ")
                if last_period > max_size * 0.7:  # At least 70% of max_size
                    end = start + last_period + 2
                    chunk = text[start:end]

            stripped_chunk = chunk.strip()
            if stripped_chunk:
                chunks.append(stripped_chunk)

            # Ensure we always make progress
            new_start = end - overlap
            if new_start <= start:
                new_start = start + 1
            start = new_start

        return [c for c in chunks if len(c) > 50]  # Filter tiny chunks


def main():
    """Main ingestion pipeline"""
    import sys

    # Check for --clear flag
    clear_first = "--clear" in sys.argv or "-c" in sys.argv

    processor = DocumentProcessor()

    if clear_first:
        print("\n[CLEAR] Clearing existing data...")
        # Clear vector store
        processor.vector_store.clear_all()

        # Clear images from SQLite
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM images")
        cursor.execute("DELETE FROM chat_history")
        try:
            cursor.execute("DELETE FROM sessions")
        except:
            pass
        conn.commit()
        conn.close()

        # Clear extracted images folder
        import shutil
        if IMAGES_DIR.exists():
            for f in IMAGES_DIR.glob("*"):
                f.unlink()
        print("[OK] Cleared all existing data\n")

    processor.process_all_documents()


if __name__ == "__main__":
    main()

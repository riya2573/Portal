#!/usr/bin/env python3
"""
FastAPI Backend Server
Run: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import json
import re
import uuid
from datetime import datetime
from pathlib import Path

from config import FRONTEND_URL, DB_PATH, IMAGES_DIR, DOCUMENTS_DIR, get_available_topics, DEFAULT_TOPIC
from embeddings import get_embeddings_service
from vector_store import get_vector_store
from llm_service import get_llm_service
from image_extractor import get_image_extractor

# Initialize FastAPI app
app = FastAPI(title="Document Chatbot API", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class Message(BaseModel):
    text: str
    session_id: Optional[str] = None
    topics: Optional[List[str]] = None  # Topic filters (multi-select)


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict] = []
    images: List[dict] = []
    session_id: Optional[str] = None
    message: Optional[str] = None


class SessionCreate(BaseModel):
    title: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


class HealthResponse(BaseModel):
    status: str
    ollama: bool
    documents_indexed: int
    images_indexed: int


# Database initialization
def init_database():
    """Initialize database tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create chat_history table with session_id
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            user_message TEXT,
            assistant_response TEXT,
            source_documents TEXT,
            images TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    # Add session_id column if it doesn't exist (for migration)
    try:
        cursor.execute("ALTER TABLE chat_history ADD COLUMN session_id TEXT")
    except:
        pass

    # Add images column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE chat_history ADD COLUMN images TEXT")
    except:
        pass

    conn.commit()
    conn.close()


# Initialize services
def init_services():
    """Initialize all services on startup"""
    try:
        init_database()
        get_embeddings_service()
        get_vector_store()
        get_llm_service()
        get_image_extractor()
        return True
    except Exception as e:
        print(f"[ERROR] Error initializing services: {str(e)}")
        return False


@app.on_event("startup")
async def startup_event():
    """Initialize services on app startup"""
    print("\n" + "=" * 60)
    print("STARTING DOCUMENT CHATBOT API v2.0")
    print("=" * 60)
    init_services()
    print("[OK] API Ready\n")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    llm_service = get_llm_service()
    vector_store = get_vector_store()

    stats = vector_store.get_collection_stats()

    # Check Ollama connection
    ollama_running = llm_service._verify_connection()

    return HealthResponse(
        status="healthy",
        ollama=ollama_running,
        documents_indexed=stats["text_documents"],
        images_indexed=stats["images"],
    )


@app.get("/topics")
async def list_topics():
    """
    Get available topic filters.
    Topics are automatically derived from subfolder names in the documents directory.
    """
    try:
        topics = get_available_topics()
        return {
            "topics": topics,
            "total": len(topics),
            "default_topic": DEFAULT_TOPIC,
            "message": "Topics are auto-discovered from subfolders in data/documents/"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SESSION MANAGEMENT ENDPOINTS
# =============================================================================

@app.post("/sessions")
async def create_session(session: SessionCreate = None):
    """Create a new chat session"""
    try:
        session_id = str(uuid.uuid4())
        title = session.title if session and session.title else "New Chat"

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (id, title) VALUES (?, ?)",
            (session_id, title)
        )
        conn.commit()
        conn.close()

        return {
            "id": session_id,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "message_count": 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions")
async def list_sessions(limit: int = 50):
    """List all sessions with message counts"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id, s.title, s.created_at, s.updated_at,
                   COUNT(ch.id) as message_count
            FROM sessions s
            LEFT JOIN chat_history ch ON s.id = ch.session_id
            GROUP BY s.id
            ORDER BY s.updated_at DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        sessions = [
            {
                "id": row[0],
                "title": row[1],
                "created_at": row[2],
                "updated_at": row[3],
                "message_count": row[4]
            }
            for row in rows
        ]

        return {"sessions": sessions, "total": len(sessions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get a session with all its messages"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get session info
        cursor.execute(
            "SELECT id, title, created_at, updated_at FROM sessions WHERE id = ?",
            (session_id,)
        )
        session_row = cursor.fetchone()

        if not session_row:
            conn.close()
            raise HTTPException(status_code=404, detail="Session not found")

        # Get messages for this session
        cursor.execute("""
            SELECT id, user_message, assistant_response, source_documents, images, created_at
            FROM chat_history
            WHERE session_id = ?
            ORDER BY id ASC
        """, (session_id,))

        message_rows = cursor.fetchall()
        conn.close()

        messages = []
        for row in message_rows:
            messages.append({
                "id": row[0],
                "user": row[1],
                "assistant": row[2],
                "sources": json.loads(row[3]) if row[3] else [],
                "images": json.loads(row[4]) if row[4] else [],
                "timestamp": row[5]
            })

        return {
            "id": session_row[0],
            "title": session_row[1],
            "created_at": session_row[2],
            "updated_at": session_row[3],
            "messages": messages
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/sessions/{session_id}")
async def update_session(session_id: str, session: SessionCreate):
    """Update session title"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
            (session.title, datetime.now().isoformat(), session_id)
        )
        conn.commit()
        updated = cursor.rowcount
        conn.close()

        if updated == 0:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"message": "Session updated", "id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and all its messages"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Delete messages first
        cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
        # Delete session
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        deleted = cursor.rowcount
        conn.close()

        if deleted == 0:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"message": "Session deleted", "id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# CHAT ENDPOINTS
# =============================================================================

@app.post("/chat", response_model=ChatResponse)
async def chat(message: Message):
    """
    Main chat endpoint
    - For image-only requests: Returns only images, no text answer
    - For questions: Returns text answer with relevant images
    - Supports topic filtering via message.topics
    """
    user_query = message.text.strip()
    session_id = message.session_id
    topics = message.topics  # Topic filters (can be None or list)

    if not user_query:
        raise HTTPException(status_code=400, detail="Empty message")

    try:
        # Initialize services
        vector_store = get_vector_store()
        llm_service = get_llm_service()
        image_extractor = get_image_extractor()

        response_images = []
        response_sources = []
        answer = ""

        # Log topic filter if used
        if topics:
            print(f"  [FILTER] Topic filter active: {topics}")

        # Detect intent: image-only request or question
        is_image_request = _is_image_only_request(user_query)

        if is_image_request:
            # IMAGE-ONLY MODE: Skip LLM, just find images
            print(f"  [INTENT] Image-only request detected: '{user_query}'")

            # Search for relevant context to help find images (with topic filter)
            text_chunks, text_metadata = vector_store.search_text(user_query, topics=topics)

            stop_words = {'what', 'is', 'the', 'a', 'an', 'how', 'does', 'show', 'me', 'explain', 'about', 'and', 'or', 'of', 'in', 'to', 'for', 'display', 'image', 'picture', 'diagram', 'figure'}
            query_words = re.findall(r'\b[a-zA-Z]{3,}\b', user_query.lower())
            search_terms = [w for w in query_words if w not in stop_words]

            if text_metadata:
                doc_name = text_metadata[0].get('document_name', '')
                page_numbers = []
                for chunk in text_chunks[:5]:
                    page_matches = re.findall(r'\[Page\s*(\d+)\]', chunk)
                    for match in page_matches:
                        page_numbers.append(int(match))
                    slide_matches = re.findall(r'\[Slide\s*(\d+)\]', chunk)
                    for match in slide_matches:
                        page_numbers.append(int(match))
                page_numbers = list(set([p for p in page_numbers if p > 0]))[:15]

                combined_text = ' '.join(text_chunks[:5])

                relevant_images = image_extractor.find_relevant_images(
                    doc_name, page_numbers, search_terms, text_content=combined_text, max_images=3, query=user_query
                )
                if relevant_images:
                    response_images = [{
                        "image_id": img["id"],
                        "document_name": img["document_name"],
                        "page_number": img["page_number"],
                        "figure_caption": img.get("figure_caption", "")
                    } for img in relevant_images]
                    # No text answer for image-only requests
                    answer = ""
                else:
                    answer = "I couldn't find any relevant images for your request."
            else:
                answer = "I couldn't find any relevant images for your request."

        else:
            # QUESTION MODE: Generate text answer + find images
            print(f"  [INTENT] Question detected: '{user_query}'")

            # Step 1: Search for text content (with topic filter)
            text_chunks, text_metadata = vector_store.search_text(user_query, topics=topics)

            if text_chunks:
                # Prepare context from retrieved documents
                context = _format_context(text_chunks, text_metadata)

                # Extract page numbers and add to source metadata
                response_sources = _enrich_sources_with_pages(text_chunks, text_metadata)

                # Generate answer
                answer = llm_service.generate_answer(context, user_query)

                # Step 2: Find relevant images - try to find up to 3
                if text_metadata:
                    doc_name = text_metadata[0].get('document_name', '')
                    stop_words = {'what', 'is', 'the', 'a', 'an', 'how', 'does', 'show', 'me', 'explain', 'about', 'and', 'or', 'of', 'in', 'to', 'for'}
                    query_words = re.findall(r'\b[a-zA-Z]{3,}\b', user_query.lower())
                    search_terms = [w for w in query_words if w not in stop_words]

                    page_numbers = []
                    for chunk in text_chunks[:5]:
                        page_matches = re.findall(r'\[Page\s*(\d+)\]', chunk)
                        for match in page_matches:
                            page_numbers.append(int(match))
                        slide_matches = re.findall(r'\[Slide\s*(\d+)\]', chunk)
                        for match in slide_matches:
                            page_numbers.append(int(match))

                    page_numbers = list(set([p for p in page_numbers if p > 0]))[:15]

                    combined_text = ' '.join(text_chunks[:5])

                    relevant_images = image_extractor.find_relevant_images(
                        doc_name, page_numbers, search_terms, text_content=combined_text, max_images=3, query=user_query
                    )
                    if relevant_images:
                        response_images = [{
                            "image_id": img["id"],
                            "document_name": img["document_name"],
                            "page_number": img["page_number"]
                        } for img in relevant_images]
            else:
                answer = "I couldn't find any relevant information in the documents to answer your question."

        # Step 3: Save to chat history
        _save_chat_history(user_query, answer, response_sources, response_images, session_id)

        # Update session title if it's the first message
        if session_id:
            _update_session_title_if_needed(session_id, user_query)

        return ChatResponse(
            answer=answer,
            sources=response_sources,
            images=response_images,
            session_id=session_id
        )

    except Exception as e:
        print(f"[ERROR] Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@app.post("/chat/stream")
async def chat_stream(message: Message):
    """
    Streaming chat endpoint - returns tokens as Server-Sent Events
    - For image-only requests: Returns only images, no text streaming
    - For questions: Streams text answer with relevant images
    - Supports topic filtering via message.topics
    """
    user_query = message.text.strip()
    session_id = message.session_id
    topics = message.topics  # Topic filters (can be None or list)

    if not user_query:
        raise HTTPException(status_code=400, detail="Empty message")

    # Detect intent outside the generator so it's available
    is_image_request = _is_image_only_request(user_query)

    # Log topic filter if used
    if topics:
        print(f"  [FILTER] Topic filter active (stream): {topics}")

    async def generate():
        response_images = []
        response_sources = []
        full_answer = ""

        try:
            vector_store = get_vector_store()
            llm_service = get_llm_service()
            image_extractor = get_image_extractor()

            # Search for text content with topic filter (needed for both modes)
            text_chunks, text_metadata = vector_store.search_text(user_query, topics=topics)

            if is_image_request:
                # IMAGE-ONLY MODE: Skip LLM streaming, just find images
                print(f"  [INTENT] Image-only request (stream): '{user_query}'")

                stop_words = {'what', 'is', 'the', 'a', 'an', 'how', 'does', 'show', 'me', 'explain', 'about', 'and', 'or', 'of', 'in', 'to', 'for', 'display', 'image', 'picture', 'diagram', 'figure'}
                query_words = re.findall(r'\b[a-zA-Z]{3,}\b', user_query.lower())
                search_terms = [w for w in query_words if w not in stop_words]

                if text_metadata:
                    doc_name = text_metadata[0].get('document_name', '')
                    page_numbers = []
                    for chunk in text_chunks[:5]:
                        page_matches = re.findall(r'\[Page\s*(\d+)\]', chunk)
                        for match in page_matches:
                            page_numbers.append(int(match))
                        slide_matches = re.findall(r'\[Slide\s*(\d+)\]', chunk)
                        for match in slide_matches:
                            page_numbers.append(int(match))
                    page_numbers = list(set([p for p in page_numbers if p > 0]))[:15]

                    combined_text = ' '.join(text_chunks[:5])

                    relevant_images = image_extractor.find_relevant_images(
                        doc_name, page_numbers, search_terms, text_content=combined_text, max_images=3, query=user_query
                    )
                    if relevant_images:
                        response_images = [{
                            "image_id": img["id"],
                            "document_name": img["document_name"],
                            "page_number": img["page_number"],
                            "figure_caption": img.get("figure_caption", "")
                        } for img in relevant_images]
                        # Send images immediately (no text answer)
                        yield f"data: {json.dumps({'type': 'images', 'images': response_images})}\n\n"
                    else:
                        full_answer = "I couldn't find any relevant images for your request."
                        yield f"data: {json.dumps({'type': 'token', 'token': full_answer})}\n\n"
                else:
                    full_answer = "I couldn't find any relevant images for your request."
                    yield f"data: {json.dumps({'type': 'token', 'token': full_answer})}\n\n"

            else:
                # QUESTION MODE: Stream text answer + find images
                print(f"  [INTENT] Question (stream): '{user_query}'")

                if text_chunks:
                    context = _format_context(text_chunks, text_metadata)
                    response_sources = _enrich_sources_with_pages(text_chunks, text_metadata)

                    # Send sources first
                    yield f"data: {json.dumps({'type': 'sources', 'sources': response_sources})}\n\n"

                    # Stream the answer
                    try:
                        for token in llm_service.generate_answer_stream(context, user_query):
                            full_answer += token
                            yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
                    except Exception as stream_error:
                        error_msg = f"Error during generation: {str(stream_error)}"
                        full_answer += error_msg
                        yield f"data: {json.dumps({'type': 'token', 'token': error_msg})}\n\n"

                    # Find images - try to find up to 3
                    if text_metadata:
                        try:
                            doc_name = text_metadata[0].get('document_name', '')
                            stop_words = {'what', 'is', 'the', 'a', 'an', 'how', 'does', 'show', 'me', 'explain', 'about', 'and', 'or', 'of', 'in', 'to', 'for'}
                            query_words = re.findall(r'\b[a-zA-Z]{3,}\b', user_query.lower())
                            search_terms = [w for w in query_words if w not in stop_words]

                            page_numbers = []
                            for chunk in text_chunks[:5]:
                                page_matches = re.findall(r'\[Page\s*(\d+)\]', chunk)
                                for match in page_matches:
                                    page_numbers.append(int(match))
                                slide_matches = re.findall(r'\[Slide\s*(\d+)\]', chunk)
                                for match in slide_matches:
                                    page_numbers.append(int(match))

                            page_numbers = list(set([p for p in page_numbers if p > 0]))[:15]

                            combined_text = ' '.join(text_chunks[:5])

                            relevant_images = image_extractor.find_relevant_images(
                                doc_name, page_numbers, search_terms, text_content=combined_text, max_images=3, query=user_query
                            )
                            if relevant_images:
                                response_images = [{
                                    "image_id": img["id"],
                                    "document_name": img["document_name"],
                                    "page_number": img["page_number"]
                                } for img in relevant_images]
                        except Exception as img_error:
                            print(f"[WARN] Error finding images: {img_error}")
                else:
                    full_answer = "I couldn't find any relevant information in the documents to answer your question."
                    yield f"data: {json.dumps({'type': 'token', 'token': full_answer})}\n\n"

                # Send images at the end for question mode
                if response_images:
                    yield f"data: {json.dumps({'type': 'images', 'images': response_images})}\n\n"

        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Stream error: {error_msg}")
            yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"

        # ALWAYS send done signal, even after errors
        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"

        # Save to history (do this after sending done to not block the response)
        try:
            if full_answer:
                _save_chat_history(user_query, full_answer, response_sources, response_images, session_id)
            if session_id:
                _update_session_title_if_needed(session_id, user_query)
        except Exception as save_error:
            print(f"[ERROR] Error saving chat history: {save_error}")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# =============================================================================
# DOCUMENT SERVING ENDPOINT
# =============================================================================

@app.get("/documents/{filename:path}")
async def get_document(filename: str):
    """Serve a document file (PDF, DOCX, PPTX) - optimized with caching"""
    try:
        # Security: prevent path traversal
        safe_filename = Path(filename).name
        doc_path = None

        # First check root documents directory
        root_path = DOCUMENTS_DIR / safe_filename
        if root_path.exists():
            doc_path = root_path
        else:
            # Search in topic subfolders
            for topic_dir in DOCUMENTS_DIR.iterdir():
                if topic_dir.is_dir():
                    subfolder_path = topic_dir / safe_filename
                    if subfolder_path.exists():
                        doc_path = subfolder_path
                        break

        if not doc_path or not doc_path.exists():
            raise HTTPException(status_code=404, detail=f"Document not found: {filename}")

        # Get file stats for caching
        file_stat = doc_path.stat()
        file_size = file_stat.st_size
        last_modified = datetime.fromtimestamp(file_stat.st_mtime).strftime('%a, %d %b %Y %H:%M:%S GMT')

        # Detect media type
        ext = doc_path.suffix.lower()
        media_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.txt': 'text/plain',
        }
        media_type = media_types.get(ext, 'application/octet-stream')

        return FileResponse(
            doc_path,
            media_type=media_type,
            filename=filename,
            headers={
                "Content-Disposition": f"inline; filename=\"{filename}\"",
                "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
                "Last-Modified": last_modified,
                "Accept-Ranges": "bytes",  # Enable partial content for large files
                "Content-Length": str(file_size),
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# IMAGE ENDPOINTS
# =============================================================================

@app.get("/images/{image_id}")
async def get_image(image_id: int):
    """Get an image by ID - optimized with caching"""
    try:
        image_extractor = get_image_extractor()
        image_data = image_extractor.get_image_by_id(image_id)

        if not image_data:
            raise HTTPException(status_code=404, detail=f"Image {image_id} not found in database")

        image_path = Path(image_data["image_path"])
        if not image_path.exists():
            raise HTTPException(status_code=404, detail=f"Image file not found: {image_path}")

        ext = image_path.suffix.lower()
        media_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp',
        }
        media_type = media_types.get(ext, 'image/png')

        return FileResponse(
            image_path,
            media_type=media_type,
            headers={
                "X-Document": image_data.get("document_name", "Unknown"),
                "X-Page": str(image_data.get("page_number", 0)),
                "Cache-Control": "public, max-age=604800",  # Cache images for 7 days
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Image endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/images")
async def list_images():
    """List all available images"""
    try:
        image_extractor = get_image_extractor()
        images = image_extractor.get_all_images()
        return {"images": images, "total": len(images)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# LEGACY CHAT HISTORY ENDPOINTS (for backward compatibility)
# =============================================================================

@app.get("/chat-history")
async def get_chat_history(limit: int = 50):
    """Get chat history (legacy - returns flat list)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, user_message, assistant_response, source_documents, images, created_at, session_id
            FROM chat_history
            ORDER BY id DESC
            LIMIT ?
        """,
            (limit,),
        )

        rows = cursor.fetchall()
        conn.close()

        history = [
            {
                "id": row[0],
                "user": row[1],
                "assistant": row[2],
                "sources": json.loads(row[3]) if row[3] else [],
                "images": json.loads(row[4]) if row[4] else [],
                "timestamp": row[5],
                "session_id": row[6],
            }
            for row in rows
        ]

        return {"history": history, "total": len(history)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/chat-history/{chat_id}")
async def delete_chat_entry(chat_id: int):
    """Delete a specific chat entry"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE id = ?", (chat_id,))
        conn.commit()
        deleted = cursor.rowcount
        conn.close()

        if deleted == 0:
            raise HTTPException(status_code=404, detail="Chat not found")

        return {"message": "Chat deleted", "id": chat_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/chat-history")
async def clear_chat_history():
    """Clear all chat history and sessions"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history")
        cursor.execute("DELETE FROM sessions")
        conn.commit()
        conn.close()

        return {"message": "Chat history cleared"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_statistics():
    """Get system statistics"""
    try:
        vector_store = get_vector_store()
        stats = vector_store.get_collection_stats()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chat_history")
        chat_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM sessions")
        session_count = cursor.fetchone()[0]
        conn.close()

        return {
            "indexed_documents": stats["text_documents"],
            "indexed_images": stats["images"],
            "chat_messages": chat_count,
            "sessions": session_count,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# HELPER METHODS
# =============================================================================

def _is_image_only_request(query: str) -> bool:
    """
    Detect if the user is asking specifically for an image/diagram/figure.

    Returns True for queries like:
    - "show me the valve diagram"
    - "display the pump figure"
    - "image of ball valve"
    - "picture of the assembly"
    - "diagram for gate valve"

    Returns False for questions like:
    - "what is a ball valve?"
    - "how does a pump work?"
    - "explain the valve operation"
    """
    query_lower = query.lower().strip()

    # Patterns that indicate image-only request
    image_request_patterns = [
        r'^show\s+(me\s+)?(the\s+|a\s+)?',
        r'^display\s+(the\s+|a\s+)?',
        r'^(get|find|fetch)\s+(me\s+)?(the\s+|a\s+)?.*?(image|picture|diagram|figure|photo|illustration)',
        r'^image\s+of\b',
        r'^picture\s+of\b',
        r'^diagram\s+(of|for)\b',
        r'^figure\s+(of|for)\b',
        r'^(can\s+you\s+)?show\b',
        r'\b(show|display|give)\s+(me\s+)?(the\s+|a\s+)?(image|picture|diagram|figure|illustration)\b',
    ]

    # Keywords that strongly indicate image request (at start or as main intent)
    image_keywords_start = ['show', 'display', 'image', 'picture', 'diagram', 'figure', 'illustration', 'photo']

    # Check if query starts with image-related word
    first_word = query_lower.split()[0] if query_lower.split() else ""
    if first_word in image_keywords_start:
        # But check it's not a question about images
        if not any(q in query_lower for q in ['what is', 'how to', 'why', 'explain', 'describe', 'tell me about']):
            return True

    # Check patterns
    for pattern in image_request_patterns:
        if re.search(pattern, query_lower):
            # Make sure it's not also asking a question
            if not any(q in query_lower for q in ['?', 'what is', 'how does', 'why', 'explain', 'describe']):
                return True

    # Check for "X diagram" or "X image" pattern (e.g., "valve diagram", "pump image")
    if re.search(r'\b(diagram|image|picture|figure|illustration)\s*$', query_lower):
        return True

    # Check for "diagram of X" or "image of X" anywhere
    if re.search(r'\b(diagram|image|picture|figure|illustration)\s+(of|for)\s+', query_lower):
        return True

    return False


def _format_context(texts: List[str], metadatas: List[dict]) -> str:
    """Format retrieved documents into context - clean format without citation markers"""
    context_parts = []

    for i, (text, metadata) in enumerate(zip(texts, metadatas), 1):
        # Clean format that doesn't encourage the LLM to add inline citations
        # Remove page markers from text for cleaner context
        clean_text = re.sub(r'\[Page\s*\d+\]\s*', '', text)
        clean_text = re.sub(r'\[Slide\s*\d+\]\s*', '', clean_text)
        context_parts.append(f"--- Document {i} ---\n{clean_text}")

    return "\n\n".join(context_parts)


def _enrich_sources_with_pages(texts: List[str], metadatas: List[dict]) -> List[dict]:
    """Extract page numbers from metadata with deduplication - optimized version"""
    seen_sources = {}  # Key: (document_name, page_number), Value: source dict

    for text, metadata in zip(texts, metadatas):
        source = dict(metadata)  # Copy metadata
        doc_name = source.get('document_name', 'Unknown')

        # Use page_number from metadata (now accurately tracked during ingestion)
        page_number = source.get('page_number', 0)

        # If still no page number, try to extract from text as last resort
        if not page_number or page_number == 0:
            # Check for page markers in text
            page_matches = re.findall(r'\[Page\s*(\d+)\]', text)
            if page_matches:
                page_number = int(page_matches[0])
            else:
                slide_matches = re.findall(r'\[Slide\s*(\d+)\]', text)
                if slide_matches:
                    page_number = int(slide_matches[0])
                else:
                    # Extract chunk_index and estimate page (rough fallback)
                    chunk_idx = source.get('chunk_index', 0)
                    # Estimate: ~2 chunks per page on average
                    page_number = max(1, (chunk_idx // 2) + 1)

        source['page_number'] = page_number

        # Determine label based on file type
        file_type = source.get('file_type', '')
        if file_type == '.pptx':
            source['page_label'] = f"Slide {page_number}"
        else:
            source['page_label'] = f"Page {page_number}"

        # Deduplicate: Keep only one source per document+page combination
        key = (doc_name, page_number)
        if key not in seen_sources:
            seen_sources[key] = source

    return list(seen_sources.values())


def _save_chat_history(user_msg: str, assistant_msg: str, sources: List[dict],
                       images: List[dict] = None, session_id: str = None):
    """Save chat to database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        sources_json = json.dumps(sources)
        images_json = json.dumps(images or [])

        cursor.execute(
            """
            INSERT INTO chat_history (session_id, user_message, assistant_response, source_documents, images)
            VALUES (?, ?, ?, ?, ?)
        """,
            (session_id, user_msg, assistant_msg, sources_json, images_json),
        )

        # Update session timestamp
        if session_id:
            cursor.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), session_id)
            )

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ERROR] Error saving chat history: {str(e)}")


def _update_session_title_if_needed(session_id: str, first_message: str):
    """Update session title based on first message if it's still 'New Chat'"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if this is the first message and title is still default
        cursor.execute(
            "SELECT title FROM sessions WHERE id = ?",
            (session_id,)
        )
        row = cursor.fetchone()

        if row and row[0] == "New Chat":
            # Generate title from first message (truncate to 50 chars)
            title = first_message[:50] + ("..." if len(first_message) > 50 else "")
            cursor.execute(
                "UPDATE sessions SET title = ? WHERE id = ?",
                (title, session_id)
            )
            conn.commit()

        conn.close()
    except Exception as e:
        print(f"[ERROR] Error updating session title: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

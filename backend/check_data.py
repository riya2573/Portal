#!/usr/bin/env python3
"""Check what data is actually indexed"""

import sqlite3
from config import DB_PATH, CHROMA_DB_DIR
from vector_store import get_vector_store

print("=" * 60)
print("DATA DIAGNOSTIC CHECK")
print("=" * 60)

# Check vector store
print("\n[1] VECTOR STORE (ChromaDB)")
try:
    vs = get_vector_store()
    stats = vs.get_collection_stats()
    print(f"    Text chunks indexed: {stats['text_documents']}")
    print(f"    Images indexed: {stats['images']}")

    if stats['text_documents'] > 0:
        # Try a sample search
        texts, metas = vs.search_text("valve", n_results=3)
        print(f"\n    Sample search for 'valve' returned {len(texts)} results:")
        for i, (t, m) in enumerate(zip(texts[:3], metas[:3])):
            print(f"    [{i+1}] {m.get('document_name', 'Unknown')} - {t[:100]}...")
    else:
        print("\n    [WARNING] No text documents indexed!")
        print("    Run: python ingest.py --clear")
except Exception as e:
    print(f"    [ERROR] {e}")

# Check SQLite for images
print("\n[2] IMAGES DATABASE (SQLite)")
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM images")
    img_count = cursor.fetchone()[0]
    print(f"    Images in database: {img_count}")

    if img_count > 0:
        cursor.execute("SELECT id, document_name, page_number FROM images LIMIT 5")
        rows = cursor.fetchall()
        print("    Sample images:")
        for row in rows:
            print(f"      ID {row[0]}: {row[1]} page {row[2]}")
    else:
        print("    [WARNING] No images extracted!")

    conn.close()
except Exception as e:
    print(f"    [ERROR] {e}")

# Check chat history
print("\n[3] SESSIONS & CHAT HISTORY")
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM sessions")
        sess_count = cursor.fetchone()[0]
        print(f"    Sessions: {sess_count}")
    except:
        print("    Sessions table not created yet")

    cursor.execute("SELECT COUNT(*) FROM chat_history")
    chat_count = cursor.fetchone()[0]
    print(f"    Chat messages: {chat_count}")

    conn.close()
except Exception as e:
    print(f"    [ERROR] {e}")

print("\n" + "=" * 60)
print("If text chunks = 0, run: python ingest.py --clear")
print("=" * 60)

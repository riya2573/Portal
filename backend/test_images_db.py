#!/usr/bin/env python3
"""Check what image contexts are stored in the database"""

import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 70)
print("IMAGE DATABASE CONTENTS")
print("=" * 70)

cursor.execute("SELECT COUNT(*) FROM images")
total = cursor.fetchone()[0]
print(f"\nTotal images: {total}")

# Show sample images with their context
cursor.execute("""
    SELECT id, page_number, context_text
    FROM images
    ORDER BY page_number
    LIMIT 20
""")

rows = cursor.fetchall()
print(f"\nSample images with context:\n")

for row in rows:
    img_id, page, context = row
    context_preview = (context[:150] + "...") if context and len(context) > 150 else context
    print(f"ID {img_id} | Page {page}")
    print(f"  Context: {context_preview}")
    print()

conn.close()

# Test search
print("=" * 70)
print("TESTING SEARCH")
print("=" * 70)

from image_extractor import get_image_extractor

extractor = get_image_extractor()

# Test searches
test_queries = ["plug valve", "globe valve", "butterfly valve", "check valve", "gate valve"]

for query in test_queries:
    terms = query.split()
    result = extractor.find_image_by_context(terms, "Valve-Selection-Handbook-Engineering-Fundamentals-for-Selecting.pdf")
    if result:
        print(f"'{query}' -> Found: Page {result['page_number']}")
    else:
        print(f"'{query}' -> No match")

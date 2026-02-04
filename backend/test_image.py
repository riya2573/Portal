#!/usr/bin/env python3
"""Test image retrieval"""

from image_extractor import get_image_extractor
from vector_store import get_vector_store
import re

print("=" * 60)
print("IMAGE RETRIEVAL TEST")
print("=" * 60)

# Initialize
image_extractor = get_image_extractor()
vector_store = get_vector_store()

# Test query
query = "fluid tightness"
print(f"\nQuery: '{query}'")

# Search for text
text_chunks, text_metadata = vector_store.search_text(query)
print(f"\nText chunks found: {len(text_chunks)}")

if text_chunks:
    # Get document name
    doc_name = text_metadata[0].get('document_name', '')
    print(f"Document: {doc_name}")

    # Extract search terms
    stop_words = {'what', 'is', 'the', 'a', 'an', 'how', 'does', 'show', 'me', 'explain', 'about', 'and', 'or', 'of', 'in', 'to', 'for'}
    query_words = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
    search_terms = [w for w in query_words if w not in stop_words]
    print(f"Search terms: {search_terms}")

    # Extract page numbers
    page_numbers = []
    for chunk in text_chunks[:5]:
        page_matches = re.findall(r'\[Page\s*(\d+)\]', chunk)
        for match in page_matches:
            page_numbers.append(int(match))
    page_numbers = list(set([p for p in page_numbers if p > 0]))[:15]
    print(f"Page numbers from chunks: {page_numbers}")

    # Try to find image
    print("\n--- Testing find_relevant_image ---")
    relevant_image = image_extractor.find_relevant_image(doc_name, page_numbers, search_terms)

    if relevant_image:
        print(f"SUCCESS! Found image:")
        print(f"  ID: {relevant_image['id']}")
        print(f"  Document: {relevant_image['document_name']}")
        print(f"  Page: {relevant_image['page_number']}")
        print(f"  Path: {relevant_image.get('image_path', 'N/A')}")
    else:
        print("FAILED: No image found")

        # Debug: try each method separately
        print("\n--- Debug: Testing individual methods ---")

        # Test context search
        print(f"\n1. find_image_by_context({search_terms}, {doc_name}):")
        img = image_extractor.find_image_by_context(search_terms, doc_name)
        print(f"   Result: {img}")

        # Test page search
        print(f"\n2. get_images_for_pages({doc_name}, {page_numbers}):")
        imgs = image_extractor.get_images_for_pages(doc_name, page_numbers)
        print(f"   Result: {imgs}")

        # Test any image fallback
        print(f"\n3. get_any_image_from_document({doc_name}):")
        img = image_extractor.get_any_image_from_document(doc_name)
        print(f"   Result: {img}")

else:
    print("No text chunks found!")

print("\n" + "=" * 60)

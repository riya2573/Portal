import os
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
import hashlib
from config import IMAGES_DIR, DB_PATH

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("[WARN] PyMuPDF not installed. Run: pip install PyMuPDF")

try:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False
    print("[WARN] python-pptx not installed. Run: pip install python-pptx")


class ImageExtractor:
    def __init__(self):
        self.images_dir = IMAGES_DIR
        self._init_image_db()

    def _init_image_db(self):
        """Initialize SQLite database for image metadata"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_hash TEXT UNIQUE,
                image_path TEXT,
                document_name TEXT,
                page_number INTEGER,
                context_text TEXT,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Add context_text column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE images ADD COLUMN context_text TEXT")
        except:
            pass  # Column already exists
        conn.commit()
        conn.close()

    def extract_images_from_pdf(self, pdf_path: str, doc_name: str) -> List[Dict]:
        """
        Extract actual figures/diagrams from PDF with captions

        Args:
            pdf_path: Path to PDF file
            doc_name: Name of document for metadata

        Returns:
            List of extracted image info dicts
        """
        if not PYMUPDF_AVAILABLE:
            print("  [WARN] PyMuPDF not available, skipping image extraction")
            return []

        extracted_images = []

        try:
            pdf = fitz.open(pdf_path)
            total_pages = len(pdf)
            print(f"  [IMG] Extracting figures from {total_pages} pages...")

            image_count = 0

            for page_num in range(total_pages):
                try:
                    page = pdf[page_num]

                    # Get FULL page text to find figure captions
                    page_text = page.get_text()

                    # Extract figure captions from the page (e.g., "Figure 3-1. Plug Valve...")
                    import re
                    figure_captions = re.findall(
                        r'(Figure\s+\d+[-.]?\d*[.:]\s*[^\n]{10,100})',
                        page_text,
                        re.IGNORECASE
                    )
                    caption_text = ' | '.join(figure_captions) if figure_captions else page_text[:500]

                    # Get all images on this page
                    image_list = page.get_images(full=True)

                    for img_index, img_info in enumerate(image_list):
                        try:
                            xref = img_info[0]

                            # Extract the image
                            base_image = pdf.extract_image(xref)
                            if not base_image:
                                continue

                            image_bytes = base_image["image"]
                            image_ext = base_image.get("ext", "png")
                            width = base_image.get("width", 0)
                            height = base_image.get("height", 0)

                            # Filter: Skip tiny images (icons, bullets, decorations)
                            if width < 150 or height < 150:
                                continue

                            # Filter: Skip very narrow/tall images (likely borders or lines)
                            aspect_ratio = width / height if height > 0 else 0
                            if aspect_ratio > 5 or aspect_ratio < 0.2:
                                continue

                            # Filter: Skip very large images (likely backgrounds)
                            if width > 2500 or height > 2500:
                                continue

                            # Filter: Skip very small file sizes (likely simple graphics)
                            if len(image_bytes) < 5000:  # Less than 5KB
                                continue

                            # Generate hash for deduplication
                            image_hash = hashlib.md5(image_bytes).hexdigest()

                            # Check if already exists
                            conn = sqlite3.connect(DB_PATH)
                            cursor = conn.cursor()
                            cursor.execute("SELECT id FROM images WHERE image_hash = ?", (image_hash,))
                            if cursor.fetchone():
                                conn.close()
                                continue
                            conn.close()

                            # Save image
                            image_filename = f"{Path(pdf_path).stem}_p{page_num + 1}_fig{img_index}.{image_ext}"
                            image_path = self.images_dir / image_filename

                            with open(image_path, "wb") as f:
                                f.write(image_bytes)

                            # Store metadata with figure caption as context
                            image_id = self._store_image_metadata(
                                image_hash=image_hash,
                                image_path=str(image_path),
                                document_name=doc_name,
                                page_number=page_num + 1,
                                context_text=caption_text  # Use extracted captions
                            )

                            if image_id:
                                extracted_images.append({
                                    "id": image_id,
                                    "path": str(image_path),
                                    "page": page_num + 1
                                })
                                image_count += 1

                        except Exception as img_err:
                            continue

                except Exception as page_err:
                    continue

                if (page_num + 1) % 100 == 0:
                    print(f"  [OK] Processed {page_num + 1}/{total_pages} pages, found {image_count} figures...")

            pdf.close()
            print(f"  [OK] Extracted {len(extracted_images)} figures/diagrams")

        except Exception as e:
            print(f"  [ERROR] Error extracting images: {str(e)}")

        return extracted_images

    def extract_images_from_pptx(self, pptx_path: str, doc_name: str) -> List[Dict]:
        """
        Extract images from PowerPoint presentations

        Args:
            pptx_path: Path to PPTX file
            doc_name: Name of document for metadata

        Returns:
            List of extracted image info dicts
        """
        if not PPTX_AVAILABLE:
            print("  [WARN] python-pptx not available, skipping PPTX image extraction")
            return []

        extracted_images = []

        try:
            prs = Presentation(pptx_path)
            total_slides = len(prs.slides)
            print(f"  [IMG] Extracting images from {total_slides} slides...")

            image_count = 0

            for slide_num, slide in enumerate(prs.slides, 1):
                try:
                    # Get slide text for context (titles, text boxes)
                    slide_text_parts = []
                    for shape in slide.shapes:
                        if hasattr(shape, "text") and shape.text.strip():
                            slide_text_parts.append(shape.text.strip())
                    slide_context = " | ".join(slide_text_parts[:5]) if slide_text_parts else f"Slide {slide_num}"

                    # Extract images from shapes
                    for shape_idx, shape in enumerate(slide.shapes):
                        try:
                            # Check if shape is a picture
                            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                                image = shape.image
                                image_bytes = image.blob
                                image_ext = image.ext  # e.g., 'png', 'jpeg'

                                # Get image dimensions
                                width = shape.width.emu // 914400  # Convert EMU to inches approx
                                height = shape.height.emu // 914400

                                # Filter: Skip tiny images (icons, bullets)
                                if shape.width.emu < 500000 or shape.height.emu < 500000:  # ~0.5 inch
                                    continue

                                # Filter: Skip very small file sizes
                                if len(image_bytes) < 3000:  # Less than 3KB
                                    continue

                                # Generate hash for deduplication
                                image_hash = hashlib.md5(image_bytes).hexdigest()

                                # Check if already exists
                                conn = sqlite3.connect(DB_PATH)
                                cursor = conn.cursor()
                                cursor.execute("SELECT id FROM images WHERE image_hash = ?", (image_hash,))
                                if cursor.fetchone():
                                    conn.close()
                                    continue
                                conn.close()

                                # Save image
                                image_filename = f"{Path(pptx_path).stem}_slide{slide_num}_img{shape_idx}.{image_ext}"
                                image_path = self.images_dir / image_filename

                                with open(image_path, "wb") as f:
                                    f.write(image_bytes)

                                # Store metadata with slide context
                                image_id = self._store_image_metadata(
                                    image_hash=image_hash,
                                    image_path=str(image_path),
                                    document_name=doc_name,
                                    page_number=slide_num,  # Using slide number as page
                                    context_text=slide_context
                                )

                                if image_id:
                                    extracted_images.append({
                                        "id": image_id,
                                        "path": str(image_path),
                                        "page": slide_num
                                    })
                                    image_count += 1

                            # Also check for images in group shapes
                            elif shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                                for group_shape in shape.shapes:
                                    if hasattr(group_shape, 'shape_type') and group_shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                                        try:
                                            image = group_shape.image
                                            image_bytes = image.blob
                                            image_ext = image.ext

                                            if len(image_bytes) < 3000:
                                                continue

                                            image_hash = hashlib.md5(image_bytes).hexdigest()

                                            conn = sqlite3.connect(DB_PATH)
                                            cursor = conn.cursor()
                                            cursor.execute("SELECT id FROM images WHERE image_hash = ?", (image_hash,))
                                            if cursor.fetchone():
                                                conn.close()
                                                continue
                                            conn.close()

                                            image_filename = f"{Path(pptx_path).stem}_slide{slide_num}_grp{shape_idx}.{image_ext}"
                                            image_path = self.images_dir / image_filename

                                            with open(image_path, "wb") as f:
                                                f.write(image_bytes)

                                            image_id = self._store_image_metadata(
                                                image_hash=image_hash,
                                                image_path=str(image_path),
                                                document_name=doc_name,
                                                page_number=slide_num,
                                                context_text=slide_context
                                            )

                                            if image_id:
                                                extracted_images.append({
                                                    "id": image_id,
                                                    "path": str(image_path),
                                                    "page": slide_num
                                                })
                                                image_count += 1
                                        except Exception:
                                            continue

                        except Exception as shape_err:
                            continue

                except Exception as slide_err:
                    continue

                if slide_num % 50 == 0:
                    print(f"  [OK] Processed {slide_num}/{total_slides} slides, found {image_count} images...")

            print(f"  [OK] Extracted {len(extracted_images)} images from PPTX")

        except Exception as e:
            print(f"  [ERROR] Error extracting PPTX images: {str(e)}")

        return extracted_images

    def _store_image_metadata(self, image_hash: str, image_path: str,
                              document_name: str, page_number: int,
                              context_text: str = "") -> Optional[int]:
        """Store image metadata in SQLite"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO images (image_hash, image_path, document_name, page_number, context_text)
                VALUES (?, ?, ?, ?, ?)
            """, (image_hash, image_path, document_name, page_number, context_text))
            conn.commit()
            image_id = cursor.lastrowid
            conn.close()
            return image_id
        except Exception as e:
            print(f"  [ERROR] Error storing image metadata: {str(e)}")
            return None

    def get_image_by_id(self, image_id: int) -> Optional[Dict]:
        """Retrieve image metadata by ID"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, image_path, document_name, page_number
            FROM images WHERE id = ?
        """, (image_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "id": row[0],
                "image_path": row[1],
                "document_name": row[2],
                "page_number": row[3]
            }
        return None

    def find_image_by_context(self, search_terms: List[str], document_name: str = None) -> Optional[Dict]:
        """
        Find an image whose caption/context BEST matches the search terms
        Returns the image with the most matching terms (ranked)
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get all images with their context
        if document_name:
            cursor.execute("""
                SELECT id, image_path, document_name, page_number, context_text
                FROM images
                WHERE document_name = ?
            """, (document_name,))
        else:
            cursor.execute("""
                SELECT id, image_path, document_name, page_number, context_text
                FROM images
            """)

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return None

        # Score each image by how many search terms match its context
        best_match = None
        best_score = 0

        for row in rows:
            img_id, img_path, doc_name, page_num, context = row
            if not context:
                continue

            context_lower = context.lower()
            score = 0

            for term in search_terms:
                if len(term) > 2 and term.lower() in context_lower:
                    # Give more weight to longer term matches
                    score += len(term)

            if score > best_score:
                best_score = score
                best_match = {
                    "id": img_id,
                    "image_path": img_path,
                    "document_name": doc_name,
                    "page_number": page_num
                }

        return best_match

    def get_images_for_pages(self, document_name: str, page_numbers: List[int], limit: int = 3) -> List[Dict]:
        """Get images from specific pages of a document"""
        if not page_numbers:
            return []

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        placeholders = ",".join("?" * len(page_numbers))
        cursor.execute(f"""
            SELECT id, image_path, document_name, page_number
            FROM images
            WHERE document_name = ? AND page_number IN ({placeholders})
            ORDER BY page_number
            LIMIT ?
        """, [document_name] + page_numbers + [limit])

        rows = cursor.fetchall()
        conn.close()

        return [{
            "id": row[0],
            "image_path": row[1],
            "document_name": row[2],
            "page_number": row[3]
        } for row in rows]

    def find_relevant_image(self, document_name: str, page_numbers: List[int],
                           search_terms: List[str] = None,
                           text_content: str = None) -> Optional[Dict]:
        """Find ONE most relevant image based on figure references or context"""

        import re

        # Strategy 1: Find figure references in text (e.g., "Figure 3-1", "Fig. 5.2")
        if text_content:
            # Extract figure numbers mentioned in the text
            figure_refs = re.findall(
                r'(?:Figure|Fig\.?)\s*(\d+)[-.]?(\d+)?',
                text_content,
                re.IGNORECASE
            )

            if figure_refs:
                # Try to find images from pages that match figure numbers
                for fig_main, fig_sub in figure_refs[:5]:  # Check first 5 references
                    # Figure numbers often correspond to chapter.figure format
                    # Search for images whose context mentions this figure
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()

                    fig_pattern = f"Figure {fig_main}"
                    if fig_sub:
                        fig_pattern += f"[-.]{fig_sub}"

                    cursor.execute("""
                        SELECT id, image_path, document_name, page_number, context_text
                        FROM images
                        WHERE document_name = ?
                        AND LOWER(context_text) LIKE LOWER(?)
                        LIMIT 1
                    """, (document_name, f"%{fig_pattern}%"))

                    row = cursor.fetchone()
                    conn.close()

                    if row:
                        print(f"  [IMG] Found image by figure reference: {fig_pattern}")
                        return {
                            "id": row[0],
                            "image_path": row[1],
                            "document_name": row[2],
                            "page_number": row[3]
                        }

        # Strategy 2: Try to find by context/caption match
        if search_terms:
            image = self.find_image_by_context(search_terms, document_name)
            if image:
                print(f"  [IMG] Found image by context match: page {image['page_number']}")
                return image

        # Strategy 3: Try page-based matching
        if page_numbers:
            images = self.get_images_for_pages(document_name, page_numbers)
            if images:
                print(f"  [IMG] Found image by page match: page {images[0]['page_number']}")
                return images[0]

        print("  [IMG] No relevant image found for query")
        return None

    def find_relevant_images(self, document_name: str, page_numbers: List[int],
                             search_terms: List[str] = None,
                             text_content: str = None,
                             max_images: int = 3) -> List[Dict]:
        """Find multiple relevant images based on figure references, context, and pages"""
        import re

        found_images = []
        seen_ids = set()

        # Strategy 1: Find figure references in text (e.g., "Figure 3-1", "Fig. 5.2")
        if text_content:
            figure_refs = re.findall(
                r'(?:Figure|Fig\.?)\s*(\d+)[-.]?(\d+)?',
                text_content,
                re.IGNORECASE
            )

            if figure_refs:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                for fig_main, fig_sub in figure_refs[:10]:  # Check more references
                    if len(found_images) >= max_images:
                        break

                    fig_pattern = f"Figure {fig_main}"
                    if fig_sub:
                        fig_pattern += f"[-.]{fig_sub}"

                    cursor.execute("""
                        SELECT id, image_path, document_name, page_number
                        FROM images
                        WHERE document_name = ?
                        AND LOWER(context_text) LIKE LOWER(?)
                    """, (document_name, f"%{fig_pattern}%"))

                    for row in cursor.fetchall():
                        if row[0] not in seen_ids and len(found_images) < max_images:
                            seen_ids.add(row[0])
                            found_images.append({
                                "id": row[0],
                                "image_path": row[1],
                                "document_name": row[2],
                                "page_number": row[3]
                            })
                            print(f"  [IMG] Found image by figure reference: {fig_pattern}")

                conn.close()

        # Strategy 2: Find by context/caption match (get top matches)
        if search_terms and len(found_images) < max_images:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            if document_name:
                cursor.execute("""
                    SELECT id, image_path, document_name, page_number, context_text
                    FROM images WHERE document_name = ?
                """, (document_name,))
            else:
                cursor.execute("""
                    SELECT id, image_path, document_name, page_number, context_text
                    FROM images
                """)

            rows = cursor.fetchall()
            conn.close()

            # Score and sort images
            scored_images = []
            for row in rows:
                img_id, img_path, doc_name, page_num, context = row
                if img_id in seen_ids or not context:
                    continue

                context_lower = context.lower()
                score = sum(len(term) for term in search_terms if len(term) > 2 and term.lower() in context_lower)

                if score > 0:
                    scored_images.append((score, {
                        "id": img_id,
                        "image_path": img_path,
                        "document_name": doc_name,
                        "page_number": page_num
                    }))

            # Sort by score descending and add top matches
            scored_images.sort(key=lambda x: x[0], reverse=True)
            for score, img in scored_images:
                if len(found_images) >= max_images:
                    break
                if img["id"] not in seen_ids:
                    seen_ids.add(img["id"])
                    found_images.append(img)
                    print(f"  [IMG] Found image by context match: page {img['page_number']}")

        # Strategy 3: Get images from relevant pages
        if page_numbers and len(found_images) < max_images:
            remaining = max_images - len(found_images)
            page_images = self.get_images_for_pages(document_name, page_numbers, limit=remaining + 3)

            for img in page_images:
                if len(found_images) >= max_images:
                    break
                if img["id"] not in seen_ids:
                    seen_ids.add(img["id"])
                    found_images.append(img)
                    print(f"  [IMG] Found image by page match: page {img['page_number']}")

        if not found_images:
            print("  [IMG] No relevant images found for query")

        return found_images[:max_images]

    def get_any_image_from_document(self, document_name: str) -> Optional[Dict]:
        """Get any image from a document as a fallback"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, image_path, document_name, page_number
            FROM images
            WHERE document_name = ?
            ORDER BY page_number
            LIMIT 1
        """, (document_name,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "id": row[0],
                "image_path": row[1],
                "document_name": row[2],
                "page_number": row[3]
            }
        return None

    def get_all_images(self) -> List[Dict]:
        """Get all stored images"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, image_path, document_name, page_number
            FROM images
        """)
        rows = cursor.fetchall()
        conn.close()

        return [{
            "id": row[0],
            "image_path": row[1],
            "document_name": row[2],
            "page_number": row[3]
        } for row in rows]


# Global instance
image_extractor = None


def get_image_extractor() -> ImageExtractor:
    """Get or create image extractor singleton"""
    global image_extractor
    if image_extractor is None:
        image_extractor = ImageExtractor()
    return image_extractor

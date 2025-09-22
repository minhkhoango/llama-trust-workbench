# src/workbench/coordinate_mapper.py
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Optional, Dict, Any, cast
from thefuzz import fuzz  # type: ignore[import-untyped]

from src.workbench.types import Block, MappedElement, Bbox


def get_pdf_text_blocks(pdf_path: Path) -> List[List[Block]]:
    """
    Extracts all text blocks with coordinate data from each page of a PDF.
    Returns a list of lists, where each inner list corresponds to a page.
    """
    doc = fitz.open(pdf_path)
    all_pages_blocks: List[List[Block]] = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        # Using 'dict' gives us detailed info including bounding boxes
        page_dict: Dict[str, Any] = cast(Dict[str, Any], page.get_text("dict"))  # type: ignore[misc]
        page_blocks_raw: List[Dict[str, Any]] = page_dict.get("blocks", [])

        # Convert to properly typed blocks and add page number
        page_blocks: List[Block] = []
        for block_raw in page_blocks_raw:
            if "lines" in block_raw:  # Only process text blocks
                block: Block = cast(Block, block_raw)
                block["page_num"] = page_num
                page_blocks.append(block)

        all_pages_blocks.append(page_blocks)

    doc.close()
    return all_pages_blocks


def find_best_match(
    text_chunk: str, page_blocks: List[Block]
) -> Optional[Block]:
    """
    Finds the best matching PDF text block for a given text chunk using fuzzy string matching.
    """
    best_score = 0
    best_block: Optional[Block] = None

    # Clean the input chunk for better matching
    clean_chunk = " ".join(text_chunk.strip().split())
    if not clean_chunk:
        return None

    for block in page_blocks:
        if "lines" not in block:
            continue

        block_text = ""
        for line in block["lines"]:
            for span in line["spans"]:
                block_text += span["text"] + " "

        clean_block_text = " ".join(block_text.strip().split())
        if not clean_block_text:
            continue

        score: int = fuzz.partial_ratio(clean_chunk, clean_block_text)  # type: ignore[misc]

        if score > best_score:
            best_score = score
            best_block = block

    # A threshold of 70 is a reasonable balance to avoid nonsensical matches
    if best_score > 70:
        return best_block
    return None


def map_text_to_coordinates(
    pdf_path: Path, markdown_content: str
) -> List[MappedElement]:
    """
    The core function. Maps chunks of markdown text to their physical coordinates in the PDF.
    """
    all_pages_blocks = get_pdf_text_blocks(pdf_path)
    mapped_elements: List[MappedElement] = []

    # Split markdown into paragraphs. A simple split on double newlines works well.
    markdown_chunks = [
        chunk for chunk in markdown_content.split("\n\n") if chunk.strip()
    ]

    # Heuristic to guess the current page number.
    # We assume the document is processed sequentially.
    current_page_index = 0

    for i, chunk in enumerate(markdown_chunks):
        # The search space for a chunk is the current page and the next one.
        # This helps handle cases where a text block crosses a page boundary.
        search_pages_indices = {current_page_index}
        if current_page_index + 1 < len(all_pages_blocks):
            search_pages_indices.add(current_page_index + 1)

        search_blocks = [
            block for idx in search_pages_indices for block in all_pages_blocks[idx]
        ]

        match = find_best_match(chunk, search_blocks)

        # Initialize with defaults
        bbox: Optional[Bbox] = None
        page_num = current_page_index
        
        if match:
            # If a good match is found, update our current page.
            matched_page_num = match.get("page_num", current_page_index)
            if matched_page_num > current_page_index:
                current_page_index = matched_page_num

            page_num = matched_page_num
            bbox = match.get("bbox")

        element: MappedElement = {
            "id": f"elem_{i}",
            "text": chunk,
            "page_num": page_num,
            "bbox": bbox
        }

        mapped_elements.append(element)

    return mapped_elements

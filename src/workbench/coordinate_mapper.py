# src/workbench/coordinate_mapper.py
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Optional, Dict, Any, cast
from thefuzz import fuzz  # type: ignore[import-untyped]

from src.workbench.types import Block, MappedElement, Bbox
from src.workbench.parser_service import PAGE_SEPARATOR


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


def find_best_match(text_chunk: str, page_blocks: List[Block]) -> Optional[Block]:
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

    # Split the markdown content into a list of pages.
    markdown_pages = markdown_content.split(PAGE_SEPARATOR)

    element_counter = 0

    # Iterate through each page's markdown content with its page number.
    for page_index, page_markdown in enumerate(markdown_pages):

        if page_index >= len(all_pages_blocks):
            # If markdown has more pages than PDF, stop.
            continue

        # Get the text blocks for the current page ONLY. This is the key.
        current_page_blocks = all_pages_blocks[page_index]

        # Split the current page's markdown into logical chunks (paragraphs).
        markdown_chunks_for_page = [
            chunk for chunk in page_markdown.split("\n\n") if chunk.strip()
        ]

        for chunk in markdown_chunks_for_page:
            # Search for this chunk only within the current page's blocks.
            match = find_best_match(chunk, current_page_blocks)

            bbox: Optional[Bbox] = None
            if match:
                bbox = match.get("bbox")

            element: MappedElement = {
                "id": f"elem_{element_counter}",
                "text": chunk,
                "page_num": page_index,  # The page number is now deterministic.
                "bbox": bbox,
            }
            mapped_elements.append(element)
            element_counter += 1

    return mapped_elements

# src/workbench/types.py
from typing import TypedDict, List, Tuple, Optional

# A bounding box is a tuple of four floats (x0, y0, x1, y1)
BoundingBox = Tuple[float, float, float, float]

# --- PyMuPDF Raw Data Structures ---

# Structure of a "span" from PyMuPDF's get_text("dict")
class PdfSpan(TypedDict):
    text: str
    # other keys like font, size, etc., exist but are not needed for this app

# Structure of a "line" from PyMuPDF
class PdfLine(TypedDict):
    spans: List[PdfSpan]
    bbox: BoundingBox
    # other keys exist

# Structure of a "block" from PyMuPDF. This is our core PdfTextBlock
class PdfTextBlock(TypedDict):
    number: int
    type: int
    bbox: BoundingBox
    lines: List[PdfLine]
    # This is a custom key we add for our own tracking
    page_num: int

# --- Workbench Data Structures ---

# An element after being mapped from markdown to its PDF coordinates
class MappedElement(TypedDict):
    id: str
    text: str
    page_num: int
    # Bbox can be None if no suitable coordinate match is found for a text chunk
    bbox: Optional[BoundingBox]

# A trace event, which is a MappedElement augmented with a simulated source
class TraceEvent(MappedElement):
    source: str
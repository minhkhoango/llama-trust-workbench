# src/workbench/types.py
from typing import TypedDict, List, Tuple, Optional, Literal

# A bounding box is a tuple of four floats (x0, y0, x1, y1)
Bbox = Tuple[float, float, float, float] | None

# --- PyMuPDF Raw Data Structures ---


# Structure of a "span" from PyMuPDF's get_text("dict")
class Span(TypedDict):
    size: float
    flags: int
    font: str
    color: int
    ascender: float
    descender: float
    text: str
    origin: Tuple[float, float]
    bbox: Bbox


# Structure of a "line" from PyMuPDF's get_text("dict")
class Line(TypedDict):
    wmode: int
    dir: Tuple[float, float]
    bbox: Bbox
    spans: List[Span]


# Structure of a "block" from PyMuPDF's get_text("dict")
class Block(TypedDict):
    page_num: int
    type: int
    bbox: Bbox
    lines: List[Line]


# --- Workbench Data Structures ---


# An element after being mapped from markdown to PDF coordinates
class MappedElement(TypedDict):
    id: str
    text: str
    page_num: int
    bbox: Bbox


# A simulated trace event, representing one step in the parsing pipeline
class TraceEvent(MappedElement):
    source: str
    error: Optional[str]  # Field for potential error messages


# Define the exact, allowed statuses for a test result. No others are valid.
TestStatus = Literal[
    "PASS",
    "FAIL - HALLUCINATION",
    "FAIL - BAD MATH",
    "FAIL - CATASTROPHIC (No Data)",
    "FAIL - FILE NOT FOUND",
]


# The final result structure from the test harness for a single document
class TestResult(TypedDict):
    status: TestStatus
    reason: str

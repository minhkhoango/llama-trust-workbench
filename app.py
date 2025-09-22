# app.py
import streamlit as st
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image, ImageDraw
import io
import asyncio
import json
import sys

from src.workbench.types import TraceEvent, Bbox, TestResult
from src.workbench.parser_service import parse_document
from src.workbench.coordinate_mapper import map_text_to_coordinates
from src.workbench.tracer import simulate_trace
from src.workbench.test_harness import run_test_harness


PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# --- Configuration ---
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS = {
    "GH-420: PPFAS Factsheet (Aug 2024)": "ppfas_factsheet_august_2024.pdf",
    "GH-304: Samsung Financials (Q4 2024)": "samsung_factsheet_q4_2024.pdf",
}

# --- Caching & Data Loading ---


@st.cache_data(show_spinner="Rendering PDF page...")
def render_pdf_page_with_highlight(
    doc_path: Path, page_num: int, highlight_bbox: Optional[Bbox]
) -> Image.Image:
    """Renders a specific page of a PDF to an image and draws a highlight box."""
    doc = fitz.open(doc_path)
    page = doc.load_page(page_num)  # type: ignore

    dpi = 150
    pix = page.get_pixmap(dpi=dpi)  # type: ignore
    img = Image.open(io.BytesIO(pix.tobytes("png")))  # type: ignore

    if highlight_bbox:
        draw = ImageDraw.Draw(img)
        # To properly scale the bounding box, we need to create a matrix that
        # represents the same transformation as rendering with a specific DPI.
        # The default PDF DPI is 72.
        zoom_factor = dpi / 72.0
        zoom_matrix = fitz.Matrix(zoom_factor, zoom_factor)
        rect = fitz.Rect(highlight_bbox)
        rect.transform(zoom_matrix)  # type: ignore
        draw.rectangle((rect.x0, rect.y0, rect.x1, rect.y1), outline="#FF0000", width=3)

    doc.close()
    return img


@st.cache_resource(show_spinner="Running backend pipeline... This may take a moment.")
def get_document_trace(pdf_path: Path) -> List[TraceEvent]:
    """Runs the entire backend pipeline for a given document."""
    try:
        markdown_content = asyncio.run(parse_document(pdf_path))

        if markdown_content.strip().startswith("# Error"):
            return [
                {
                    "id": "error_id",
                    "text": f"Failed to parse document: {markdown_content}",
                    "page_num": 0,
                    "bbox": None,
                    "source": "Error",
                    "error": f"Failed to parse document: {markdown_content}",
                }
            ]

        mapped_elements = map_text_to_coordinates(pdf_path, markdown_content)
        trace_events = simulate_trace(mapped_elements)

        return trace_events
    except ValueError as e:
        st.error(f"Fatal Error: {e}. Is your .env file configured correctly?")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred in the backend pipeline: {e}")
        import traceback

        st.code(traceback.format_exc())
        return []


@st.cache_data
def load_fixed_trace_data(json_path: Path) -> List[TraceEvent]:
    """Loads the pre-canned 'correct' trace data from a JSON file."""
    with open(json_path, "r") as f:
        data: List[TraceEvent] = json.load(f)
    return data


@st.cache_resource(show_spinner="Running test harness...")
def get_test_results(pdf_filename: str) -> Dict[str, TestResult]:
    """Runs the test harness on a single document."""
    cache_dir = PROJECT_ROOT / ".cache"
    return run_test_harness(pdf_filename, cache_dir)


# --- UI Layout ---

st.set_page_config(layout="wide", page_title="LlamaTrust Workbench")

st.title("🦙 LlamaTrust Workbench")
st.markdown(
    "An interactive diagnostic workbench for `llama-parse` that provides ground-truth analysis for revenue-critical enterprise documents."
)

# --- State Initialization ---
if "selected_element_id" not in st.session_state:
    st.session_state.selected_element_id = None
if "simulate_fix" not in st.session_state:
    st.session_state.simulate_fix = False


# --- Sidebar Controls ---
def _reset_state():
    st.session_state.pop("selected_element_id", None)
    st.session_state.pop("simulate_fix", None)


# --- Sidebar Controls ---
st.sidebar.title("Controls")
selected_doc_name = st.sidebar.selectbox(
    "Select a Test Document",
    options=list(ARTIFACTS.keys()),
    key="selected_doc_key",
    # When changing doc, reset selection and simulation
    on_change=_reset_state,
)

if not selected_doc_name:
    st.stop()

pdf_filename = ARTIFACTS[selected_doc_name]
pdf_path = DATA_DIR / pdf_filename

# --- Test Harness Display ---
st.subheader("Test Harness Result")

# Ensure the document is parsed so the cache is available for the test harness
asyncio.run(parse_document(pdf_path))

test_results = get_test_results(pdf_filename)

# This maps the document name to the test name used in the test harness
doc_to_test_map = {
    "GH-420: PPFAS Factsheet (Aug 2024)": "GH-420 (Hallucination)",
    "GH-304: Samsung Financials (Q4 2024)": "GH-304 (Bad Math/Omission)",
}
test_key = doc_to_test_map.get(selected_doc_name)

if test_key and test_key in test_results:
    result = test_results[test_key]
    with st.container(border=True):
        st.markdown(f"**{selected_doc_name}**")
        if result["status"] == "PASS":
            st.success(f"{result['status']}", icon="✅")
        else:
            st.error(f"{result['status']}", icon="❌")
        st.caption(result["reason"])
else:
    st.warning("Could not find a test result for the selected document.")


st.divider()


# --- Fix Simulation Control ---
samsung_doc_key = "GH-304: Samsung Financials (Q4 2024)"
# Map document names to test result keys
doc_to_test_map = {
    "GH-420: PPFAS Factsheet (Aug 2024)": "GH-420 (Hallucination)",
    "GH-304: Samsung Financials (Q4 2024)": "GH-304 (Bad Math/Omission)",
}
if (
    selected_doc_name == samsung_doc_key
    and test_key in test_results
    and test_results[test_key]["status"] != "PASS"
):
    st.sidebar.toggle(
        "Simulate Fix with Premium Mode",
        key="simulate_fix",
        help="This simulates the expected output from a more robust parsing model, demonstrating a clear path to resolution.",
    )

# --- Main Application Logic ---
if st.session_state.simulate_fix and selected_doc_name == samsung_doc_key:
    st.info(
        "Showing simulated 'fixed' data. This is a hard-coded representation of the expected correct output.",
        icon="ℹ️",
    )
    fixed_trace_path = DATA_DIR / "samsung_fixed_trace.json"

    try:
        all_trace_events = load_fixed_trace_data(fixed_trace_path)
    except Exception as e:
        st.error(f"Error loading fixed trace: {e}")
        all_trace_events = []
else:
    try:
        all_trace_events = get_document_trace(pdf_path)
    except Exception as e:
        st.error(f"Error getting document trace: {e}")
        all_trace_events = []

if not all_trace_events:
    st.warning(
        "Could not retrieve parsing trace. Backend may have failed or the document may be empty."
    )
    st.stop()

# Handle potential error message from the trace
if len(all_trace_events) > 0 and all_trace_events[0].get("error") is not None:
    error_msg = all_trace_events[0]["error"]
    st.error(f"Error in parsing: {error_msg}")
    st.stop()

events_by_page: Dict[int, List[TraceEvent]] = {}
for event in all_trace_events:
    events_by_page.setdefault(event["page_num"], []).append(event)


# --- Main Content Display ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Document Viewer")

    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    doc.close()

    page_num_to_view = (
        st.number_input(
            "Page",
            min_value=1,
            max_value=num_pages,
            value=1,
            on_change=lambda: st.session_state.pop("selected_element_id", None),
        )
        - 1
    )

    highlight_bbox: Optional[Bbox] = None
    if st.session_state.selected_element_id:
        selected_event = next(
            (
                e
                for e in all_trace_events
                if e["id"] == st.session_state.selected_element_id
            ),
            None,
        )
        if selected_event and selected_event["page_num"] == page_num_to_view:
            highlight_bbox = selected_event["bbox"]

    pdf_image = render_pdf_page_with_highlight(
        pdf_path, page_num_to_view, highlight_bbox
    )
    st.image(pdf_image, width="stretch")

with col2:
    st.subheader("Parsing Trace (Simulated)")

    page_events = events_by_page.get(page_num_to_view, [])

    # Filter out PAGE-BREAK elements
    page_events = [
        event for event in page_events if "---PAGE_BREAK---" not in event["text"]
    ]

    if not page_events:
        st.info(f"No parsed elements found on page {page_num_to_view + 1}.")
    else:
        st.write(f"Found **{len(page_events)}** parsed elements on this page.")

        # Helper function to get display text (first 30 chars, no page breaks)
        def get_display_text(text: str) -> str:
            # Remove page breaks
            clean_text = text.replace("\n\n---PAGE_BREAK---\n\n", " ")
            # Get first 30 chars
            if len(clean_text) <= 30:
                return clean_text.strip()
            return clean_text[:30].strip() + "..."

        # Sort elements by top-to-bottom, then left-to-right reading order
        def _get_sort_key(event: TraceEvent) -> tuple[float, float]:
            bbox = event["bbox"]
            if bbox is None:
                return (0.0, 0.0)
            return (bbox[1], bbox[0])

        with st.container(height=700):
            # Display simple clickable elements for all page events
            for event in sorted(page_events, key=_get_sort_key):
                display_text = get_display_text(event["text"])

                source_color = {
                    "Heuristic Paragraph Extraction": "blue",
                    "Heuristic Table Detection": "orange",
                    "Multimodal LLM Call (Table)": "green",
                    "Unknown": "gray",
                }.get(event["source"], "gray")

                # Simple clickable button showing first 30 characters
                if st.button(
                    f"{display_text}", key=event["id"], use_container_width=True
                ):
                    st.session_state.selected_element_id = event["id"]
                    st.rerun()

                # Show full text in-place if this element is selected
                if st.session_state.selected_element_id == event["id"]:
                    with st.container(border=True):
                        st.markdown(f"**Source**: :{source_color}[{event['source']}]")
                        st.code(event["text"], language="markdown", line_numbers=True)

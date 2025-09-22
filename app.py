# app.py
import streamlit as st
import fitz
from pathlib import Path
from typing import List, Dict, Optional, Any
from PIL import Image, ImageDraw
import io
import asyncio
import sys

from src.workbench.types import TraceEvent, Bbox
from src.workbench.parser_service import parse_document
from src.workbench.coordinate_mapper import map_text_to_coordinates
from src.workbench.tracer import simulate_trace


# This navigates up from the directory where the script is, to the project root
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
# --- End Project Structure Setup ---

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
    doc: Any = fitz.open(doc_path)
    page: Any = doc.load_page(page_num)

    # Render page to a pixmap (an image format)
    pix: Any = page.get_pixmap(dpi=150)
    img = Image.open(io.BytesIO(pix.tobytes("png")))

    if highlight_bbox:
        draw = ImageDraw.Draw(img)
        # The pixmap is scaled, so we need to scale the bbox coordinates
        zoom_matrix: Any = page.get_pixmap(dpi=150).matrix

        # Transform the fitz.Rect to a tuple for drawing
        rect = fitz.Rect(highlight_bbox)
        rect.transform(zoom_matrix)

        draw.rectangle((rect.x0, rect.y0, rect.x1, rect.y1), outline="red", width=3)

    doc.close()
    return img


@st.cache_resource(show_spinner="Running backend pipeline... This may take a moment.")
def get_document_trace(pdf_path: Path) -> List[TraceEvent]:
    """
    Runs the entire backend pipeline for a given document.
    This is the most expensive operation, so it's cached.
    """
    try:
        # Since Streamlit runs in an async-incompatible way, we run our async
        # function using asyncio's event loop management.
        markdown_content = asyncio.run(parse_document(pdf_path))

        if markdown_content.strip().startswith("# Error"):
            st.error(f"Failed to parse document: {markdown_content}")
            return []

        mapped_elements = map_text_to_coordinates(pdf_path, markdown_content)
        trace_events = simulate_trace(mapped_elements)
        return trace_events
    except ValueError as e:
        # This typically happens if the API key is missing
        st.error(f"Fatal Error: {e}. Is your .env file configured correctly?")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred in the backend pipeline: {e}")
        return []


# --- UI Layout ---

st.set_page_config(layout="wide", page_title="LlamaTrust Workbench")

st.title("🦙 LlamaTrust Workbench")
st.markdown(
    "An interactive diagnostic tool for LlamaParse to visually trace and "
    "root-cause parsing errors in complex enterprise documents."
)

# --- State Initialization ---
if "selected_element_id" not in st.session_state:
    st.session_state.selected_element_id = None

# --- Sidebar Controls ---
st.sidebar.title("Controls")
selected_doc_name = st.sidebar.selectbox(
    "Select a Test Document",
    options=list(ARTIFACTS.keys()),
    key="selected_doc_key",
    on_change=lambda: st.session_state.pop(
        "selected_element_id", None
    ),  # Reset highlight on doc change
)

if not selected_doc_name:
    st.stop()  # Should not happen with a selectbox, but good practice

pdf_filename = ARTIFACTS[selected_doc_name]
pdf_path = DATA_DIR / pdf_filename

# --- Main Application Logic ---
all_trace_events = get_document_trace(pdf_path)

if not all_trace_events:
    st.warning("Could not retrieve parsing trace. Backend may have failed.")
    st.stop()

# Group events by page number for easy access
events_by_page: Dict[int, List[TraceEvent]] = {}
for event in all_trace_events:
    events_by_page.setdefault(event["page_num"], []).append(event)

# --- Main Content Display ---
col1, col2 = st.columns(2)

# PDF Viewer Column
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
            on_change=lambda: st.session_state.pop(
                "selected_element_id", None
            ),  # Reset highlight on page change
        )
        - 1
    )  # Convert to 0-based index

    # Find the bbox of the selected element to highlight it
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

# Trace Viewer Column
with col2:
    st.subheader("Parsing Trace (Simulated)")

    page_events = events_by_page.get(page_num_to_view, [])

    if not page_events:
        st.info(f"No parsed elements found on page {page_num_to_view + 1}.")
    else:
        st.write(f"Found **{len(page_events)}** parsed elements on this page.")

        for event in sorted(
            page_events, key=lambda e: (e["bbox"][1], e["bbox"][0]) if e["bbox"] is not None else (float('inf'), float('inf'))
        ):  # Sort by vertical, then horizontal position

            # Simple color coding for different sources
            source_color = {
                "Heuristic Paragraph Extraction": "blue",
                "Heuristic Table Detection": "orange",
                "Multimodal LLM Call (Table)": "green",
                "Unknown": "gray",
            }.get(event["source"], "gray")

            with st.container(border=True):
                st.markdown(f"**Source**: :{source_color}[{event['source']}]")

                # Use a button for interactivity. When clicked, it sets the session state.
                if st.button("Highlight on PDF", key=event["id"]):
                    st.session_state.selected_element_id = event["id"]
                    # This re-runs the script, and the PDF viewer will now have the highlight_bbox
                    st.rerun()

                with st.expander("View Parsed Text"):
                    st.markdown(f"```markdown\n{event['text']}\n```")

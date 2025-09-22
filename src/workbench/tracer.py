# src/workbench/tracer.py
from typing import List
from src.workbench.types import MappedElement, TraceEvent


def simulate_trace(mapped_data: List[MappedElement]) -> List[TraceEvent]:
    """
    Augments the coordinate-mapped data with a simulated trace of the parsing process.

    This is a heuristic-based simulation. It guesses the origin of a text block
    based on its content.
    """
    trace_events: List[TraceEvent] = []

    for element in mapped_data:
        text: str = element["text"]
        source = "Heuristic Paragraph Extraction"  # Default assumption

        # Simple heuristic: if the text contains markdown table syntax,
        # we assume it came from a more complex, multimodal model.
        if "|" in text and "---" in text:
            source = "Multimodal Table Detection (LLM)"
        # Heuristic for titles or headers
        elif text.startswith("#"):
            source = "Heuristic Header Detection"

        # Create a new TraceEvent, combining the MappedElement with the new source
        event: TraceEvent = {
            "id": element["id"],
            "text": element["text"],
            "page_num": element["page_num"],
            "bbox": element["bbox"],
            "source": source,
            "error": None,
        }

        trace_events.append(event)

    return trace_events

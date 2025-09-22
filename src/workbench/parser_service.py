# src/workbench/parser_service.py
import os
from pathlib import Path
from llama_parse import LlamaParse  # type: ignore
from dotenv import load_dotenv

# --- CONFIGURATION ---
CACHE_DIR = Path(__file__).resolve().parent.parent.parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

# --- SERVICE INITIALIZATION ---
def get_parser() -> LlamaParse:
    """
    Initializes and returns the LlamaParse parser.
    Loads the API key from environment variables.
    """
    load_dotenv()
    api_key: str | None = os.getenv("LLAMA_CLOUD_API_KEY")
    if not api_key:
        raise ValueError(
            "LLAMA_CLOUD_API_KEY is not set. "
            "Please create a .env file and add your API key."
        )
    return LlamaParse(api_key=api_key, result_type="markdown", verbose=True)  # type: ignore

# --- CORE FUNCTIONALITY ---
async def parse_document(pdf_path: Path) -> str:
    """
    Parses a single PDF document using LlamaParse.
    Implements file-based caching to avoid re-processing.
    """
    cache_path: Path = CACHE_DIR / f"{pdf_path.stem}.md"

    if cache_path.exists():
        print(f"Cache hit for {pdf_path.name}. Loading from {cache_path}")
        return cache_path.read_text(encoding="utf-8")

    print(f"Cache miss for {pdf_path.name}. Calling LlamaParse API...")
    parser = get_parser()

    try:
        documents = await parser.aload_data(str(pdf_path))  # type: ignore
        if not documents:
            raise IOError("LlamaParse returned no documents.")
        
        parsed_content: str = documents[0].get_content()

        # Save to cache
        cache_path.write_text(parsed_content, encoding="utf-8")
        print(f"Successfully parsed and cached {pdf_path.name}")

        return parsed_content
    except Exception as e:
        print(f"Error parsing document {pdf_path.name}: {e}")
        # Return a specific error message that can be displayed in the UI
        return f"# Error\n\nFailed to parse document: {e}"
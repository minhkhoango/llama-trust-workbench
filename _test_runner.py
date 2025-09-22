# _test_runner.py
import asyncio
from pathlib import Path

from src.workbench.parser_service import parse_document
from src.workbench.coordinate_mapper import map_text_to_coordinates
from src.workbench.tracer import simulate_trace
from src.workbench.test_harness import run_tests

# --- CONFIGURATION ---
# This assumes you run the script from the root of your project
DATA_DIR = Path(__file__).resolve().parent / "data"
CACHE_DIR = Path(__file__).resolve().parent / ".cache"

# The specific files we want to process
PDF_FILES = [
    "ppfas_factsheet_august_2024.pdf",
    "samsung_factsheet_q4_2024.pdf"
]

async def test_pipeline_for_file(pdf_name: str) -> None:
    """Runs the entire backend pipeline for a single file and prints the output."""
    pdf_path = DATA_DIR / pdf_name
    
    if not pdf_path.exists():
        print(f"ERROR: PDF file not found at {pdf_path}")
        print("Please run 'poetry run python scripts/get_artifacts.py' first.")
        return

    print("\n" + "="*80)
    print(f"🚀 STARTING PIPELINE FOR: {pdf_name}")
    print("="*80)

    # --- STAGE 1: PARSING ---
    print("\n[STAGE 1/3] Calling LlamaParse API...")
    print(f"   - Target: {pdf_path.name}")
    print("   - NOTE: This is the slow part, especially for large documents.")
    print("   - The script is waiting for their server to finish processing. Let it run.")
    
    markdown_content = await parse_document(pdf_path)
    
    if markdown_content.strip().startswith("# Error"):
        print("❌ PARSING FAILED.")
        print(markdown_content)
        return
        
    print(f"✅ Parsing successful. Received {len(markdown_content)} characters.")

    # --- STAGE 2: COORDINATE MAPPING ---
    print("\n[STAGE 2/3] Mapping markdown to PDF coordinates...")
    mapped_elements = map_text_to_coordinates(pdf_path, markdown_content)
    print(f"✅ Mapping complete. Found {len(mapped_elements)} elements.")
    if mapped_elements:
        print("   Sample Mapped Element:")
        print(f"   {mapped_elements[0]}")

    # --- STAGE 3: TRACE SIMULATION ---
    print("\n[STAGE 3/3] Simulating parsing trace...")
    trace_events = simulate_trace(mapped_elements)
    print(f"✅ Trace simulation complete. Generated {len(trace_events)} events.")
    if trace_events:
        print("   Sample Trace Event:")
        print(f"   {trace_events[0]}")

    print(f"\n✅ PIPELINE SUCCEEDED FOR: {pdf_name}")


async def main() -> None:
    """The main entry point for the test runner."""
    # Run the full pipeline for each document to populate the cache
    for pdf_file in PDF_FILES:
        await test_pipeline_for_file(pdf_file)
        
    # --- FINAL STAGE: TEST HARNESS ---
    print("\n" + "="*80)
    print("📊 RUNNING TEST HARNESS ON CACHED RESULTS")
    print("="*80)
    
    # The test harness runs synchronously on the cached files
    test_results = run_tests(CACHE_DIR)
    
    print("\nFinal Test Results:")
    for test_name, result in test_results.items():
        status_icon = "❌" if result.startswith("FAIL") else "✅" if result == "PASS" else "⏳"
        print(f"  {status_icon} {test_name}: {result}")
    print("\n" + "="*80)


if __name__ == "__main__":
    # Ensure you have a .env file with your LLAMA_CLOUD_API_KEY
    try:
        asyncio.run(main())
    except ValueError as e:
        print(f"\nCRITICAL ERROR: {e}")
        print("Please ensure your .env file is correctly set up.")
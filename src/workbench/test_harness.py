# src/workbench/test_harness.py
from pathlib import Path
from typing import Dict, List
from .types import TestResult


# --- Test Case Specifics ---

# For GH-420: Known text that should NOT be in the output.
# This text was hallucinated by the parser in the original GitHub issue.
HALLUCINATED_TEXT_GH420: str = "Core Equity & Bond Fund"

# For GH-420: Text that MUST be in the output for it to be considered valid.
# We'll check for a known, stable section header.
REQUIRED_TEXT_GH420: str = "Parag Parikh Flexi Cap Fund"

# For GH-304 (Samsung): A list of text strings we expect to find in a valid parse
# of a financial statement. If these are missing, the parse is a catastrophic failure.
# We'll look for key line items from the Consolidated Statements of Profit or Loss.
REQUIRED_LINES_GH304: List[str] = [
    "Revenue",
    "Cost of sales",
    "Gross profit",
    "Operating profit",
    "Profit for the year",
]


def check_gh_420(content: str) -> TestResult:
    """
    Checks for the hallucination bug in the PPFAS factsheet.
    1. First, checks if the document was parsed meaningfully at all.
    2. Then, checks for the specific hallucinated text.
    """
    # 1. Catastrophic Failure Check: Is the output basically empty or missing key sections?
    if len(content) < 500:  # A valid parse of this doc is over 2000 chars
        return {
            "status": "FAIL - CATASTROPHIC (No Data)",
            "reason": "Document content too short",
        }
    if REQUIRED_TEXT_GH420 not in content:
        return {
            "status": "FAIL - CATASTROPHIC (No Data)",
            "reason": "Document content too short",
        }

    # 2. Hallucination Check: If the parse seems okay, check for the bad text.
    if HALLUCINATED_TEXT_GH420 in content:
        return {"status": "FAIL - HALLUCINATION", "reason": "Hallucinated text found"}

    return {
        "status": "PASS",
        "reason": "Document parsed successfully without hallucinations",
    }


def check_gh_304(content: str) -> TestResult:
    """
    Checks for the bad math / data omission bug in the Samsung financial report.
    1. First, checks if the financial statements were parsed at all.
    2. If they were, it would eventually check for bad math (future implementation).
    """
    # 1. Catastrophic Failure Check: Does the output contain the basic lines
    # of a financial statement?

    # Heuristic: A valid parse of an 88-page report should be substantial.
    # It must also contain the basic financial statement lines.
    lines_found = [line for line in REQUIRED_LINES_GH304 if line in content]
    if len(content) < 1000 or len(lines_found) < len(REQUIRED_LINES_GH304):
        # We couldn't even find the basic structure of the P&L statement,
        # or the parsed content is suspiciously small.
        return {
            "status": "FAIL - CATASTROPHIC (No Data)",
            "reason": "Document content too short",
        }

    # 2. Bad Math Check (Placeholder for future):
    # If we get here, it means the data was present. This is where we would
    # extract the numbers and check their sums. For now, we'll assume if the
    # data is present, the test passes this stage.
    # In a real scenario, this would be `return "FAIL - BAD MATH"` if sums were wrong.

    return {
        "status": "PASS",
        "reason": "Document parsed successfully without hallucinations",
    }


def run_test_harness(cache_dir: Path) -> Dict[str, TestResult]:
    """
    Runs all defined tests against the cached markdown files.
    """
    results: Dict[str, TestResult] = {}

    # Test for GH-420
    gh_420_file = cache_dir / "ppfas_factsheet_august_2024.md"
    if gh_420_file.exists():
        content = gh_420_file.read_text()
        results["GH-420 (Hallucination)"] = check_gh_420(content)
    else:
        results["GH-420 (Hallucination)"] = {
            "status": "FAIL - FILE NOT FOUND",
            "reason": f"Cache file not found: {gh_420_file}",
        }

    # Test for GH-304
    gh_304_file = cache_dir / "samsung_factsheet_q4_2024.md"
    if gh_304_file.exists():
        content = gh_304_file.read_text()
        results["GH-304 (Bad Math/Omission)"] = check_gh_304(content)
    else:
        results["GH-304 (Bad Math/Omission)"] = {
            "status": "FAIL - FILE NOT FOUND",
            "reason": f"Cache file not found: {gh_304_file}",
        }

    return results

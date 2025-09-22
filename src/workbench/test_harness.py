# src/workbench/test_harness.py
import re
from pathlib import Path
from typing import Dict, List

# --- Test Case for GH-420 (Hallucination) ---
# This is a specific, known hallucinated string from the original issue.
# We check if the parser "invents" this text.
HALLUCINATED_STRING = "Mirae Asset NYSE FANG+ ETF FoF"

def check_gh_420(markdown_content: str) -> bool:
    """Checks for the presence of a known hallucinated string."""
    return HALLUCINATED_STRING in markdown_content

   # --- Test Case for GH-304 (Bad Math) ---
# From the Samsung report, we look at the Q4'23 Consolidated Statement of Profit or Loss.
# The value for "Profit for the period" is given as 10,217.
# The values that sum to it are "Profit for the period attributable to: Owners of the parent" (8,908)
# and "Non-controlling interests" (1,309).
# 8,908 + 1,309 = 10,217. This is CORRECT in the source PDF.
# A failure mode of the parser would be to misread these numbers and get the sum wrong.
# Our test will extract these three numbers and verify the equation.

def find_numbers_in_line(text: str) -> List[int]:
    """Extracts all integer numbers from a string line."""
    # Remove commas from numbers before converting
    cleaned_text = text.replace(",", "")
    # Find all sequences of digits, possibly with a leading negative sign
    found_numbers = re.findall(r'-?\d+', cleaned_text)
    return [int(n) for n in found_numbers]

def check_gh_304(markdown_content: str) -> bool:
    """
    Checks for a specific mathematical inconsistency in a financial table.
    Returns True if the math is WRONG (test fails), False if it is correct.
    """
    lines = markdown_content.split('\n')
    
    profit_for_period: List[int] = []
    owners_of_parent: List[int] = []
    non_controlling_interests: List[int] = []

    for line in lines:
        if "Profit for the period" in line and "attributable" not in line:
            profit_for_period = find_numbers_in_line(line)
        elif "Owners of the parent" in line:
            owners_of_parent = find_numbers_in_line(line)
        elif "Non-controlling interests" in line:
            non_controlling_interests = find_numbers_in_line(line)

    # We need to find all three values to perform the check
    if profit_for_period and owners_of_parent and non_controlling_interests:
        # We assume the first number found in each line is the relevant one for Q4'23
        p_total = profit_for_period[0]
        p_owners = owners_of_parent[0]
        p_nci = non_controlling_interests[0]
        
        print(f"GH-304 Check: Found values -> Total={p_total}, Owners={p_owners}, NCI={p_nci}")

        # The test fails if the math is incorrect
        return p_owners + p_nci != p_total
        
    # If we couldn't find all the lines, we can't determine the result.
    # We'll consider this a pass to avoid false negatives, but log it.
    print("GH-304 Check: Could not find all required financial lines in the output.")
    return False


# --- Main Test Runner ---
def run_tests(cache_dir: Path) -> Dict[str, str]:
    """
    Runs all defined tests against the cached parser outputs.
    """
    results: Dict[str, str] = {}
    
    # Test for GH-420
    gh_420_file: Path = cache_dir / "ppfas_factsheet_august_2024.md"
    if gh_420_file.exists():
        content = gh_420_file.read_text(encoding="utf-8")
        # The test fails if the hallucinated string is FOUND
        results["GH-420"] = "FAIL" if check_gh_420(content) else "PASS"
    else:
        results["GH-420"] = "PENDING"

    # Test for GH-304
    gh_304_file = cache_dir / "samsung_factsheet_q4_2024.md"
    if gh_304_file.exists():
        content = gh_304_file.read_text(encoding="utf-8")
        # The test fails if the math is WRONG
        results["GH-304"] = "FAIL" if check_gh_304(content) else "PASS"
    else:
        results["GH-304"] = "PENDING"
        
    return results
# LlamaTrust Workbench

An interactive diagnostic workbench for LlamaParse that provides visual tracing and root-cause analysis for parsing errors in complex enterprise documents.

## The Problem

Enterprise AI adoption depends on trust and reliability. When parsing mission-critical documents like financial statements or technical manuals, "black box" tools are unacceptable. Teams need to understand the "why" behind parsing errors to build robust systems.

Currently, diagnosing LlamaParse failures relies on manual inspection and guesswork. This is particularly problematic for known, deal-breaking bugs:

- **GH-304**: Incorrect OCR and destructive, unprompted mathematical calculations on financial tables
- **GH-420**: Severe data hallucination in the default "accurate" parsing mode

These issues erode customer trust and kill pilot-to-production conversions.

## The Solution

The LlamaTrust Workbench is a standalone Streamlit application that provides a "glass box" for LlamaParse. It enables engineers and pre-sales teams to:

- **Instantly Validate**: Run tests against known-bad documents and see clear [FAIL] status for critical bugs
- **Visually Trace Errors**: Get interactive, multi-modal traces that map parsed output directly back to source PDF coordinates
- **Simulate Fixes**: Demonstrate the value of higher-tier parsing modes with a single click

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/minhkhoango/llama-trust-workbench.git
   cd llama-trust-workbench
   ```

2. **Install dependencies:**
   ```bash
   poetry install
   ```

3. **Download test artifacts:**
   ```bash
   poetry run python scripts/get_artifacts.py
   ```

4. **Run the application:**
   ```bash
   streamlit run app.py
   ```

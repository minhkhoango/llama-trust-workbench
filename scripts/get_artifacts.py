import requests
from pathlib import Path
import sys
from typing import Dict

# Define the target directory for artifacts
DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data"

# Define the artifacts to be downloaded
ARTIFACTS: Dict[str, str] = {
    "ppfas_factsheet_august_2024.pdf": "https://amc.ppfas.com/downloads/factsheet/2024/ppfas-mf-factsheet-for-August-2024.pdf?10092024",
    "samsung_factsheet_q4_2024.pdf": "https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2024_con_quarter04_all.pdf"
}

def download_file(url: str, output_path: Path) -> None:
    """Downloads a file from a URL to a specified path."""
    try:
        print(f"Downloading {output_path.name} from {url}...")
        response = requests.get(url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()  # Raise an exception for bad status codes

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded {output_path.name}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {output_path.name}: {e}", file=sys.stderr)
        sys.exit(1)

def main() -> None:
    """Main function to download all artifacts."""
    print(f"Ensuring data directory exists at: {DATA_DIR}")
    DATA_DIR.mkdir(exist_ok=True)

    for filename, url in ARTIFACTS.items():
        output_path: Path = DATA_DIR / filename
        if output_path.exists():
            print(f"{filename} already exists. Skipping download.")
        else:
            download_file(url, output_path)

    print("\nArtifact acquisition complete.")

if __name__ == "__main__":
    main()
from __future__ import annotations

from pathlib import Path
import sys
import contextlib


import logging
LOGGER = logging.getLogger(__name__)

try:
    from pdf2image import convert_from_path
    # ...other imports and extractor setup...
except ImportError as e:
    LOGGER.error("Failed to import 'pdf2image' for PDF extraction: %s", e)
    LOGGER.error("Please install the missing dependency with: pip install pdf2image")
    raise

def run_intake_extractor(
    pdf_path: Path,
    output_json: Path,
    log_file: Path,
    repo_path: Path | None = None,
) -> bool:
    r"""Run external extractor from another repo and capture logs to a file.

    Defaults repo_path to:
    C:\Users\raghu\Documents\Python Projects\pdf-parser
    """
    repo_path = repo_path or Path(r"C:\Users\raghu\Documents\Python Projects\pdf-parser")
    success = False
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "w", encoding="utf-8", errors="ignore") as lf:
        with contextlib.redirect_stdout(lf), contextlib.redirect_stderr(lf):
            sys.path.insert(0, str(repo_path))
            try:
                from extractor import run_extractor_from_config  # type: ignore
            except Exception as e:
                print(f"Failed to import extractor from {repo_path}: {e}")
                return False
            try:
                data = run_extractor_from_config(
                    pdf_path=str(pdf_path),
                    output_path=str(output_json),
                )
                print("Done; pages:", len((data or {}).get("pages", [])))
                success = True
            except Exception as e:
                print(f"Extractor run failed: {e}")
    return success

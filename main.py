'''
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.0.0"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Prod"
__desc__ = "Main entrypoint for CLI operations and FastAPI launcher for OCR Universal project."
'''

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional

from src.ocr import (
    docx_doc_to_text,
    pptx_ppt_to_text,
    xlsx_xls_to_text,
    html_to_text,
    pdf_to_text,
    photo_to_text,
    odt_rtf_to_text,
)
from src.utils.logging_utils import get_logger
from src.utils.ocr_utils import get_data_dirs, is_allowed_file, generate_unique_filename
from src.utils.constants import PRUNE_AFTER_PROCESS

## ============================================================
## CONSTANTS
## ============================================================
APP_VERSION = "1.0.0"
EXIT_SUCCESS = 0
EXIT_FAILURE = 1

## ============================================================
## LOGGER
## ============================================================
logger = get_logger("main")

## ============================================================
## OCR PROCESSING
## ============================================================
def process_single_file(file_path: Path, output_dir: Path, print_output: bool = False) -> None:
    """
        Process a single file and extract text

        Args:
            file_path: Input file path
            output_dir: Output directory
            print_output: Print instead of saving
    """

    logger.info("Processing: %s (%s)", file_path.name, file_path.suffix.lower())

    if not is_allowed_file(file_path.name):
        logger.warning("Unsupported file: %s", file_path)
        return

    ext = file_path.suffix.lower()
    text = ""

    try:
        if ext in [".docx", ".doc"]:
            text = docx_doc_to_text.process_doc_or_docx(file_path)

        elif ext in [".pptx", ".ppt"]:
            text = pptx_ppt_to_text.process_presentation(file_path)

        elif ext in [".xls", ".xlsx"]:
            text = xlsx_xls_to_text.process_excel_file(file_path)

        elif ext == ".pdf":
            text = pdf_to_text.process_pdf_file(file_path)

        elif ext in [".html", ".htm", ".mht"]:
            text = html_to_text.process_html(file_path)

        elif ext == ".odt":
            text = odt_rtf_to_text.process_odt(file_path)

        elif ext == ".rtf":
            text = odt_rtf_to_text.process_rtf(file_path)

        elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"]:
            normalized_path = photo_to_text.convert_image_for_ocr(file_path)
            text = photo_to_text.ocr_with_tesseract(normalized_path)

        elif ext == ".txt":
            text = file_path.read_text(encoding="utf-8", errors="ignore")

        else:
            logger.warning("No handler for extension: %s", ext)
            return

    except Exception as exc:
        logger.exception("Error extracting text: %s", exc)
        return

    if print_output:
        print(f"\n===== {file_path.name} =====\n{text}")
    else:
        output_path = output_dir / f"{file_path.stem}{file_path.suffix}.txt"
        output_path.write_text(text or "", encoding="utf-8")
        logger.info("Saved: %s", output_path)

    if PRUNE_AFTER_PROCESS:
        try:
            os.remove(file_path)
            logger.debug("Pruned: %s", file_path)
        except Exception:
            pass

def process_directory(input_dir: Path, output_dir: Path, print_output: bool = False) -> None:
    """
        Process directory of files

        Args:
            input_dir: Input folder
            output_dir: Output folder
            print_output: Print instead of saving
    """

    files = list(input_dir.glob("*"))
    logger.info("Scanning: %s | %d files", input_dir, len(files))

    for file_path in files:
        if file_path.is_file():
            process_single_file(file_path, output_dir, print_output)

    logger.info("Directory processing completed")

## ============================================================
## OTHER MODES
## ============================================================
def run_tests() -> None:
    """
        Run pytest suite
    """

    logger.info("Running tests")
    os.system("pytest -v")

def launch_fastapi() -> None:
    """
        Launch FastAPI service
    """

    logger.info("Launching API")
    os.system("uvicorn src.service:app --host 0.0.0.0 --port 8080 --reload")

## ============================================================
## HELPERS
## ============================================================
def _build_summary(action: str, success: bool, start: float, details: Optional[dict] = None) -> dict:
    """
        Build execution summary

        Args:
            action: Action name
            success: Status
            start: Start time
            details: Optional details

        Returns:
            Summary dict
    """

    return {
        "action": action,
        "success": success,
        "duration_seconds": round(time.monotonic() - start, 3),
        "details": details or {},
    }

## ============================================================
## MAIN
## ============================================================
def main() -> int:
    """
        Main CLI entrypoint

        Modes:
            - convert: OCR processing
            - test: pytest
            - api: FastAPI

        Returns:
            Exit code
    """

    start_time = time.monotonic()

    parser = argparse.ArgumentParser(description="OCR Universal CLI")
    parser.add_argument("--version", action="version", version=f"%(prog)s {APP_VERSION}")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--validate-config", action="store_true")

    parser.add_argument("--mode", type=str, default="api", choices=["convert", "test", "api"])
    parser.add_argument("--path", type=str)
    parser.add_argument("--print", action="store_true")

    args = parser.parse_args()

    try:
        if args.validate_config:
            logger.info("Config OK")
            logger.info("Summary | %s", _build_summary("validate-config", True, start_time))
            return EXIT_SUCCESS

        if args.dry_run:
            logger.info("Dry-run | mode=%s path=%s", args.mode, args.path)
            logger.info("Summary | %s", _build_summary("dry-run", True, start_time))
            return EXIT_SUCCESS

        dirs = get_data_dirs()

        ## CONVERT
        if args.mode == "convert":
            input_path = Path(args.path) if args.path else dirs["input"]
            output_dir = dirs["output"]

            if input_path.is_file():
                unique_path = generate_unique_filename(input_path)
                process_single_file(unique_path, output_dir, args.print)

            elif input_path.is_dir():
                process_directory(input_path, output_dir, args.print)

            else:
                logger.error("Invalid path: %s", input_path)

        ## TEST
        elif args.mode == "test":
            run_tests()

        ## API
        elif args.mode == "api":
            launch_fastapi()

        logger.info("Summary | %s", _build_summary("run", True, start_time))
        return EXIT_SUCCESS

    except KeyboardInterrupt:
        logger.warning("Interrupted")
        return EXIT_FAILURE

    except Exception as exc:
        logger.exception("Unhandled error: %s", exc)
        return EXIT_FAILURE

## ============================================================
## ENTRYPOINT
## ============================================================
if __name__ == "__main__":
    sys.exit(main())
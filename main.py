'''
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.0.0"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Prod"
__desc__ = "Main entrypoint for CLI operations and FastAPI launcher for OCR Universal project."
'''

import os
import sys
import argparse
import subprocess
from pathlib import Path

from src.ocr import (
    docx_doc_to_text,
    pptx_ppt_to_text,
    xlsx_xls_to_text,
    html_to_text,
    pdf_to_text,
    photo_to_text,
    odt_rtf_to_text
)
from src.utils.logging_utils import get_logger
from src.utils.ocr_utils import get_data_dirs, is_allowed_file, generate_unique_filename
from src.utils.constants import PRUNE_AFTER_PROCESS

## ============================================================
## LOGGER INITIALIZATION
## ============================================================

## Initialize main logger
logger = get_logger("main")

## ============================================================
## CLI CORE FUNCTIONS
## ============================================================
def process_single_file(file_path: Path, output_dir: Path, print_output: bool = False) -> None:
    """
        Detect the file type and extract text accordingly

        Args:
            file_path (Path): Path to input file
            output_dir (Path): Directory to save output text file
            print_output (bool): If True, print text in terminal instead of saving
    """
    logger.info(f"Processing: {file_path.name} ({file_path.suffix.lower()})")

    ## Check if file type is allowed
    if not is_allowed_file(file_path.name):
        logger.warning(f"File skipped (unsupported type): {file_path}")
        return

    ## Detect file extension and prepare extraction
    ext = file_path.suffix.lower()
    text = ""

    ## Dispatch processing based on file extension
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

        elif ext in [".odt"]:
            text = odt_rtf_to_text.process_odt(file_path)
        
        elif ext in [".rtf"]:
            text = odt_rtf_to_text.process_rtf(file_path)

        elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"]:
            ## IMPORTANT:
            ## Your project uses `photo_to_text.py`, not `image_to_text.py`.
            ## We normalize the image (dpi/format) then run OCR with Tesseract.
            normalized_path = photo_to_text.convert_image_for_ocr(file_path)
            text = photo_to_text.ocr_with_tesseract(normalized_path)

            ## Optional: if you want Vision fallback when tesseract returns nothing,
            ## uncomment the block below (and make sure your Vision deps/creds are set).
            # if not text.strip():
            #     logger.warning("Tesseract returned empty text. Trying Google Vision fallback...")
            #     text = photo_to_text.ocr_with_google_vision(normalized_path)

        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as infile:
                text = infile.read()

        else:
            logger.warning(f"No handler for extension: {ext}")
            return

    except Exception as e:
        ## Use exception() to keep full traceback in logs
        logger.exception(f"Error extracting text from {file_path}: {e}")
        return

    ## Output: print or save to file
    if print_output:
        print(f"\n===== {file_path.name} =====\n")
        print(text)
    else:
        if text == None:
            text = ""
            
        # output_path = output_dir / f"{file_path.stem}.txt"
        output_path = output_dir / f"{file_path.stem}{file_path.suffix}.txt"
        with open(output_path, "w", encoding="utf-8") as out_file:
            out_file.write(text)
        logger.info(f"Saved extracted text: {output_path}")

    ## Optionally delete processed file
    if PRUNE_AFTER_PROCESS:
        try:
            os.remove(file_path)
            logger.debug(f"Pruned file: {file_path}")
        except Exception:
            pass
            
def process_directory(input_dir: Path, output_dir: Path, print_output: bool = False) -> None:
    """
        Process all allowed files in a given directory

        Args:
            input_dir (Path): Folder containing input files
            output_dir (Path): Folder for output text files
            print_output (bool): Print text instead of saving to files
    """
    
    ok = 0
    skipped = 0
    failed = 0

    files = list(input_dir.glob("*"))
    logger.info(f"Scanning folder: {input_dir} | {len(files)} entries")

    for file_path in files:
        if not file_path.is_file():
            continue

        try:
            before = ok
            process_single_file(file_path, output_dir, print_output)
            # si un fichier est traité, on logge dans process_single_file (voir C)
            if ok == before:
                pass
        except Exception as exc:
            failed += 1
            logger.exception(f"FAILED file: {file_path} | {exc}")

    logger.info(f"Done. ok={ok} skipped={skipped} failed={failed}")

def run_tests() -> None:
    """
        Execute unit tests using pytest
    """
    
    logger.info("Running unit tests with pytest...")
    os.system("pytest -v")

def launch_fastapi() -> None:
    """
        Launch FastAPI service using uvicorn
    """
    
    logger.info("Launching FastAPI service on port 8080...")
    os.system("uvicorn src.service:app --host 0.0.0.0 --port 8080 --reload")

## ============================================================
## CLI ENTRY POINT
## ============================================================
def main():
    """
        CLI entrypoint for OCR Universal project

        Provides three main options:
            1. Convert a single file or directory
            2. Run unit tests
            3. Launch FastAPI API
    """

    ## Argument parser setup
    parser = argparse.ArgumentParser( description="OCR Universal - Convert, Test, or Launch API")
    parser.add_argument("--mode",  type=str, default="api", choices=["convert", "test", "api"], help="Mode to run: convert | test | api")
    parser.add_argument("--path", type=str, help="Path to input file or folder (only for convert mode)")
    parser.add_argument("--print", action="store_true", help="Print output instead of saving to file (convert mode)")

    args = parser.parse_args()
    dirs = get_data_dirs()

    ## Mode: Convert (file or directory)
    if args.mode == "convert":
        if not args.path:
            logger.warning("No path provided. Using default input folder.")
            input_path = dirs["input"]
        else:
            input_path = Path(args.path)

        output_dir = dirs["output"]

        if input_path.is_file():
            unique_path = generate_unique_filename(input_path)
            process_single_file(unique_path, output_dir, args.print)
        elif input_path.is_dir():
            process_directory(input_path, output_dir, args.print)
        else:
            logger.error(f"Invalid path: {input_path} | exists={input_path.exists()}")
            logger.error(f"Invalid path: {input_path}")

    ## Mode: Tests
    elif args.mode == "test":
        run_tests()

    ## Mode: FastAPI
    elif args.mode == "api":
        launch_fastapi()

## ============================================================
## MAIN ENTRY POINT
## ============================================================
if __name__ == "__main__":
    main()

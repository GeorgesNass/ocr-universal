'''
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.2.2"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Prod"
__desc__ = "Extract text from PDFs using Tika, PyPDF2, pdftotext, and fallback OCR via Tesseract/Google Vision with quality control and heuristics."
'''

import io
import os
import re
import sys
import time
from pathlib import Path
from typing import List

import pdf2image
from PyPDF2 import PdfReader
import pdftotext
from tika import parser
from PIL import Image  # kept for future image operations if needed

from src.utils import get_logger, log_execution_time_and_path
from src.utils.constants import (
    INPUT_DIR,
    CONVERTED_DIR,
    OUTPUT_DIR,
    ALLOWED_EXTENSIONS,
    USE_TIKA,
    USE_PYPDF2,
    USE_PDFTOTEXT,
    USE_PDF2IMAGE,
    USE_TESSERACT,
    USE_GOOGLE_VISION,
    MAX_PDF_SIZE_MB,
)
from src.ocr.photo_to_text import ocr_with_tesseract, ocr_with_google_vision

## ============================================================
## LOGGER INITIALIZATION
## ============================================================
logger = get_logger("pdf_to_text")

## ============================================================
## HEURISTIC VALIDATION
## ============================================================
def is_text_valid(text: str) -> bool:
    """
        Heuristic filter to determine if extracted text is valid and not just noise

        The heuristic checks:
            - Minimum text length (≥30 characters)
            - Ratio of non-alphanumeric symbols (≤ 0.4 allowed)

        Args:
            text (str): Extracted text content to validate

        Returns:
            bool: True if the text seems meaningful, False otherwise
    """
    ## Strip spaces and newlines
    clean = text.strip()

    ## Reject too short text
    if len(clean) < 30:
        return False

    ## Calculate symbol density
    noise_ratio = len(re.findall(r"[^a-zA-Z0-9\s.,;:!?%€$@()\-]", clean)) / max(len(clean), 1)

    ## Reject if too many special symbols
    if noise_ratio > 0.4:
        return False

    return True

## ============================================================
## DIRECT EXTRACTION METHODS
## ============================================================
@log_execution_time_and_path
def extract_text_with_tika(pdf_path: Path) -> str:
    """
        Extract text using Apache Tika parser

        Args:
            pdf_path (Path): Path to the input PDF file

        Returns:
            str: Extracted text content
    """
    try:
        ## Call Tika parser on the file
        result = parser.from_file(str(pdf_path))
        text = result.get("content", "") or ""
        logger.info(f"Tika extracted {len(text)} chars from {pdf_path.name}")
        return text
    except Exception as e:
        logger.error(f"Tika failed on {pdf_path.name}: {e}")
        return ""

@log_execution_time_and_path
def extract_text_with_pypdf2(pdf_path: Path) -> str:
    """
        Extract text using PyPDF2 pure Python library

        Args:
            pdf_path (Path): Path to the input PDF file

        Returns:
            str: Extracted text content
    """
    try:
        ## Initialize PDF reader
        reader = PdfReader(pdf_path)

        ## Extract text page by page
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

        logger.info(f"PyPDF2 extracted {len(text)} chars from {pdf_path.name}")
        return text
    except Exception as e:
        logger.error(f"PyPDF2 failed on {pdf_path.name}: {e}")
        return ""

@log_execution_time_and_path
def extract_text_with_pdftotext(pdf_path: Path) -> str:
    """
        Extract text using pdftotext (Poppler backend)

        Args:
            pdf_path (Path): Path to the input PDF file

        Returns:
            str: Extracted text content
    """
    try:
        ## Open PDF in binary mode
        with open(pdf_path, "rb") as f:
            pdf = pdftotext.PDF(f)

        ## Join all pages together
        text = "\n\n".join(pdf)
        logger.info(f"pdftotext extracted {len(text)} chars from {pdf_path.name}")
        return text
    except Exception as e:
        logger.error(f"pdftotext failed on {pdf_path.name}: {e}")
        return ""

## ============================================================
## PDF → IMAGE CONVERSION
## ============================================================
@log_execution_time_and_path
def convert_pdf_to_images(pdf_path: Path, dpi: int = 500) -> List[Path]:
    """
        Convert each page of a PDF into a high-resolution PNG image for OCR

        Args:
            pdf_path (Path): Input PDF file path
            dpi (int): Output image resolution in DPI (default 500)

        Returns:
            List[Path]: List of image paths (one per page)
    """
    image_paths: List[Path] = []

    try:
        CONVERTED_DIR.mkdir(parents=True, exist_ok=True)

        ## Convert all pages using pdf2image
        pages = pdf2image.convert_from_path(str(pdf_path), dpi=dpi)

        ## Save each page as PNG in converted directory
        for i, page in enumerate(pages, start=1):
            img_path = CONVERTED_DIR / f"{pdf_path.stem}_page{i:03d}.png"
            page.save(img_path, "PNG")
            image_paths.append(img_path)
            logger.debug(f"Created page image: {img_path}")

        logger.info(f"{len(image_paths)} page(s) converted from {pdf_path.name}")

    except Exception as e:
        logger.error(f"Failed to convert {pdf_path.name} to images: {e}")

    return image_paths

## ============================================================
## OCR FALLBACK (TESSERACT + GOOGLE VISION)
## ============================================================
@log_execution_time_and_path
def perform_ocr_on_images(image_paths: List[Path]) -> str:
    """
        Run OCR on a list of image files using Tesseract and/or Google Vision

        Args:
            image_paths (List[Path]): Paths to images (one per PDF page)

        Returns:
            str: Combined OCR text from all pages
    """
    ocr_texts: List[str] = []

    for img_path in image_paths:
        text = ""

        ## Try Tesseract first
        if USE_TESSERACT:
            text = ocr_with_tesseract(img_path)

        ## Fallback to Vision if needed
        if not text.strip() and USE_GOOGLE_VISION:
            logger.info(f"Tesseract empty on {img_path.name}, using Google Vision.")
            text = ocr_with_google_vision(img_path)

        ocr_texts.append(text)

    return "\n\n".join(ocr_texts)

## ============================================================
## MAIN PIPELINE
## ============================================================
@log_execution_time_and_path
def process_pdf_file(src_path: str) -> None:
    """
        Full pipeline for extracting text from a PDF:
            1. Check size limit to avoid heavy memory usage
            2. Try Tika, PyPDF2, and pdftotext sequentially
            3. Validate text quality using heuristics
            4. If invalid → convert pages to PNG images
            5. Perform OCR (Tesseract, then Vision fallback)
            6. Save text to data/output/

        Args:
            src_path (str): File path complet to process
    """
    
    ## Build path to PDF
    #pdf_path = INPUT_DIR / file_name
    if not os.path.exists(str(src_path)):
        logger.error(f"File not found: {src_path}")
        return

    ## Check file size before processing
    pdf_size_mb = src_path.stat().st_size / (1024 * 1024)
    if pdf_size_mb > MAX_PDF_SIZE_MB:
        logger.warning(
            f"Skipping {src_path.name}: size {pdf_size_mb:.2f} MB exceeds limit ({MAX_PDF_SIZE_MB} MB)."
        )
        return

    logger.info(f"Processing PDF: {src_path.name}")

    ## ========================================================
    ## STEP 1: Direct extraction attempts
    ## ========================================================
    text = ""

    if USE_TIKA:
        text = extract_text_with_tika(src_path)

    if not is_text_valid(text) and USE_PYPDF2:
        text = extract_text_with_pypdf2(src_path)

    if not is_text_valid(text) and USE_PDFTOTEXT:
        text = extract_text_with_pdftotext(src_path)

    ## ========================================================
    ## STEP 2: If text is invalid → Fallback to OCR
    ## ========================================================
    if not is_text_valid(text):
        logger.warning(f"Direct extraction failed or noisy for {file_name}, switching to OCR.")

        if USE_PDF2IMAGE:
            image_paths = convert_pdf_to_images(src_path, dpi=500)
            if image_paths:
                text = perform_ocr_on_images(image_paths)
            else:
                logger.error(f"No images generated for OCR from {src_path.name}")
                return
        else:
            logger.error(f"PDF2Image disabled, OCR fallback not available for {file_name}")
            return

    ## ========================================================
    ## STEP 3: Save final text result
    ## ========================================================
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    out_path = OUTPUT_DIR / f"{src_path.stem}.txt"
    try:
        with io.open(out_path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(text)
        logger.info(f"Text successfully saved: {out_path}")
    except Exception as e:
        logger.exception(f"Error saving text for {src_path.name}: {e}")

## ============================================================
## MAIN ENTRY POINT (CLI)
## ============================================================
if __name__ == "__main__":
    """
        CLI usage:
            python pdf_to_text.py <pdf_file>

        Example:
            python pdf_to_text.py contract.pdf
    """
    
    ## Validate input argument
    if len(sys.argv) < 2:
        logger.error("Usage: python pdf_to_text.py <pdf_file>")
        sys.exit(1)

    ## Get file name from command line
    pdf_file = sys.argv[1]

    ## Measure total runtime
    start_time = time.time()
    process_pdf_file(pdf_file)
    duration = time.time() - start_time

    logger.info(f"Completed in {duration:.2f}s for {pdf_file}")

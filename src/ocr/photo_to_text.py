'''
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.0.0"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Prod"
__desc__ = "OCR extraction from image/PDF files using Tesseract first, with Google Vision fallback. Uses data/input, data/converted, data/output."
'''
from __future__ import annotations

import os
import io
import sys
import time
from pathlib import Path
from typing import Optional, TYPE_CHECKING

import pytesseract
from PIL import Image

# try:
    # from google.cloud import vision
# except Exception:
    # vision = None
try:
    from google.cloud import vision
except Exception:
    vision = None

if TYPE_CHECKING:
    from google.cloud.vision import ImageAnnotatorClient  # type: ignore
    
from src.utils import get_logger, log_execution_time_and_path
from src.utils.constants import (
    INPUT_DIR,
    CONVERTED_DIR,
    OUTPUT_DIR,
    PATH_LIBRE_OFFICE,
    ALLOWED_EXTENSIONS,
    USE_TESSERACT,
    USE_GOOGLE_VISION
)

## ============================================================
## LOGGER
## ============================================================
logger = get_logger("photo_to_text")

## ============================================================
## GOOGLE VISION INITIALIZATION
## ============================================================
def _init_google_vision_client() -> Optional["ImageAnnotatorClient"]:
#def _init_google_vision_client() -> Optional[vision.ImageAnnotatorClient]:
    """
        Initialize Google Vision client if library and credentials are available

        Returns:
            Optional[vision.ImageAnnotatorClient]: Vision client or None if unavailable
    """
    
    ## Ensure the library is importable and creds are present
    if vision is None:
        logger.warning("google-cloud-vision not available. Skipping Vision fallback.")
        return None

    ## Instantiate client (uses env var GOOGLE_APPLICATION_CREDENTIALS)
    try:
        client = vision.ImageAnnotatorClient()
        logger.info("Google Vision client initialized.")
        return client
    except Exception as exc:
        logger.error(f"Cannot init Google Vision client: {exc}")
        return None

## ============================================================
## IMAGE NORMALIZATION / CONVERSION
## ============================================================
@log_execution_time_and_path
def convert_image_for_ocr(src_path: Path) -> Path:
    """
        Normalize image to a Tesseract-friendly format
            - TIFF/TIF → PNG via Pillow
            - SVG → PNG via LibreOffice (headless)
            - PDF → keep as-is (Tesseract can handle PDFs page-by-page if configured externally)
            - Others → unchanged

        Args:
            src_path (Path): Source file path from data/input

        Returns:
            Path: Path to the normalized/converted file (inside data/converted when applicable)
    """
    
    ## Determine lowercase extension
    ext = src_path.suffix.lower()

    ## Target normalized path (PNG) inside converted folder
    png_target = CONVERTED_DIR / f"{src_path.stem}.png"

    try:
        ## Convert TIFF → PNG using Pillow
        if ext in [".tif", ".tiff"]:
            
            img = Image.open(src_path)
            img.save(png_target, "PNG")
            logger.info(f"Converted TIFF to PNG: {png_target}")
            
            return png_target

        ## Convert SVG → PNG using LibreOffice
        if ext == ".svg": 
 
            ## Ensure LibreOffice path is set
            if not PATH_LIBRE_OFFICE:
                logger.warning("PATH_LIBRE_OFFICE not set — skipping SVG conversion.")
                return src_path
            
            ## Build LO cmd
            CONVERTED_DIR.mkdir(parents=True, exist_ok=True)
            cmd = f'{PATH_LIBRE_OFFICE} --headless --convert-to png "{src_path}" --outdir "{CONVERTED_DIR}"'
            logger.info(f"Converting SVG via LibreOffice: {cmd}")
            os.system(cmd)
 
            ## Check result 
            if png_target.exists():
                logger.info(f"SVG converted to PNG: {png_target}")
                return png_target
            
            logger.error(f"SVG conversion failed, using original: {src_path}")
            return src_path

        ## Keep PDF, PNG, JPG, JPEG, BMP as-is
        return src_path

    except Exception as exc:
        logger.exception(f"Conversion failed for {src_path}: {exc}")
        return src_path

## ============================================================
## OCR ENGINES
## ============================================================
@log_execution_time_and_path
def ocr_with_tesseract(img_path: Path) -> str:
    """
        Extract text using Tesseract OCR (multi-lang: eng+fra)

        Args:
            img_path (Path): Path to image/PDF

        Returns:
            str: Extracted text, empty string if none
    """
    
    ## Load image (Pillow supports many raster formats)
    try:
        img = Image.open(img_path)
        text = pytesseract.image_to_string(img, lang="eng+fra")
        text = text.strip()
        
        if text:
            logger.info(f"Tesseract extracted text from: {img_path.name}")
        else:
            logger.warning(f"Tesseract returned empty text: {img_path.name}")
        return text

    except Exception as exc:
        logger.error(f"Tesseract OCR error on {img_path}: {exc}")
        return ""
        
@log_execution_time_and_path
def ocr_with_google_vision(img_path: Path) -> str:
    """
        Extract text using Google Vision OCR (fallback)

        Args:
            img_path (Path): Path to image/PDF

        Returns:
            str: Extracted text, empty string if none
    """
   
    ## Try to get client   
    client = _init_google_vision_client()
    if client is None:
        return ""

    try:
        ## Open file in binary mode
        with io.open(img_path, "rb") as f:
            content = f.read()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        
        ## Check API-level errors
        if response.error.message:
            logger.error(f"Vision API error: {response.error.message}")
            return ""
            
        annotations = response.text_annotations or []
        
        if not annotations:
            logger.warning(f"Vision found no text in: {img_path.name}")
            return ""
        
        ## Full text
        text = (annotations[0].description or "").strip()
        
        if text:
            logger.info(f"Vision extracted text from: {img_path.name}")  ## OK
        return text
    
    except Exception as exc:
        logger.error(f"Vision OCR error on {img_path}: {exc}")  ## Log failure
        return ""

## ============================================================
## SAVE OUTPUT
## ============================================================
def _save_text(stem: str, text: str) -> Path:
    """
        Save text into data/output/<stem>.txt

        Args:
            stem (str): Base name (no extension) for the output file
            text (str): Text content to save

        Returns:
            Path: Path to the saved .txt file
    """
    
    ## Ensure output folder exists and build output path
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{stem}.txt"
   
    with open(out_path, "w", encoding="utf-8", errors="ignore") as f:
        f.write(text)
    
    logger.info(f"Saved OCR text: {out_path}")
    
    return out_path

## ============================================================
## MAIN PIPELINE
## ============================================================
@log_execution_time_and_path
def process_image_file(src_path: str) -> None:
    """
        Full pipeline for a single input file:
            - Resolve data/input/<file>
            - Normalize/convert if needed (e.g., TIFF/SVG → PNG)
            - OCR with Tesseract first, then Vision fallback
            - Save to data/output/<stem>.txt

        Args:
            src_path (str): File path complet to process
    """
    
    ## Resolve source path
    # src_path = INPUT_DIR / file_name
    if not os.path.exists(str(src_path)):
        logger.error(f"Input not found: {src_path}")
        return

    ## Basic extension guard (images/PDF only)
    ext = src_path.suffix.lower().lstrip(".") 
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"Unsupported extension '{ext}' for: {src_path.name}")
        return

    ## Prepare normalized asset for OCR
    norm_path = convert_image_for_ocr(src_path)

    ## Prefer Tesseract first as requested
    text = ""
    if USE_TESSERACT:
        text = ocr_with_tesseract(norm_path)
        
    ## Fallback to Google Vision if needed and allowed
    if (not text) and USE_GOOGLE_VISION:
        logger.info(f"Falling back to Google Vision for: {norm_path.name}")
        text = ocr_with_google_vision(norm_path)

    ## Store or report failure
    if text:
        _save_text(src_path.stem, text)
    else:
        logger.error(f"No OCR text extracted from: {src_path.name}")

## ============================================================
## MAIN ENTRY POINT (CLI)
## ============================================================
if __name__ == "__main__":
    """
        CLI usage:
            python photo_to_text.py <image_or_pdf>
        Example:
            python photo_to_text.py invoice_scan.tiff
    """
    
    ## Validate presence of an argument
    if len(sys.argv) < 2:
        logger.error("Usage: python photo_to_text.py <image_or_pdf>")
        sys.exit(1)

    ## Run pipeline on the provided file
    arg = sys.argv[1]
    start = time.time()
    process_image_file(arg)
    elapsed = time.time() - start
    logger.info(f"OCR finished in {elapsed:.2f}s for: {arg}")

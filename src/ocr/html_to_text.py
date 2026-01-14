'''
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.0.0"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Prod"
__desc__ = "Extract text from HTML/HTM/MHT files using BeautifulSoup, html2text, or urllib."
'''

import os
import io
import sys
import time
from pathlib import Path
from bs4 import BeautifulSoup
import html2text
import urllib.request

from src.utils import get_logger, log_execution_time_and_path
from src.utils.constants import (
    INPUT_DIR,
    CONVERTED_DIR,
    OUTPUT_DIR,
    USE_HTML2TEXT,
    USE_URLLIB,
    USE_BEAUTIFULSOUP
)

## ============================================================
## LOGGER INITIALIZATION
## ============================================================
logger = get_logger("html_to_text")

## ============================================================
## FUNCTION: Resolve input path
## ============================================================
@log_execution_time_and_path
def resolve_input_path(file_name: str) -> Path:
    """
        Resolve the absolute path of a file by checking both input and converted directories

        Args:
            file_name (str): Name of the file to resolve

        Returns:
            Path: Path to the file if found, None otherwise
    """
    
    ## Check input directory first
    candidate = INPUT_DIR / file_name
    if candidate.exists():
        logger.debug(f"Resolved path in input: {candidate}")
        return candidate

    ## Then check converted directory
    candidate = CONVERTED_DIR / file_name
    if candidate.exists():
        logger.debug(f"Resolved path in converted: {candidate}")
        return candidate

    ## Log error if not found
    logger.error(f"File not found in input or converted: {file_name}")
    
    return None

## ============================================================
## FUNCTION: Build output path
## ============================================================
@log_execution_time_and_path
def build_output_path(source_path: Path) -> Path:
    """
        Build output TXT path in the output directory based on the input file name

        Args:
            source_path (Path): Source HTML file path

        Returns:
            Path: Destination path for TXT output
    """
    
    ## Create output path with same stem as input
    out_path = OUTPUT_DIR / f"{source_path.stem}.txt"
    logger.debug(f"Output path built: {out_path}")
    
    return out_path

## ============================================================
## FUNCTION: Extract text from HTML
## ============================================================
@log_execution_time_and_path
def html_to_text(source_path: Path) -> str:
    """
        Extract plain text content from an HTML/HTM file using the enabled flag:
            - BeautifulSoup
            - html2text
            - urllib fallback

        Args:
            source_path (Path): Path to the HTML file

        Returns:
            str: Extracted plain text
    """
    
    try:
        ## Read HTML file content
        html_content = source_path.read_text(encoding="utf-8", errors="ignore")

        ## ============================================================
        ## Strategy 1: BeautifulSoup (default)
        ## ============================================================
        if USE_BEAUTIFULSOUP:
            logger.info("Using BeautifulSoup for HTML parsing")
            soup = BeautifulSoup(html_content, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            return text.strip()

        ## ============================================================
        ## Strategy 2: html2text
        ## ============================================================
        elif USE_HTML2TEXT:
            logger.info("Using html2text for HTML parsing")
            text = html2text.html2text(html_content)
            return text.strip()

        ## ============================================================
        ## Strategy 3: urllib (basic extraction)
        ## ============================================================
        elif USE_URLLIB:
            logger.info("Using urllib fallback for HTML parsing")
            with urllib.request.urlopen(f"file://{source_path}") as response:
                data = response.read().decode("utf-8", errors="ignore")
                text = BeautifulSoup(data, "html.parser").get_text(separator="\n", strip=True)
                return text.strip()

        ## ============================================================
        ## Default fallback
        ## ============================================================
        else:
            logger.warning("No HTML extraction method enabled. Returning empty string.")
            return ""

    except Exception as exc:
        logger.exception(f"Failed to extract HTML text from {source_path}: {exc}")
        return ""

## ============================================================
## FUNCTION: Save extracted text
## ============================================================
@log_execution_time_and_path
def save_text(text: str, out_path: Path) -> None:
    """
        Save the extracted text into a UTF-8 encoded TXT file

        Args:
            text (str): Extracted plain text content
            out_path (Path): Output path for the TXT file
    """
    
    ## Write the text to the file safely
    with io.open(out_path, "w", encoding="utf-8", errors="ignore") as f:
        f.write(text)
    
    logger.info(f"Text saved successfully to: {out_path}")

## ============================================================
## PIPELINE: Process HTML file
## ============================================================
@log_execution_time_and_path
def process_html(src_path: str) -> None:
    """
        Full pipeline for HTML/HTM/MHT files:
            - Resolve file path
            - Extract text
            - Save output file

        Args:
            src_path (str): File path complet to process
    """
    
    ## Resolve the file path
    # src = resolve_input_path(src_path)
    if not os.path.exists(str(src_path)):
        return

    ## Extract text
    text = html_to_text(src_path)

    ## Build output path
    out_path = build_output_path(src_path)

    ## Save text to output
    save_text(text, out_path)

## ============================================================
## MAIN ENTRY POINT
## ============================================================
if __name__ == "__main__":
    """
        Command-line entry point for HTML/HTM/MHT text extraction
    """
    
    ## Ensure a file name is provided
    if len(sys.argv) < 2:
        logger.error("Usage: python html_to_txt.py <file_name.html|file_name.htm|file_name.mht>")
        sys.exit(1)

    ## Measure total runtime
    file_arg = sys.argv[1]
    start = time.time()

    ## Execute processing pipeline
    process_html(file_arg)

    ## Log total elapsed time
    elapsed = time.time() - start
    logger.info(f"HTML extraction completed in {elapsed:.2f} seconds")
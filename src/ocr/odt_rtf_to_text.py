'''
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.0.0"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Prod"
__desc__ = "Extract text from ODT and RTF files and save as UTF-8 TXT in data/output."
'''
import os
import io
import sys
import time
import subprocess
from pathlib import Path
from typing import Optional

from odf.opendocument import load as odf_load
from odf import teletype
from striprtf.striprtf import rtf_to_text

from src.utils.constants import INPUT_DIR, CONVERTED_DIR, OUTPUT_DIR, PATH_LIBRE_OFFICE
from src.utils import get_logger, log_execution_time_and_path

## ============================================================
## LOGGER INITIALIZATION
## ============================================================
logger = get_logger("odt_rtf_to_text")

## ============================================================
## FUNCTION: Resolve input path
## ============================================================
@log_execution_time_and_path
def resolve_input_path(file_name: str) -> Optional[Path]:
    """
        Resolve the absolute path of a file by checking both input and converted directories

        Args:
            file_name (str): Name of the file to resolve

        Returns:
            Optional[Path]: Absolute path if found, None otherwise
    """
    
    ## Check if file exists in input directory
    candidate = INPUT_DIR / file_name
    if candidate.exists():
        logger.debug(f"Resolved path in input: {candidate}")
        return candidate

    ## Check if file exists in converted directory
    candidate = CONVERTED_DIR / file_name
    if candidate.exists():
        logger.debug(f"Resolved path in converted: {candidate}")
        return candidate

    ## Log error if file is missing
    logger.error(f"File not found in input or converted: {file_name}")
    return None

## ============================================================
## FUNCTION: Build output path
## ============================================================
@log_execution_time_and_path
def build_output_path(source_path: Path) -> Path:
    """
        Build an output TXT path in the output directory based on the input file name

        Args:
            source_path (Path): Path of the source file

        Returns:
            Path: Target path for the generated TXT file
    """
    
    ## Construct the output file path
    out_path = OUTPUT_DIR / f"{source_path.stem}.txt"
    logger.debug(f"Output path built: {out_path}")
    
    return out_path

## ============================================================
## FUNCTION: Extract text from ODT
## ============================================================
@log_execution_time_and_path
def odt_to_text(source_path: Path) -> str:
    """
        Extract plain text content from an ODT file using odfpy

        Args:
            source_path (Path): Path to the ODT file

        Returns:
            str: Extracted plain text content
    """
    
    try:
        ## Load the ODT document
        doc = odf_load(str(source_path))

        ## Extract plain text content
        text_content = teletype.extractText(doc.text)

        ## Return text or empty string if nothing extracted
        return text_content if text_content else ""
    except Exception as exc:
        logger.exception(f"Failed to process ODT file {source_path}: {exc}")
        return ""

## ============================================================
## FUNCTION: Extract text from RTF
## ============================================================
@log_execution_time_and_path
def rtf_to_text_safe(source_path: Path) -> str:
    """
        Extract plain text from an RTF file using striprtf

        Args:
            source_path (Path): Path to the RTF file

        Returns:
            str: Extracted plain text content
    """
    
    try:
        ## Read file safely with UTF-8 encoding
        data = source_path.read_text(encoding="utf-8", errors="ignore")

        ## Convert RTF markup to plain text
        text_content = rtf_to_text(data)

        ## Return text or empty string
        return text_content if text_content else ""
    except Exception as exc:
        logger.exception(f"Failed to process RTF file {source_path}: {exc}")
        return ""

## ============================================================
## FUNCTION: Convert to TXT using LibreOffice
## ============================================================
@log_execution_time_and_path
def convert_to_txt(file_path: Path) -> Optional[Path]:
    """
        Convert ODT or RTF file to plain text using LibreOffice (headless mode)

        Args:
            file_path (Path): Path of the source file

        Returns:
            Optional[Path]: Path to the converted TXT file or None on failure
    """
    
    try:
        output_path = CONVERTED_DIR / f"{file_path.stem}.txt"
        cmd = [
            "soffice",
            "--headless",
            "--convert-to",
            "txt:Text",
            "--outdir",
            str(CONVERTED_DIR),
            str(file_path)
        ]

        ## Run LibreOffice conversion securely
        result = subprocess.run(cmd, capture_output=True, text=True)

        ## Handle conversion failure
        if result.returncode != 0:
            logger.error(f"LibreOffice conversion failed: {result.stderr.strip()}")
            return None

        ## Verify the output file exists
        if not output_path.exists():
            logger.error(f"Expected converted file not found: {output_path}")
            return None

        logger.info(f"Conversion successful: {output_path}")
        return output_path

    except Exception as exc:
        logger.exception(f"Error converting {file_path} with LibreOffice: {exc}")
        return None

## ============================================================
## FUNCTION: Save extracted text
## ============================================================
@log_execution_time_and_path
def save_text(text: str, out_path: Path) -> None:
    """
        Save the extracted text into a UTF-8 encoded TXT file

        Args:
            text (str): Extracted plain text to save
            out_path (Path): Destination file path
    """
    
    ## Skip empty output
    if not text.strip():
        logger.warning(f"Attempted to save empty text file: {out_path}")
        return
    
    ## Write text content to a file
    with io.open(out_path, "w", encoding="utf-8", errors="ignore") as f:
        f.write(text)
        
    logger.info(f"Text saved successfully to: {out_path}")

## ============================================================
## PIPELINE: Process ODT file
## ============================================================
@log_execution_time_and_path
def process_odt(src_path: str) -> None:
    """
        Full pipeline for ODT files:
            - Resolve path
            - Extract text
            - Save output

        Args:
            src_path (str): File path complet to process
    """
    
    ## Resolve the source file path
    if not os.path.exists(str(src_path)):
        logger.error(f"File not found: {src_path}")
        return

    ## Extract and save text
    text = odt_to_text(src_path)
    out_path = build_output_path(src_path)
    save_text(text, out_path)

## ============================================================
## PIPELINE: Process RTF file
## ============================================================
@log_execution_time_and_path
def process_rtf(src_path: str) -> None:
    """
        Full pipeline for RTF files:
            - Resolve path
            - Extract text
            - Save output

        Args:
            src_path (str): File path complet to process
    """
    
    ## Resolve the source file path
    # src = resolve_input_path(file_name)
    if not os.path.exists(str(src_path)):
        logger.error(f"File not found: {src_path}")
        return

    ## Extract and save text
    text = rtf_to_text_safe(src_path)
    out_path = build_output_path(src_path)
    save_text(text, out_path)

## ============================================================
## MAIN ENTRY POINT
## ============================================================
if __name__ == "__main__":
    """
        Command-line entry point for processing ODT and RTF files
    """
    
    ## Ensure at least one argument is passed
    if len(sys.argv) < 2:
        logger.error("Usage: python odt_rtf_to_text.py <file_name.odt|file_name.rtf>")
        sys.exit(1)

    ## Start execution timer
    file_arg = sys.argv[1]
    start = time.time()

    ## Dispatch based on file extension
    if file_arg.lower().endswith(".odt"):
        process_odt(file_arg)
    elif file_arg.lower().endswith(".rtf"):
        process_rtf(file_arg)
    else:
        logger.error("Unsupported file extension. Use .odt or .rtf only.")
        sys.exit(1)

    ## Log elapsed time
    elapsed = time.time() - start
    logger.info(f"Processing completed in {elapsed:.2f} seconds")
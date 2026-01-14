'''
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.0.0"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Prod"
__desc__ = "Global OCR configuration, constants, encoding detection, and path initialization for all document processing modules."
'''

import os
import platform
import secrets
from pathlib import Path
import chardet
from src.utils import get_logger
from src.utils.constants import (
    BASE_DIR,
    INPUT_DIR,
    CONVERTED_DIR,
    OUTPUT_DIR,
    ALLOWED_EXTENSIONS,
    ENCODINGS_TO_TRY,
    PRUNE_AFTER_PROCESS
)

## ============================================================
## LOGGER INITIALIZATION
## ============================================================

logger = get_logger("ocr_utils")

## ============================================================
## HELPER FUNCTIONS
## ============================================================
def get_base_dir() -> Path:
    """
        Return the absolute base directory of the project

        Returns:
            Path: The project's base directory
    """
    
    return BASE_DIR

def get_data_dirs() -> dict:
    """
        Return a dictionary with paths to input, converted, and output folders

        Returns:
            dict: Paths of data directories
    """
    
    return {
        "input": INPUT_DIR,
        "converted": CONVERTED_DIR,
        "output": OUTPUT_DIR,
    }


def is_allowed_file(filename: str) -> bool:
    """
        Check whether the given file has an allowed extension

        Args:
            filename (str): File name to validate

        Returns:
            bool: True if extension is allowed, False otherwise
    """
    
    ## Extract file extension
    ext = filename.lower().split(".")[-1]

    ## Check if extension is allowed
    allowed = ext in ALLOWED_EXTENSIONS
    logger.debug(f"File '{filename}' allowed: {allowed}")

    return allowed

def generate_unique_filename(file_path: Path) -> Path:
    """
        Generate a unique filename if the same name already exists
        in input, converted, or output directories

        Args:
            file_path (Path): Original file path (e.g. data/input/toto.pdf)

        Returns:
            Path: Unique file path (e.g. data/input/toto_XCEZFV.pdf)
    """
    
    ## Extract filename components
    base_name = file_path.stem
    ext = file_path.suffix

    ## List of all directories to check for name collisions
    all_dirs = [INPUT_DIR, CONVERTED_DIR, OUTPUT_DIR]

    ## If conflict found, append random suffix until name is unique
    while any((d / f"{base_name}{ext}").exists() for d in all_dirs):
        random_tag = "_" + secrets.token_hex(3).upper()
        base_name = file_path.stem + random_tag

    ## Construct new file path with unique name
    new_path = file_path.parent / f"{base_name}{ext}"
    logger.debug(f"Generated unique filename: {new_path}")

    return new_path

## ============================================================
## SAFE TEXT FILE READING WITH ENCODING DETECTION
## ============================================================
def read_text_file_safely(path_file: str, log_path: str = "identified_files_bugs.txt") -> str:
    """
        Safely read a text file by trying multiple encodings until one works correctly

        The function:
            1. Uses chardet to get an initial guess of the encoding
            2. Iteratively tries a list of common encodings from ENCODINGS_TO_TRY
            3. Falls back to UTF-8 with errors ignored if all attempts fail
            4. Logs empty or unreadable files into a text log

        Args:
            path_file (str): Path to the text file to read
            log_path (str): Path of the log file where unreadable files are stored

        Returns:
            str: File content decoded to UTF-8 string
    """

    ## Initialize variables
    text_content = ""
    detected_encoding = None

    ## Step 1: Try to detect encoding using chardet (best-effort guess)
    try:
        with open(path_file, "rb") as f:
            raw_data = f.read(4096)
        guess = chardet.detect(raw_data)
        
        if guess and guess.get("encoding"):
            if guess["encoding"] not in ENCODINGS_TO_TRY:
                ENCODINGS_TO_TRY.insert(0, guess["encoding"])
            detected_encoding = guess["encoding"]
            logger.debug(f"Chardet suggests {detected_encoding} for {path_file}")
            
    except Exception as e:
        logger.warning(f"Failed to detect encoding for {path_file}: {e}")

    ## Step 2: Try all encodings one by one
    for enc in ENCODINGS_TO_TRY:
        try:
            with open(path_file, "r", encoding=enc) as infile:
                text = infile.read()

                ## Check for excessive replacement characters (indicating bad decoding)
                if text.count("�") / max(len(text), 1) > 0.01:
                    logger.debug(f"Encoding {enc} produced noise for {path_file}")
                    continue

                ## If decoding succeeded, store and break
                text_content = text
                detected_encoding = enc
                logger.info(f"Successfully read {path_file} with encoding: {enc}")
                break

        except Exception:
            continue

    ## Step 3: Fallback - try UTF-8 with ignore option
    if not text_content:
        try:
            with open(path_file, "r", encoding="utf-8", errors="ignore") as infile:
                text_content = infile.read()
                detected_encoding = "utf-8 (ignore errors)"
                logger.info(f"Fallback UTF-8 (ignore errors) used for {path_file}")
        except Exception as e:
            logger.error(f"All encoding attempts failed for {path_file}: {e}")
            text_content = ""

    ## Step 4: Log empty or unreadable files
    if len(text_content.strip()) == 0:
        try:
            with open(log_path, "a", encoding="utf-8") as log_file:
                print(f"Empty or unreadable file: {path_file}", file=log_file)
            logger.warning(f"File is empty or unreadable, logged: {path_file}")
        except Exception as e:
            logger.error(f"Could not write to log file {log_path}: {e}")

    ## Return text content (UTF-8 normalized)
    return text_content
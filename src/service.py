'''
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.0.0"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Prod"
__desc__ = "FastAPI service providing OCR conversion endpoints for multiple document types."
'''

import os
import shutil
from pathlib import Path
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from src.utils import get_logger
from src.utils.ocr_utils import (
    get_data_dirs,
    is_allowed_file,
    generate_unique_filename
)
from src.utils.constants import PRUNE_AFTER_PROCESS
from src.ocr import (
    docx_doc_to_text,
    pptx_ppt_to_text,
    xlsx_xls_to_text,
    html_to_text,
    pdf_to_text,
    photo_to_text,
    odt_rtf_to_text
)

## ============================================================
## LOGGER INITIALIZATION
## ============================================================

## Initialize logger for FastAPI service
logger = get_logger("service")

## ============================================================
## FASTAPI APP INITIALIZATION
## ============================================================
app = FastAPI(
    title="OCR Universal API",
    description="Convert documents of multiple formats into text via OCR or parsing.",
    version="1.0.0"
)

## ============================================================
## HELPER FUNCTION
## ============================================================
def extract_text_from_file(file_path: Path) -> str:
    """
        Detect file type and extract text accordingly

        Args:
            file_path (Path): Path to file to process

        Returns:
            str: Extracted text content
    """

    ext = file_path.suffix.lower()
    text = ""

    try:
        ## DOC / DOCX
        if ext in [".docx", ".doc"]:
            text = docx_doc_to_text.process_doc_or_docx(file_path)
        ## PPT / PPTX
        elif ext in [".pptx", ".ppt"]:
            text = pptx_ppt_to_text.process_presentation(file_path)
        ## XLS / XLSX
        elif ext in [".xls", ".xlsx"]:
            text = xlsx_xls_to_text.process_excel_file(file_path)
        ## PDF
        elif ext == ".pdf":
            text = pdf_to_text.process_pdf_file(file_path)

        elif ext in [".odt"]:
            text = odt_rtf_to_text.process_odt(file_path)
        
        elif ext in [".rtf"]:
            text = odt_rtf_to_text.process_rtf(file_path)
            
        ## HTML / HTM
        elif ext in [".html", ".htm", ".mht"]:
            text = html_to_text.process_html(file_path)
        ## IMAGE FORMATS
        elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"]:
            normalized_path = photo_to_text.convert_image_for_ocr(file_path)
            text = photo_to_text.ocr_with_tesseract(normalized_path)
        ## TXT
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as infile:
                text = infile.read()
        else:
            logger.warning(f"Unsupported file extension: {ext}")
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")

    return text

## ============================================================
## ROUTE: HEALTH CHECK
## ============================================================
@app.get("/healthcheck")
def health_check():
    """
        Simple route to verify the API is alive and responsive

        Returns:
            dict: Status message
    """
    
    logger.debug("Health check endpoint called.")
    
    # return {"status": "ok", "message": "OCR Universal API is running."}
    return {"status": "ok"}

## ============================================================
## ROUTE: SINGLE FILE CONVERSION
## ============================================================
@app.post("/convert")
async def convert_file(file: UploadFile = File(...)):
    """
        Convert a single uploaded file into extracted text.

        Args:
            file (UploadFile): Uploaded document.

        Returns:
            dict: File name and extracted text.
    """

    dirs = get_data_dirs()
    input_dir = dirs["input"]
    output_dir = dirs["output"]

    ## Validate file type
    if not is_allowed_file(file.filename):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")

    ## Generate safe unique name and save file
    original_path = input_dir / file.filename
    unique_path = generate_unique_filename(original_path)
    with open(unique_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    logger.info(f"File uploaded: {unique_path}")

    ## Extract text
    text = extract_text_from_file(unique_path)

    ## Save output
    output_path = output_dir / f"{unique_path.stem}.txt"
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(text)
    logger.info(f"Saved text to {output_path}")

    ## Prune if enabled
    if PRUNE_AFTER_PROCESS:
        try:
            os.remove(unique_path)
            logger.debug(f"Pruned temporary file: {unique_path}")
        except Exception:
            pass

    ## Return structured response
    return JSONResponse(content={
        "file_name": file.filename,
        "text": text
    })

## ============================================================
## ROUTE: MULTIPLE FILE CONVERSION (BATCH)
## ============================================================
@app.post("/convert_batch")
async def convert_batch(files: List[UploadFile] = File(...)):
    """
        Convert multiple uploaded files into extracted texts

        Args:
            files (List[UploadFile]): List of uploaded documents

        Returns:
            list: JSON list with file names and extracted texts
    """

    dirs = get_data_dirs()
    input_dir = dirs["input"]
    output_dir = dirs["output"]

    results = []

    for file in files:
        ## Validate extension
        if not is_allowed_file(file.filename):
            logger.warning(f"Unsupported file skipped: {file.filename}")
            continue

        ## Save unique copy
        original_path = input_dir / file.filename
        unique_path = generate_unique_filename(original_path)
        with open(unique_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.debug(f"File saved: {unique_path}")

        ## Extract text
        text = extract_text_from_file(unique_path)

        ## Save output
        output_path = output_dir / f"{unique_path.stem}.txt"
        with open(output_path, "w", encoding="utf-8") as out:
            out.write(text)
        logger.info(f"Output written: {output_path}")

        ## Optional cleanup
        if PRUNE_AFTER_PROCESS:
            try:
                os.remove(unique_path)
                logger.debug(f"Pruned file: {unique_path}")
            except Exception:
                pass

        ## Append result
        results.append({
            "file_name": file.filename,
            "text": text
        })

    return JSONResponse(content=results)
        
## ============================================================
## ROUTE: FOLDER CONVERSION (SERVER-SIDE)
## ============================================================
@app.post("/convert_folder")
async def convert_folder(folder_path: str):
    """
        Convert all supported files located in a given server-side folder

        Args:
            folder_path (str): Path to the folder containing files to process

        Returns:
            list: JSON list with file names and extracted texts
    """

    logger.info(f"Requested folder conversion: {folder_path}")

    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        logger.error(f"Invalid folder path: {folder}")
        raise HTTPException(status_code=400, detail="Invalid or unreadable folder path")

    dirs = get_data_dirs()
    output_dir = dirs["output"]

    results = []

    for file_path in folder.rglob("*"):
        if not file_path.is_file():
            continue

        ## Skip unsupported types
        if not is_allowed_file(file_path.name):
            logger.debug(f"Skipping unsupported file: {file_path}")
            continue

        try:
            text = extract_text_from_file(file_path)
            #output_path = output_dir / f"{file_path.stem}.txt"
            output_path = output_dir / f"{file_path.stem}{file_path.suffix}.txt"

            with open(output_path, "w", encoding="utf-8") as out:
                out.write(text)
            logger.info(f"Processed file: {file_path}")

            results.append({
                "file_name": file_path.name,
                "text": text
            })

            ## Optional cleanup
            if PRUNE_AFTER_PROCESS:
                try:
                    os.remove(file_path)
                    logger.debug(f"Pruned file: {file_path}")
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            continue

    if not results:
        raise HTTPException(status_code=400, detail="No valid files found in the folder")

    logger.info(f"Folder processing completed. {len(results)} file(s) processed.")
    return JSONResponse(content=results)

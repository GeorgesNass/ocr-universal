'''
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.0.0"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Prod"
__desc__ = "Convert XLS to XLSX and extract text using LibreOffice, pandas, and xlrd with optional detailed extraction."
'''

import os
import io
import sys
import time
import pandas as pd
import xlrd
from pathlib import Path
from typing import Optional
import subprocess

from src.utils import get_logger, log_execution_time_and_path
from src.utils.constants import (
    INPUT_DIR,
    CONVERTED_DIR,
    OUTPUT_DIR,
    CSV_SEPARATOR,
    CSV_EXTENSION,
    PATH_LIBRE_OFFICE,
    USE_DETAILED_EXCEL_EXTRACTION
)

## ============================================================
## LOGGER INITIALIZATION
## ============================================================

logger = get_logger("xlsx_xls_to_text")

## ============================================================
## FUNCTION: CONVERT XLS → XLSX
## ============================================================
@log_execution_time_and_path
def convert_xls_to_xlsx(src_path: str) -> Optional[str]:
    """
        Convert a .xls file into .xlsx using LibreOffice in headless mode

        Args:
            src_path (str): File path complet to the file

        Returns:
            Optional[str]: Path to converted .xlsx file, or None if failed
    """
    
    ## Keep homogeneous exists check (like PDF)
    if not os.path.exists(str(src_path)):
        logger.error(f"Source file not found: {src_path}")
        return None

    if not PATH_LIBRE_OFFICE:
        logger.warning("PATH_LIBRE_OFFICE not set — skipping XLS→XLSX conversion.")
        return None

    ## Normalize to Path only for stem building
    src_path = Path(src_path)

    cmd = f'"{PATH_LIBRE_OFFICE}" --headless --convert-to xlsx "{src_path}" --outdir "{CONVERTED_DIR}"'
    logger.info(f"Executing LibreOffice command: {cmd}")
    os.system(cmd)

    output_path = CONVERTED_DIR / f"{src_path.stem}.xlsx"

    if os.path.exists(str(output_path)):
        try:
            os.chmod(output_path, 0o777)
        except Exception:
            pass
        logger.info(f"Conversion successful: {output_path}")
        return str(output_path)

    logger.error(f"Conversion failed: {output_path} not found.")
    return None
    
## ============================================================
## FUNCTION: EXTRACT TEXT FROM XLSX
## ============================================================
@log_execution_time_and_path
def xlsx_to_text(source_file: str, output_file: str) -> None:
    """
        Convert an Excel file (.xlsx) into a tab-separated text file (.txt)

        Args:
            source_file (str): Path to the Excel file
            output_file (str): Path to save extracted text
    """
    
    try:
        ## =====================================================
        ## SIMPLE EXTRACTION MODE (default with pandas)
        ## =====================================================
        if not USE_DETAILED_EXCEL_EXTRACTION:
            logger.info("Using simple Excel extraction mode (pandas only)")
            df = pd.read_excel(source_file, dtype=str, engine="openpyxl")
            df = df.fillna("")
            df.to_csv(output_file, sep=CSV_SEPARATOR, encoding="utf-8", index=False)
            logger.info(f"Text successfully extracted to: {output_file}")
            return

        ## =====================================================
        ## DETAILED EXTRACTION MODE (fallback to xlrd)
        ## =====================================================
        else:
            logger.info("Using detailed Excel extraction mode (xlrd fallback enabled)")
            wb = xlrd.open_workbook(source_file, logfile=open(os.devnull, "w"))
            xl_sheet = wb.sheet_by_index(0)

            with io.open(output_file, "w", encoding="utf-8", errors="ignore") as file:
                for rownum in range(xl_sheet.nrows):
                    cells = []
                    for element in xl_sheet.row_values(rownum):
                        element = str(element).strip().replace(";", "")
                        cells.append(element)
                    file.write(CSV_SEPARATOR.join(cells) + "\n")

            logger.info(f"Detailed text extraction succeeded: {output_file}")

    except Exception as e:
        logger.exception(f"Primary extraction failed for {source_file}: {e}")
        try:
            ## Try alternate method if the first failed
            df = pd.read_excel(source_file, dtype=str, engine="openpyxl")
            df.to_csv(output_file, sep=CSV_SEPARATOR, encoding="utf-8", index=False)
            logger.warning(f"Fallback (pandas + xlrd) succeeded for: {source_file}")
        except Exception as e2:
            logger.error(f"All extraction methods failed for {source_file}: {e2}")

## ============================================================
## FUNCTION: GENERATE OUTPUT FILE PATH
## ============================================================
@log_execution_time_and_path
def create_output_file(file_path: Path) -> str:
    """
        Create clean .txt output path inside /data/output

        Args:
            file_path (Path): Input file path

        Returns:
            str: Generated .txt output path
    """
    
    out_path = OUTPUT_DIR / f"{file_path.stem}{CSV_EXTENSION}"
    logger.debug(f"Output file path created: {out_path}")
    
    return str(out_path)

## ============================================================
## MAIN PIPELINE
## ============================================================
@log_execution_time_and_path
def process_excel_file(src_path: str) -> None:
    """
        Complete pipeline:
            - Convert XLS to XLSX if needed
            - Extract text
            - Save as .txt file

        Args:
            src_path (str): File path complet to process
    """
    
    ## Normalize path
    src_path = Path(src_path)

    if not os.path.exists(str(src_path)):
        logger.error(f"File not found: {src_path}")
        return

    ## Convert XLS → XLSX if needed
    if src_path.suffix.lower() == ".xls":
        logger.info(f"Detected .xls file, starting conversion: {src_path}")
        converted = convert_xls_to_xlsx(str(src_path))
        if not converted:
            return
        src_path = Path(converted)

    ## Generate output file path
    out_file = create_output_file(src_path)

    ## Extract text
    xlsx_to_text(str(src_path), out_file)


## ============================================================
## MAIN ENTRY POINT
## ============================================================
if __name__ == "__main__":
    """
        Example standalone execution:
        python xlsx_xls_to_text.py <file_name>
    """
    
    logger.info("Starting manual execution: Excel text extraction")

    ## Defensive: ensure INPUT_DIR exists
    if not INPUT_DIR.exists():
        logger.error(f"INPUT_DIR does not exist: {INPUT_DIR}")
        raise SystemExit(1)

    ## Process only XLS/XLSX
    for file in INPUT_DIR.glob("*"):
        if not file.is_file():
            continue

        if file.suffix.lower() in [".xls", ".xlsx"]:
            logger.info(f"Processing file: {file}")
            try:
                ## Ensure str is passed (process_excel_file expects str)
                process_excel_file(str(file))
            except Exception as e:
                logger.exception(f"Failed processing file {file}: {e}")

    logger.info("Finished manual processing of Excel files.")
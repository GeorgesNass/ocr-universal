"""
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.0.0"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Prod"
__desc__ = "Initialization file for the OCR package, allowing modular import of all OCR conversion tools."
"""

from src.utils import get_logger

## ============================================================
## LOGGER INITIALIZATION
## ============================================================
logger = get_logger("ocr_init")

## ============================================================
## IMPORT SUBMODULES
## ============================================================
from src.ocr import (
    docx_doc_to_text,
    pptx_ppt_to_text,
    xlsx_xls_to_text,
    pdf_to_text,
    html_to_text,
    odt_rtf_to_text,
    photo_to_text,
)

__all__ = [
    "docx_doc_to_text",
    "pptx_ppt_to_text",
    "xlsx_xls_to_text",
    "pdf_to_text",
    "html_to_text",
    "odt_rtf_to_text",
    "photo_to_text",
]

logger.debug("OCR package initialized and all modules imported.")
'''
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.0.0"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Prod"
__desc__ = "Centralized OCR constants, environment loading, and directory configuration."
'''

import os
import platform
from pathlib import Path
from dotenv import load_dotenv

## ============================================================
## ENVIRONMENT LOADING (AVANT LOGGER)
## ============================================================
load_dotenv()
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

from src.utils import get_logger

## ============================================================
## LOGGER INITIALIZATION
## ============================================================
logger = get_logger("constants")

if env_path.exists():
    logger.info(f"Loaded environment variables from {env_path}")
else:
    logger.warning(".env file not found, using default values")
    
## ============================================================
## SYSTEM AND PATH MANAGEMENT
## ============================================================
CURRENT_OS = platform.system().lower()
logger.info(f"Operating system detected: {CURRENT_OS}")

if "linux" in CURRENT_OS:
    DIR_SEPARATOR = "/"
    PYTHON_ENV = "python3.10"
else:
    DIR_SEPARATOR = "\\"
    PYTHON_ENV = "python"

BASE_DIR = Path(__file__).resolve().parent.parent
PARENT_DIR = Path(__file__).resolve().parent.parent.parent

INPUT_DIR = PARENT_DIR / "data" / "input"
CONVERTED_DIR = PARENT_DIR / "data" / "converted"
OUTPUT_DIR = PARENT_DIR / "data" / "output"
# PATH_LIBRE_OFFICE = os.getenv("PATH_LIBRE_OFFICE", "soffice")

## ============================================================
## LIBREOFFICE PATH (OS-AWARE)
## ============================================================
CURRENT_OS = platform.system().lower()

if "windows" in CURRENT_OS:
    PATH_LIBRE_OFFICE = Path(
        os.getenv(
            "PATH_LIBRE_OFFICE",
            r"C:\Program Files\LibreOffice\program\soffice.exe"
        )
    )
elif "linux" in CURRENT_OS:
    PATH_LIBRE_OFFICE = Path(
        os.getenv(
            "PATH_LIBRE_OFFICE",
            "/usr/bin/libreoffice"
        )
    )
else:
    PATH_LIBRE_OFFICE = Path(os.getenv("PATH_LIBRE_OFFICE", "soffice"))

logger.info(f"LibreOffice executable resolved to: {PATH_LIBRE_OFFICE}")

for folder in [INPUT_DIR, CONVERTED_DIR, OUTPUT_DIR]:
    folder.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Verified or created folder: {folder}")

## ============================================================
## OCR ENGINE FLAGS
## ============================================================
USE_TESSERACT = os.getenv("USE_TESSERACT", "True").lower() == "true"
USE_GOOGLE_VISION = os.getenv("USE_GOOGLE_VISION", "False").lower() == "true"
USE_TIKA = os.getenv("USE_TIKA", "true").lower() == "true"
USE_PYPDF2 = os.getenv("USE_PYPDF2", "true").lower() == "true"
USE_PDFTOTEXT = os.getenv("USE_PDFTOTEXT", "true").lower() == "true"
USE_PDF2IMAGE = os.getenv("USE_PDF2IMAGE", "true").lower() == "true"

## ============================================================
## PARSING FLAGS
## ============================================================
USE_BEAUTIFULSOUP = os.getenv("USE_BEAUTIFULSOUP", "True").lower() == "true"
USE_HTML2TEXT = os.getenv("USE_HTML2TEXT", "False").lower() == "true"
USE_URLLIB = os.getenv("USE_URLLIB", "False").lower() == "true"

## ============================================================
## DOCX EXTRACTION FLAGS
## ============================================================
INCLUDE_DOCX_HEADERS = os.getenv("INCLUDE_DOCX_HEADERS", "True").lower() == "true"
INCLUDE_DOCX_TABLES = os.getenv("INCLUDE_DOCX_TABLES", "True").lower() == "true"

## ============================================================
## XLSX EXTRACTION FLAGS
## ============================================================
USE_DETAILED_EXCEL_EXTRACTION = os.getenv("USE_DETAILED_EXCEL_EXTRACTION", "false").lower() == "true"

## ============================================================
## PPTX EXTRACTION FLAGS
## ============================================================
USE_DETAILED_PPTX_EXTRACTION = os.getenv("USE_DETAILED_PPTX_EXTRACTION", "false").lower() == "true"

## ============================================================
## FILE MANAGEMENT FLAGS
## ============================================================
PRUNE_AFTER_PROCESS = os.getenv("PRUNE_AFTER_PROCESS", "True").lower() == "true"
MAX_PDF_SIZE_MB = int(os.getenv("MAX_PDF_SIZE_MB", "50"))
 
## ============================================================
## FILE FORMATS AND ENCODINGS
## ============================================================
ALLOWED_EXTENSIONS = {
    'html', 'htm', 'mht', 'odt', 'rtf', 'docx', 'doc', 'pptx',
    'ppt', 'txt', 'pdf', 'png', 'jpg', 'jpeg', 'svg', 'tif',
    'tiff', 'bitmap', 'bmp', 'gif', 'jfif', 'webp', 'xls', 'xlsx'
}

CSV_SEPARATOR = "\t"
CSV_EXTENSION = ".txt"

ENCODINGS_TO_TRY = [
    "utf-8", "utf-8-sig", "latin-1", "windows-1252", "iso8859-1",
    "iso8859-15", "mac_roman", "cp850", "cp1250", "cp1254",
    "ascii", "big5", "shift_jis", "euc-jp", "gb18030"
]

## ============================================================
## CONFIGURATION SUMMARY LOG
## ============================================================
logger.info("===== CONFIGURATION SUMMARY =====")
logger.info(f"BASE_DIR: {BASE_DIR}")
logger.info(f"INPUT_DIR: {INPUT_DIR}")
logger.info(f"CONVERTED_DIR: {CONVERTED_DIR}")
logger.info(f"OUTPUT_DIR: {OUTPUT_DIR}")
logger.info(f"PATH_LIBRE_OFFICE: {PATH_LIBRE_OFFICE}")
logger.info(f"USE_TESSERACT: {USE_TESSERACT}")
logger.info(f"USE_GOOGLE_VISION: {USE_GOOGLE_VISION}")
logger.info(f"USE_BEAUTIFULSOUP: {USE_BEAUTIFULSOUP}")
logger.info(f"USE_HTML2TEXT: {USE_HTML2TEXT}")
logger.info(f"INCLUDE_DOCX_HEADERS: {INCLUDE_DOCX_HEADERS}")
logger.info(f"INCLUDE_DOCX_TABLES: {INCLUDE_DOCX_TABLES}")
logger.info(f"PRUNE_AFTER_PROCESS: {PRUNE_AFTER_PROCESS}")
logger.info(f"ALLOWED_EXTENSIONS: {len(ALLOWED_EXTENSIONS)} types defined")
logger.info(f"ENCODINGS_TO_TRY: {len(ENCODINGS_TO_TRY)} encodings supported")
logger.info("=================================")
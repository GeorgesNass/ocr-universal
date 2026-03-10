# 👁️ OCR Universal API

Universal OCR API — extract text from **any document or image**  
(images, PDFs, Microsoft Office, OpenDocument or HTML formats).

---

## 🎯 Project Overview

Main capabilities:

* Extract text from images and documents
* Support multiple OCR engines
* Process single files, batch uploads, or folders
* Convert office documents before OCR processing
* REST API powered by **FastAPI**
* Docker-based deployment

The system provides a **universal OCR pipeline capable of processing heterogeneous document formats** 
using different OCR engines (`Tesseract`, `EasyOCR`, `PaddleOCR`, `Pdf2text`, `Beautifullsoup`, etc.).

Supports single files, multiple uploads, or entire folder processing.

---

## ⚙️ Tech Stack

Core technologies used in the project:

* Python
* FastAPI / Uvicorn
* Tesseract OCR
* Google Cloud Vision OCR
* pdf2image / PyPDF2
* python-docx / python-pptx / xlrd
* html2text / striprtf
* odfpy
* Docker

---

## 📂 Project Structure

```text
ocr-universal/
├── .dockerignore                      ## Docker ignore rules
├── .env                               ## Environment configuration
├── .gitignore                         ## Git ignore rules
├── Dockerfile                         ## Docker image definition
├── LICENSE                            ## Project license
├── main.py                            ## FastAPI application entrypoint
├── pytest.ini                         ## Pytest configuration
├── README.md                          ## Project documentation
├── requirements.txt                   ## Python dependencies
├── swagger.yaml                       ## API specification (Swagger)
│
├── data/
│   ├── input/                         ## Input documents (images, PDFs, Office files)
│   ├── converted/                     ## Temporary converted files (LibreOffice / preprocessing)
│   └── output/                        ## Extracted OCR text files
│
├── logs/                              ## Application logs
│
├── tests/
│   └── test_service.py                ## API unit tests
│
└── src/
	├── service.py                     ## FastAPI routes and API logic
	│
	├── ocr/                           ## OCR extraction modules per document type
	│   ├── docx_doc_to_text.py        ## DOC / DOCX extraction
	│   ├── html_to_text.py            ## HTML extraction
	│   ├── odt_rtf_to_text.py         ## ODT / RTF extraction
	│   ├── pdf_to_text.py             ## PDF extraction
	│   ├── photo_to_text.py           ## Image OCR
	│   ├── pptx_ppt_to_text.py        ## PPT / PPTX extraction
	│   └── xlsx_xls_to_text.py        ## XLS / XLSX extraction
	│
	└── utils/
	    ├── constants.py               ## Global constants
	    ├── logging_utils.py           ## Centralized logging utilities
        └── ocr_utils.py               ## OCR helper utilities

```
---

## ❓ Problem Statement

Organizations often need to extract text from many document formats:

* scanned PDFs
* images
* office documents
* web files

However:

* each format requires different preprocessing
* OCR engines behave differently depending on document quality
* batch document processing is complex

This project provides a **single API capable of processing multiple document formats with interchangeable OCR engines**.

---

## 🧠 Approach / Methodology / Strategy

The system implements a **multi-engine OCR processing pipeline**.


### Supported File Types

These are all file extensions processed by the project.

| Category | Supported Extensions |
|--------|----------------------|
| Images | `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.tif`, `.gif`, `.webp`, `.svg` |
| PDF | `.pdf` |
| Microsoft Office | `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`, `.rtf` |
| OpenDocument | `.odt`, `.ods`, `.odp` |
| Web formats | `.html`, `.htm` |

### Document Conversion

Office documents are first converted using **LibreOffice** before OCR extraction.

Supported conversions:

* DOC / DOCX
* XLS / XLSX
* PPT / PPTX

---

### OCR Engine Selection

OCR engines are dynamically selected via `.env`.

Supported engines:

* **Tesseract**
* **EasyOCR**
* **PaddleOCR**

This allows switching OCR engines without changing the code.

---

### API Processing

The API supports three workflows for single or multiple uploaded files, or an entire server folder:

| Endpoint | Method | Description |
|-----------|---------|-------------|
| `/healthcheck` | `GET` | Check service health |
| `/convert` | `POST` | Convert a single uploaded file |
| `/convert_batch` | `POST` | Convert multiple uploaded files |
| `/convert_folder` | `POST` | Convert all files in a given server folder |

---

## 🏗 Pipeline Architecture

```
Input Document(s) or server folder
      ↓
Document Conversion (if needed)
      ↓
OCR Engine Selection
      ↓
Text Extraction
      ↓
Output Text File
```

---

## 📊 Exploratory Data Analysis

Operational diagnostics include:

* processed file statistics
* OCR extraction logs
* conversion success rates

Outputs are stored in:

```
logs/
data/output/
```

---

## 🔧 Setup & Installation

In this section we explain the minimum OS verification, python usage and docker setup.

### 1. Requirements

* Python ≥ 3.10
* Docker & Docker Compose (optional)
* API Security: `Authorization: Bearer <API_KEY>`

### 2. OS prerequisites

Verify that required packages are installed.

#### Windows / WSL2 (recommended)

```powershell
wsl --status
wsl --install
wsl --list --online
wsl --install -d Ubuntu
wsl -d Ubuntu

docker --version
docker compose version
```

#### Ubuntu

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip build-essential curl git
python3 --version
```

---

### 3. Python environment

```bash
python -m venv .ocr_env
source .ocr_env/bin/activate							## for windows : .ocr_env\Scripts\activate.bat
python -m pip install --upgrade pip 				    ## for windows : .ocr_env\Scripts\python.exe -m pip install --upgrade pip
pip install -r requirements.txt
```

---

### 4. Docker setup

```bash
docker build -t ocr_universal_api .
docker run -d -p 8080:8080 --name ocr_universal_api_container ocr_universal_api
docker logs -f ocr_universal_api_container
```

---

## ▶️ Usage & End-to-End Testing

```bash

## Run FastAPI server
uvicorn src.service:app --host 0.0.0.0 --port 8080 --reload

## Open API documentation (Swagger UI)
curl -X GET http://localhost:8080/docs

## Open API documentation (ReDoc)
curl -X GET http://localhost:8080/redoc

## Healthcheck endpoint
curl -X GET http://localhost:8080/healthcheck

## Convert single file
curl -X POST "http://localhost:8080/convert" -H "accept: application/json" -F "file=@data/input/test.png"

## Convert multiple files
curl -X POST "http://localhost:8080/convert_batch" -H "accept: application/json" -F "files=@data/input/test1.jpg" -F "files=@data/input/test2.pdf"

## Convert folder
curl -X POST "http://localhost:8080/convert_folder" -H "Content-Type: application/json" -d '{"folder_path": "data/input_docs"}'

## Run unit tests
pytest tests/ -v
```

---

## 📛 Common Errors & Troubleshooting

| Error                          | Cause                | Solution                    |
| ------------------------------ | -------------------- | --------------------------- |
| OCR engine failure             | Engine not installed | Verify `.env` configuration |
| LibreOffice conversion failure | LibreOffice missing  | Install LibreOffice         |
| API startup error              | Missing dependencies | Reinstall requirements      |
| Batch conversion failure       | Invalid input path   | Verify folder path          |

---

## 👤 Author

**Georges Nassopoulos**
[georges.nassopoulos@gmail.com](mailto:georges.nassopoulos@gmail.com)

**Status:** Universal OCR / Text Extraction Project

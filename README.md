# 🧠 OCR Universal API

### 🧾 Description
Universal OCR API — extract text from **any document or image**.  
Supports single files, multiple uploads, or entire folder processing.  
The OCR engine (`Tesseract`, `EasyOCR`, `PaddleOCR`, etc.) is selected via `.env`.

---

## ⚙️ Setup (Manual Installation)

```bash
# 🧭 Go to your working directory
cd ~/git_projets/

# 🐍 Install Python 3.10 if not already installed
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3.10-dev

# 📦 Create and activate virtual environment
python3.10 -m venv ocr_env
source ocr_env/bin/activate

# 🚀 Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt
```

---

## 🐳 Docker Setup

```bash
# 🧭 Go to project root
cd ~/git_projets/

# 🐳 Build Docker image
docker build -t ocr_universal_api .

# ▶️ Run container
docker run -d -p 8080:8080 --name ocr_universal_api_container ocr_universal_api

# 🔍 View logs
docker logs -f ocr_universal_api_container
```

---

## ⚙️ Environment Variables (`.env`)

| Variable | Description | Example |
|-----------|--------------|----------|
| `OCR_ENGINE` | OCR engine to use (`tesseract`, `easyocr`, `paddleocr`) | `tesseract` |
| `INPUT_DIR` | Directory containing input files | `data/input` |
| `OUTPUT_DIR` | Directory for output text files | `data/output` |
| `CONVERTED_DIR` | Directory for temporary converted files | `data/converted` |
| `PATH_TESSERACT` | Absolute path to Tesseract executable | `/usr/bin/tesseract` |
| `PATH_LIBRE_OFFICE` | Path to LibreOffice binary (for DOC/PPT conversions) | `/usr/bin/libreoffice` |
| `INCLUDE_DOCX_HEADERS` | Include headers in DOCX text extraction | `True` |
| `INCLUDE_DOCX_TABLES` | Include tables in DOCX extraction | `False` |
| `LOG_LEVEL` | Logging verbosity (`INFO`, `DEBUG`, `ERROR`) | `INFO` |
| `API_KEY` | Optional API key for secured endpoints | `my_secret_token` |

---

## 🧩 Supported File Types

### 🖼️ Image Formats
`.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.tif`, `.gif`, `.webp`, `.svg`

### 📄 PDF Formats
`.pdf` (scanned or text-based)

### 📝 Microsoft Office Documents
`.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`, `.rtf`

### 📑 OpenDocument Formats
`.odt`, `.ods`, `.odp`

### 💾 Text-Based Files
`.html`, `.htm`

---

## 🚀 Run the API

```bash
# Run FastAPI with Uvicorn
uvicorn src.service:app --host 0.0.0.0 --port 8080 --reload
```

Access the app at:  
👉 [http://localhost:8080/docs](http://localhost:8080/docs) (Swagger UI)  
👉 [http://localhost:8080/redoc](http://localhost:8080/redoc) (ReDoc)

---

## 🧪 Run Tests

```bash
pytest tests/ -v
```

---

## 🔥 Endpoints Summary

| Endpoint | Method | Description |
|-----------|---------|-------------|
| `/healthcheck` | `GET` | Check service health |
| `/convert` | `POST` | Convert a single uploaded file |
| `/convert_batch` | `POST` | Convert multiple uploaded files |
| `/convert_folder` | `POST` | Convert all files in a given server folder |

---

## 📦 Example API Calls (cURL)

```bash
# ✅ Healthcheck
curl -X GET http://localhost:8080/healthcheck

# 📄 Convert single file
curl -X POST "http://localhost:8080/convert"   -H "accept: application/json"   -F "file=@data/input/test.png"

# 📁 Convert multiple files
curl -X POST "http://localhost:8080/convert_batch"   -H "accept: application/json"   -F "files=@data/input/test1.jpg"   -F "files=@data/input/test2.pdf"

# 📂 Convert folder
curl -X POST "http://localhost:8080/convert_folder"   -H "Content-Type: application/json"   -d '{"folder_path": "data/input_docs"}'
```

---

## 🧠 Notes

- All OCR engines are interchangeable via `.env`
- LibreOffice is required for DOC, XLS, PPT conversion
- Logs are stored in `logs/`
- Extracted text files are saved to `data/output/`

---

## 🧾 Example Output Structure

```
data/
├── input/
│   ├── test1.png
│   ├── report.pdf
│   └── notes.docx
├── converted/
│   ├── report_converted.png
│   └── notes_converted.docx
└── output/
    ├── test1.txt
    ├── report.txt
    └── notes.txt
```

---

## 🔑 API Security

This API supports optional key-based security via header:
```
Authorization: Bearer <API_KEY>
```

If `API_KEY` is not defined in `.env`, routes are accessible without authentication.

---

## 🧑‍💻 Author

**Georges Nassopoulos**  
📧 `georges.nassopoulos@gmail.com`  
🧾 Version: `1.1.0` — Status: `Prod`

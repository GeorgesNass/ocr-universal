'''
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.0.0"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Prod"
__desc__ = "Unit tests for FastAPI OCR service endpoints (/healthcheck, /convert, /convert_batch)."
'''

import io
import sys
from pathlib import Path
from fastapi.testclient import TestClient

## Add src/ to Python path (important if tests are outside src/)
from src.service import app

## ============================================================
## INITIALIZATION
## ============================================================
client = TestClient(app)

## ============================================================
## FIXTURES AND HELPERS
## ============================================================
def create_dummy_file(content: str = "Sample OCR text file", filename: str = "sample.txt") -> tuple:
    """
        Create a dummy in-memory text file to simulate file uploads

        Args:
            content (str): Text content to include in the file
            filename (str): Name of the fake uploaded file

        Returns:
            tuple: (filename, file_bytes)
    """
    
    return (filename, io.BytesIO(content.encode("utf-8")))

## ============================================================
## TESTS
## ============================================================
def test_healthcheck():
    """
        Test the /healthcheck endpoint to ensure the API is running properly

        Expected:
            - Status code: 200
            - Response contains {"status": "ok"}
    """
    
    response = client.get("/healthcheck")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_convert_single_file():
    """
        Test the /convert endpoint with a dummy text file upload

        Expected:
            - Status code: 200
            - JSON response containing "file_name" and "text"
            - Text content matches uploaded file
    """
    
    filename, file_bytes = create_dummy_file("Hello OCR world!", "testfile.txt")
    response = client.post(
        "/convert",
        files={"file": (filename, file_bytes, "text/plain")}
    )

    assert response.status_code == 200
    
    data = response.json()
    
    assert "file_name" in data
    assert "text" in data
    assert "Hello OCR world" in data["text"]

def test_convert_batch_multiple_files():
    """
        Test the /convert_batch endpoint with multiple uploaded files

        Expected:
            - Status code: 200
            - Response is a list of dicts [{"file_name":..., "text":...}, ...]
            - Each file has valid text output
    """
    
    files = [
        ("files", ("file1.txt", io.BytesIO(b"First OCR test"), "text/plain")),
        ("files", ("file2.txt", io.BytesIO(b"Second OCR test"), "text/plain"))
    ]

    response = client.post("/convert_batch", files=files)

    assert response.status_code == 200
    
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) == 2
    assert all("file_name" in item and "text" in item for item in data)
    assert "First OCR test" in data[0]["text"]
    assert "Second OCR test" in data[1]["text"]
    
def test_convert_folder(tmp_path):
    """
        Test the /convert_folder endpoint using a temporary directory

        Expected:
            - Status code: 200
            - Response is a list of dicts [{"file_name":..., "text":...}, ...]
            - Each text corresponds to content in test files
    """
    
    ## Create two fake text files inside a temp directory
    file1 = tmp_path / "doc1.txt"
    file2 = tmp_path / "doc2.txt"
    file1.write_text("This is document 1.", encoding="utf-8")
    file2.write_text("This is document 2.", encoding="utf-8")

    ## Call the API
    response = client.post("/convert_folder", params={"folder_path": str(tmp_path)})

    assert response.status_code == 200

    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) == 2
    assert any("document 1" in item["text"] for item in data)
    assert any("document 2" in item["text"] for item in data)

def test_convert_invalid_file():
    """
        Test invalid file upload

        Expected:
            - Status code: 400 or 422
    """

    response = client.post(
        "/convert",
        files={"file": ("file.exe", io.BytesIO(b"bad"), "application/octet-stream")}
    )

    assert response.status_code in (400, 422)
    
def test_convert_folder_empty(tmp_path):
    """
        Test empty folder

        Expected:
            - Status code: 200
            - Empty list
    """

    response = client.post("/convert_folder", params={"folder_path": str(tmp_path)})

    assert response.status_code == 200
    assert response.json() == []
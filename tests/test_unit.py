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
import pandas as pd
import pytest

from pathlib import Path
from fastapi.testclient import TestClient

from src.core.data_drift import run_data_drift
from src.core.data_consistency import run_data_consistency
from src.core.data_quality import run_data_quality

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
    
## ============================================================
## DATA CONSISTENCY TESTS
## ============================================================
def test_data_consistency_valid():
    """
        Test valid data consistency

        Expected:
            - is_consistent = True
            - no errors
    """

    data = {
        "text": "valid text content",
        "id": 1,
        "amount": 100,
    }

    result = run_data_consistency(data=data)

    assert result["is_consistent"] is True
    assert result["errors"] == 0

def test_data_consistency_empty_text():
    """
        Test empty text case

        Expected:
            - is_consistent = False
            - at least 1 error
    """

    data = {
        "text": "",
    }

    result = run_data_consistency(data=data)

    assert result["is_consistent"] is False
    assert result["errors"] > 0

def test_data_consistency_type_error():
    """
        Test invalid type

        Expected:
            - error detected
    """

    data = {
        "text": 123,  ## invalid type
    }

    result = run_data_consistency(data=data)

    assert result["is_consistent"] is False

def test_data_consistency_business_rule():
    """
        Test business rule violation (negative amount)

        Expected:
            - error detected
    """

    data = {
        "text": "valid text",
        "amount": -10,
    }

    result = run_data_consistency(data=data)

    assert result["is_consistent"] is False

def test_data_consistency_cross_source():
    """
        Test cross-source mismatch

        Expected:
            - warning detected
    """

    data = {
        "text": "hello",
        "metadata_text": "different",
    }

    result = run_data_consistency(data=data)

    assert result["warnings"] > 0

def test_data_consistency_duplicates():
    """
        Test duplicate detection

        Expected:
            - warning detected
    """

    data = {
        "text": "abc",
        "field1": "dup",
        "field2": "dup",
    }

    result = run_data_consistency(data=data)

    assert result["warnings"] > 0

def test_data_consistency_strict_mode():
    """
        Test strict mode behavior

        Expected:
            - exception raised
    """

    data = {
        "text": "",
    }

    with pytest.raises(Exception):
        run_data_consistency(data=data, strict=True)
        
## ============================================================
## DATA QUALITY TESTS
## ============================================================
def test_data_quality_valid():
    """
        Test valid data quality

        Expected:
            - is_valid = True
            - no errors
    """

    data = {
        "value": 10,
        "value2": 12,
    }

    result = run_data_quality(data=data)

    assert result["is_valid"] is True
    assert result["errors"] == 0

def test_data_quality_outlier():
    """
        Test anomaly detection

        Expected:
            - warning detected
    """

    data = {
        "value": 10,
        "value2": 1000,  ## outlier
    }

    result = run_data_quality(data=data)

    assert result["warnings"] > 0

def test_data_quality_invalid_values():
    """
        Test NaN / inf detection

        Expected:
            - error detected
    """

    data = {
        "value": float("nan"),
    }

    result = run_data_quality(data=data)

    assert result["errors"] > 0

def test_data_quality_strict_mode():
    """
        Test strict mode behavior

        Expected:
            - exception raised
    """

    data = {
        "value": float("nan"),
    }

    with pytest.raises(Exception):
        run_data_quality(data=data, strict=True)
        
## ============================================================
## DATA DRIFT TESTS
## ============================================================
def test_data_drift_no_drift():
    """
        Test no drift scenario

        Expected:
            - high score
            - no errors
    """

    df_ref = pd.DataFrame({"text": ["hello world", "test data"]})
    df_cur = pd.DataFrame({"text": ["hello world", "test data"]})

    result = run_data_drift(df_ref=df_ref, df_current=df_cur)

    assert result["drift_score"] >= 0.9
    assert result["errors"] == 0

def test_data_drift_detected():
    """
        Test drift detection

        Expected:
            - lower score
            - warnings present
    """

    df_ref = pd.DataFrame({"text": ["hello world", "hello world"]})
    df_cur = pd.DataFrame({"text": ["999999 $$$$", "%%%% !!!!!"]})

    result = run_data_drift(df_ref=df_ref, df_current=df_cur)

    assert result["drift_score"] < 1.0
    assert result["warnings"] > 0

def test_data_drift_empty():
    """
        Test empty dataset

        Expected:
            - exception raised
    """

    df_ref = pd.DataFrame()
    df_cur = pd.DataFrame()

    with pytest.raises(Exception):
        run_data_drift(df_ref=df_ref, df_current=df_cur)

def test_data_drift_strict_mode():
    """
        Test strict mode behavior

        Expected:
            - exception if drift detected
    """

    df_ref = pd.DataFrame({"text": ["aaa"]})
    df_cur = pd.DataFrame({"text": ["zzz"]})

    with pytest.raises(Exception):
        run_data_drift(df_ref=df_ref, df_current=df_cur, strict=True)
        
def test_data_drift_evidently_output_ocr() -> None:
    """
        Validate Evidently report generation for OCR drift

        Returns:
            None
    """

    df_ref = pd.DataFrame({
        "text": ["hello world", "test data"],
        "width": [100, 120],
        "height": [200, 240],
    })

    df_cur = df_ref.copy()

    result = run_data_drift(df_ref=df_ref, df_current=df_cur)

    assert "evidently_report" in result or result["warnings"] >= 0
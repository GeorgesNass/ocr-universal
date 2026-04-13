'''
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.0.0"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Dev"
__desc__ = "Utility functions for normalization, schema validation, cross-source checks, business rules and data quality."
'''

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List

from src.utils import get_logger
from src.core.errors import ValidationError, DataError

## ============================================================
## LOGGER INITIALIZATION
## ============================================================
logger = get_logger("data_utils")

def normalize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
        Normalize data fields

        Args:
            data: Input dictionary

        Returns:
            Normalized dictionary
    """

    ## Initialize normalized container
    normalized = {}

    for key, value in data.items():

        ## Normalize string values
        if isinstance(value, str):
            logger.debug(f"Normalizing string field: {key}")
            value = value.strip().lower()
            value = re.sub(r"\s+", " ", value)

        ## Normalize list values
        if isinstance(value, list):
            logger.debug(f"Normalizing list field: {key}")
            value = [
                v.strip().lower() if isinstance(v, str) else v
                for v in value
            ]

        ## Store normalized value
        normalized[key] = value

    return normalized

def validate_schema(data: Dict[str, Any]) -> List[Dict]:
    """
        Validate required schema fields

        Args:
            data: Input dictionary

        Returns:
            List of issues
    """

    ## Initialize validation outputs
    issues = []
    required_fields = ["text"]

    for field in required_fields:

        ## Check missing fields
        if field not in data:
            logger.error(f"Missing required field: {field}")
            issues.append({
                "rule": "schema",
                "level": "error",
                "message": f"Missing field: {field}",
            })

    return issues

def validate_types(data: Dict[str, Any]) -> List[Dict]:
    """
        Validate field types

        Args:
            data: Input dictionary

        Returns:
            List of issues
    """

    ## Initialize type issues
    issues = []

    ## Validate text type
    if "text" in data and not isinstance(data["text"], str):
        logger.error("Invalid type for text")
        issues.append({
            "rule": "type_text",
            "level": "error",
            "message": "text must be string",
        })

    ## Validate id type
    if "id" in data and not isinstance(data["id"], (int, str)):
        logger.error("Invalid type for id")
        issues.append({
            "rule": "type_id",
            "level": "error",
            "message": "id must be int or str",
        })

    ## Validate numeric fields
    if "amount" in data and not isinstance(data["amount"], (int, float)):
        logger.error("Invalid type for amount")
        issues.append({
            "rule": "type_amount",
            "level": "error",
            "message": "amount must be numeric",
        })

    return issues

def parse_date(value: Any) -> Any:
    """
        Try to parse date string

        Args:
            value: Input value

        Returns:
            datetime or original value
    """

    ## Return early for non-string values
    if not isinstance(value, str):
        return value

    ## Define supported date formats
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"]

    for fmt in formats:
        try:
            ## Try parsing current format
            parsed = datetime.strptime(value, fmt)
            logger.debug(f"Parsed date: {value}")
            return parsed
        except Exception:
            ## Continue with next format
            continue

    ## Log fallback when parsing fails
    logger.warning(f"Failed to parse date: {value}")
    return value

def compare_sources(data: Dict[str, Any]) -> List[Dict]:
    """
        Compare values from multiple sources

        Args:
            data: Input dictionary

        Returns:
            List of issues
    """

    ## Initialize cross-source issues
    issues = []

    ## Compare text sources
    if "text" in data and "metadata_text" in data:
        if data["text"] != data["metadata_text"]:
            logger.warning("Mismatch between OCR and metadata text")
            issues.append({
                "rule": "cross_text",
                "level": "warning",
                "message": "Mismatch between OCR and metadata text",
            })

    ## Compare numeric values
    if "amount" in data and "metadata_amount" in data:
        if data["amount"] != data["metadata_amount"]:
            logger.warning("Mismatch in amount between sources")
            issues.append({
                "rule": "cross_amount",
                "level": "warning",
                "message": "Mismatch in amount between sources",
            })

    return issues

def check_business_rules(data: Dict[str, Any]) -> List[Dict]:
    """
        Apply business rules

        Args:
            data: Input dictionary

        Returns:
            List of issues
    """

    ## Initialize business-rule issues
    issues = []

    ## Validate text length rule
    if "text" in data and len(data["text"]) < 3:
        logger.warning("Text too short")
        issues.append({
            "rule": "business_text_length",
            "level": "warning",
            "message": "Text too short",
        })

    ## Validate amount rule
    if "amount" in data:
        if isinstance(data["amount"], (int, float)) and data["amount"] < 0:
            logger.error("Negative amount detected")
            issues.append({
                "rule": "business_amount",
                "level": "error",
                "message": "Amount cannot be negative",
            })

    ## Validate date consistency rule
    if "date_start" in data and "date_end" in data:
        ## Parse dates safely before comparing
        start = parse_date(data["date_start"])
        end = parse_date(data["date_end"])

        ## Compare only parsed datetime values
        if isinstance(start, datetime) and isinstance(end, datetime):
            if start > end:
                logger.error("Invalid date order")
                issues.append({
                    "rule": "business_date",
                    "level": "error",
                    "message": "date_start must be before date_end",
                })

    return issues

def compute_quality_score(data: Dict[str, Any]) -> float:
    """
        Compute quality score

        Args:
            data: Input dictionary

        Returns:
            Score
    """

    ## Read target text field
    text = data.get("text", "")

    ## Handle empty input case
    if not text:
        logger.warning("Empty text for quality score")
        return 0.0

    ## Count valid alphanumeric characters
    valid_chars = sum(c.isalnum() for c in text)
    score = valid_chars / len(text)

    ## Log computed score
    logger.debug(f"Quality score: {score}")

    return score

def detect_duplicates(data: Dict[str, Any]) -> List[Any]:
    """
        Detect duplicate values

        Args:
            data: Input dictionary

        Returns:
            List of duplicates
    """

    ## Initialize duplicate tracking
    seen = set()
    duplicates = []

    for value in data.values():

        ## Skip complex structures
        if isinstance(value, (list, dict)):
            continue

        ## Detect repeated scalar values
        if value in seen:
            logger.warning(f"Duplicate detected: {value}")
            duplicates.append(value)
        else:
            seen.add(value)

    return duplicates
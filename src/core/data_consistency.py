'''
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.0.0"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Dev"
__desc__ = "Centralized data consistency checks: schema, types, cross-source, business rules and data quality."
'''

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logging_utils import get_logger
from src.utils.data_utils import (
    normalize_data,
    validate_schema,
    validate_types,
    compare_sources,
    check_business_rules,
    compute_quality_score,
    detect_duplicates,
)

try:
    from src.core.errors import ValidationError, DataError
except Exception:
    ValidationError = ValueError
    DataError = RuntimeError

## ============================================================
## LOGGER
## ============================================================
logger = get_logger("data_consistency")

## ============================================================
## ISSUE HANDLING
## ============================================================
def _create_issue(
    rule: str,
    level: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
        Create standardized issue object

        Args:
            rule: Rule name
            level: Severity level
            message: Description
            details: Optional metadata

        Returns:
            Issue dictionary
    """

    ## Build issue structure
    issue = {
        "rule": rule,
        "level": level,
        "message": message,
        "details": details or {},
    }

    logger.debug(f"Issue created: {rule} - {level}")

    return issue

def _add_issue(
    issues: List[Dict[str, Any]],
    rule: str,
    level: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
        Append issue and log it

        Args:
            issues: Issue list
            rule: Rule name
            level: Severity
            message: Description
            details: Metadata
    """

    ## Create issue
    issue = _create_issue(rule, level, message, details)

    ## Append to list
    issues.append(issue)

    ## Log issue depending on level
    if level == "error":
        logger.error(f"{rule} - {message}")
    else:
        logger.warning(f"{rule} - {message}")

## ============================================================
## VALIDATIONS
## ============================================================
def _validate_file(
    file_path: Optional[str | Path],
    issues: List[Dict[str, Any]],
) -> Optional[Path]:
    """
        Validate file input

        Args:
            file_path: Path input
            issues: Issue list

        Returns:
            Path or None
    """

    ## Skip if no file provided
    if file_path is None:
        logger.debug("No file path provided")
        return None

    path = Path(file_path)

    ## Check existence
    if not path.exists():
        logger.error(f"File not found: {path}")
        _add_issue(issues, "file_exists", "error", "File does not exist", {"file": str(path)})
        return None

    ## Check file type
    if not path.is_file():
        logger.error(f"Invalid file path: {path}")
        _add_issue(issues, "file_type", "error", "Path is not a file")
        return None

    logger.debug(f"File validated: {path}")
    return path

def _validate_text(
    data: Dict[str, Any],
    issues: List[Dict[str, Any]],
) -> None:
    """
        Validate and normalize text

        Args:
            data: Input data
            issues: Issue list
    """

    ## Extract raw text
    raw_text = data.get("text", "")

    ## Normalize text
    normalized = normalize_data({"text": raw_text}).get("text", "")
    data["text"] = normalized

    logger.debug("Text normalized")

    ## Check empty text
    if not normalized:
        logger.error("Empty text after normalization")
        _add_issue(issues, "empty_text", "error", "Text is empty after normalization")

    ## Check minimal length
    if len(normalized) < 3:
        logger.warning("Text too short")
        _add_issue(issues, "short_text", "warning", "Text too short", {"length": len(normalized)})


def _validate_structure(
    data: Dict[str, Any],
    issues: List[Dict[str, Any]],
) -> None:
    """
        Validate schema and types

        Args:
            data: Input data
            issues: Issue list
    """

    ## Validate schema
    schema_issues = validate_schema(data)
    logger.debug(f"Schema issues count: {len(schema_issues)}")

    for s in schema_issues:
        _add_issue(issues, s["rule"], s["level"], s["message"])

    ## Validate types
    type_issues = validate_types(data)
    logger.debug(f"Type issues count: {len(type_issues)}")

    for t in type_issues:
        _add_issue(issues, t["rule"], t["level"], t["message"])

def _validate_cross_source(
    data: Dict[str, Any],
    issues: List[Dict[str, Any]],
) -> None:
    """
        Validate cross-source consistency

        Args:
            data: Input data
            issues: Issue list
    """

    ## Run cross-source checks
    results = compare_sources(data)

    logger.debug(f"Cross-source issues count: {len(results)}")

    for r in results:
        _add_issue(issues, r["rule"], r["level"], r["message"], r.get("details"))

def _validate_business(
    data: Dict[str, Any],
    issues: List[Dict[str, Any]],
) -> None:
    """
        Apply business rules

        Args:
            data: Input data
            issues: Issue list
    """

    ## Run business rules
    results = check_business_rules(data)

    logger.debug(f"Business issues count: {len(results)}")

    for r in results:
        _add_issue(issues, r["rule"], r["level"], r["message"], r.get("details"))

def _validate_duplicates(
    data: Dict[str, Any],
    issues: List[Dict[str, Any]],
) -> None:
    """
        Detect duplicates

        Args:
            data: Input data
            issues: Issue list
    """

    ## Detect duplicates
    duplicates = detect_duplicates(data)

    if duplicates:
        logger.warning(f"Duplicates detected: {duplicates}")
        _add_issue(issues, "duplicates", "warning", "Duplicate values detected", {"values": duplicates})

def _compute_quality(
    data: Dict[str, Any],
) -> float:
    """
        Compute quality score

        Args:
            data: Input data

        Returns:
            Score
    """

    ## Compute score
    score = compute_quality_score(data)

    logger.debug(f"Quality score computed: {score}")

    return score

## ============================================================
## MAIN ENTRYPOINT
## ============================================================
def run_data_consistency(
    data: Dict[str, Any],
    file_path: Optional[str | Path] = None,
    strict: bool = False,
) -> Dict[str, Any]:
    """
        Run full consistency pipeline

        High-level workflow:
            1) Validate file
            2) Normalize and validate text
            3) Validate schema and types
            4) Validate cross-source consistency
            5) Apply business rules
            6) Detect duplicates
            7) Compute quality score

        Args:
            data: Input data
            file_path: Optional file path
            strict: Raise error if inconsistency

        Returns:
            Result dictionary
    """

    ## Initialize issue container
    issues: List[Dict[str, Any]] = []

    try:
        ## Validate file
        path = _validate_file(file_path, issues)

        ## Validate text
        _validate_text(data, issues)

        ## Validate structure
        _validate_structure(data, issues)

        ## Validate cross-source
        _validate_cross_source(data, issues)

        ## Apply business rules
        _validate_business(data, issues)

        ## Detect duplicates
        _validate_duplicates(data, issues)

        ## Compute quality score
        quality_score = _compute_quality(data)

        ## Extract error issues
        errors = [i for i in issues if i["level"] == "error"]

        ## Build final result
        result = {
            "is_consistent": len(errors) == 0,
            "errors": len(errors),
            "warnings": len(issues) - len(errors),
            "quality_score": quality_score,
            "issues": issues,
            "file": str(path) if path else None,
        }

        logger.info(f"Consistency result: {result['is_consistent']}")

        ## Apply strict mode
        if strict and errors:
            logger.error("Strict mode failure")
            raise ValidationError("Data consistency failed")

        return result

    except ValidationError:
        raise

    except Exception as exc:
        logger.exception(f"Unexpected error: {exc}")
        raise DataError("Consistency pipeline failed") from exc
'''
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.0.0"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Dev"
__desc__ = "Centralized anomaly detection: z-score, IQR and data quality checks."
'''

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from src.utils.logging_utils import get_logger
from src.utils.stats_utils import (
    compute_mean_std,
    compute_iqr_bounds,
    winsorize_series,
)

try:
    from src.core.errors import ValidationError, DataError
except Exception:
    ValidationError = ValueError
    DataError = RuntimeError

## ============================================================
## LOGGER
## ============================================================
logger = get_logger("data_quality")

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

    ## build issue structure
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

    ## create issue
    issue = _create_issue(rule, level, message, details)

    ## append issue
    issues.append(issue)

    ## log depending on severity
    if level == "error":
        logger.error(f"{rule} - {message}")
    else:
        logger.warning(f"{rule} - {message}")

## ============================================================
## QUALITY DETECTIONS
## ============================================================
def _detect_zscore(
    series: pd.Series,
    threshold: float,
    issues: List[Dict[str, Any]],
    column: str,
) -> pd.Series:
    """
        Detect outliers using z-score

        High-level workflow:
            1) Compute mean and standard deviation
            2) Compute z-score
            3) Flag values above threshold

        Args:
            series: Numerical pandas Series
            threshold: Z-score threshold
            issues: Issue container
            column: Column name

        Returns:
            Boolean mask of outliers
    """

    ## compute statistics
    mean, std = compute_mean_std(series)

    ## avoid division by zero
    if std == 0:
        return pd.Series(False, index=series.index)

    ## compute z-score
    z_scores = (series - mean) / std
    mask = z_scores.abs() > threshold

    ## register issue
    if mask.any():
        _add_issue(
            issues,
            "zscore_outliers",
            "warning",
            f"Outliers detected in column {column}",
            {"count": int(mask.sum())},
        )

    return mask

def _detect_iqr(
    series: pd.Series,
    multiplier: float,
    issues: List[Dict[str, Any]],
    column: str,
) -> pd.Series:
    """
        Detect outliers using IQR

        High-level workflow:
            1) Compute Q1 and Q3
            2) Compute IQR
            3) Define lower and upper bounds
            4) Flag outliers

        Args:
            series: Numerical pandas Series
            multiplier: IQR multiplier
            issues: Issue container
            column: Column name

        Returns:
            Boolean mask of outliers
    """

    ## compute bounds
    lower, upper = compute_iqr_bounds(series, multiplier)

    ## detect outliers
    mask = (series < lower) | (series > upper)

    ## register issue
    if mask.any():
        _add_issue(
            issues,
            "iqr_outliers",
            "warning",
            f"IQR outliers detected in column {column}",
            {"count": int(mask.sum())},
        )

    return mask

## ============================================================
## MAIN ENTRYPOINT
## ============================================================
def run_data_quality(
    data: Union[pd.DataFrame, List[float], np.ndarray],
    method: str = "zscore",
    z_threshold: float = 3.0,
    iqr_multiplier: float = 1.5,
    strict: bool = False,
) -> Dict[str, Any]:
    """
        Run anomaly detection pipeline

        High-level workflow:
            1) Normalize input data
            2) Detect invalid values (NaN / inf)
            3) Apply anomaly detection (z-score / IQR)
            4) Aggregate issues
            5) Compute anomaly score

        Design choice:
            - Centralized anomaly detection logic
            - Issue-based reporting for consistency with data_consistency

        Args:
            data: Input dataset
            method: Detection method ("zscore" or "iqr")
            z_threshold: Z-score threshold
            iqr_multiplier: IQR multiplier
            strict: Raise error if anomalies detected

        Returns:
            Result dictionary with score and issues
    """

    ## initialize issues
    issues: List[Dict[str, Any]] = []

    try:
        ## normalize input
        df = pd.DataFrame(data) if not isinstance(data, pd.DataFrame) else data.copy()

        ## select numeric columns
        columns = df.select_dtypes(include=[np.number]).columns.tolist()

        ## handle empty case
        if not columns:
            logger.warning("No numeric columns found")
            return {"is_valid": True, "issues": [], "score": 1.0}

        global_mask = pd.Series(False, index=df.index)

        ## iterate columns
        for col in columns:
            series = df[col].astype(float)

            ## detect invalid values
            invalid_mask = series.isna() | np.isinf(series)

            if invalid_mask.any():
                _add_issue(
                    issues,
                    "invalid_values",
                    "error",
                    f"NaN or inf detected in {col}",
                    {"count": int(invalid_mask.sum())},
                )

            ## anomaly detection
            if method == "zscore":
                mask = _detect_zscore(series, z_threshold, issues, col)
            elif method == "iqr":
                mask = _detect_iqr(series, iqr_multiplier, issues, col)
            else:
                raise ValidationError("Invalid anomaly detection method")

            ## merge masks
            global_mask = global_mask | mask | invalid_mask

        ## compute anomaly score
        score = 1.0 - float(global_mask.mean())

        ## separate errors
        errors = [i for i in issues if i["level"] == "error"]

        ## build result
        result = {
            "is_valid": len(errors) == 0,
            "errors": len(errors),
            "warnings": len(issues) - len(errors),
            "score": score,
            "issues": issues,
        }

        logger.info(f"Data quality score: {score}")

        ## strict mode
        if strict and errors:
            logger.error("Strict mode failure")
            raise ValidationError("Data quality failed")

        return result

    except ValidationError:
        raise

    except Exception as exc:
        logger.exception(f"Unexpected error: {exc}")
        raise DataError("Data quality pipeline failed") from exc
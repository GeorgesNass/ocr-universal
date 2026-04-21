'''
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.0.0"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Dev"
__desc__ = "Drift utilities for OCR: statistical tests, feature extraction and reporting."
'''

from __future__ import annotations

from typing import Dict, Tuple, Any

import json
import numpy as np
import pandas as pd

from pathlib import Path
from scipy.stats import ks_2samp, chi2_contingency
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset

from src.utils.logging_utils import get_logger

try:
    from src.core.errors import ValidationError, DataError
except Exception:
    ValidationError = ValueError
    DataError = RuntimeError

## ============================================================
## LOGGER
## ============================================================
logger = get_logger("drift_utils")

def compute_ks_test(ref: pd.Series, cur: pd.Series) -> Tuple[float, float]:
    """
        Compute Kolmogorov-Smirnov test

        Args:
            ref: Reference series
            cur: Current series

        Returns:
            statistic, p_value
    """

    ## drop NaN values
    ref_clean = ref.dropna()
    cur_clean = cur.dropna()

    ## handle empty cases
    if ref_clean.empty or cur_clean.empty:
        return 0.0, 1.0

    ## compute KS test
    stat, p_value = ks_2samp(ref_clean, cur_clean)

    return float(stat), float(p_value)

def compute_chi2_test(ref: pd.Series, cur: pd.Series) -> Tuple[float, float]:
    """
        Compute Chi-square test

        Args:
            ref: Reference series
            cur: Current series

        Returns:
            statistic, p_value
    """

    ## compute value counts
    ref_counts = ref.value_counts()
    cur_counts = cur.value_counts()

    ## align categories
    all_index = ref_counts.index.union(cur_counts.index)
    ref_aligned = ref_counts.reindex(all_index, fill_value=0)
    cur_aligned = cur_counts.reindex(all_index, fill_value=0)

    ## build contingency table
    table = np.array([ref_aligned.values, cur_aligned.values])

    ## handle invalid table
    if table.sum() == 0:
        return 0.0, 1.0

    ## compute Chi2 test
    stat, p_value, _, _ = chi2_contingency(table)

    return float(stat), float(p_value)

def compute_image_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
        Compute image-related features for drift detection

        Args:
            df: Input dataset

        Returns:
            DataFrame with image features
    """

    data: Dict[str, pd.Series] = {}

    ## width / height
    if "width" in df.columns:
        data["width"] = df["width"].astype(float)

    if "height" in df.columns:
        data["height"] = df["height"].astype(float)

    ## aspect ratio
    if "width" in df.columns and "height" in df.columns:
        height_safe = df["height"].replace(0, np.nan)
        data["aspect_ratio"] = df["width"] / height_safe

    ## quality metrics
    for col in ["brightness", "contrast", "blur"]:
        if col in df.columns:
            data[col] = df[col].astype(float)

    return pd.DataFrame(data)

def compute_text_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
        Compute text-related features for drift detection

        Args:
            df: Input dataset

        Returns:
            DataFrame with text features
    """

    data: Dict[str, pd.Series] = {}

    ## require text column
    if "text" not in df.columns:
        return pd.DataFrame()

    text_series = df["text"].fillna("").astype(str)

    ## length
    data["text_length"] = text_series.str.len()

    ## word count
    data["word_count"] = text_series.str.split().apply(len)

    ## digit ratio
    data["digit_ratio"] = text_series.apply(
        lambda x: sum(c.isdigit() for c in x) / len(x) if len(x) > 0 else 0
    )

    ## uppercase ratio
    data["uppercase_ratio"] = text_series.apply(
        lambda x: sum(c.isupper() for c in x) / len(x) if len(x) > 0 else 0
    )

    ## special char ratio
    data["special_char_ratio"] = text_series.apply(
        lambda x: sum(not c.isalnum() for c in x) / len(x) if len(x) > 0 else 0
    )

    return pd.DataFrame(data)

def generate_drift_report(metrics: Dict[str, Any], output_dir: str = "reports") -> Dict[str, str]:
    """
        Generate drift report files (JSON + HTML)

        Args:
            metrics: Drift metrics
            output_dir: Output directory

        Returns:
            Dict with report paths
    """

    ## ensure directory exists
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    ## JSON report
    json_path = path / "drift_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    ## HTML report
    html_path = path / "drift_report.html"
    html_content = "<html><body><h1>Data Drift Report</h1><pre>"
    html_content += json.dumps(metrics, indent=2)
    html_content += "</pre></body></html>"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return {
        "report_json": str(json_path),
        "report_html": str(html_path),
    }

def generate_evidently_report(
    df_ref: pd.DataFrame,
    df_cur: pd.DataFrame,
    output_dir: str = "reports",
) -> Dict[str, str]:
    """
        Generate Evidently data drift report for OCR pipeline

        High-level workflow:
            1) Initialize Evidently report
            2) Run drift analysis
            3) Save HTML report

        Args:
            df_ref: Reference dataset
            df_cur: Current dataset
            output_dir: Output directory

        Returns:
            Dictionary with report path
    """

    report = Report(metrics=[DataDriftPreset()])

    report.run(
        reference_data=df_ref,
        current_data=df_cur,
    )

    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    html_path = path / "evidently_report.html"
    report.save_html(str(html_path))

    return {
        "evidently_html": str(html_path),
    }
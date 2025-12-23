from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from .config import Settings
from .schemas import DatasetRequest, IssuePayload

LOGGER = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    dataset_name: str
    total_rows: int
    missing_rate: float
    duplicate_count: int
    outlier_rate: float
    issues: List[IssuePayload]


class DataValidator:
    """Applies a series of data quality checks on pandas DataFrames."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def validate(self, df: pd.DataFrame, dataset_name: str) -> ValidationResult:
        issues: List[IssuePayload] = []
        total_rows = len(df)
        missing_rate, missing_issues = self._check_missing(df)
        issues.extend(missing_issues)

        dup_count, dup_issues = self._check_duplicates(df)
        issues.extend(dup_issues)

        outlier_rate, outlier_issues = self._check_outliers(df)
        issues.extend(outlier_issues)

        if df.isnull().all().any():
            empty_cols = df.columns[df.isnull().all()].tolist()
            issues.append(
                IssuePayload(
                    issue_type="schema",
                    severity="high",
                    description="Columns contain only null values.",
                    recommendation="Drop or repopulate columns with valid data.",
                    affected_columns=empty_cols,
                )
            )

        return ValidationResult(
            dataset_name=dataset_name,
            total_rows=total_rows,
            missing_rate=missing_rate,
            duplicate_count=dup_count,
            outlier_rate=outlier_rate,
            issues=issues,
        )

    def _check_missing(self, df: pd.DataFrame) -> Tuple[float, List[IssuePayload]]:
        missing_count = df.isna().sum().sum()
        total_values = df.shape[0] * df.shape[1] if df.shape[0] else 1
        missing_rate = missing_count / total_values
        issues: List[IssuePayload] = []
        if missing_rate > self.settings.missing_threshold:
            cols = df.columns[df.isna().any()].tolist()
            issues.append(
                IssuePayload(
                    issue_type="missing_values",
                    severity="high" if missing_rate > 0.2 else "medium",
                    description=f"Missing value rate {missing_rate:.2%} exceeds threshold {self.settings.missing_threshold:.0%}.",
                    recommendation="Impute missing values or remove affected rows.",
                    affected_columns=cols,
                )
            )
        return missing_rate, issues

    def _check_duplicates(self, df: pd.DataFrame) -> Tuple[int, List[IssuePayload]]:
        dup_count = int(df.duplicated().sum())
        issues: List[IssuePayload] = []
        if dup_count > self.settings.duplicate_tolerance:
            issues.append(
                IssuePayload(
                    issue_type="duplicates",
                    severity="medium" if dup_count < len(df) * 0.1 else "high",
                    description=f"Detected {dup_count} duplicate rows.",
                    recommendation="Deduplicate by key columns or drop identical rows.",
                )
            )
        return dup_count, issues

    def _check_outliers(self, df: pd.DataFrame) -> Tuple[float, List[IssuePayload]]:
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return 0.0, []
        z_scores = np.abs(stats.zscore(numeric_df, nan_policy="omit"))
        if isinstance(z_scores, np.ndarray):
            z_mask = z_scores > self.settings.outlier_zscore
        else:
            z_mask = np.zeros_like(numeric_df.to_numpy(), dtype=bool)

        q1 = numeric_df.quantile(0.25)
        q3 = numeric_df.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        iqr_mask = (numeric_df < lower) | (numeric_df > upper)

        combined_mask = z_mask | iqr_mask.to_numpy()
        outlier_count = int(np.nansum(combined_mask))
        total_values = int(np.prod(numeric_df.shape)) if numeric_df.size else 1
        outlier_rate = outlier_count / total_values

        issues: List[IssuePayload] = []
        if outlier_count:
            cols = numeric_df.columns[combined_mask.any(axis=0)].tolist()
            issues.append(
                IssuePayload(
                    issue_type="outliers",
                    severity="medium" if outlier_rate < 0.05 else "high",
                    description=(
                        f"Detected {outlier_count} outliers using z-score>{self.settings.outlier_zscore} or IQR fences."
                    ),
                    recommendation="Review data collection or cap outliers with winsorization/transformations.",
                    affected_columns=cols,
                )
            )
        return outlier_rate, issues


def load_dataset(settings: Settings, payload: DatasetRequest) -> Tuple[pd.DataFrame, str]:
    if payload.records:
        df = pd.DataFrame(payload.records)
        name = payload.dataset_name or "inline_dataset"
        return df, name
    if payload.data_path:
        path = Path(payload.data_path)
        if not path.is_absolute():
            path = settings.data_root / path
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {path}")
        if payload.fmt.lower() == "json" or path.suffix.lower() == ".json":
            df = pd.read_json(path)
        else:
            df = pd.read_csv(path)
        name = payload.dataset_name or path.stem
        return df, name
    raise ValueError("Either records or data_path must be provided.")

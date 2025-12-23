from __future__ import annotations

import pandas as pd

from backend.config import Settings
from backend.validators import DataValidator


def test_validator_detects_missing_and_duplicates():
    settings = Settings(use_fake_llm=True, missing_threshold=0.1, duplicate_tolerance=0)
    validator = DataValidator(settings)
    df = pd.DataFrame(
        [
            {"a": 1, "b": 2},
            {"a": None, "b": 2},
            {"a": 1, "b": 2},
            {"a": 10, "b": 200},
        ]
    )
    result = validator.validate(df, "test")
    issue_types = {issue.issue_type for issue in result.issues}
    assert "missing_values" in issue_types
    assert "duplicates" in issue_types
    assert result.total_rows == 4


def test_validator_outlier_detection():
    settings = Settings(use_fake_llm=True, outlier_zscore=2.0)
    validator = DataValidator(settings)
    df = pd.DataFrame({"value": [1, 2, 3, 100]})
    result = validator.validate(df, "outlier")
    assert any(issue.issue_type == "outliers" for issue in result.issues)

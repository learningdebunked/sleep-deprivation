#!/usr/bin/env python3
"""
NHANES Feature Engineering — Stage 3 spec implementation.
Produces:
  - Text serialization template string (for LLM tokenization)
  - Derived numerical features (social jetlag, chronic short/long sleep flags)

NHANES P_SLQ variables used (2017-2020 and 2013-2014 cohorts):
  SLD012  : Weekday sleep hours
  SLD013  : Weekend sleep hours
  SLQ030  : Snoring frequency (ordinal 1-5)
  SLQ040  : Snort/stop-breathing frequency (ordinal 1-5)
  SLQ050  : Told doctor about sleepiness (binary 1/2)
  SLQ120  : Days/month felt unrested (ordinal 0-4)

Secondary cohort (2013-2014):
  SLD010H : Weeknight sleep hours
  SLQ050  : Told doctor about sleepiness
  SLQ060  : Sleepiness a problem this month
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Any

# ── Categorical label maps ────────────────────────────────────────────────────
SLQ030_MAP = {
    1: "Never or rarely",
    2: "Occasionally (1-2 nights/week)",
    3: "Frequently (3-4 nights/week)",
    4: "Almost every night",
    7: "Refused",
    9: "Don't know",
}
SLQ040_MAP = {
    1: "Never or rarely",
    2: "Occasionally (1-2 nights/week)",
    3: "Frequently (3-4 nights/week)",
    4: "Almost every night",
    7: "Refused",
    9: "Don't know",
}
SLQ050_MAP = {1: "Yes", 2: "No", 7: "Refused", 9: "Don't know"}
SLQ120_MAP = {0: "0 days", 1: "1-2 days", 2: "3-5 days", 3: "6-8 days", 4: "9+ days",
              7: "Refused", 9: "Don't know"}

# ── Text template (locked in Stage 3) ────────────────────────────────────────
NHANES_TEXT_TEMPLATE = (
    "Subject sleeps {SLD012} hours on weekdays and {SLD013} hours on weekends. "
    "Snoring: {SLQ030_text}. "
    "Snort or stop breathing: {SLQ040_text}. "
    "Trouble staying awake: {SLQ050_text}. "
    "Sleepiness days per month: {SLQ120_text}."
)


def _safe_map(value: Any, mapping: dict, missing: str = "unknown") -> str:
    """Look up a categorical code; return readable label or 'unknown'."""
    if pd.isna(value) if isinstance(value, float) else value is None:
        return missing
    return mapping.get(int(value), missing)


def _safe_float(value: Any, missing_val: float = np.nan) -> float:
    """Return float or NaN for missing/refused/don't-know NHANES codes."""
    if pd.isna(value) if isinstance(value, float) else value is None:
        return missing_val
    fv = float(value)
    if fv in (7.0, 9.0, 77.0, 99.0):  # NHANES refused / don't know codes
        return missing_val
    return fv


class NHANESFeatureEngineer:
    """Build text template strings and derived features from NHANES sleep records.

    Designed to work on a single row (dict/Series) or a DataFrame.
    """

    def build_text(self, row: dict | pd.Series) -> str:
        """Serialize one NHANES record to the locked text template.

        Args:
            row: Dict or Series with NHANES column names.

        Returns:
            Filled template string for LLM tokenization.
        """
        sld012 = _safe_float(row.get("SLD012", np.nan))
        sld013 = _safe_float(row.get("SLD013", np.nan))

        sld012_str = f"{sld012:.1f}" if not np.isnan(sld012) else "unknown"
        sld013_str = f"{sld013:.1f}" if not np.isnan(sld013) else "unknown"

        slq030_text = _safe_map(row.get("SLQ030"), SLQ030_MAP)
        slq040_text = _safe_map(row.get("SLQ040"), SLQ040_MAP)
        slq050_text = _safe_map(row.get("SLQ050"), SLQ050_MAP)
        slq120_text = _safe_map(row.get("SLQ120"), SLQ120_MAP)

        return NHANES_TEXT_TEMPLATE.format(
            SLD012=sld012_str,
            SLD013=sld013_str,
            SLQ030_text=slq030_text,
            SLQ040_text=slq040_text,
            SLQ050_text=slq050_text,
            SLQ120_text=slq120_text,
        )

    def compute_derived(self, row: dict | pd.Series) -> dict:
        """Compute three derived features from raw NHANES sleep variables.

        Returns:
            dict with keys:
              social_jetlag       : |SLD012 - SLD013|; NaN if either missing
              chronic_short_sleep : 1 if SLD012 < 6, else 0; NaN if missing
              chronic_long_sleep  : 1 if SLD012 > 9, else 0; NaN if missing
        """
        sld012 = _safe_float(row.get("SLD012", np.nan))
        sld013 = _safe_float(row.get("SLD013", np.nan))

        social_jetlag = abs(sld012 - sld013) if not (np.isnan(sld012) or np.isnan(sld013)) else np.nan
        chronic_short = float(sld012 < 6) if not np.isnan(sld012) else np.nan
        chronic_long = float(sld012 > 9) if not np.isnan(sld012) else np.nan

        return {
            "social_jetlag": social_jetlag,
            "chronic_short_sleep": chronic_short,
            "chronic_long_sleep": chronic_long,
        }

    def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add text template and derived features to a NHANES DataFrame.

        Args:
            df: DataFrame with NHANES P_SLQ columns.

        Returns:
            df with added columns:
              nhanes_text, social_jetlag, chronic_short_sleep, chronic_long_sleep
        """
        df = df.copy()
        df["nhanes_text"] = df.apply(self.build_text, axis=1)
        derived = df.apply(self.compute_derived, axis=1, result_type="expand")
        df = pd.concat([df, derived], axis=1)
        return df

    @staticmethod
    def get_feature_names() -> list[str]:
        """Return the 9 primary + 3 derived NHANES feature names."""
        return [
            "SLD012", "SLD013", "SLQ030", "SLQ040", "SLQ050", "SLQ120",
            # Secondary cohort
            "SLD010H", "SLQ060",
            # Derived
            "social_jetlag", "chronic_short_sleep", "chronic_long_sleep",
        ]

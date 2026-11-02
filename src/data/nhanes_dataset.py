#!/usr/bin/env python3
"""
NHANES Dataset Loader — Modules 1 & 3.

Handles two cohorts:
  A. NHANES P_SLQ 2017-2020 (n=10,195): survey features only, no labels.
     Used for inference via Module 1 + Module 3.
  B. NHANES 2013-2014 SLQ_H + CFQ_H (n~1,400): survey + DSST pseudo-labels.
     Used for Stage 3 bridge training and H4 baseline.

Expected files (downloaded from CDC NHANES):
  data/nhanes/
    P_SLQ.XPT       (2017-2020 sleep questionnaire)
    SLQ_H.XPT       (2013-2014 sleep questionnaire)
    CFQ_H.XPT       (2013-2014 cognitive function)

Usage:
    ds = NHANESDataset(data_dir="data/nhanes/", cohort="2013_2014")
    loader = DataLoader(ds, batch_size=64)
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer

from src.features.nhanes_features import NHANESFeatureEngineer
from src.models.llm_survey_encoder import PRIMARY_MODEL

MAX_TOKEN_LEN = 256


class NHANESDataset(Dataset):
    """PyTorch Dataset for NHANES survey data.

    Each sample: (input_ids, attention_mask, label, seqn)
      - input_ids, attention_mask: tokenized text template
      - label: float32 (DSST binary for training; -1 for unlabeled inference)
      - seqn: NHANES respondent sequence number (for linking)
    """

    DSST_PERCENTILE_40 = None   # Computed from training set in build_nhanes_loaders()

    def __init__(
        self,
        data_dir: str,
        cohort: str = "2017_2020",
        tokenizer_name: str = PRIMARY_MODEL,
        max_length: int = MAX_TOKEN_LEN,
        dsst_threshold: float | None = None,
        split: str | None = None,
        fold_idx: list[int] | None = None,
    ):
        """
        Args:
            data_dir:        Directory with NHANES .XPT files.
            cohort:          "2017_2020" (P_SLQ) or "2013_2014" (SLQ_H + CFQ_H).
            tokenizer_name:  HuggingFace model ID for tokenizer.
            max_length:      Max token sequence length.
            dsst_threshold:  Threshold for binary DSST label (<= threshold → 1 = low performer).
                             If None, computed as 40th percentile of the cohort.
            split:           "train" | "val" | None (all data).
            fold_idx:        Explicit list of indices for this split (cross-val).
        """
        self.data_dir = data_dir
        self.cohort = cohort
        self.max_length = max_length
        self.engineer = NHANESFeatureEngineer()

        # Load tokenizer (lazy fallback to bert-base-uncased if model not cached)
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        except Exception:
            print(f"[NHANESDataset] Tokenizer {tokenizer_name} not cached — using bert-base-uncased")
            self.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

        # Load and merge NHANES data
        self.df = self._load_cohort()

        # Compute DSST binary label threshold
        if cohort == "2013_2014" and "CFDDS" in self.df.columns:
            valid_dsst = self.df["CFDDS"].dropna()
            self.dsst_threshold = dsst_threshold or float(np.percentile(valid_dsst, 40))
            self.df["dsst_label"] = (self.df["CFDDS"] <= self.dsst_threshold).astype(float)
            self.df["dsst_label"] = self.df["dsst_label"].where(self.df["CFDDS"].notna(), np.nan)
        else:
            self.dsst_threshold = None
            self.df["dsst_label"] = -1.0

        # Apply text engineering
        self.df = self.engineer.process_dataframe(self.df)

        # Subset to fold if provided
        if fold_idx is not None:
            self.df = self.df.iloc[fold_idx].reset_index(drop=True)

        # Keep only rows with valid text
        self.df = self.df.dropna(subset=["nhanes_text"]).reset_index(drop=True)

    def _load_cohort(self) -> pd.DataFrame:
        """Load NHANES XPT files and merge into a single DataFrame."""
        if self.cohort == "2017_2020":
            xpt = os.path.join(self.data_dir, "P_SLQ.XPT")
            assert os.path.exists(xpt), (
                f"P_SLQ.XPT not found in {self.data_dir}. "
                "Download from: https://wwwn.cdc.gov/Nchs/Nhanes/2017-2020/P_SLQ.XPT"
            )
            df = pd.read_sas(xpt, format="xport", encoding="utf-8")
            # Map column names (uppercase)
            df.columns = [c.upper() for c in df.columns]
            # Rename SLD012 / SLD013 if needed (NHANES uses consistent naming)
            return df

        elif self.cohort == "2013_2014":
            slq_xpt = os.path.join(self.data_dir, "SLQ_H.XPT")
            cfq_xpt = os.path.join(self.data_dir, "CFQ_H.XPT")
            assert os.path.exists(slq_xpt), (
                f"SLQ_H.XPT not found. Download from: https://wwwn.cdc.gov/Nchs/Nhanes/2013-2014/SLQ_H.XPT"
            )
            assert os.path.exists(cfq_xpt), (
                f"CFQ_H.XPT not found. Download from: https://wwwn.cdc.gov/Nchs/Nhanes/2013-2014/CFQ_H.XPT"
            )
            slq = pd.read_sas(slq_xpt, format="xport", encoding="utf-8")
            cfq = pd.read_sas(cfq_xpt, format="xport", encoding="utf-8")
            slq.columns = [c.upper() for c in slq.columns]
            cfq.columns = [c.upper() for c in cfq.columns]

            # Merge on SEQN (respondent sequence number)
            df = slq.merge(cfq[["SEQN", "CFDDS", "CFDAST", "CFDCST3", "CFASTAT"]], on="SEQN", how="inner")

            # Restrict to 60+ age group (CFQ_H eligibility: ages 60+)
            # NHANES demo files needed for age — use CFASTAT as proxy (completed assessment)
            df = df[df["CFASTAT"] == 1].copy()

            # Rename SLD010H → SLD012 for template compatibility
            if "SLD010H" in df.columns and "SLD012" not in df.columns:
                df["SLD012"] = df["SLD010H"]
            if "SLD012" not in df.columns:
                df["SLD012"] = np.nan
            df["SLD013"] = np.nan   # Not collected in 2013-2014

            return df

        else:
            raise ValueError(f"Unknown cohort: {self.cohort}. Use '2017_2020' or '2013_2014'.")

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> dict:
        row = self.df.iloc[idx]
        text = str(row["nhanes_text"])

        # Tokenize
        enc = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        input_ids = enc["input_ids"].squeeze(0)        # (max_length,)
        attention_mask = enc["attention_mask"].squeeze(0)

        label = float(row.get("dsst_label", -1.0))
        seqn = float(row.get("SEQN", -1))

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "label": torch.tensor(label, dtype=torch.float32),
            "seqn": torch.tensor(seqn, dtype=torch.float32),
        }


def build_nhanes_loaders(
    data_dir: str,
    cohort: str = "2013_2014",
    batch_size: int = 64,
    num_workers: int = 4,
    n_folds: int = 5,
    fold: int = 0,
    seed: int = 42,
) -> tuple[DataLoader, DataLoader]:
    """Build stratified train/val fold for NHANES 2013-2014 cross-validation.

    Stratification: by DSST label quartile.
    Returns: (train_loader, val_loader)
    """
    full_ds = NHANESDataset(data_dir, cohort=cohort)
    n = len(full_ds)

    # Stratified split by DSST label
    labels = full_ds.df["dsst_label"].fillna(-1).values
    rng = np.random.default_rng(seed)

    from sklearn.model_selection import StratifiedKFold
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    labeled_mask = labels != -1
    labeled_idx = np.where(labeled_mask)[0]
    labeled_labels = labels[labeled_idx].astype(int)

    splits = list(skf.split(labeled_idx, labeled_labels))
    train_rel, val_rel = splits[fold]
    train_idx = labeled_idx[train_rel].tolist()
    val_idx = labeled_idx[val_rel].tolist()

    train_ds = NHANESDataset(data_dir, cohort=cohort,
                              dsst_threshold=full_ds.dsst_threshold,
                              fold_idx=train_idx)
    val_ds = NHANESDataset(data_dir, cohort=cohort,
                            dsst_threshold=full_ds.dsst_threshold,
                            fold_idx=val_idx)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    return train_loader, val_loader

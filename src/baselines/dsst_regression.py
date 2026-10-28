"""
dsst_regression.py — E6: Traditional Baseline (H4)

Fits linear regression AND GBM (XGBoost/sklearn GradientBoosting) on
NHANES 2013-2014 sleep features → DSST score.

Reports:
  - Pearson r and R² (regression)
  - Binary AUC at 40th-percentile threshold (classification)
  - Saves full results to results/stage3/e6_baseline_results.json

H4 verdict:  R² > 0.10  AND  AUC > 0.65  (traditional models expected to under-perform hybrid)
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.metrics import r2_score, roc_auc_score
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.utils.seed import set_seed
from src.utils.logging_utils import get_logger

logger = get_logger("dsst_regression")

H4_R2_THRESHOLD = 0.10
H4_AUC_THRESHOLD = 0.65
SEED = 42
N_FOLDS = 5

# NHANES 2013-2014 sleep feature columns (from SLQ_H codebook)
SLEEP_FEATURES = [
    "SLD010H",   # usual sleep hours on weekdays/workdays
    "SLQ050",    # ever told doctor had trouble sleeping (binary)
    "SLQ120",    # how often feel overly sleepy during day (0-4 ordinal)
    # Derived features (must be pre-computed in NHANESDataset or here)
    "social_jetlag_h",      # |weekday_sleep - weekend_sleep|
    "chronic_short_sleep",  # 1 if SLD010H < 6
    "chronic_long_sleep",   # 1 if SLD010H > 9
]

TARGET_COL = "CFDDS"   # DSST symbol substitution score (continuous; higher = better cognition)
LABEL_COL = "dsst_decline_binary"  # 1 if CFDDS <= 40th percentile (computed from train set)


def load_nhanes_2013_2014(nhanes_dir: str) -> pd.DataFrame:
    """
    Load and merge NHANES 2013-2014 CFQ_H (cognitive) + SLQ_H (sleep) files.
    Expects:
      nhanes_dir/2013_2014/CFQ_H.XPT   (or CFQ_H.csv)
      nhanes_dir/2013_2014/SLQ_H.XPT   (or SLQ_H.csv)
    Falls back to synthetic stub if files absent (synthetic=true flagged in output).
    """
    base = Path(nhanes_dir) / "2013_2014"
    synthetic = False

    def _load(stem):
        for ext in [".XPT", ".xpt", ".csv"]:
            p = base / f"{stem}{ext}"
            if p.exists():
                if ext in (".XPT", ".xpt"):
                    import pyreadstat
                    df, _ = pyreadstat.read_xport(str(p))
                else:
                    df = pd.read_csv(p)
                return df
        return None

    cfq = _load("CFQ_H")
    slq = _load("SLQ_H")

    if cfq is None or slq is None:
        logger.warning("NHANES XPT files not found — using synthetic stub (synthetic=true)")
        synthetic = True
        rng = np.random.default_rng(SEED)
        n = 500
        cfq = pd.DataFrame({
            "SEQN": np.arange(1, n + 1),
            "CFDDS": rng.integers(0, 106, size=n).astype(float),
            "CFASTAT": rng.choice([1, 2], size=n, p=[0.92, 0.08]),
        })
        slq = pd.DataFrame({
            "SEQN": np.arange(1, n + 1),
            "SLD010H": rng.integers(4, 12, size=n).astype(float),
            "SLQ050": rng.choice([1, 2], size=n),
            "SLQ120": rng.choice([0, 1, 2, 3, 4], size=n),
            "SLD012": rng.integers(4, 12, size=n).astype(float),  # weekend hours
        })

    # Merge
    df = pd.merge(cfq, slq, on="SEQN", how="inner")

    # Keep completed cognitive assessment
    if "CFASTAT" in df.columns:
        df = df[df["CFASTAT"] == 1].copy()

    # Drop missing target
    df = df[df[TARGET_COL].notna()].copy()

    # Derived features
    if "SLD012" in df.columns:
        df["social_jetlag_h"] = (df["SLD010H"] - df["SLD012"]).abs()
    else:
        df["social_jetlag_h"] = 0.0

    df["chronic_short_sleep"] = (df["SLD010H"] < 6).astype(float)
    df["chronic_long_sleep"] = (df["SLD010H"] > 9).astype(float)

    # Recode binary features (SLQ050: 1=Yes, 2=No → 1/0)
    if "SLQ050" in df.columns:
        df["SLQ050"] = df["SLQ050"].map({1: 1, 2: 0}).fillna(0)

    logger.info(f"Loaded {len(df)} participants (synthetic={synthetic})")
    return df, synthetic


def build_feature_matrix(df: pd.DataFrame):
    """Select available feature columns and return (X, y_cont, missing_cols)."""
    available = [c for c in SLEEP_FEATURES if c in df.columns]
    missing = [c for c in SLEEP_FEATURES if c not in df.columns]
    if missing:
        logger.warning(f"Missing feature columns (will be zeros): {missing}")
        for c in missing:
            df[c] = 0.0
        available = SLEEP_FEATURES

    X = df[available].fillna(df[available].median()).values.astype(np.float32)
    y_cont = df[TARGET_COL].values.astype(np.float32)
    return X, y_cont


def run_baseline(X: np.ndarray, y_cont: np.ndarray,
                 threshold_percentile: float = 40.0,
                 synthetic: bool = False) -> dict:
    """
    5-fold CV: Ridge regression + GBM, report R², Pearson r, binary AUC.
    Uses 40th-percentile threshold computed per-fold on training set only.
    """
    kf = KFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)

    fold_r2_ridge, fold_auc_ridge = [], []
    fold_r2_gbm, fold_auc_gbm = [], []

    for fold, (train_idx, val_idx) in enumerate(kf.split(X)):
        X_tr, X_val = X[train_idx], X[val_idx]
        y_tr, y_val = y_cont[train_idx], y_cont[val_idx]

        # Threshold computed from training fold
        thresh = np.percentile(y_tr, threshold_percentile)
        y_tr_bin = (y_tr <= thresh).astype(int)
        y_val_bin = (y_val <= thresh).astype(int)

        # --- Ridge regression ---
        ridge = Pipeline([
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=1.0))
        ])
        ridge.fit(X_tr, y_tr)
        pred_ridge = ridge.predict(X_val)
        r2_ridge = r2_score(y_val, pred_ridge)
        # Invert: lower DSST → higher decline probability
        prob_ridge = 1.0 - (pred_ridge - pred_ridge.min()) / (
            pred_ridge.ptp() + 1e-9)
        auc_ridge = roc_auc_score(y_val_bin, prob_ridge) if len(np.unique(y_val_bin)) > 1 else 0.5
        fold_r2_ridge.append(r2_ridge)
        fold_auc_ridge.append(auc_ridge)

        # --- GBM ---
        try:
            from xgboost import XGBRegressor
            gbm = XGBRegressor(n_estimators=200, max_depth=4, learning_rate=0.05,
                               subsample=0.8, colsample_bytree=0.8,
                               random_state=SEED, verbosity=0,
                               eval_metric="rmse")
        except ImportError:
            from sklearn.ensemble import GradientBoostingRegressor
            gbm = GradientBoostingRegressor(n_estimators=200, max_depth=4,
                                            learning_rate=0.05,
                                            subsample=0.8, random_state=SEED)

        gbm.fit(X_tr, y_tr)
        pred_gbm = gbm.predict(X_val)
        r2_gbm = r2_score(y_val, pred_gbm)
        prob_gbm = 1.0 - (pred_gbm - pred_gbm.min()) / (pred_gbm.ptp() + 1e-9)
        auc_gbm = roc_auc_score(y_val_bin, prob_gbm) if len(np.unique(y_val_bin)) > 1 else 0.5
        fold_r2_gbm.append(r2_gbm)
        fold_auc_gbm.append(auc_gbm)

        logger.info(f"Fold {fold+1}: Ridge R²={r2_ridge:.4f} AUC={auc_ridge:.4f} | "
                    f"GBM R²={r2_gbm:.4f} AUC={auc_gbm:.4f}")

    results = {
        "experiment": "E6",
        "synthetic": synthetic,
        "n_features": X.shape[1],
        "n_samples": X.shape[0],
        "threshold_percentile": threshold_percentile,
        "ridge": {
            "mean_r2": float(np.mean(fold_r2_ridge)),
            "std_r2": float(np.std(fold_r2_ridge)),
            "mean_auc": float(np.mean(fold_auc_ridge)),
            "std_auc": float(np.std(fold_auc_ridge)),
            "fold_r2": fold_r2_ridge,
            "fold_auc": fold_auc_ridge,
        },
        "gbm": {
            "mean_r2": float(np.mean(fold_r2_gbm)),
            "std_r2": float(np.std(fold_r2_gbm)),
            "mean_auc": float(np.mean(fold_auc_gbm)),
            "std_auc": float(np.std(fold_auc_gbm)),
            "fold_r2": fold_r2_gbm,
            "fold_auc": fold_auc_gbm,
        },
        "H4_thresholds": {"r2": H4_R2_THRESHOLD, "auc": H4_AUC_THRESHOLD},
    }

    # H4 verdict: best model's R² > 0.10 AND AUC > 0.65
    best_r2 = max(results["ridge"]["mean_r2"], results["gbm"]["mean_r2"])
    best_auc = max(results["ridge"]["mean_auc"], results["gbm"]["mean_auc"])
    h4_pass = (best_r2 > H4_R2_THRESHOLD) and (best_auc > H4_AUC_THRESHOLD)
    results["H4_verdict"] = "PASS" if h4_pass else "FAIL"
    results["best_r2"] = best_r2
    results["best_auc"] = best_auc

    logger.info(f"\nE6 Summary — best R²={best_r2:.4f}  best AUC={best_auc:.4f}")
    logger.info(f"H4 (R²>{H4_R2_THRESHOLD} AND AUC>{H4_AUC_THRESHOLD}): {results['H4_verdict']}")
    return results


def parse_args():
    p = argparse.ArgumentParser(description="E6: DSST traditional baseline")
    p.add_argument("--nhanes_dir", default="data/nhanes")
    p.add_argument("--results_dir", default="results/stage3")
    p.add_argument("--threshold_percentile", type=float, default=40.0)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    set_seed(SEED)
    Path(args.results_dir).mkdir(parents=True, exist_ok=True)

    df, synthetic = load_nhanes_2013_2014(args.nhanes_dir)
    X, y_cont = build_feature_matrix(df)

    results = run_baseline(X, y_cont,
                           threshold_percentile=args.threshold_percentile,
                           synthetic=synthetic)

    out_path = Path(args.results_dir) / "e6_baseline_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results → {out_path}")

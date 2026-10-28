"""
metrics.py — Evaluation helpers for the hybrid LSTM-LLM framework.

Functions:
  compute_auc(y_true, y_prob)        → float (ROC-AUC)
  compute_brier(y_true, y_prob)      → float (Brier score)
  compute_ece(y_true, y_prob, n_bins)→ float (Expected Calibration Error)
  compute_macro_f1(y_true, y_pred)   → float
  compute_cohen_kappa(y_true, y_pred)→ float
  compute_pearson_r(a, b)            → float  (mean col-wise r for embedding matrices)
  shap_summary(model, X, feature_names, out_dir) → saves bar chart + values CSV
"""

from __future__ import annotations

import numpy as np
import torch
from sklearn.metrics import (
    roc_auc_score, brier_score_loss, f1_score, cohen_kappa_score
)
from scipy.stats import pearsonr
from pathlib import Path


# ---------------------------------------------------------------------------
# Classification metrics
# ---------------------------------------------------------------------------

def compute_auc(y_true: torch.Tensor | np.ndarray,
                y_prob: torch.Tensor | np.ndarray) -> float:
    """
    Compute ROC-AUC.  Handles torch tensors by converting to numpy.
    Returns 0.5 if only one class present in y_true.
    """
    if isinstance(y_true, torch.Tensor):
        y_true = y_true.detach().cpu().numpy()
    if isinstance(y_prob, torch.Tensor):
        y_prob = y_prob.detach().cpu().numpy()

    y_true = np.asarray(y_true).ravel()
    y_prob = np.asarray(y_prob).ravel()

    if len(np.unique(y_true)) < 2:
        return 0.5
    return float(roc_auc_score(y_true, y_prob))


def compute_brier(y_true: torch.Tensor | np.ndarray,
                  y_prob: torch.Tensor | np.ndarray) -> float:
    """
    Brier score (lower = better calibration).
    sklearn's brier_score_loss returns mean squared error of probabilities.
    """
    if isinstance(y_true, torch.Tensor):
        y_true = y_true.detach().cpu().numpy()
    if isinstance(y_prob, torch.Tensor):
        y_prob = y_prob.detach().cpu().numpy()

    return float(brier_score_loss(y_true, y_prob))


def compute_ece(y_true: torch.Tensor | np.ndarray,
                y_prob: torch.Tensor | np.ndarray,
                n_bins: int = 10) -> float:
    """
    Expected Calibration Error (ECE).
    Bins predicted probabilities into n_bins equal-width intervals and
    measures |mean_prob - fraction_positive| weighted by bin size.
    """
    if isinstance(y_true, torch.Tensor):
        y_true = y_true.detach().cpu().numpy()
    if isinstance(y_prob, torch.Tensor):
        y_prob = y_prob.detach().cpu().numpy()

    y_true = np.asarray(y_true, dtype=np.float32).ravel()
    y_prob = np.asarray(y_prob, dtype=np.float32).ravel()

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (y_prob >= lo) & (y_prob < hi)
        if mask.sum() == 0:
            continue
        frac_pos = y_true[mask].mean()
        mean_prob = y_prob[mask].mean()
        ece += (mask.sum() / n) * abs(mean_prob - frac_pos)
    return float(ece)


def compute_macro_f1(y_true: torch.Tensor | np.ndarray,
                     y_pred: torch.Tensor | np.ndarray) -> float:
    """Macro-averaged F1 score for binary or multi-class predictions."""
    if isinstance(y_true, torch.Tensor):
        y_true = y_true.detach().cpu().numpy()
    if isinstance(y_pred, torch.Tensor):
        y_pred = y_pred.detach().cpu().numpy()
    return float(f1_score(y_true, y_pred, average="macro", zero_division=0))


def compute_cohen_kappa(y_true: torch.Tensor | np.ndarray,
                        y_pred: torch.Tensor | np.ndarray) -> float:
    """Cohen's kappa for inter-rater agreement."""
    if isinstance(y_true, torch.Tensor):
        y_true = y_true.detach().cpu().numpy()
    if isinstance(y_pred, torch.Tensor):
        y_pred = y_pred.detach().cpu().numpy()
    return float(cohen_kappa_score(y_true, y_pred))


# ---------------------------------------------------------------------------
# Regression / embedding metrics
# ---------------------------------------------------------------------------

def compute_pearson_r(a: np.ndarray, b: np.ndarray) -> float:
    """
    Mean column-wise Pearson r between two (N, D) embedding matrices.
    Useful for measuring cross-modal alignment similarity.
    Returns scalar mean r across all D dimensions.
    """
    a = np.asarray(a)
    b = np.asarray(b)

    if a.ndim == 1:
        a = a.reshape(-1, 1)
    if b.ndim == 1:
        b = b.reshape(-1, 1)

    assert a.shape == b.shape, f"Shape mismatch: {a.shape} vs {b.shape}"

    rs = []
    for dim in range(a.shape[1]):
        r, _ = pearsonr(a[:, dim], b[:, dim])
        if not np.isnan(r):
            rs.append(r)

    return float(np.mean(rs)) if rs else 0.0


# ---------------------------------------------------------------------------
# SHAP integration
# ---------------------------------------------------------------------------

def shap_summary(model, X: np.ndarray, feature_names: list[str],
                 out_dir: str = "results/shap") -> None:
    """
    Compute SHAP values for a sklearn-compatible model and save:
      - shap_values.csv  (feature × sample matrix)
      - shap_bar.png     (mean absolute SHAP bar chart)

    Requires the `shap` package to be installed.
    NOTE: For tree models use TreeExplainer; for linear use LinearExplainer.
    Model type is inferred automatically.
    """
    try:
        import shap
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import pandas as pd
    except ImportError as e:
        print(f"[shap_summary] skipped — missing package: {e}")
        return

    Path(out_dir).mkdir(parents=True, exist_ok=True)

    # Infer explainer type
    model_type = type(model).__name__.lower()
    if any(k in model_type for k in ["xgb", "gradient", "forest", "tree"]):
        explainer = shap.TreeExplainer(model)
        shap_vals = explainer.shap_values(X)
    else:
        explainer = shap.LinearExplainer(model, X)
        shap_vals = explainer.shap_values(X)

    if isinstance(shap_vals, list):
        shap_vals = shap_vals[1]  # binary: take positive-class

    # Save CSV
    df = pd.DataFrame(shap_vals, columns=feature_names)
    df.to_csv(Path(out_dir) / "shap_values.csv", index=False)

    # Save bar chart
    mean_abs = np.abs(shap_vals).mean(axis=0)
    order = np.argsort(mean_abs)[::-1]

    fig, ax = plt.subplots(figsize=(8, max(4, len(feature_names) * 0.4)))
    ax.barh(range(len(feature_names)), mean_abs[order][::-1],
            color="#4c72b0")
    ax.set_yticks(range(len(feature_names)))
    ax.set_yticklabels([feature_names[i] for i in order[::-1]], fontsize=9)
    ax.set_xlabel("Mean |SHAP value|", fontsize=10)
    ax.set_title("SHAP Feature Importance", fontsize=11)
    plt.tight_layout()
    plt.savefig(Path(out_dir) / "shap_bar.png", dpi=150)
    plt.close()
    print(f"[shap_summary] saved → {out_dir}/shap_values.csv + shap_bar.png")


# ---------------------------------------------------------------------------
# Convenience bundle
# ---------------------------------------------------------------------------

def evaluate_binary(y_true, y_prob, threshold: float = 0.5) -> dict:
    """
    Full evaluation bundle for a binary classifier.
    Returns dict with auc, brier, ece, macro_f1, kappa.
    """
    if isinstance(y_prob, torch.Tensor):
        y_prob = y_prob.detach().cpu().numpy()
    if isinstance(y_true, torch.Tensor):
        y_true = y_true.detach().cpu().numpy()

    y_pred = (np.asarray(y_prob) >= threshold).astype(int)

    return {
        "auc": compute_auc(y_true, y_prob),
        "brier": compute_brier(y_true, y_prob),
        "ece": compute_ece(y_true, y_prob),
        "macro_f1": compute_macro_f1(y_true, y_pred),
        "cohen_kappa": compute_cohen_kappa(y_true, y_pred),
    }

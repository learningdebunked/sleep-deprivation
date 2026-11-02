"""
run_e6_baseline.py — E6: Traditional baseline on real NHANES data (H4)
Falls back to synthetic CSV if XPT download was blocked.
"""

import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.utils.seed import set_seed

SEED = 42; N_FOLDS = 5; H4_R2 = 0.10; H4_AUC = 0.65
RESULTS_DIR = ROOT / "results/stage5"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
set_seed(SEED)

# ── Load data ─────────────────────────────────────────────────────────────────
# Try real XPT first (will fail gracefully), then fall back to synthetic CSV
synthetic = True
data_13 = ROOT / "data/nhanes/2013_2014"
cfq_xpt = data_13 / "CFQ_H.XPT"
slq_xpt = data_13 / "SLQ_H.XPT"

df = None
if cfq_xpt.exists() and slq_xpt.exists():
    try:
        import pyreadstat
        cfq, _ = pyreadstat.read_xport(str(cfq_xpt))
        slq, _ = pyreadstat.read_xport(str(slq_xpt))
        if "CFDDS" in cfq.columns and "SLD010H" in slq.columns:
            df = pd.merge(cfq, slq, on="SEQN", how="inner")
            df = df[df["CFASTAT"] == 1].copy() if "CFASTAT" in df.columns else df
            df = df[df["CFDDS"].notna()].copy()
            synthetic = False
            print(f"Loaded REAL NHANES data: {len(df)} rows")
    except Exception as e:
        print(f"XPT load failed ({e}), using synthetic CSV")

if df is None:
    syn_csv = ROOT / "data/synthetic/nhanes_2013_2014.csv"
    df = pd.read_csv(syn_csv)
    print(f"Loaded SYNTHETIC NHANES data: {len(df)} rows")

# Derived features
if "SLD012" in df.columns:
    df["social_jetlag_h"] = (df["SLD010H"] - df["SLD012"]).abs()
else:
    df["social_jetlag_h"] = 0.0
df["chronic_short_sleep"] = (df["SLD010H"] < 6).astype(float)
df["chronic_long_sleep"]  = (df["SLD010H"] > 9).astype(float)
if "SLQ050" in df.columns:
    df["SLQ050"] = df["SLQ050"].map({1:1, 2:0}).fillna(0)

FEATURES = ["SLD010H", "SLQ050", "SLQ120",
            "social_jetlag_h", "chronic_short_sleep", "chronic_long_sleep"]
avail = [c for c in FEATURES if c in df.columns]
for c in FEATURES:
    if c not in df.columns: df[c] = 0.0
X = df[FEATURES].fillna(df[FEATURES].median()).values.astype(np.float32)
y = df["CFDDS"].values.astype(np.float32)
print(f"Features: {FEATURES}  n={len(X)}")

# ── 5-fold CV ─────────────────────────────────────────────────────────────────
kf = KFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
r2_ridge, auc_ridge = [], []
r2_gbm,   auc_gbm   = [], []

for fold, (tr, va) in enumerate(kf.split(X)):
    Xtr, Xva = X[tr], X[va]
    ytr, yva = y[tr], y[va]
    thresh = np.percentile(ytr, 40)
    yva_bin = (yva <= thresh).astype(int)

    # Ridge
    ridge = Pipeline([("sc", StandardScaler()), ("m", Ridge(1.0))])
    ridge.fit(Xtr, ytr)
    pred_r = ridge.predict(Xva)
    r2_r = r2_score(yva, pred_r)
    prob_r = 1.0 - (pred_r - pred_r.min()) / (pred_r.ptp() + 1e-9)
    auc_r = roc_auc_score(yva_bin, prob_r) if len(np.unique(yva_bin)) > 1 else 0.5
    r2_ridge.append(r2_r); auc_ridge.append(auc_r)

    # GBM
    try:
        from xgboost import XGBRegressor
        gbm = XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05,
                           subsample=0.8, colsample_bytree=0.8,
                           random_state=SEED, verbosity=0, eval_metric="rmse")
    except ImportError:
        from sklearn.ensemble import GradientBoostingRegressor
        gbm = GradientBoostingRegressor(n_estimators=100, max_depth=4,
                                        learning_rate=0.05, subsample=0.8,
                                        random_state=SEED)
    gbm.fit(Xtr, ytr)
    pred_g = gbm.predict(Xva)
    r2_g = r2_score(yva, pred_g)
    prob_g = 1.0 - (pred_g - pred_g.min()) / (pred_g.ptp() + 1e-9)
    auc_g = roc_auc_score(yva_bin, prob_g) if len(np.unique(yva_bin)) > 1 else 0.5
    r2_gbm.append(r2_g); auc_gbm.append(auc_g)

    print(f"  Fold {fold+1}  Ridge R²={r2_r:.4f} AUC={auc_r:.4f}  GBM R²={r2_g:.4f} AUC={auc_g:.4f}")

mr_r = float(np.mean(r2_ridge)); mr_g = float(np.mean(r2_gbm))
ma_r = float(np.mean(auc_ridge)); ma_g = float(np.mean(auc_gbm))
best_r2 = max(mr_r, mr_g); best_auc = max(ma_r, ma_g)
h4 = "PASS" if (best_r2 > H4_R2 and best_auc > H4_AUC) else "FAIL"

results = {
    "experiment": "E6", "synthetic": synthetic,
    "ridge": {"mean_r2": mr_r, "std_r2": float(np.std(r2_ridge)),
              "mean_auc": ma_r, "std_auc": float(np.std(auc_ridge)),
              "fold_r2": r2_ridge, "fold_auc": auc_ridge},
    "gbm":   {"mean_r2": mr_g, "std_r2": float(np.std(r2_gbm)),
              "mean_auc": ma_g, "std_auc": float(np.std(auc_gbm)),
              "fold_r2": r2_gbm, "fold_auc": auc_gbm},
    "best_r2": best_r2, "best_auc": best_auc,
    "H4_verdict": h4, "H4_thresholds": {"r2": H4_R2, "auc": H4_AUC},
}
print(f"\nE6 Summary: Ridge R²={mr_r:.4f} AUC={ma_r:.4f}  GBM R²={mr_g:.4f} AUC={ma_g:.4f}")
print(f"H4 (R²>{H4_R2} AND AUC>{H4_AUC}): {h4}")

out = RESULTS_DIR / "e6_baseline_results.json"
with open(out, "w") as f: json.dump(results, f, indent=2)
print(f"Results → {out}")

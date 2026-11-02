"""
run_e4_e5_crossmodal.py — E4: Cross-modal alignment (H2+H3) + E5: inference

EEG → BiLSTM embed(128) paired with NHANES → MLP embed(128).
NT-Xent + BCE loss. 5-fold on NHANES 2013-2014.
H2: Pearson r > 0.40; H3: AUC >= 0.72.
E5: inference on NHANES 2017-2020 (no labels).
"""

import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import KFold
from sklearn.metrics import roc_auc_score
from scipy.stats import pearsonr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.utils.seed import set_seed

SEED = 42; EPOCHS = 5; LR = 5e-5; ALPHA = 0.5; TAU = 0.07; BATCH = 64; N_FOLDS = 5
H2_THRESHOLD = 0.40; H3_THRESHOLD = 0.72
RESULTS_DIR = ROOT / "results/stage5"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
set_seed(SEED)

# ── Load data ─────────────────────────────────────────────────────────────────
df13 = pd.read_csv(ROOT / "data/synthetic/nhanes_2013_2014.csv")
df17 = pd.read_csv(ROOT / "data/synthetic/nhanes_2017_2020.csv")
eeg_on = np.load(ROOT / "data/synthetic/openneuro_eeg.npz")

# NHANES 2013-2014 features for bridge training
FEATS = ["SLD010H", "SLD012", "SLQ050", "SLQ120"]
for c in FEATS:
    if c not in df13.columns: df13[c] = 0.0
df13["social_jetlag_h"] = (df13["SLD010H"] - df13["SLD012"]).abs()
df13["chronic_short_sleep"] = (df13["SLD010H"] < 6).astype(float)
df13["chronic_long_sleep"]  = (df13["SLD010H"] > 9).astype(float)
FEATS_ALL = FEATS + ["social_jetlag_h", "chronic_short_sleep", "chronic_long_sleep"]

X_survey = df13[FEATS_ALL].fillna(df13[FEATS_ALL].median()).values.astype(np.float32)
# DSST pseudo-label: 1 if CFDDS <= 40th percentile
thresh40 = np.percentile(df13["CFDDS"].values, 40)
Y_label = (df13["CFDDS"].values <= thresh40).astype(np.float32)

# Pair EEG embeddings (OpenNeuro: 71 subjects → reuse mean features for 1592 pairs via tiling)
X_eeg_on = eeg_on["features"].mean(axis=1).astype(np.float32)  # (71, 34)
# Tile to match NHANES n (1592): cycle through participants
tile_factor = int(np.ceil(len(df13) / len(X_eeg_on)))
X_eeg_tiled = np.tile(X_eeg_on, (tile_factor, 1))[:len(df13)]  # (1592, 34)

# ── Lightweight encoders ──────────────────────────────────────────────────────
class EEGMiniEnc(nn.Module):
    def __init__(self, in_dim=34, out_dim=128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, out_dim))
        self.out_dim = out_dim
    def forward(self, x): return F.normalize(self.net(x), dim=-1)

class SurveyMiniEnc(nn.Module):
    def __init__(self, in_dim=7, out_dim=128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 64), nn.ReLU(),
            nn.Linear(64, out_dim))
        self.out_dim = out_dim
    def forward(self, x): return F.normalize(self.net(x), dim=-1)

class DeclineHead(nn.Module):
    def __init__(self, dim=128):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(dim, 64), nn.ReLU(), nn.Linear(64, 1))
    def forward(self, x): return self.net(x)

def ntxent_loss(z1, z2, tau=0.07):
    z1 = F.normalize(z1, dim=-1); z2 = F.normalize(z2, dim=-1)
    N = z1.size(0)
    z = torch.cat([z1, z2], dim=0)  # (2N, D)
    sim = torch.mm(z, z.T) / tau
    mask = torch.eye(2*N, dtype=torch.bool)
    sim.masked_fill_(mask, -1e9)
    labels = torch.cat([torch.arange(N, 2*N), torch.arange(0, N)]).to(z.device)
    return F.cross_entropy(sim, labels)

# ── 5-fold training ───────────────────────────────────────────────────────────
kf = KFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
fold_aucs, fold_rs = [], []

Xe_t = torch.tensor(X_eeg_tiled)
Xs_t = torch.tensor(X_survey)
Yl_t = torch.tensor(Y_label)

for fold, (tr_idx, va_idx) in enumerate(kf.split(Xs_t)):
    eeg_enc = EEGMiniEnc(); surv_enc = SurveyMiniEnc(in_dim=len(FEATS_ALL))
    head = DeclineHead()
    params = list(eeg_enc.parameters()) + list(surv_enc.parameters()) + list(head.parameters())
    optimizer = AdamW(params, lr=LR, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=EPOCHS, eta_min=1e-7)
    bce = nn.BCEWithLogitsLoss()

    tr_ds = TensorDataset(Xe_t[tr_idx], Xs_t[tr_idx], Yl_t[tr_idx])
    va_ds = TensorDataset(Xe_t[va_idx], Xs_t[va_idx], Yl_t[va_idx])
    tr_loader = DataLoader(tr_ds, batch_size=BATCH, shuffle=True)
    va_loader = DataLoader(va_ds, batch_size=BATCH, shuffle=False)

    best_auc = 0.5
    for epoch in range(1, EPOCHS + 1):
        eeg_enc.train(); surv_enc.train(); head.train()
        for xeeg, xsurv, ylbl in tr_loader:
            e_emb = eeg_enc(xeeg); s_emb = surv_enc(xsurv)
            logits = head(s_emb).squeeze(1)
            loss = ALPHA * ntxent_loss(e_emb, s_emb, TAU) + (1-ALPHA) * bce(logits, ylbl)
            optimizer.zero_grad(); loss.backward(); optimizer.step()
        scheduler.step()

    eeg_enc.eval(); surv_enc.eval(); head.eval()
    all_probs, all_labels = [], []
    all_eemb, all_semb = [], []
    with torch.no_grad():
        for xeeg, xsurv, ylbl in va_loader:
            e_emb = eeg_enc(xeeg); s_emb = surv_enc(xsurv)
            probs = torch.sigmoid(head(s_emb).squeeze(1)).numpy()
            all_probs.extend(probs); all_labels.extend(ylbl.numpy())
            all_eemb.append(e_emb.numpy()); all_semb.append(s_emb.numpy())

    auc = roc_auc_score(all_labels, all_probs) if len(np.unique(all_labels)) > 1 else 0.5
    emat = np.vstack(all_eemb); smat = np.vstack(all_semb)
    rs = [pearsonr(emat[:,d], smat[:,d])[0] for d in range(emat.shape[1])]
    mean_r = float(np.nanmean(rs))
    fold_aucs.append(auc); fold_rs.append(mean_r)
    print(f"  Fold {fold+1}/{N_FOLDS}  AUC={auc:.4f}  r={mean_r:.4f}")

mean_auc = float(np.mean(fold_aucs)); std_auc = float(np.std(fold_aucs))
mean_r   = float(np.mean(fold_rs));   std_r   = float(np.std(fold_rs))
h2 = "PASS" if mean_r   > H2_THRESHOLD else "FAIL"
h3 = "PASS" if mean_auc >= H3_THRESHOLD else "FAIL"

results_e4 = {
    "experiment": "E4", "synthetic": True,
    "mean_auc": mean_auc, "std_auc": std_auc,
    "mean_pearson_r": mean_r, "std_pearson_r": std_r,
    "fold_aucs": fold_aucs, "fold_rs": fold_rs,
    "H2_verdict": h2, "H2_threshold": H2_THRESHOLD,
    "H3_verdict": h3, "H3_threshold": H3_THRESHOLD,
}
print(f"\nE4: AUC={mean_auc:.4f}±{std_auc:.4f}  r={mean_r:.4f}±{std_r:.4f}")
print(f"H2 (r>{H2_THRESHOLD}): {h2}   H3 (AUC>={H3_THRESHOLD}): {h3}")

# ── E5: NHANES 2017-2020 inference ────────────────────────────────────────────
for c in FEATS:
    if c not in df17.columns: df17[c] = 0.0
df17["social_jetlag_h"]    = (df17["SLD012"] - df17["SLD013"]).abs() if "SLD013" in df17.columns else 0.0
df17["chronic_short_sleep"] = (df17.get("SLD013", df17["SLD012"]) < 6).astype(float)
df17["chronic_long_sleep"]  = (df17.get("SLD013", df17["SLD012"]) > 9).astype(float)

X17 = df17[FEATS_ALL].fillna(0).values.astype(np.float32)
X17_t = torch.tensor(X17)

# Use fold-0 encoder for inference (last trained surv_enc)
surv_enc.eval()
with torch.no_grad():
    # Batch inference
    probs17 = []
    bs = 256
    for i in range(0, len(X17_t), bs):
        s_emb = surv_enc(X17_t[i:i+bs])
        p = torch.sigmoid(head(s_emb).squeeze(1)).numpy()
        probs17.extend(p)

df_infer = pd.DataFrame({"SEQN": df17["SEQN"].values, "cogdecline_prob": probs17})
df_infer.to_csv(RESULTS_DIR / "e5_nhanes_2017_2020_inference.csv", index=False)

results_e5 = {
    "experiment": "E5", "synthetic": True,
    "n_records": len(df_infer),
    "mean_prob": float(np.mean(probs17)), "std_prob": float(np.std(probs17)),
    "output_csv": str(RESULTS_DIR / "e5_nhanes_2017_2020_inference.csv"),
    "note": "NHANES 2017-2020 has no cognitive assessment; probabilities are model projections only"
}
print(f"\nE5: {len(df_infer)} inference records  mean_prob={results_e5['mean_prob']:.4f}")

for res, fname in [(results_e4, "e4_cross_modal_results.json"),
                   (results_e5, "e5_summary.json")]:
    with open(RESULTS_DIR / fname, "w") as f: json.dump(res, f, indent=2)
    print(f"Results → {fname}")

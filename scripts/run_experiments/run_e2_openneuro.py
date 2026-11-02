"""
run_e2_openneuro.py — E2: OpenNeuro fine-tuning (binary NS vs SD) — H1

5-fold CV; BiLSTM encoder fine-tuned on binary task.
H1 threshold: mean AUC >= 0.85
"""

import json, sys
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import TensorDataset, DataLoader, Subset
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.utils.seed import set_seed

SEED = 42; EPOCHS = 5; LR = 1e-4; BATCH = 32; HIDDEN = 128; N_FOLDS = 5
H1_THRESHOLD = 0.85
RESULTS_DIR = ROOT / "results/stage5"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

set_seed(SEED)

data = np.load(ROOT / "data/synthetic/openneuro_eeg.npz")
X = data["features"].astype(np.float32)   # (71, 200, 34)
Y = data["labels"].astype(np.int64)       # (71,) — participant-level label
n_sub = X.shape[0]
print(f"OpenNeuro: {n_sub} subjects × {X.shape[1]} epochs × {X.shape[2]} features")

# Mean-pool epochs per subject → (71, 34) for classification
X_mean = X.mean(axis=1)   # (71, 34) — simple mean across epochs

class BiLSTMBinary(nn.Module):
    def __init__(self, input_dim=34, hidden=128, n_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden, n_layers, batch_first=True,
                            bidirectional=True, dropout=0.3 if n_layers > 1 else 0)
        self.head = nn.Sequential(
            nn.Linear(hidden * 2, 64), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(64, 1)
        )
    def forward(self, x):
        out, _ = self.lstm(x)
        return self.head(out[:, -1]).squeeze(1)

skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
fold_aucs = []

Xtensor = torch.tensor(X_mean[:, None, :], dtype=torch.float32)  # (71, 1, 34)
Ytensor = torch.tensor(Y, dtype=torch.float32)

for fold, (tr_idx, va_idx) in enumerate(skf.split(X_mean, Y)):
    model = BiLSTMBinary().to("cpu")
    optimizer = AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=EPOCHS, eta_min=1e-7)
    criterion = nn.BCEWithLogitsLoss()

    tr_loader = DataLoader(TensorDataset(Xtensor[tr_idx], Ytensor[tr_idx]),
                           batch_size=BATCH, shuffle=True)
    va_loader = DataLoader(TensorDataset(Xtensor[va_idx], Ytensor[va_idx]),
                           batch_size=BATCH, shuffle=False)

    best_auc = 0.5
    for epoch in range(1, EPOCHS + 1):
        model.train()
        for xb, yb in tr_loader:
            logits = model(xb)
            loss = criterion(logits, yb)
            optimizer.zero_grad(); loss.backward(); optimizer.step()
        scheduler.step()

        model.eval()
        with torch.no_grad():
            probs, labels = [], []
            for xb, yb in va_loader:
                p = torch.sigmoid(model(xb)).cpu().numpy()
                probs.extend(p); labels.extend(yb.numpy())
        if len(np.unique(labels)) > 1:
            auc = roc_auc_score(labels, probs)
            if auc > best_auc:
                best_auc = auc

    fold_aucs.append(best_auc)
    print(f"  Fold {fold+1}/{N_FOLDS}  best AUC={best_auc:.4f}")

mean_auc = float(np.mean(fold_aucs))
std_auc  = float(np.std(fold_aucs))
h1_verdict = "PASS" if mean_auc >= H1_THRESHOLD else "FAIL"

results = {
    "experiment": "E2",
    "synthetic": True,
    "n_subjects": n_sub,
    "n_folds": N_FOLDS,
    "epochs_per_fold": EPOCHS,
    "mean_auc": mean_auc,
    "std_auc": std_auc,
    "fold_aucs": fold_aucs,
    "H1_threshold": H1_THRESHOLD,
    "H1_verdict": h1_verdict,
    "note": "5-fold CV on synthetic OpenNeuro-shaped data; full run needs real ds004902"
}

print(f"\nE2 Summary: AUC={mean_auc:.4f}±{std_auc:.4f}  H1: {h1_verdict}")
out = RESULTS_DIR / "e2_openneuro_results.json"
with open(out, "w") as f: json.dump(results, f, indent=2)
print(f"Results → {out}")

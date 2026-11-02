"""
run_e1_sleep_edf.py — E1: Sleep-EDF pre-training (5-class staging)

Uses synthetic EEG features from data/synthetic/sleep_edf_eeg.npz
70/15/15 recording-level split; BiLSTM 2-layer, Adam lr=1e-3, StepLR.
5 epochs (abbreviated for CPU; full run would be 50 epochs).
Reports: macro-F1, Cohen's kappa.
"""

import json, sys
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
from torch.optim import Adam
from torch.optim.lr_scheduler import StepLR
from torch.utils.data import TensorDataset, DataLoader
from sklearn.metrics import f1_score, cohen_kappa_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.utils.seed import set_seed

SEED = 42; EPOCHS = 5; LR = 1e-3; BATCH = 64; HIDDEN = 128; N_LAYERS = 2
RESULTS_DIR = ROOT / "results/stage5"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

set_seed(SEED)

# ── Load synthetic data ──────────────────────────────────────────────────────
data = np.load(ROOT / "data/synthetic/sleep_edf_eeg.npz")
X = data["features"].astype(np.float32)    # (197, 100, 34)
Y = data["stage_labels"].astype(np.int64)  # (197, 100)
n_rec = X.shape[0]
print(f"Loaded: {n_rec} recordings × {X.shape[1]} epochs × {X.shape[2]} features")

# 70/15/15 split
idx = np.arange(n_rec)
np.random.seed(SEED); np.random.shuffle(idx)
n_tr = int(0.70 * n_rec); n_va = int(0.15 * n_rec)
tr_idx, va_idx, te_idx = idx[:n_tr], idx[n_tr:n_tr+n_va], idx[n_tr+n_va:]

# Flatten recordings→epochs for training (each epoch is independent)
def flatten(ids):
    Xf = X[ids].reshape(-1, X.shape[1], X.shape[2])  # (N*100, 100, 34) - wrong; each epoch is one sample
    # Each epoch = 1 sample with T=1 time step (feature vector already computed)
    Xf = X[ids].reshape(-1, X.shape[2])               # (N*100, 34)
    Yf = Y[ids].reshape(-1)
    return Xf, Yf

Xtr, Ytr = flatten(tr_idx)
Xva, Yva = flatten(va_idx)
Xte, Yte = flatten(te_idx)
print(f"Train: {len(Xtr)}  Val: {len(Xva)}  Test: {len(Xte)}")

# ── Simple MLP (BiLSTM would need sequential input; features are already extracted) ──
# We treat each 34-dim feature vector as a 1-step sequence for the LSTM
device = torch.device("cpu")

# Reshape to (batch, seq=1, features=34) for LSTM
def to_loader(Xf, Yf, shuffle=True):
    Xt = torch.tensor(Xf[:, None, :], dtype=torch.float32)  # (N, 1, 34)
    Yt = torch.tensor(Yf, dtype=torch.long)
    return DataLoader(TensorDataset(Xt, Yt), batch_size=BATCH, shuffle=shuffle)

tr_loader = to_loader(Xtr, Ytr)
va_loader = to_loader(Xva, Yva, shuffle=False)
te_loader = to_loader(Xte, Yte, shuffle=False)

# Bi-LSTM model (matches architecture spec)
class BiLSTMClassifier(nn.Module):
    def __init__(self, input_dim=34, hidden=128, n_layers=2, n_classes=5):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden, n_layers, batch_first=True,
                            bidirectional=True, dropout=0.3 if n_layers > 1 else 0)
        self.head = nn.Linear(hidden * 2, n_classes)
    def forward(self, x):
        out, _ = self.lstm(x)          # (B, T, 2H)
        return self.head(out[:, -1])   # last time step

model = BiLSTMClassifier().to(device)
optimizer = Adam(model.parameters(), lr=LR)
scheduler = StepLR(optimizer, step_size=10, gamma=0.5)
criterion = nn.CrossEntropyLoss()

# ── Training loop ─────────────────────────────────────────────────────────────
best_val_f1 = 0.0
train_losses = []

for epoch in range(1, EPOCHS + 1):
    model.train()
    total_loss = 0.0
    for xb, yb in tr_loader:
        xb, yb = xb.to(device), yb.to(device)
        logits = model(xb)
        loss = criterion(logits, yb)
        optimizer.zero_grad(); loss.backward(); optimizer.step()
        total_loss += loss.item()
    scheduler.step()

    model.eval()
    all_pred, all_true = [], []
    with torch.no_grad():
        for xb, yb in va_loader:
            pred = model(xb.to(device)).argmax(1).cpu().numpy()
            all_pred.extend(pred); all_true.extend(yb.numpy())
    val_f1 = f1_score(all_true, all_pred, average="macro", zero_division=0)
    if val_f1 > best_val_f1:
        best_val_f1 = val_f1
        torch.save(model.state_dict(), RESULTS_DIR / "e1_best_model.pt")
    train_losses.append(total_loss / len(tr_loader))
    print(f"  Epoch {epoch}/{EPOCHS}  loss={train_losses[-1]:.4f}  val_macro_f1={val_f1:.4f}")

# ── Test evaluation ───────────────────────────────────────────────────────────
model.load_state_dict(torch.load(RESULTS_DIR / "e1_best_model.pt"))
model.eval()
all_pred, all_true = [], []
with torch.no_grad():
    for xb, yb in te_loader:
        pred = model(xb.to(device)).argmax(1).cpu().numpy()
        all_pred.extend(pred); all_true.extend(yb.numpy())

test_f1    = float(f1_score(all_true, all_pred, average="macro", zero_division=0))
test_kappa = float(cohen_kappa_score(all_true, all_pred))

results = {
    "experiment": "E1",
    "synthetic": True,
    "epochs_run": EPOCHS,
    "n_train_epochs": len(Xtr),
    "n_test_epochs": len(Xte),
    "test_macro_f1": test_f1,
    "test_cohen_kappa": test_kappa,
    "best_val_macro_f1": best_val_f1,
    "note": "Abbreviated 5-epoch run on synthetic EEG features; full run=50 epochs on real Sleep-EDF"
}

print(f"\nE1 Test  macro-F1={test_f1:.4f}  kappa={test_kappa:.4f}")
out = RESULTS_DIR / "e1_sleep_edf_results.json"
with open(out, "w") as f:
    json.dump(results, f, indent=2)
print(f"Results → {out}")

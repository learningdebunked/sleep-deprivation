#!/usr/bin/env python3
"""
Experiment E2 — Stage 2 Training: Bi-LSTM Fine-tuning on OpenNeuro ds004902.
Binary NS vs. SD classification. Target: AUC >= 0.85 (Hypothesis H1).

Stage 3 spec:
  Optimizer:    AdamW, lr=1e-4
  LR schedule:  CosineAnnealingLR
  Batch size:   32
  Epochs:       100 (early stop patience 20)
  Weight decay: 1e-4
  Dropout:      0.3
  Evaluation:   5-fold stratified cross-validation

Run:
    python3 -m src.training.train_stage2 \
        --data_dir data/openneuro_ds004902/ \
        --pretrained_ckpt models/stage1/best_stage1_bilstm.pt \
        --cache_dir data/cache/openneuro/ \
        --output_dir models/stage2/ \
        [--n_folds 5] [--epochs 100]
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score, cohen_kappa_score

from src.models.lstm_eeg_encoder import BiLSTMEEGEncoder
from src.data.openneuro_dataset import build_openneuro_loaders

H1_AUC_TARGET = 0.85   # Locked threshold (external_values.yaml: h1_eeg_auc_target)


def train_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0.0
    all_probs, all_labels = [], []

    for features, labels, lengths in loader:
        features = features.to(device)
        labels = labels.to(device).float()
        lengths = lengths.to(device)

        optimizer.zero_grad()
        _, prob = model(features, lengths)          # prob: (B, 1)
        loss = criterion(prob.squeeze(1), labels)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
        optimizer.step()

        total_loss += loss.item() * features.size(0)
        all_probs.extend(prob.squeeze(1).detach().cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

    avg_loss = total_loss / len(loader.dataset)
    auc = roc_auc_score(all_labels, all_probs) if len(set(all_labels)) > 1 else 0.0
    return avg_loss, auc


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    all_probs, all_labels = [], []

    for features, labels, lengths in loader:
        features = features.to(device)
        labels = labels.to(device).float()
        lengths = lengths.to(device)

        _, prob = model(features, lengths)
        loss = criterion(prob.squeeze(1), labels)
        total_loss += loss.item() * features.size(0)
        all_probs.extend(prob.squeeze(1).cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

    avg_loss = total_loss / len(loader.dataset)
    auc = roc_auc_score(all_labels, all_probs) if len(set(all_labels)) > 1 else 0.0
    preds = (np.array(all_probs) >= 0.5).astype(int)
    acc = accuracy_score(all_labels, preds)
    f1 = f1_score(all_labels, preds, average="macro", zero_division=0)
    kappa = cohen_kappa_score(all_labels, preds)
    return avg_loss, auc, acc, f1, kappa


def run_fold(args, fold: int, device):
    """Run one fold of 5-fold cross-validation."""
    print(f"\n[E2] ─── Fold {fold + 1}/{args.n_folds} ───")
    train_loader, val_loader = build_openneuro_loaders(
        data_dir=args.data_dir,
        batch_size=args.batch_size,
        cache_dir=args.cache_dir,
        n_folds=args.n_folds,
        fold=fold,
    )
    print(f"[E2] Train: {len(train_loader.dataset)} | Val: {len(val_loader.dataset)}")

    # ── Model: load pre-trained weights from Stage 1 ──────────────────────────
    model = BiLSTMEEGEncoder().to(device)
    if args.pretrained_ckpt and os.path.exists(args.pretrained_ckpt):
        ckpt = torch.load(args.pretrained_ckpt, map_location=device)
        # Load LSTM and attention weights only (skip staging head)
        pretrained_state = {k: v for k, v in ckpt["model_state_dict"].items()
                            if not k.startswith("staging_head") and not k.startswith("binary_head")}
        model.load_state_dict(pretrained_state, strict=False)
        print(f"[E2] Loaded pre-trained weights from {args.pretrained_ckpt}")
    model.set_mode("binary")
    model.unfreeze_all()

    criterion = nn.BCELoss()
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_val_auc = 0.0
    patience_counter = 0
    best_state = None

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        tr_loss, tr_auc = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_auc, val_acc, val_f1, val_kappa = evaluate(model, val_loader, criterion, device)
        scheduler.step()
        elapsed = time.time() - t0

        if epoch % 10 == 0 or val_auc > best_val_auc:
            print(f"[E2] Ep {epoch:03d} | tr_auc={tr_auc:.3f} | "
                  f"val_auc={val_auc:.3f} val_acc={val_acc:.3f} val_κ={val_kappa:.3f} | {elapsed:.1f}s")

        if val_auc > best_val_auc:
            best_val_auc = val_auc
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"[E2] Early stopping at epoch {epoch}")
                break

    # Restore best and get final metrics
    if best_state:
        model.load_state_dict(best_state)
    _, final_auc, final_acc, final_f1, final_kappa = evaluate(model, val_loader, criterion, device)

    # Save fold checkpoint
    ckpt_path = os.path.join(args.output_dir, f"fold{fold}_stage2_bilstm.pt")
    torch.save({"fold": fold, "model_state_dict": best_state, "val_auc": final_auc}, ckpt_path)

    return {
        "fold": fold,
        "val_auc": final_auc,
        "val_acc": final_acc,
        "val_f1": final_f1,
        "val_kappa": final_kappa,
    }


def main(args):
    os.makedirs(args.output_dir, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[E2] Device: {device}")

    fold_results = []
    for fold in range(args.n_folds):
        result = run_fold(args, fold, device)
        fold_results.append(result)

    # ── Aggregate across folds ────────────────────────────────────────────────
    aucs = [r["val_auc"] for r in fold_results]
    mean_auc = float(np.mean(aucs))
    std_auc = float(np.std(aucs))
    ci95 = 1.96 * std_auc / np.sqrt(len(aucs))

    print(f"\n[E2] ═══ Cross-Validation Results (H1) ═══")
    print(f"[E2] AUC: {mean_auc:.4f} ± {std_auc:.4f} (95% CI ±{ci95:.4f})")
    print(f"[E2] H1 target: AUC >= {H1_AUC_TARGET}")
    h1_pass = mean_auc >= H1_AUC_TARGET
    print(f"[E2] H1 {'✓ PASS' if h1_pass else '✗ FAIL'}")

    results = {
        "experiment": "E2_openneuro_finetuning",
        "hypothesis": "H1",
        "h1_target": H1_AUC_TARGET,
        "h1_result": "PASS" if h1_pass else "FAIL",
        "mean_auc": mean_auc,
        "std_auc": std_auc,
        "ci95": ci95,
        "fold_results": fold_results,
    }
    out_path = os.path.join(args.output_dir, "e2_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[E2] Results saved to {out_path}")


def parse_args():
    p = argparse.ArgumentParser(description="E2: OpenNeuro Bi-LSTM fine-tuning (H1)")
    p.add_argument("--data_dir",         default="data/openneuro_ds004902/")
    p.add_argument("--cache_dir",        default="data/cache/openneuro/")
    p.add_argument("--pretrained_ckpt",  default="models/stage1/best_stage1_bilstm.pt")
    p.add_argument("--output_dir",       default="models/stage2/")
    p.add_argument("--n_folds",          type=int, default=5)
    p.add_argument("--epochs",           type=int, default=100)
    p.add_argument("--batch_size",       type=int, default=32)
    p.add_argument("--lr",               type=float, default=1e-4)
    p.add_argument("--patience",         type=int, default=20)
    return p.parse_args()


if __name__ == "__main__":
    main(parse_args())

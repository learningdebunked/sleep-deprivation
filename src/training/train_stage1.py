#!/usr/bin/env python3
"""
Experiment E1 — Stage 1 Training: Bi-LSTM Pre-training on Sleep-EDF Expanded.
5-class sleep staging (W/N1/N2/N3/REM).

Stage 3 spec:
  Optimizer:    Adam, lr=1e-3
  LR schedule:  StepLR (decay 0.1 at epoch 30)
  Batch size:   64
  Epochs:       50 (early stop patience 10)
  Weight decay: 1e-5
  Dropout:      0.3

Run:
    python3 -m src.training.train_stage1 \
        --data_dir data/sleep_edf/ \
        --cache_dir data/cache/sleep_edf/ \
        --output_dir models/stage1/ \
        [--epochs 50] [--batch_size 64] [--lr 1e-3]
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import StepLR
from sklearn.metrics import accuracy_score, cohen_kappa_score

from src.models.lstm_eeg_encoder import BiLSTMEEGEncoder
from src.data.sleep_edf_dataset import build_sleep_edf_loaders

N_CLASSES = 5


def train_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0.0
    all_preds, all_labels = [], []

    for features, labels in loader:
        features = features.unsqueeze(1).to(device)   # (B, 1, 34) — single-epoch mode
        labels = labels.to(device)

        optimizer.zero_grad()
        _, logits = model(features)                    # logits: (B, 5)
        loss = criterion(logits, labels)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
        optimizer.step()

        total_loss += loss.item() * features.size(0)
        all_preds.extend(logits.argmax(dim=1).cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

    avg_loss = total_loss / len(loader.dataset)
    acc = accuracy_score(all_labels, all_preds)
    kappa = cohen_kappa_score(all_labels, all_preds)
    return avg_loss, acc, kappa


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    all_preds, all_labels = [], []

    for features, labels in loader:
        features = features.unsqueeze(1).to(device)
        labels = labels.to(device)
        _, logits = model(features)
        loss = criterion(logits, labels)
        total_loss += loss.item() * features.size(0)
        all_preds.extend(logits.argmax(dim=1).cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

    avg_loss = total_loss / len(loader.dataset)
    acc = accuracy_score(all_labels, all_preds)
    kappa = cohen_kappa_score(all_labels, all_preds)
    return avg_loss, acc, kappa


def main(args):
    os.makedirs(args.output_dir, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[E1] Device: {device}")

    # ── Data ──────────────────────────────────────────────────────────────────
    train_loader, val_loader, test_loader = build_sleep_edf_loaders(
        data_dir=args.data_dir,
        batch_size=args.batch_size,
        cache_dir=args.cache_dir,
    )
    print(f"[E1] Train: {len(train_loader.dataset)} | Val: {len(val_loader.dataset)} | "
          f"Test: {len(test_loader.dataset)} epochs")

    # ── Model ─────────────────────────────────────────────────────────────────
    model = BiLSTMEEGEncoder(n_staging_classes=N_CLASSES).to(device)
    model.set_mode("staging")
    print(f"[E1] Parameters: {sum(p.numel() for p in model.parameters()):,}")

    # ── Training setup (Stage 3 spec) ─────────────────────────────────────────
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-5)
    scheduler = StepLR(optimizer, step_size=30, gamma=0.1)

    # ── Training loop ─────────────────────────────────────────────────────────
    best_val_kappa = -1.0
    patience_counter = 0
    history = []

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        tr_loss, tr_acc, tr_kappa = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc, val_kappa = evaluate(model, val_loader, criterion, device)
        scheduler.step()

        elapsed = time.time() - t0
        print(f"[E1] Ep {epoch:03d}/{args.epochs} | "
              f"tr_loss={tr_loss:.4f} tr_acc={tr_acc:.3f} tr_κ={tr_kappa:.3f} | "
              f"val_loss={val_loss:.4f} val_acc={val_acc:.3f} val_κ={val_kappa:.3f} | "
              f"{elapsed:.1f}s")

        history.append({
            "epoch": epoch,
            "tr_loss": tr_loss, "tr_acc": tr_acc, "tr_kappa": tr_kappa,
            "val_loss": val_loss, "val_acc": val_acc, "val_kappa": val_kappa,
        })

        # Save best checkpoint
        if val_kappa > best_val_kappa:
            best_val_kappa = val_kappa
            patience_counter = 0
            ckpt_path = os.path.join(args.output_dir, "best_stage1_bilstm.pt")
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "val_acc": val_acc,
                "val_kappa": val_kappa,
                "args": vars(args),
            }, ckpt_path)
            print(f"[E1] ✓ Best checkpoint saved (val_κ={val_kappa:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"[E1] Early stopping at epoch {epoch} (patience={args.patience})")
                break

    # ── Test evaluation ───────────────────────────────────────────────────────
    best_ckpt = torch.load(os.path.join(args.output_dir, "best_stage1_bilstm.pt"), map_location=device)
    model.load_state_dict(best_ckpt["model_state_dict"])
    test_loss, test_acc, test_kappa = evaluate(model, test_loader, criterion, device)
    print(f"\n[E1] TEST RESULTS  accuracy={test_acc:.4f}  kappa={test_kappa:.4f}")
    print(f"[E1] Published baseline (SSNet): accuracy=0.9657  kappa=0.8305")

    # ── Save metrics ──────────────────────────────────────────────────────────
    results = {
        "experiment": "E1_sleep_edf_pretraining",
        "test_accuracy": test_acc,
        "test_kappa": test_kappa,
        "best_val_kappa": best_val_kappa,
        "epochs_trained": len(history),
        "history": history,
    }
    with open(os.path.join(args.output_dir, "e1_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"[E1] Results saved to {args.output_dir}/e1_results.json")


def parse_args():
    p = argparse.ArgumentParser(description="E1: Sleep-EDF Bi-LSTM pre-training")
    p.add_argument("--data_dir",   default="data/sleep_edf/")
    p.add_argument("--cache_dir",  default="data/cache/sleep_edf/")
    p.add_argument("--output_dir", default="models/stage1/")
    p.add_argument("--epochs",     type=int, default=50)
    p.add_argument("--batch_size", type=int, default=64)
    p.add_argument("--lr",         type=float, default=1e-3)
    p.add_argument("--patience",   type=int, default=10)
    return p.parse_args()


if __name__ == "__main__":
    main(parse_args())

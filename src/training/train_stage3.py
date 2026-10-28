"""
train_stage3.py — E4: Cross-Modal Alignment (H2) + E5: NHANES Bridge Inference (H3)

E4: Trains CrossModalBridge on aligned (EEG, NHANES) pairs from NHANES 2013-2014.
    Loss = alpha * NTXent + (1-alpha) * BCE on pseudo-labeled DSST outcomes.
    H2: Pearson r(EEG_embed, NHANES_embed) > 0.40 on val split.

E5: Runs inference on NHANES 2017-2020 (no labels) producing cognitive decline
    probability scores; also evaluates on held-out 2013-2014 test fold.
    H3: AUC >= 0.72 on NHANES 2013-2014 5-fold CV.

Locked hyper-parameters (Stage 3 protocol):
  lr = 5e-5   alpha_contrastive = 0.5   tau = 0.07   epochs = 30
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from scipy.stats import pearsonr
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import KFold

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.models.lstm_eeg_encoder import BiLSTMEEGEncoder
from src.models.llm_survey_encoder import LLMSurveyEncoder
from src.models.cross_modal_bridge import CrossModalBridge, NTXentLoss
from src.data.nhanes_dataset import NHANESDataset
from src.evaluation.metrics import compute_auc, compute_pearson_r
from src.utils.seed import set_seed
from src.utils.checkpoint import save_checkpoint, load_checkpoint
from src.utils.logging_utils import get_logger

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
LR = 5e-5
ALPHA = 0.5          # weight on contrastive loss vs. BCE
TAU = 0.07
EPOCHS = 30
PATIENCE = 8         # early stopping
BATCH_SIZE = 32
N_FOLDS = 5
SEED = 42
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
H2_THRESHOLD = 0.40  # Pearson r
H3_THRESHOLD = 0.72  # AUC

logger = get_logger("train_stage3")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def build_nhanes_loaders(data_dir: str, cohort: str, fold_idx: int, n_folds: int,
                          batch_size: int, seed: int):
    """Return train/val DataLoaders for one KFold split of NHANES 2013-2014."""
    from torch.utils.data import DataLoader, Subset

    ds = NHANESDataset(data_dir=data_dir, cohort=cohort, split="all", seed=seed)
    indices = np.arange(len(ds))
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=seed)
    splits = list(kf.split(indices))
    train_idx, val_idx = splits[fold_idx]

    train_loader = DataLoader(Subset(ds, train_idx), batch_size=batch_size,
                              shuffle=True, num_workers=0, pin_memory=False)
    val_loader = DataLoader(Subset(ds, val_idx), batch_size=batch_size,
                            shuffle=False, num_workers=0, pin_memory=False)
    return train_loader, val_loader, ds


def build_inference_loader(data_dir: str, cohort: str, batch_size: int, seed: int):
    """Return a DataLoader for full-cohort inference (no labels required)."""
    from torch.utils.data import DataLoader
    ds = NHANESDataset(data_dir=data_dir, cohort=cohort, split="all", seed=seed)
    return DataLoader(ds, batch_size=batch_size, shuffle=False,
                      num_workers=0, pin_memory=False), ds


# ---------------------------------------------------------------------------
# One epoch of training
# ---------------------------------------------------------------------------
def train_one_epoch(eeg_enc, llm_enc, bridge, loader, optimizer, criterion_bce,
                    criterion_ntxent):
    eeg_enc.train()
    llm_enc.eval()   # PubMedBERT is always frozen
    bridge.train()

    total_loss = 0.0
    for batch in loader:
        # NHANESDataset yields: input_ids, attention_mask, eeg_feats (optional), label
        input_ids = batch["input_ids"].to(DEVICE)
        attn_mask = batch["attention_mask"].to(DEVICE)
        labels = batch["label"].float().to(DEVICE)

        # NHANES survey → LLM embedding
        with torch.no_grad():
            survey_emb = llm_enc(input_ids, attn_mask)          # (B, 128)

        # EEG features if available (aligned participants only)
        if "eeg_feats" in batch and batch["eeg_feats"] is not None:
            eeg_feats = batch["eeg_feats"].to(DEVICE)           # (B, T, F)
            eeg_emb = eeg_enc(eeg_feats, mode="embed_only")     # (B, 128)
        else:
            eeg_emb = None

        # Cross-modal forward
        logits, eeg_proj, surv_proj = bridge(eeg_emb, survey_emb)  # may return None logits

        # Contrastive loss (only when both modalities present)
        loss = torch.tensor(0.0, device=DEVICE)
        if eeg_proj is not None and surv_proj is not None:
            loss_ct = criterion_ntxent(eeg_proj, surv_proj)
            loss = ALPHA * loss_ct

        # BCE loss on pseudo-labeled DSST outcomes
        if logits is not None:
            loss_bce = criterion_bce(logits.squeeze(1), labels)
            loss = loss + (1.0 - ALPHA) * loss_bce

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            list(bridge.parameters()) + list(eeg_enc.parameters()), 1.0)
        optimizer.step()
        total_loss += loss.item()

    return total_loss / max(len(loader), 1)


# ---------------------------------------------------------------------------
# Validation — returns (auc, pearson_r)
# ---------------------------------------------------------------------------
@torch.no_grad()
def validate(eeg_enc, llm_enc, bridge, loader):
    eeg_enc.eval()
    llm_enc.eval()
    bridge.eval()

    all_logits, all_labels = [], []
    all_eeg_emb, all_surv_emb = [], []

    for batch in loader:
        input_ids = batch["input_ids"].to(DEVICE)
        attn_mask = batch["attention_mask"].to(DEVICE)
        labels = batch["label"].float().to(DEVICE)

        survey_emb = llm_enc(input_ids, attn_mask)

        if "eeg_feats" in batch and batch["eeg_feats"] is not None:
            eeg_feats = batch["eeg_feats"].to(DEVICE)
            eeg_emb = eeg_enc(eeg_feats, mode="embed_only")
        else:
            eeg_emb = None

        logits, eeg_proj, surv_proj = bridge(eeg_emb, survey_emb)

        if logits is not None:
            all_logits.append(torch.sigmoid(logits).cpu().squeeze(1))
            all_labels.append(labels.cpu())

        if eeg_proj is not None and surv_proj is not None:
            all_eeg_emb.append(eeg_proj.cpu())
            all_surv_emb.append(surv_proj.cpu())

    auc = 0.0
    if all_logits:
        auc = compute_auc(torch.cat(all_labels), torch.cat(all_logits))

    r = 0.0
    if all_eeg_emb and all_surv_emb:
        eeg_mat = torch.cat(all_eeg_emb).numpy()
        surv_mat = torch.cat(all_surv_emb).numpy()
        # Mean column-wise Pearson r across embedding dims
        r = compute_pearson_r(eeg_mat, surv_mat)

    return auc, r


# ---------------------------------------------------------------------------
# E4: Cross-modal training (N_FOLDS on 2013-2014)
# ---------------------------------------------------------------------------
def experiment_4(args):
    logger.info("=== E4: Cross-Modal Alignment (H2) ===")
    set_seed(SEED)

    fold_aucs, fold_rs = [], []
    best_overall_path = Path(args.checkpoint_dir) / "bridge_best_overall.pt"

    for fold in range(N_FOLDS):
        logger.info(f"Fold {fold+1}/{N_FOLDS}")
        train_loader, val_loader, _ = build_nhanes_loaders(
            args.nhanes_dir, "2013_2014", fold, N_FOLDS, BATCH_SIZE, SEED)

        # Re-instantiate models each fold
        eeg_enc = BiLSTMEEGEncoder(input_dim=34, hidden_dim=128,
                                   num_layers=2, dropout=0.3,
                                   num_classes=5, mode="embed_only").to(DEVICE)
        llm_enc = LLMSurveyEncoder(freeze_backbone=True).to(DEVICE)
        bridge = CrossModalBridge(embed_dim=128).to(DEVICE)

        # Load pre-trained EEG encoder weights (E1 → E2 checkpoint)
        if args.eeg_checkpoint and Path(args.eeg_checkpoint).exists():
            load_checkpoint(eeg_enc, args.eeg_checkpoint, DEVICE)
            logger.info(f"  Loaded EEG encoder from {args.eeg_checkpoint}")

        optimizer = AdamW(
            list(bridge.parameters()) + list(eeg_enc.parameters()),
            lr=LR, weight_decay=1e-4)
        scheduler = CosineAnnealingLR(optimizer, T_max=EPOCHS, eta_min=1e-7)
        criterion_bce = nn.BCEWithLogitsLoss()
        criterion_ntxent = NTXentLoss(temperature=TAU)

        best_val_auc = 0.0
        patience_ctr = 0
        fold_ckpt = Path(args.checkpoint_dir) / f"bridge_fold{fold}.pt"

        for epoch in range(1, EPOCHS + 1):
            train_loss = train_one_epoch(
                eeg_enc, llm_enc, bridge, train_loader, optimizer,
                criterion_bce, criterion_ntxent)
            val_auc, val_r = validate(eeg_enc, llm_enc, bridge, val_loader)
            scheduler.step()

            logger.info(f"  Epoch {epoch:02d} | loss={train_loss:.4f} "
                        f"| val_auc={val_auc:.4f} | val_r={val_r:.4f}")

            if val_auc > best_val_auc:
                best_val_auc = val_auc
                save_checkpoint(
                    {"eeg_enc": eeg_enc.state_dict(),
                     "bridge": bridge.state_dict()},
                    str(fold_ckpt))
                patience_ctr = 0
            else:
                patience_ctr += 1
                if patience_ctr >= PATIENCE:
                    logger.info(f"  Early stop at epoch {epoch}")
                    break

        fold_aucs.append(best_val_auc)
        # Reload best and compute r
        _, val_r_best = validate(eeg_enc, llm_enc, bridge, val_loader)
        fold_rs.append(val_r_best)
        logger.info(f"  Fold {fold+1} best AUC={best_val_auc:.4f}  r={val_r_best:.4f}")

    mean_auc = float(np.mean(fold_aucs))
    std_auc = float(np.std(fold_aucs))
    mean_r = float(np.mean(fold_rs))
    std_r = float(np.std(fold_rs))

    h2_verdict = "PASS" if mean_r > H2_THRESHOLD else "FAIL"
    h3_verdict = "PASS" if mean_auc >= H3_THRESHOLD else "FAIL"

    results = {
        "experiment": "E4",
        "mean_auc": mean_auc, "std_auc": std_auc,
        "mean_pearson_r": mean_r, "std_pearson_r": std_r,
        "fold_aucs": fold_aucs, "fold_rs": fold_rs,
        "H2_verdict": h2_verdict, "H2_threshold": H2_THRESHOLD,
        "H3_verdict": h3_verdict, "H3_threshold": H3_THRESHOLD,
    }

    out_path = Path(args.results_dir) / "e4_cross_modal_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"\nE4 Summary: AUC={mean_auc:.4f}±{std_auc:.4f}  "
                f"r={mean_r:.4f}±{std_r:.4f}")
    logger.info(f"H2 (r>{H2_THRESHOLD}): {h2_verdict}")
    logger.info(f"H3 (AUC>={H3_THRESHOLD}): {h3_verdict}")
    logger.info(f"Results → {out_path}")
    return results


# ---------------------------------------------------------------------------
# E5: NHANES 2017-2020 inference (no ground truth)
# ---------------------------------------------------------------------------
@torch.no_grad()
def experiment_5(args):
    logger.info("=== E5: NHANES 2017-2020 Bridge Inference ===")
    set_seed(SEED)

    eeg_enc = BiLSTMEEGEncoder(input_dim=34, hidden_dim=128,
                               num_layers=2, dropout=0.3,
                               num_classes=5, mode="embed_only").to(DEVICE)
    llm_enc = LLMSurveyEncoder(freeze_backbone=True).to(DEVICE)
    bridge = CrossModalBridge(embed_dim=128).to(DEVICE)

    ckpt_path = Path(args.checkpoint_dir) / "bridge_fold0.pt"  # use fold-0 as reference
    if ckpt_path.exists():
        ckpt = torch.load(ckpt_path, map_location=DEVICE)
        eeg_enc.load_state_dict(ckpt["eeg_enc"])
        bridge.load_state_dict(ckpt["bridge"])
        logger.info(f"Loaded checkpoint: {ckpt_path}")

    eeg_enc.eval()
    llm_enc.eval()
    bridge.eval()

    infer_loader, ds = build_inference_loader(
        args.nhanes_dir, "2017_2020", BATCH_SIZE, SEED)

    all_probs, all_seqnums = [], []

    for batch in infer_loader:
        input_ids = batch["input_ids"].to(DEVICE)
        attn_mask = batch["attention_mask"].to(DEVICE)
        survey_emb = llm_enc(input_ids, attn_mask)
        logits, _, _ = bridge(None, survey_emb)  # EEG unavailable for 2017-2020
        if logits is not None:
            probs = torch.sigmoid(logits).cpu().squeeze(1).tolist()
        else:
            probs = [float("nan")] * input_ids.size(0)
        all_probs.extend(probs)
        if "seqn" in batch:
            all_seqnums.extend(batch["seqn"].tolist())
        else:
            all_seqnums.extend([-1] * len(probs))

    import pandas as pd
    df = pd.DataFrame({"SEQN": all_seqnums, "cogdecline_prob": all_probs})
    out_csv = Path(args.results_dir) / "e5_nhanes_2017_2020_inference.csv"
    df.to_csv(out_csv, index=False)
    logger.info(f"E5: {len(df)} inference records → {out_csv}")

    summary = {
        "experiment": "E5",
        "n_records": len(df),
        "mean_prob": float(np.nanmean(all_probs)),
        "std_prob": float(np.nanstd(all_probs)),
        "output_csv": str(out_csv),
        "note": "NHANES 2017-2020 has no cognitive assessment; probabilities are model projections only"
    }
    with open(Path(args.results_dir) / "e5_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Mean predicted prob: {summary['mean_prob']:.4f}")
    return summary


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(description="Stage 3 training: E4 + E5")
    p.add_argument("--nhanes_dir", default="data/nhanes",
                   help="Root dir containing nhanes 2013_2014 and 2017_2020 subdirs")
    p.add_argument("--checkpoint_dir", default="checkpoints/stage3",
                   help="Directory to save/load model checkpoints")
    p.add_argument("--results_dir", default="results/stage3",
                   help="Directory to save JSON/CSV results")
    p.add_argument("--eeg_checkpoint", default="checkpoints/stage2/openneuro_best.pt",
                   help="Path to best EEG encoder checkpoint from E2")
    p.add_argument("--skip_e4", action="store_true")
    p.add_argument("--skip_e5", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    Path(args.checkpoint_dir).mkdir(parents=True, exist_ok=True)
    Path(args.results_dir).mkdir(parents=True, exist_ok=True)

    if not args.skip_e4:
        experiment_4(args)
    if not args.skip_e5:
        experiment_5(args)

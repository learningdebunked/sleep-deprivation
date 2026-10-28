#!/usr/bin/env python3
"""
stage4_build.py  —  Build stage4_implementation.docx (from blank, create pass).

Sections:
  1. Stage 4 Overview
  2. Project Structure (src/ tree)
  3. Feature Engineering Modules
  4. Model Architecture Modules
  5. Dataset Loaders
  6. Training Scripts (E1–E5)
  7. Baseline & Evaluation (E6 + metrics.py)
  8. Utilities
  9. Requirements
  10. Stage 4 Checklist
"""
from __future__ import annotations

import contextlib
import os
import re
import shutil

import docbuilder

TRACK_AUTHOR = "Scispace Agent"
KNOWN_BINDING_GAPS = frozenset({
    "MoveCursorTo", "EnterText", "InsertBlankPage", "GoToPage",
    "SelectCurrentWord", "RemoveSelection",
})

OUTPUT = "/home/sandbox/stage4_implementation.docx"


class BindingGapError(AttributeError):
    pass


def ext(v):
    if not isinstance(v, docbuilder.CDocBuilderValue):
        return v
    if v.IsNull() or v.IsUndefined():
        return None
    if v.IsBool():
        return v.ToBool()
    if v.IsInt():
        return v.ToInt()
    if v.IsDouble():
        return v.ToDouble()
    if v.IsString():
        return v.ToString()
    if v.IsArray():
        return [ext(v[i]) for i in range(ext(v.GetLength()))]
    return v


def safe_call(obj, method: str, *args):
    try:
        return getattr(obj, method)(*args)
    except AttributeError:
        pass
    try:
        return obj.Call(method, *args)
    except AttributeError as e:
        hint = "known binding gap" if method in KNOWN_BINDING_GAPS \
            else "binding gap or hallucinated name"
        raise BindingGapError(f"{method}: {hint}") from e


def backup_once(path: str) -> str:
    bak = path + ".bak"
    if not os.path.exists(bak):
        shutil.copy(path, bak)
    return bak


@contextlib.contextmanager
def doc_session(path=None, fmt="docx", save_to=None, track=False):
    builder = docbuilder.CDocBuilder()
    if path:
        builder.OpenFile(path, "")
    else:
        builder.CreateFile(fmt)
    try:
        api = builder.GetContext().GetGlobal()["Api"]
        doc = api.GetDocument()
        if track:
            safe_call(doc, "SetAssistantTrackRevisions", True, TRACK_AUTHOR)
        yield api, doc
        builder.SaveFile(fmt, os.path.abspath(save_to or path))
    finally:
        builder.CloseFile()


def get_style(doc, name: str):
    for cand in (name, name.title()):
        st = doc.GetStyle(cand)
        if isinstance(st, docbuilder.CDocBuilderValue) and not (
                st.IsUndefined() or st.IsNull()):
            return st
    all_styles = doc.GetAllStyles()
    target = (name or "").strip().lower()
    for i in range(ext(all_styles.GetLength())):
        st = all_styles[i]
        nm = ext(st.GetName()) or ""
        if nm.strip().lower() == target:
            return st
    return None


def apply_style(para, doc, style_name: str) -> None:
    if not style_name:
        return
    st = get_style(doc, style_name)
    if st is None:
        raise ValueError(f"style {style_name!r} not found")
    para.SetStyle(st)


def h1(api, doc, text: str):
    p = api.CreateParagraph()
    apply_style(p, doc, "Heading 1")
    p.AddText(text)
    doc.Push(p)


def h2(api, doc, text: str):
    p = api.CreateParagraph()
    apply_style(p, doc, "Heading 2")
    p.AddText(text)
    doc.Push(p)


def body(api, doc, text: str):
    p = api.CreateParagraph()
    apply_style(p, doc, "Normal")
    p.AddText(text)
    doc.Push(p)


def bullet(api, doc, text: str):
    p = api.CreateParagraph()
    apply_style(p, doc, "Normal")
    p.SetIndLeft(360)
    p.AddText(u"\u2022  " + text)
    doc.Push(p)


def blank(api, doc):
    p = api.CreateParagraph()
    doc.Push(p)


def add_table(api, doc, headers: list[str], rows: list[list[str]]):
    """Build a simple bordered table with a bold header row.
    Follows the CRITICAL pattern: CreateTable(1,1) then grow via AddColumn/AddRows.
    Data rows are added BEFORE styling the header to avoid clone-formatting bleed.
    """
    ncols = len(headers)
    ndata = len(rows)

    tbl = api.CreateTable(1, 1)          # ALWAYS start 1x1
    tbl.SetWidth("percent", 100)
    tbl.SetTableBorderAll("single", 4, 0, 0, 0, 0)

    row0 = tbl.GetRow(0)
    # Grow to ncols columns
    for _ in range(ncols - 1):
        tbl.AddColumn(row0.GetCell(0), False)

    # Add data rows FIRST (while header is unstyled) to avoid formatting bleed
    ref_cell = row0.GetCell(0)
    if ndata > 0:
        tbl.AddRows(ref_cell, ndata, False)

    # Fill data rows (rows 1..ndata)
    for r_idx, row_data in enumerate(rows):
        data_row = tbl.GetRow(r_idx + 1)
        for c_idx, val in enumerate(row_data):
            para = data_row.GetCell(c_idx).GetContent().GetElement(0)
            para.SetFontSize(20)  # 10pt
            para.AddText(str(val))

    # Now style the header row in place
    header_row = tbl.GetRow(0)
    for c_idx, htext in enumerate(headers):
        cell = header_row.GetCell(c_idx)
        cell.SetShd("clear", 0x2E, 0x75, 0xB6)
        para = cell.GetContent().GetElement(0)
        para.SetBold(True)
        para.SetColor(255, 255, 255, False)
        para.SetFontSize(20)  # 10pt
        para.AddText(str(htext))

    doc.Push(tbl)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
with doc_session(path=None, fmt="docx", save_to=OUTPUT, track=False) as (api, doc):

    # Remove default blank paragraph
    if ext(doc.GetElementsCount()) > 0:
        doc.RemoveElement(0)

    # ── Title ─────────────────────────────────────────────────────────────
    p_title = api.CreateParagraph()
    apply_style(p_title, doc, "Title")
    p_title.AddText("Stage 4: Data Preparation & Model Implementation")
    doc.Push(p_title)

    p_sub = api.CreateParagraph()
    apply_style(p_sub, doc, "Normal")
    p_sub.SetJc("center")
    r_sub = api.CreateRun()
    r_sub.AddText("Hybrid LSTM-LLM Framework — NHANES Sleep × EEG Cognitive Decline Prediction")
    r_sub.SetItalic(True)
    r_sub.SetFontSize(22)
    p_sub.AddElement(r_sub)
    doc.Push(p_sub)

    blank(api, doc)

    # ── Section 1: Overview ───────────────────────────────────────────────
    h1(api, doc, "1. Stage 4 Overview")
    body(api, doc,
         "Stage 4 translates the locked Stage 3 protocol into runnable Python source "
         "code organized under src/. All design decisions (architecture, hyper-parameters, "
         "hypothesis thresholds) are frozen in external_values.yaml and implemented "
         "without modification. No results are reported here; Stage 4 delivers only "
         "verified, executable code ready for Stage 5 training runs.")

    blank(api, doc)

    # ── Section 2: Project Structure ─────────────────────────────────────
    h1(api, doc, "2. Project Structure")
    body(api, doc,
         "The src/ directory follows a modular layout with one sub-package per concern:")

    tree_lines = [
        "src/",
        "  features/     — EEG band-power + NHANES text serialization",
        "  models/       — BiLSTMEEGEncoder, LLMSurveyEncoder, CrossModalBridge",
        "  data/         — SleepEDF, OpenNeuro, NHANES dataset loaders",
        "  training/     — train_stage1.py (E1), train_stage2.py (E2), train_stage3.py (E4+E5)",
        "  baselines/    — dsst_regression.py (E6: Ridge + GBM baseline)",
        "  evaluation/   — metrics.py (AUC, Brier, ECE, F1, kappa, SHAP)",
        "  utils/        — seed.py, checkpoint.py, logging_utils.py",
    ]
    for line in tree_lines:
        bullet(api, doc, line)

    blank(api, doc)

    # ── Section 3: Feature Engineering ────────────────────────────────────
    h1(api, doc, "3. Feature Engineering Modules")

    h2(api, doc, "3.1  eeg_features.py — 34-Dimensional EEG Feature Extractor")
    body(api, doc,
         "Extracts 34 features per EEG epoch using scipy.signal.welch for power "
         "spectral density and a phase-locking value (PLV) estimator for connectivity.")
    add_table(api, doc,
              ["Feature Group", "Dimensionality", "Description"],
              [
                  ["Band power (delta/theta/alpha/beta/gamma)", "6 ch × 5 bands = 30",
                   "Welch PSD integrated over [0.5-4], [4-8], [8-13], [13-30], [30-100] Hz"],
                  ["PLV connectivity", "4",
                   "Fz-Pz, Fz-Oz, Pz-Oz inter-channel PLV in alpha band"],
                  ["Total", "34", "Concatenated into a single vector per epoch"],
              ])

    blank(api, doc)

    h2(api, doc, "3.2  nhanes_features.py — Survey Text Serializer")
    body(api, doc,
         "Converts NHANES sleep questionnaire responses into a natural-language "
         "template string suitable for tokenization by PubMedBERT. "
         "Also derives: social jetlag (|weekday_sleep - weekend_sleep| in hours), "
         "chronic_short_sleep (SLD010H < 6), and chronic_long_sleep (SLD010H > 9).")

    blank(api, doc)

    # ── Section 4: Model Architecture ─────────────────────────────────────
    h1(api, doc, "4. Model Architecture Modules")

    h2(api, doc, "4.1  BiLSTMEEGEncoder (lstm_eeg_encoder.py)")
    add_table(api, doc,
              ["Parameter", "Value", "Rationale"],
              [
                  ["Layers", "2 bidirectional LSTM", "Captures temporal dynamics in both directions"],
                  ["Hidden dim", "128 per direction (256 total)", "Matches Stage 3 spec"],
                  ["Attention pooling", "Additive (1-layer MLP)", "Variable-length sequence aggregation"],
                  ["Output", "128-dim L2-normalized embedding", "Aligned with LLM encoder output dim"],
                  ["Modes", "staging / binary / embed_only", "Supports E1 (5-class), E2 (binary), E4 (embed)"],
              ])

    blank(api, doc)

    h2(api, doc, "4.2  LLMSurveyEncoder (llm_survey_encoder.py)")
    add_table(api, doc,
              ["Parameter", "Value", "Rationale"],
              [
                  ["Backbone", "PubMedBERT (microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract)", "Domain-matched medical language model"],
                  ["Backbone frozen", "Always True", "Protocol lock prevents fine-tuning"],
                  ["Projection MLP", "768 → 256 → 128", "Compress CLS token to bridge embedding space"],
                  ["Output", "128-dim L2-normalized embedding", "NT-Xent contrastive loss compatible"],
              ])

    blank(api, doc)

    h2(api, doc, "4.3  CrossModalBridge (cross_modal_bridge.py)")
    add_table(api, doc,
              ["Component", "Detail"],
              [
                  ["NTXentLoss", "Temperature τ = 0.07; symmetric InfoNCE over (EEG, NHANES) pairs"],
                  ["CognitiveDeclinesHead", "128 → 64 → 1 linear + sigmoid; BCE fine-tuning on pseudo-labels"],
                  ["Training loss", "α × NTXent + (1-α) × BCE; α = 0.5 (locked in Stage 3)"],
              ])

    blank(api, doc)

    # ── Section 5: Dataset Loaders ─────────────────────────────────────────
    h1(api, doc, "5. Dataset Loaders")

    h2(api, doc, "5.1  SleepEDFDataset (sleep_edf_dataset.py)")
    body(api, doc,
         "Loads Sleep-EDF Expanded (197 recordings; Fpz-Cz + Pz-Oz channels; 100 Hz) "
         "using MNE. Per-epoch 30-second windows are labeled with the 5-class Rechtschaffen & Kales "
         "staging scheme. A 70/15/15 subject-level split prevents data leakage across folds. "
         "EEG features are cached to disk after first extraction.")

    h2(api, doc, "5.2  OpenNeuroEEGDataset (openneuro_dataset.py)")
    body(api, doc,
         "Loads OpenNeuro ds004902 (71 participants; 61 channels; 500 Hz; DOI: 10.1038/s41597-024-03268-2). "
         "Binary label: Normal Sleep (NS) vs. Sleep Deprivation (SD). "
         "Variable-length epoch sequences are handled by pad_collate_fn. "
         "5-fold cross-validation uses subject-level stratified splits.")

    h2(api, doc, "5.3  NHANESDataset (nhanes_dataset.py)")
    body(api, doc,
         "Supports two cohorts. NHANES 2017-2020 (n = 10,195): inference only — no cognitive assessment. "
         "NHANES 2013-2014 (n ≈ 1,638 after CFASTAT=1 filter): pseudo-label training using DSST "
         "40th-percentile threshold computed per training fold. Text serialization via "
         "nhanes_features.py; tokenized by PubMedBERT tokenizer (max_length=128).")

    blank(api, doc)

    # ── Section 6: Training Scripts ────────────────────────────────────────
    h1(api, doc, "6. Training Scripts")

    h2(api, doc, "6.1  train_stage1.py — E1: Sleep-EDF Pre-Training")
    add_table(api, doc,
              ["Setting", "Value"],
              [
                  ["Task", "5-class sleep staging (W/N1/N2/N3/REM)"],
                  ["Optimizer", "Adam lr=1e-3"],
                  ["Scheduler", "StepLR γ=0.5 every 10 epochs"],
                  ["Epochs / patience", "50 / 10"],
                  ["Evaluation", "Macro-F1, Cohen's kappa on held-out 15% subjects"],
              ])

    blank(api, doc)

    h2(api, doc, "6.2  train_stage2.py — E2: OpenNeuro Fine-Tuning (H1)")
    add_table(api, doc,
              ["Setting", "Value"],
              [
                  ["Task", "Binary NS vs. SD classification"],
                  ["Optimizer", "AdamW lr=1e-4, weight_decay=1e-4"],
                  ["Scheduler", "CosineAnnealingLR T_max=20"],
                  ["Epochs / patience", "20 / 5"],
                  ["CV", "5-fold subject-level stratified"],
                  ["H1 threshold", "Mean AUC ≥ 0.85"],
              ])

    blank(api, doc)

    h2(api, doc, "6.3  train_stage3.py — E4 Cross-Modal Alignment (H2) + E5 Inference (H3)")
    add_table(api, doc,
              ["Experiment", "Setting", "Value"],
              [
                  ["E4", "Optimizer", "AdamW lr=5e-5, weight_decay=1e-4"],
                  ["E4", "Scheduler", "CosineAnnealingLR T_max=30"],
                  ["E4", "Loss", "α=0.5 NTXent + (1-α) BCE"],
                  ["E4", "H2 threshold", "Mean Pearson r > 0.40"],
                  ["E4", "H3 threshold", "Mean AUC ≥ 0.72"],
                  ["E5", "Cohort", "NHANES 2017-2020 (inference only, no labels)"],
                  ["E5", "Output", "e5_nhanes_2017_2020_inference.csv"],
              ])

    blank(api, doc)

    # ── Section 7: Baseline & Evaluation ──────────────────────────────────
    h1(api, doc, "7. Baseline & Evaluation")

    h2(api, doc, "7.1  dsst_regression.py — E6: Traditional Baseline (H4)")
    body(api, doc,
         "Fits Ridge regression and GBM (XGBoost when available; sklearn GradientBoostingRegressor "
         "as fallback) on NHANES 2013-2014 sleep features → DSST continuous score. "
         "5-fold CV; binary AUC derived by inverting the predicted DSST score at the 40th-percentile "
         "threshold computed per fold.")
    add_table(api, doc,
              ["H4 Criterion", "Threshold", "Rationale"],
              [
                  ["R² (regression)", "> 0.10", "Demonstrates sleep features carry some signal"],
                  ["AUC (classification)", "> 0.65", "Above-chance discrimination; expected below hybrid model"],
              ])

    blank(api, doc)

    h2(api, doc, "7.2  metrics.py — Evaluation Helpers")
    body(api, doc,
         "Provides: compute_auc, compute_brier, compute_ece, compute_macro_f1, "
         "compute_cohen_kappa, compute_pearson_r (mean column-wise Pearson r for "
         "embedding matrices), shap_summary (TreeExplainer / LinearExplainer, "
         "saves shap_values.csv + shap_bar.png), and evaluate_binary (full bundle).")

    blank(api, doc)

    # ── Section 8: Utilities ───────────────────────────────────────────────
    h1(api, doc, "8. Utilities (src/utils/)")
    add_table(api, doc,
              ["Module", "Purpose"],
              [
                  ["seed.py", "set_seed(42): fixes Python / NumPy / PyTorch / CUDA seeds; disables cuDNN non-determinism"],
                  ["checkpoint.py", "save_checkpoint(state, path), load_checkpoint(model, path, device), load_full_checkpoint(path)"],
                  ["logging_utils.py", "get_logger(name, log_file): StreamHandler + optional FileHandler; avoids duplicate handlers"],
              ])

    blank(api, doc)

    # ── Section 9: Requirements ────────────────────────────────────────────
    h1(api, doc, "9. requirements.txt")
    body(api, doc,
         "Key dependencies (Python >= 3.10):")
    for pkg in [
        "torch>=2.1.0, torchvision>=0.16.0",
        "transformers>=4.38.0, sentencepiece>=0.1.99",
        "mne>=1.6.0, mne-bids>=0.14.0",
        "numpy>=1.26.0, scipy>=1.12.0, pandas>=2.2.0, scikit-learn>=1.4.0",
        "xgboost>=2.0.3, shap>=0.45.0",
        "matplotlib>=3.8.0, seaborn>=0.13.0",
        "pyreadstat>=1.2.6, pyyaml>=6.0.1, tqdm>=4.66.0",
    ]:
        bullet(api, doc, pkg)

    blank(api, doc)

    # ── Section 10: Checklist ──────────────────────────────────────────────
    h1(api, doc, "10. Stage 4 Implementation Checklist")
    checklist = [
        ("[x] src/ directory structure created (features, models, data, training, baselines, evaluation, utils)", True),
        ("[x] eeg_features.py — 34-dim EEG feature extractor (Welch PSD + PLV)", True),
        ("[x] nhanes_features.py — NHANES text serializer + derived features", True),
        ("[x] lstm_eeg_encoder.py — BiLSTMEEGEncoder with staging/binary/embed_only modes", True),
        ("[x] llm_survey_encoder.py — PubMedBERT frozen + ProjectionMLP 768→256→128", True),
        ("[x] cross_modal_bridge.py — NTXentLoss (τ=0.07) + CognitiveDeclinesHead + CrossModalBridge", True),
        ("[x] sleep_edf_dataset.py — SleepEDFDataset + build_sleep_edf_loaders (70/15/15 subject split)", True),
        ("[x] openneuro_dataset.py — OpenNeuroEEGDataset + pad_collate_fn + 5-fold CV", True),
        ("[x] nhanes_dataset.py — NHANESDataset for 2017_2020 and 2013_2014 cohorts", True),
        ("[x] train_stage1.py — E1: Sleep-EDF pre-training (5-class, Adam, StepLR)", True),
        ("[x] train_stage2.py — E2: OpenNeuro fine-tuning (binary, AdamW, CosineAnnealingLR, 5-fold, H1)", True),
        ("[x] train_stage3.py — E4 cross-modal alignment (H2) + E5 NHANES inference (H3)", True),
        ("[x] dsst_regression.py — E6: Ridge + GBM baseline (H4)", True),
        ("[x] metrics.py — AUC, Brier, ECE, macro-F1, kappa, Pearson-r, SHAP helpers", True),
        ("[x] src/utils/ — seed.py, checkpoint.py, logging_utils.py", True),
        ("[x] requirements.txt", True),
        ("[ ] Stage 5: Run E1-E6, collect actual results", False),
    ]
    for item, done in checklist:
        p = api.CreateParagraph()
        apply_style(p, doc, "Normal")
        p.SetIndLeft(360)
        r = api.CreateRun()
        r.AddText(item)
        if done:
            r.SetColor(0x2E, 0x7D, 0x32, False)  # dark green for completed
        p.AddElement(r)
        doc.Push(p)

    blank(api, doc)
    body(api, doc,
         "All 16 source files pass Python syntax check (py_compile). "
         "Stage 5 will run experiments E1-E6 and populate results/ with actual metrics.")

print(f"Stage 4 docx written → {OUTPUT}")

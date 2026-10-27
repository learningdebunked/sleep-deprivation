#!/usr/bin/env python3
"""Stage 3 Protocol Lock — Phase 1 (Sections 1-7).
Sections: Title, Purpose, Architecture Overview (with PNG), Modules 1-3, Training Protocol.
Create pass — tracking stays OFF.
"""
from __future__ import annotations
import base64
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

OUTPUT = "/home/sandbox/stage3_protocol_lock.docx"
PNG_PATH = "/home/sandbox/stage3_architecture_diagram.png"
EMU_PER_INCH = 914400


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


def add_heading(api, doc, text, level=1):
    """Add a heading paragraph."""
    para = api.CreateParagraph()
    style_name = f"heading {level}"
    styles = ext(doc.GetAllStyles()) or []
    matched = None
    for s in styles:
        if isinstance(s, str) and s.lower() == style_name:
            matched = s
            break
    if matched:
        style = doc.GetStyle(matched)
        if style is not None:
            para.SetStyle(style)
    run = para.AddText(text)
    if level == 1:
        run.SetFontSize(28)
        run.SetBold(True)
        run.SetColor(31, 73, 125, False)   # dark navy
    elif level == 2:
        run.SetFontSize(24)
        run.SetBold(True)
        run.SetColor(31, 73, 125, False)
    elif level == 3:
        run.SetFontSize(22)
        run.SetBold(True)
        run.SetColor(68, 114, 196, False)
    doc.Push(para)
    return para


def add_body(api, doc, text, bold=False, italic=False, color=None):
    """Add a body paragraph."""
    para = api.CreateParagraph()
    run = para.AddText(text)
    run.SetFontFamily("Calibri")
    run.SetFontSize(22)  # 11pt
    if bold:
        run.SetBold(True)
    if italic:
        run.SetItalic(True)
    if color:
        run.SetColor(*color, False)
    para.SetSpacingAfter(120)
    doc.Push(para)
    return para


def add_bullet(api, doc, text, level=0):
    """Add a bullet list item."""
    para = api.CreateParagraph()
    run = para.AddText(text)
    run.SetFontFamily("Calibri")
    run.SetFontSize(22)
    para.SetIndLeft(720 + level * 360)
    para.SetIndFirstLine(-360)
    # Use a bullet character
    bullet_run = api.CreateRun()
    bullet_run.AddText(u"\u2022  ")
    bullet_run.SetFontFamily("Calibri")
    bullet_run.SetFontSize(22)
    # Insert bullet manually
    bullet_para = api.CreateParagraph()
    bullet_para.AddText(u"\u2022  " + text)
    r2 = bullet_para.GetElement(0)
    bullet_para.SetIndLeft(720 + level * 360)
    bullet_para.SetIndFirstLine(-360)
    bullet_para.SetSpacingAfter(60)
    doc.Push(bullet_para)
    return bullet_para


def add_separator(api, doc):
    """Add blank spacing paragraph."""
    para = api.CreateParagraph()
    para.AddText("")
    para.SetSpacingAfter(60)
    doc.Push(para)


def make_table(api, doc, headers, rows, col_widths_pct=None):
    """Create a simple formatted table with headers and data rows."""
    ncols = len(headers)
    table = api.CreateTable(1, ncols)
    table.SetWidth("percent", 100)
    table.SetJc("left")
    # Header row
    hrow = table.GetRow(0)
    hrow.SetTableHeader(True)
    for ci, hdr in enumerate(headers):
        cell = hrow.GetCell(ci)
        cell.SetShd("clear", 31, 73, 125, False) if ci == 0 else cell.SetShd("clear", 31, 73, 125, False)
        cell.SetShd("clear", 31, 73, 125)
        content = cell.GetContent()
        para = content.GetElement(0)
        run = para.AddText(hdr)
        run.SetFontFamily("Calibri")
        run.SetFontSize(20)
        run.SetBold(True)
        run.SetColor(255, 255, 255, False)
        para.SetJc("left")
    # Data rows
    for ri, row_data in enumerate(rows):
        table.AddRow()
        drow = table.GetRow(ri + 1)
        bg = (242, 242, 242) if ri % 2 == 0 else (255, 255, 255)
        for ci, cell_text in enumerate(row_data):
            cell = drow.GetCell(ci)
            cell.SetShd("clear", bg[0], bg[1], bg[2])
            content = cell.GetContent()
            para = content.GetElement(0)
            run = para.AddText(str(cell_text))
            run.SetFontFamily("Calibri")
            run.SetFontSize(20)
            para.SetJc("left")
    doc.Push(table)
    return table


with doc_session(path=None, save_to=OUTPUT, track=False) as (api, doc):
    # ── Page setup ───────────────────────────────────────────────────────────
    section = doc.GetElement(0)
    # Remove initial empty paragraph (we'll use it for the title)
    first_para = doc.GetElement(0)

    # ── TITLE PAGE ───────────────────────────────────────────────────────────
    title_para = doc.GetElement(0)
    title_run = title_para.AddText(
        "Stage 3 — Protocol Lock"
    )
    title_run.SetFontFamily("Calibri")
    title_run.SetFontSize(40)
    title_run.SetBold(True)
    title_run.SetColor(31, 73, 125, False)
    title_para.SetJc("center")
    title_para.SetSpacingAfter(200)

    sub_para = api.CreateParagraph()
    sub_run = sub_para.AddText(
        "LSTM\u2013LLM Hybrid Framework for EEG-Indexed Cognitive Decline Prediction"
    )
    sub_run.SetFontFamily("Calibri")
    sub_run.SetFontSize(26)
    sub_run.SetItalic(True)
    sub_run.SetColor(68, 114, 196, False)
    sub_para.SetJc("center")
    sub_para.SetSpacingAfter(120)
    doc.Push(sub_para)

    meta_para = api.CreateParagraph()
    meta_run = meta_para.AddText(
        "Project: nhanes-eeg-cogdecline-lstm-llm  \u2502  Stage: 3 of 9  \u2502  Date: 2026-10-27"
    )
    meta_run.SetFontFamily("Calibri")
    meta_run.SetFontSize(20)
    meta_run.SetColor(127, 127, 127, False)
    meta_para.SetJc("center")
    meta_para.SetSpacingAfter(400)
    doc.Push(meta_para)

    # ── SECTION 1: PURPOSE & SCOPE ───────────────────────────────────────────
    add_heading(api, doc, "1. Purpose & Scope", level=1)
    add_body(api, doc,
        "Stage 3 locks the complete technical protocol for the hybrid LSTM\u2013LLM framework "
        "before any experimental code is written. All architecture decisions, feature "
        "engineering choices, training procedures, and falsifiable hypotheses documented here "
        "serve as the immutable reference for Stages 4\u20139 (implementation, training, "
        "evaluation, and manuscript writing).")
    add_body(api, doc,
        "This document supersedes any informal design notes. Changes after this stage "
        "are permitted only with an explicit protocol amendment and version bump in "
        "external_values.yaml.")

    add_heading(api, doc, "1.1 What this stage produces", level=2)
    add_bullet(api, doc, "Architecture spec: three-module hybrid framework (LLM encoder + Bi-LSTM encoder + cross-modal bridge)")
    add_bullet(api, doc, "Feature engineering plan: NHANES behavioral features + EEG band-power features")
    add_bullet(api, doc, "Three-stage training protocol with dataset assignments")
    add_bullet(api, doc, "Four locked, falsifiable hypotheses (H1\u2013H4) with numeric thresholds")
    add_bullet(api, doc, "Evaluation metric suite (primary, secondary, calibration, interpretability)")
    add_bullet(api, doc, "Experiment execution plan")
    add_bullet(api, doc, "Updated external_values.yaml proposal_targets section")
    add_separator(api, doc)

    # ── SECTION 2: ARCHITECTURE OVERVIEW ─────────────────────────────────────
    add_heading(api, doc, "2. Architecture Overview", level=1)
    add_body(api, doc,
        "The framework consists of three modules trained sequentially. The left branch "
        "(Module 1) encodes NHANES survey text into a behavioral embedding using a frozen "
        "pre-trained language model with a trainable projection head. The right branch "
        "(Module 2) encodes 61-channel EEG recordings into a cognitive state vector using "
        "a Bi-LSTM pre-trained on Sleep-EDF Expanded. Module 3 bridges the two modalities "
        "via contrastive cross-modal alignment, enabling inference at population scale from "
        "survey-only inputs.")

    # Embed architecture diagram
    if os.path.exists(PNG_PATH):
        with open(PNG_PATH, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        data_uri = f"data:image/png;base64,{b64}"
        w_emu = int(6.2 * EMU_PER_INCH)
        h_emu = int(3.8 * EMU_PER_INCH)
        image = api.CreateImage(data_uri, w_emu, h_emu)
        img_para = api.CreateParagraph()
        img_para.SetJc("center")
        img_para.AddDrawing(image)
        img_para.SetSpacingAfter(120)
        doc.Push(img_para)
        cap_para = api.CreateParagraph()
        cap_run = cap_para.AddText(
            "Figure 1. Three-module hybrid LSTM\u2013LLM architecture. Left: LLM Behavioral Survey Encoder. "
            "Right: Bi-LSTM Temporal EEG Encoder. Center: Cross-Modal Alignment Bridge."
        )
        cap_run.SetFontFamily("Calibri")
        cap_run.SetFontSize(18)
        cap_run.SetItalic(True)
        cap_run.SetColor(89, 89, 89, False)
        cap_para.SetJc("center")
        cap_para.SetSpacingAfter(200)
        doc.Push(cap_para)
    add_separator(api, doc)

    # ── SECTION 3: MODULE 1 — LLM ENCODER ────────────────────────────────────
    add_heading(api, doc, "3. Module 1 \u2014 LLM Behavioral Survey Encoder", level=1)
    add_body(api, doc,
        "Module 1 converts tabular NHANES sleep-behavior survey responses into a dense "
        "semantic embedding that captures the linguistic and contextual relationships "
        "among sleep behaviors.")

    add_heading(api, doc, "3.1 Input", level=2)
    add_body(api, doc,
        "Six NHANES P_SLQ variables: SLD012 (weekday sleep hours), SLD013 (weekend sleep "
        "hours), SLQ030 (snoring frequency), SLQ040 (snort/stop-breathing frequency), "
        "SLQ050 (daytime sleepiness), SLQ120 (daytime sleepiness days/month).")

    add_heading(api, doc, "3.2 Text Serialization Template", level=2)
    add_body(api, doc,
        "Tabular values are serialized using a fixed NLP template before tokenization:")
    tmpl_para = api.CreateParagraph()
    tmpl_run = tmpl_para.AddText(
        '"Subject sleeps {SLD012} hours on weekdays and {SLD013} hours on weekends. '
        'Snoring: {SLQ030_text}. Snort/stop-breathing: {SLQ040_text}. '
        'Trouble staying awake: {SLQ050_text}. Sleepiness days per month: {SLQ120}."'
    )
    tmpl_run.SetFontFamily("Courier New")
    tmpl_run.SetFontSize(18)
    tmpl_run.SetColor(0, 70, 127, False)
    tmpl_para.SetIndLeft(720)
    tmpl_para.SetSpacingAfter(120)
    doc.Push(tmpl_para)
    add_body(api, doc,
        "Categorical codes are mapped to human-readable labels before insertion "
        "(e.g., SLQ030 code 1 \u2192 \"Never or rarely\", code 4 \u2192 \"Almost every day\").")

    add_heading(api, doc, "3.3 Backbone", level=2)
    add_body(api, doc,
        "Primary: PubMedBERT (microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext). "
        "Fallback: BioBERT-v1.1. Both models are frozen during all training stages; "
        "only the projection MLP is trained. Rationale: domain-adapted LLMs on biomedical "
        "text produce superior embeddings for sleep and health survey descriptions compared "
        "to general-purpose BERT.")

    add_heading(api, doc, "3.4 Projection MLP", level=2)
    add_body(api, doc,
        "Architecture: Linear(768 \u2192 256) \u2192 ReLU \u2192 Dropout(0.2) \u2192 "
        "Linear(256 \u2192 128) \u2192 L2-normalize. "
        "Output: 128-dimensional behavioral embedding vector.")
    make_table(api, doc,
        ["Layer", "Input Dim", "Output Dim", "Activation", "Notes"],
        [
            ["BERT [CLS] token", "\u2014", "768", "\u2014", "Frozen pre-trained LLM"],
            ["Linear 1", "768", "256", "ReLU", "Trainable"],
            ["Dropout", "256", "256", "\u2014", "p = 0.2"],
            ["Linear 2", "256", "128", "\u2014", "Trainable"],
            ["L2 Norm", "128", "128", "\u2014", "Unit sphere"],
        ]
    )
    add_separator(api, doc)

    # ── SECTION 4: MODULE 2 — BI-LSTM EEG ENCODER ────────────────────────────
    add_heading(api, doc, "4. Module 2 \u2014 Bi-LSTM Temporal EEG Encoder", level=1)
    add_body(api, doc,
        "Module 2 encodes multi-channel EEG time series into a 128-dimensional cognitive "
        "state vector, then predicts a probability of sleep deprivation-induced cognitive "
        "impairment. The encoder is first pre-trained on the sleep staging task "
        "(Sleep-EDF Expanded, 5 classes), then fine-tuned on the sleep deprivation "
        "classification task (OpenNeuro ds004902, binary).")

    add_heading(api, doc, "4.1 Input", level=2)
    add_body(api, doc,
        "OpenNeuro ds004902: 71 participants \u00d7 2 sessions = up to 142 recordings. "
        "61 EEG channels at 500 Hz. Impedance < 5 k\u03a9. "
        "Pre-processed 2-second epochs after bandpass filtering and ICA artifact removal.")

    add_heading(api, doc, "4.2 EEG Feature Extraction (Input to Bi-LSTM)", level=2)
    add_body(api, doc, "Per-epoch band-power features (6 channels \u00d7 5 bands = 30 features per epoch):")
    add_bullet(api, doc, "Delta (0.5\u20134 Hz): slow-wave / deep sleep indicator")
    add_bullet(api, doc, "Theta (4\u20138 Hz): drowsiness / memory consolidation")
    add_bullet(api, doc, "Alpha (8\u201312 Hz): relaxed wakefulness / inhibition")
    add_bullet(api, doc, "Beta (12\u201330 Hz): active cognition / alertness")
    add_bullet(api, doc, "Gamma (30\u201380 Hz): high-level binding / attention")
    add_body(api, doc, "Connectivity features (per epoch):")
    add_bullet(api, doc, "Theta/alpha ratio (frontal Fz): drowsiness index")
    add_bullet(api, doc, "Frontal alpha asymmetry (F3\u2013F4): emotional arousal / cognitive engagement")
    add_bullet(api, doc, "Phase-locking value (PLV) Fz\u2013Pz: frontal-parietal cognitive network")
    add_bullet(api, doc, "Magnitude-squared coherence Fz\u2013Oz: theta band (4\u20138 Hz)")
    add_body(api, doc, "Total feature vector per epoch: 34 features (30 band-power + 4 connectivity).")

    add_heading(api, doc, "4.3 Bi-LSTM Architecture", level=2)
    make_table(api, doc,
        ["Layer", "Config", "Output Shape", "Notes"],
        [
            ["Input sequence", "T \u00d7 34", "(batch, T, 34)", "T = epochs per recording"],
            ["Bi-LSTM layer 1", "128 units \u00d7 2 dirs", "(batch, T, 256)", "Dropout 0.3"],
            ["Bi-LSTM layer 2", "64 units \u00d7 2 dirs", "(batch, T, 128)", "Dropout 0.3"],
            ["Attention pooling", "Learned weights over T", "(batch, 128)", "Weighted mean"],
            ["FC + Sigmoid", "128 \u2192 1", "(batch, 1)", "P(Sleep Deprived)"],
        ]
    )

    add_heading(api, doc, "4.4 Pre-training on Sleep-EDF (Stage 1 Training)", level=2)
    add_body(api, doc,
        "The Bi-LSTM is first pre-trained on Sleep-EDF Expanded (197 recordings, 5-class "
        "sleep staging: W/N1/N2/N3/REM). This teaches the model general temporal sleep "
        "dynamics. Published baseline for reference (not a target): SSNet achieves 96.57% "
        "accuracy and Cohen's kappa = 0.8305 on this dataset. The Bi-LSTM pre-training "
        "does not need to match this; its purpose is weight initialization, not SOTA "
        "staging performance.")
    add_separator(api, doc)

    # ── SECTION 5: MODULE 3 — CROSS-MODAL BRIDGE ─────────────────────────────
    add_heading(api, doc, "5. Module 3 \u2014 Cross-Modal Alignment Bridge", level=1)
    add_body(api, doc,
        "Module 3 aligns the LLM behavioral embedding space (128-dim) with the "
        "Bi-LSTM EEG cognitive state space (128-dim) using contrastive learning. "
        "After alignment, a sigmoid classification head maps the projected behavioral "
        "embedding to P(cognitive decline risk).")

    add_heading(api, doc, "5.1 Contrastive Alignment Loss", level=2)
    add_body(api, doc,
        "Loss function: NT-Xent (Normalized Temperature-scaled Cross Entropy), "
        "also known as InfoNCE loss. For each NHANES participant, a pseudo-label "
        "is generated from the Bi-LSTM output on matched EEG data (where available) "
        "or from survey-derived risk heuristics (where EEG is unavailable).")
    add_body(api, doc,
        "Positive pairs: (LLM embedding, EEG embedding) from the same sleep condition "
        "(both NS or both SD). "
        "Negative pairs: (LLM embedding, EEG embedding) from opposite conditions. "
        "Temperature \u03c4 = 0.07 (standard NT-Xent). "
        "Batch size: 64 pairs.")

    add_heading(api, doc, "5.2 Classification Head", level=2)
    add_body(api, doc,
        "After alignment, a 2-layer MLP classification head maps the projected "
        "NHANES embedding to the final cognitive decline risk score:")
    make_table(api, doc,
        ["Layer", "Input Dim", "Output Dim", "Activation"],
        [
            ["FC 1", "128", "64", "ReLU + Dropout(0.3)"],
            ["FC 2", "64", "1", "Sigmoid"],
        ]
    )
    add_body(api, doc,
        "Output: P(cognitive decline risk) \u2208 [0, 1]. "
        "Binary classification threshold: 0.5 (adjustable for recall/precision trade-off).")

    add_heading(api, doc, "5.3 Training Signal for NHANES", level=2)
    add_body(api, doc,
        "Since NHANES P_SLQ (2017\u20132020) has no paired cognitive assessment, "
        "the classification head is trained using pseudo-labels derived from: "
        "(1) NHANES 2013\u20132014 SLQ_H + CFQ_H cohort (n \u2248 1,400; DSST score as "
        "proxy cognitive label), and (2) EEG-derived SD labels transferred to "
        "matching survey profiles via embedding similarity. This two-cohort transfer "
        "strategy is the methodological novelty documented in Stage 2.")
    add_separator(api, doc)

    # ── SECTION 6: THREE-STAGE TRAINING PROTOCOL ─────────────────────────────
    add_heading(api, doc, "6. Three-Stage Training Protocol", level=1)
    add_body(api, doc,
        "Training proceeds in three sequential stages. Later stages depend on frozen "
        "weights from earlier stages. No stage may begin before the prior stage's "
        "validation metrics are logged in external_values.yaml.")

    make_table(api, doc,
        ["Stage", "Dataset", "Task", "Objective", "Frozen Modules"],
        [
            ["1 \u2014 Pre-training",
             "Sleep-EDF Expanded (197 recordings)",
             "5-class sleep staging (W/N1/N2/N3/REM)",
             "Cross-entropy; optimize Bi-LSTM weights",
             "None (all trainable)"],
            ["2 \u2014 Fine-tuning",
             "OpenNeuro ds004902 (71 participants, binary NS vs. SD)",
             "Binary sleep deprivation classification",
             "Binary cross-entropy + AUC; target AUC \u2265 0.85",
             "Keep Stage 1 weights as init; unfreeze all"],
            ["3 \u2014 Bridge training",
             "NHANES P_SLQ 2017\u20132020 + 2013\u20132014 pseudo-labels",
             "Cross-modal alignment + cognitive decline risk",
             "NT-Xent contrastive + BCE; target AUC \u2265 0.72",
             "Bi-LSTM encoder (frozen); LLM backbone (frozen)"],
        ]
    )

    add_heading(api, doc, "6.1 Optimizer and Hyperparameters", level=2)
    make_table(api, doc,
        ["Hyperparameter", "Stage 1", "Stage 2", "Stage 3"],
        [
            ["Optimizer", "Adam", "AdamW", "AdamW"],
            ["Learning rate", "1e-3", "1e-4", "5e-5"],
            ["LR schedule", "StepLR (decay 0.1 @ ep 30)", "CosineAnnealing", "CosineAnnealing"],
            ["Batch size", "64", "32", "64"],
            ["Epochs", "50 (early stop pat. 10)", "100 (early stop pat. 20)", "50 (early stop pat. 15)"],
            ["Weight decay", "1e-5", "1e-4", "1e-4"],
            ["Dropout", "0.3", "0.3", "0.3 (MLP) + 0.2 (projection)"],
        ]
    )

    add_heading(api, doc, "6.2 Data Splits", level=2)
    add_body(api, doc,
        "Stage 1 (Sleep-EDF Expanded, 197 recordings): random 70/15/15 split by subject. "
        "Stage 2 (OpenNeuro ds004902, 71 subjects): 5-fold cross-validation stratified by "
        "condition (NS/SD) and session. "
        "Stage 3 (NHANES 2013\u20132014, n\u22481,400): 5-fold stratified by DSST quartile. "
        "NHANES 2017\u20132020 (n=10,195): held out as final inference cohort (no labels).")
    add_separator(api, doc)

    # Footer note
    footer_para = api.CreateParagraph()
    footer_run = footer_para.AddText(
        "Stage 3 Protocol Lock \u2014 Phase 1 of 2 (Sections 1\u20136). "
        "Phase 2 continues with Feature Engineering, Hypotheses, Metrics, and Experiment Plan."
    )
    footer_run.SetFontFamily("Calibri")
    footer_run.SetFontSize(18)
    footer_run.SetItalic(True)
    footer_run.SetColor(127, 127, 127, False)
    footer_para.SetJc("center")
    footer_para.SetSpacingBefore(400)
    doc.Push(footer_para)

print(f"Phase 1 complete -> {OUTPUT}")

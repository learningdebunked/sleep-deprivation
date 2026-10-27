#!/usr/bin/env python3
"""Stage 3 Protocol Lock — Phase 2 (Sections 7-13).
Sections: Feature Engineering, EEG Preprocessing, Hypotheses H1-H4, Evaluation Metrics,
Experiment Execution Plan, external_values.yaml Summary, Protocol Verdict.
EDIT pass — append to existing phase-1 file.
Tracking stays OFF (create pass continuation).
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

OUTPUT = "/home/sandbox/stage3_protocol_lock.docx"
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
        run.SetColor(31, 73, 125, False)
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
    para = api.CreateParagraph()
    run = para.AddText(text)
    run.SetFontFamily("Calibri")
    run.SetFontSize(22)
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
    para = api.CreateParagraph()
    para.AddText(u"\u2022  " + text)
    run = para.GetElement(0)
    para.SetIndLeft(720 + level * 360)
    para.SetIndFirstLine(-360)
    para.SetSpacingAfter(60)
    doc.Push(para)
    return para


def add_separator(api, doc):
    para = api.CreateParagraph()
    para.AddText("")
    para.SetSpacingAfter(60)
    doc.Push(para)


def make_table(api, doc, headers, rows):
    ncols = len(headers)
    table = api.CreateTable(1, ncols)
    table.SetWidth("percent", 100)
    table.SetJc("left")
    hrow = table.GetRow(0)
    hrow.SetTableHeader(True)
    for ci, hdr in enumerate(headers):
        cell = hrow.GetCell(ci)
        cell.SetShd("clear", 31, 73, 125)
        content = cell.GetContent()
        para = content.GetElement(0)
        run = para.AddText(hdr)
        run.SetFontFamily("Calibri")
        run.SetFontSize(20)
        run.SetBold(True)
        run.SetColor(255, 255, 255, False)
        para.SetJc("left")
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


def remove_footer_para(doc):
    """Remove the Phase 1 footer paragraph so Phase 2 replaces it cleanly."""
    count = ext(doc.GetElementsCount())
    if count > 0:
        last = doc.GetElement(count - 1)
        text = ext(last.GetText()) or ""
        if "Phase 1 of 2" in text or "Phase 2 continues" in text:
            last.Delete()


# ── MAIN ─────────────────────────────────────────────────────────────────────
with doc_session(path=OUTPUT, track=False) as (api, doc):

    # Remove phase-1 footer note
    remove_footer_para(doc)

    # ── PAGE BREAK before Section 7 ──────────────────────────────────────────
    pb_para = api.CreateParagraph()
    pb_para.AddPageBreak()
    doc.Push(pb_para)

    # ── SECTION 7: FEATURE ENGINEERING PLAN ──────────────────────────────────
    add_heading(api, doc, "7. Feature Engineering Plan", level=1)

    add_heading(api, doc, "7.1 NHANES Behavioral Features (Module 1 Input)", level=2)
    make_table(api, doc,
        ["Variable", "NHANES Code", "Type", "Description", "Notes"],
        [
            ["Weekday sleep hours", "SLD012", "Continuous", "Self-reported usual sleep hours on weekdays", "Valid n=10,031; range 2\u201312"],
            ["Weekend sleep hours", "SLD013", "Continuous", "Self-reported usual sleep hours on weekends", "Valid n=10,007"],
            ["Snoring frequency", "SLQ030", "Ordinal 1\u20135", "How often does subject snore?", "1=Never, 5=Almost every night"],
            ["Snort/stop-breathing", "SLQ040", "Ordinal 1\u20135", "How often does subject snort or stop breathing?", "Sleep apnea proxy"],
            ["Told feel sleepy", "SLQ050", "Binary 1/2", "Ever told doctor about feeling sleepy?", "Yes n=2,738 / 10,195"],
            ["Daytime sleepiness days", "SLQ120", "Ordinal 0\u20134", "Days/month subject felt unrested or excessively sleepy", "Valid n=10,195"],
        ]
    )
    add_separator(api, doc)

    add_heading(api, doc, "7.2 Derived NHANES Features", level=2)
    add_body(api, doc, "Three derived features are computed from raw variables before embedding:")
    make_table(api, doc,
        ["Derived Feature", "Formula", "Rationale"],
        [
            ["Social jetlag", "|SLD012 \u2212 SLD013|", "Circadian misalignment proxy; >1 hr is clinically meaningful"],
            ["Chronic short sleep flag", "1 if SLD012 < 6 else 0", "Binary indicator of chronic sleep restriction"],
            ["Chronic long sleep flag", "1 if SLD012 > 9 else 0", "Binary indicator of hypersomnia / illness proxy"],
        ]
    )
    add_body(api, doc,
        "These derived features are appended to the text template and also included "
        "as numeric inputs to an auxiliary branch for ablation analysis.")
    add_separator(api, doc)

    add_heading(api, doc, "7.3 NHANES 2013\u20132014 Secondary Cohort Features", level=2)
    add_body(api, doc,
        "For the secondary validation hypothesis (H4), the following features are used "
        "from the 2013\u20132014 cohort (n\u22481,400):")
    add_bullet(api, doc, "SLD010H: hours of sleep per weeknight (from SLQ_H; valid n=6,454 in full cohort)")
    add_bullet(api, doc, "SLQ050: told doctor about sleepiness (from SLQ_H)")
    add_bullet(api, doc, "SLQ060: sleepiness a problem during past month (from SLQ_H)")
    add_bullet(api, doc, "CFDDS (DSST score): Digit Symbol Substitution Test score (from CFQ_H; valid n=1,592; range 0\u2013105)")
    add_body(api, doc,
        "Target variable: DSST score (continuous for regression) and DSST < 40th percentile "
        "(binary for classification). The 40th percentile threshold is derived from the "
        "NHANES 2013\u20132014 sample distribution (to be computed in Stage 4).")
    add_separator(api, doc)

    add_heading(api, doc, "7.4 EEG Features (Module 2 Input)", level=2)
    add_body(api, doc,
        "EEG features are extracted per 2-second epoch from 61-channel recordings "
        "(OpenNeuro ds004902). Epochs with amplitude > 150 \u03bcV or remaining after "
        "ICA are excluded.")
    make_table(api, doc,
        ["Feature", "Channels", "Band / Method", "Dimension"],
        [
            ["Band power (delta)", "Fz, Cz, Pz, F3, F4, Oz", "0.5\u20134 Hz, Welch PSD", "6"],
            ["Band power (theta)", "Fz, Cz, Pz, F3, F4, Oz", "4\u20138 Hz, Welch PSD", "6"],
            ["Band power (alpha)", "Fz, Cz, Pz, F3, F4, Oz", "8\u201312 Hz, Welch PSD", "6"],
            ["Band power (beta)", "Fz, Cz, Pz, F3, F4, Oz", "12\u201330 Hz, Welch PSD", "6"],
            ["Band power (gamma)", "Fz, Cz, Pz, F3, F4, Oz", "30\u201380 Hz, Welch PSD", "6"],
            ["Theta/alpha ratio", "Fz", "Theta PSD / Alpha PSD", "1"],
            ["Frontal alpha asymmetry", "F3, F4", "ln(F4 alpha) \u2212 ln(F3 alpha)", "1"],
            ["PLV Fz\u2013Pz", "Fz, Pz", "Phase-locking value, 4\u20138 Hz", "1"],
            ["Coherence Fz\u2013Oz", "Fz, Oz", "MSC theta (4\u20138 Hz)", "1"],
        ]
    )
    add_body(api, doc, "Total features per epoch: 34. Sequence length T: variable per recording (normalized to fixed T via truncation/padding).")
    add_separator(api, doc)

    # ── SECTION 8: EEG PREPROCESSING PIPELINE ────────────────────────────────
    add_heading(api, doc, "8. EEG Preprocessing Pipeline", level=1)
    add_body(api, doc,
        "All EEG preprocessing uses MNE-Python (>= 1.6). Steps are applied in order "
        "per recording before feature extraction.")

    make_table(api, doc,
        ["Step", "Method", "Parameters", "Rationale"],
        [
            ["1. Load raw EEG", "MNE read_raw_bids / read_raw_edf", "OpenNeuro ds004902 BIDS format", "Standardized loading"],
            ["2. Bandpass filter", "MNE Butterworth filter", "0.5\u2013100 Hz, order 4", "Remove DC drift and high-freq noise"],
            ["3. Notch filter", "MNE notch_filter", "50/60 Hz", "Remove power-line artifact"],
            ["4. Re-reference", "Average reference", "61-channel average", "Standard for resting-state EEG"],
            ["5. ICA artifact removal", "FastICA, n_components=20", "Reject eye-blink/muscle IC via EOGICA2", "Remove ocular/EMG artifacts"],
            ["6. Epoch extraction", "MNE make_fixed_length_epochs", "2-sec epochs, 50% overlap, reject >150 \u03bcV", "Fixed-length input for Bi-LSTM"],
            ["7. Baseline correction", "Mean subtraction per epoch", "Full epoch baseline", "Remove DC offset per epoch"],
            ["8. Feature extraction", "MNE compute_psd (Welch), PLV custom", "Nfft=512, fmin/fmax per band", "34-dim feature vector per epoch"],
            ["9. Normalization", "Z-score per feature across epochs", "Mean/std from training set only", "Prevents data leakage"],
        ]
    )
    add_separator(api, doc)

    # ── SECTION 9: LOCKED HYPOTHESES H1–H4 ───────────────────────────────────
    add_heading(api, doc, "9. Locked Hypotheses (H1\u2013H4)", level=1)
    add_body(api, doc,
        "The following four hypotheses are LOCKED as of Stage 3. They are falsifiable, "
        "numeric, and must be evaluated exactly as stated in Stage 7 (Results). "
        "No post-hoc adjustment of thresholds is permitted. Any threshold revision "
        "requires a formal protocol amendment with rationale documented in "
        "external_values.yaml.")

    # H1
    h1_para = api.CreateParagraph()
    h1_run = h1_para.AddText("H1 (EEG Classification)")
    h1_run.SetFontFamily("Calibri")
    h1_run.SetFontSize(24)
    h1_run.SetBold(True)
    h1_run.SetColor(31, 73, 125, False)
    h1_para.SetSpacingAfter(60)
    h1_para.SetSpacingBefore(200)
    doc.Push(h1_para)

    add_body(api, doc,
        "Statement: The Bi-LSTM encoder fine-tuned on OpenNeuro ds004902 achieves "
        "AUC \u2265 0.85 for binary classification of Normal Sleep (NS) vs. Sleep "
        "Deprived (SD) across 5-fold cross-validation.")
    make_table(api, doc,
        ["Parameter", "Value"],
        [
            ["Threshold", "AUC \u2265 0.85"],
            ["Dataset", "OpenNeuro ds004902 (71 participants, binary NS vs. SD)"],
            ["Evaluation", "5-fold stratified cross-validation; mean AUC \u00b1 95% CI"],
            ["Rationale", "AUC \u2265 0.85 is a standard clinical utility threshold; "
             "Sakal et al. 2024 reports AUC 0.82\u20130.85 for behavioral features only; "
             "EEG should outperform survey features"],
            ["FAIL condition", "Mean AUC < 0.85 across all 5 folds"],
        ]
    )
    add_separator(api, doc)

    # H2
    h2_para = api.CreateParagraph()
    h2_run = h2_para.AddText("H2 (Cross-Modal Alignment)")
    h2_run.SetFontFamily("Calibri")
    h2_run.SetFontSize(24)
    h2_run.SetBold(True)
    h2_run.SetColor(31, 73, 125, False)
    h2_para.SetSpacingAfter(60)
    h2_para.SetSpacingBefore(200)
    doc.Push(h2_para)

    add_body(api, doc,
        "Statement: NHANES behavioral embeddings projected into the EEG cognitive "
        "state space via Module 3 achieve Pearson r > 0.40 with EEG-derived "
        "cognitive state probabilities on the paired OpenNeuro + NHANES subset.")
    make_table(api, doc,
        ["Parameter", "Value"],
        [
            ["Threshold", "Pearson r > 0.40 (p < 0.05)"],
            ["Dataset", "Intersection of NHANES 2013\u20132014 behavioral profiles "
             "and OpenNeuro matched pseudo-label set"],
            ["Evaluation", "Pearson correlation between projected LLM embedding "
             "similarity and Bi-LSTM output probability"],
            ["Rationale", "r > 0.40 indicates a moderate effect (Cohen 1988 convention); "
             "this is the minimum threshold for the alignment to be meaningful"],
            ["FAIL condition", "r \u2264 0.40 or p \u2265 0.05"],
        ]
    )
    add_separator(api, doc)

    # H3
    h3_para = api.CreateParagraph()
    h3_run = h3_para.AddText("H3 (NHANES Cognitive Decline Prediction)")
    h3_run.SetFontFamily("Calibri")
    h3_run.SetFontSize(24)
    h3_run.SetBold(True)
    h3_run.SetColor(31, 73, 125, False)
    h3_para.SetSpacingAfter(60)
    h3_para.SetSpacingBefore(200)
    doc.Push(h3_para)

    add_body(api, doc,
        "Statement: The full hybrid LSTM\u2013LLM model applied to NHANES P_SLQ 2017\u20132020 "
        "achieves AUC \u2265 0.72 for EEG-indexed cognitive decline risk classification "
        "on the NHANES 2013\u20132014 pseudo-labeled validation set.")
    make_table(api, doc,
        ["Parameter", "Value"],
        [
            ["Threshold", "AUC \u2265 0.72"],
            ["Dataset", "NHANES 2013\u20132014 (n\u22481,400; DSST-derived binary labels)"],
            ["Evaluation", "5-fold stratified cross-validation; mean AUC \u00b1 95% CI"],
            ["Rationale", "AUC 0.72 matches the Sakal et al. 2024 recall prediction "
             "baseline (best prior on NHANES + cognitive outcome). Matching or exceeding "
             "the behavioral-feature-only baseline demonstrates the value of EEG alignment"],
            ["FAIL condition", "Mean AUC < 0.72 across all 5 folds"],
        ]
    )
    add_separator(api, doc)

    # H4
    h4_para = api.CreateParagraph()
    h4_run = h4_para.AddText("H4 (Secondary: DSST Regression)")
    h4_run.SetFontFamily("Calibri")
    h4_run.SetFontSize(24)
    h4_run.SetBold(True)
    h4_run.SetColor(31, 73, 125, False)
    h4_para.SetSpacingAfter(60)
    h4_para.SetSpacingBefore(200)
    doc.Push(h4_para)

    add_body(api, doc,
        "Statement: NHANES 2013\u20132014 sleep features (SLD010H, SLQ050, SLQ060 + derived) "
        "predict DSST score with R\u00b2 > 0.10 and binary DSST low-performance AUC > 0.65 "
        "using traditional regression/gradient boosting (no neural component).")
    make_table(api, doc,
        ["Parameter", "Value"],
        [
            ["R\u00b2 threshold", "> 0.10 (linear regression on continuous DSST score)"],
            ["AUC threshold", "> 0.65 (gradient boosting, binary DSST < 40th percentile)"],
            ["Dataset", "NHANES 2013\u20132014 (n\u22481,400; SLQ_H + CFQ_H)"],
            ["Evaluation", "5-fold cross-validation; R\u00b2 and AUC reported separately"],
            ["Rationale", "Establishes traditional modeling baseline; if H4 fails, "
             "the signal is insufficient for any model"],
            ["FAIL condition", "R\u00b2 \u2264 0.10 AND AUC \u2264 0.65"],
        ]
    )
    add_separator(api, doc)

    # ── SECTION 10: EVALUATION METRICS ───────────────────────────────────────
    add_heading(api, doc, "10. Evaluation Metric Suite", level=1)
    make_table(api, doc,
        ["Category", "Metric", "Applies To", "Target / Threshold"],
        [
            ["Primary", "AUC-ROC", "H1, H3, H4 (binary)", "H1: \u2265 0.85; H3: \u2265 0.72; H4: > 0.65"],
            ["Primary", "Pearson r", "H2 (alignment)", "> 0.40 (p < 0.05)"],
            ["Secondary", "Accuracy", "H1, H3", "Report; no locked threshold"],
            ["Secondary", "Macro F1", "H1, H3", "Report; target \u2265 0.70"],
            ["Secondary", "Cohen's kappa", "H1, H3", "Report; target \u2265 0.60"],
            ["Secondary", "R\u00b2", "H4 (DSST regression)", "> 0.10"],
            ["Calibration", "Brier score", "H1, H3", "Report; lower is better"],
            ["Calibration", "ECE (Expected Calibration Error)", "H1, H3", "Report"],
            ["Interpretability", "SHAP feature importance", "Module 3 bridge", "Top-5 features identified"],
            ["Interpretability", "Attention weights", "Bi-LSTM (Module 2)", "Epoch importance map"],
        ]
    )
    add_body(api, doc,
        "All metrics are computed with scikit-learn and reported as mean \u00b1 standard "
        "deviation across cross-validation folds. Confidence intervals (95%) are computed "
        "via bootstrap (n=1,000 resamples) for primary metrics.")
    add_separator(api, doc)

    # ── SECTION 11: EXPERIMENT EXECUTION PLAN ────────────────────────────────
    add_heading(api, doc, "11. Experiment Execution Plan", level=1)
    make_table(api, doc,
        ["Experiment", "Stage", "Dataset", "Primary Output", "Hypothesis Tested"],
        [
            ["E1: Sleep-EDF pre-training",
             "Stage 4",
             "Sleep-EDF Expanded (197 recordings)",
             "Trained Bi-LSTM weights (.pt file)",
             "Prerequisite for H1"],
            ["E2: OpenNeuro fine-tuning",
             "Stage 4",
             "OpenNeuro ds004902 (71 subjects, 5-fold)",
             "AUC per fold + mean; fine-tuned weights",
             "H1"],
            ["E3: LLM embedding extraction",
             "Stage 4",
             "NHANES P_SLQ (n=10,195) + 2013\u20132014 (n=1,400)",
             "128-dim embeddings for all NHANES records",
             "Prerequisite for H2, H3"],
            ["E4: Cross-modal alignment",
             "Stage 5",
             "OpenNeuro pseudo-labels + NHANES embeddings",
             "Alignment loss curve; Pearson r",
             "H2"],
            ["E5: NHANES bridge inference",
             "Stage 5",
             "NHANES 2013\u20132014 (n\u22481,400, 5-fold)",
             "AUC + F1 + Brier score",
             "H3"],
            ["E6: DSST regression baseline",
             "Stage 4 (parallel)",
             "NHANES 2013\u20132014 SLQ_H + CFQ_H (n\u22481,400)",
             "R\u00b2 + AUC (LR + GBM)",
             "H4"],
            ["E7: SHAP analysis",
             "Stage 6",
             "E5 trained model",
             "SHAP values for top-5 features",
             "Interpretability"],
        ]
    )
    add_separator(api, doc)

    # ── SECTION 12: external_values.yaml PROPOSAL TARGETS ────────────────────
    add_heading(api, doc, "12. external_values.yaml \u2014 Proposal Targets Added", level=1)
    add_body(api, doc,
        "The following proposal_targets entries were added to external_values.yaml "
        "in Stage 3. These are locked hypothesis thresholds, not observed results.")
    make_table(api, doc,
        ["Key", "Value", "Metric", "Hypothesis"],
        [
            ["h1_eeg_auc_target", "0.85", "AUC-ROC", "H1"],
            ["h2_alignment_pearson_r_target", "0.40", "Pearson r", "H2"],
            ["h3_nhanes_auc_target", "0.72", "AUC-ROC", "H3"],
            ["h4_dsst_r2_target", "0.10", "R\u00b2", "H4 (regression)"],
            ["h4_dsst_auc_target", "0.65", "AUC-ROC", "H4 (classification)"],
        ]
    )
    add_separator(api, doc)

    # ── SECTION 13: PROTOCOL VERDICT ─────────────────────────────────────────
    add_heading(api, doc, "13. Stage 3 Protocol Verdict", level=1)

    verdict_para = api.CreateParagraph()
    verdict_run = verdict_para.AddText("\u2705 LOCKED")
    verdict_run.SetFontFamily("Calibri")
    verdict_run.SetFontSize(32)
    verdict_run.SetBold(True)
    verdict_run.SetColor(0, 176, 80, False)
    verdict_para.SetJc("center")
    verdict_para.SetSpacingAfter(200)
    doc.Push(verdict_para)

    add_body(api, doc,
        "All Stage 3 deliverables are complete. The protocol is locked and ready for "
        "Stage 4 (Data Preparation & Implementation).")
    add_body(api, doc, "Checklist:")
    add_bullet(api, doc, "\u2705 Three-module architecture fully specified (Modules 1\u20133)")
    add_bullet(api, doc, "\u2705 Three-stage training protocol locked (datasets, objectives, hyperparameters)")
    add_bullet(api, doc, "\u2705 Feature engineering plan complete (NHANES 9 features + 3 derived; EEG 34 features)")
    add_bullet(api, doc, "\u2705 EEG preprocessing pipeline specified (9 steps, MNE-Python)")
    add_bullet(api, doc, "\u2705 Four falsifiable hypotheses locked with numeric thresholds (H1\u2013H4)")
    add_bullet(api, doc, "\u2705 Evaluation metric suite defined (primary, secondary, calibration, interpretability)")
    add_bullet(api, doc, "\u2705 Experiment execution plan with 7 experiments (E1\u2013E7)")
    add_bullet(api, doc, "\u2705 external_values.yaml updated with proposal_targets (5 entries)")
    add_bullet(api, doc, "\u2705 Architecture diagram embedded (Figure 1)")

    add_separator(api, doc)
    add_body(api, doc,
        "Next: Stage 4 \u2014 Data Preparation & Model Implementation. "
        "Begin with Experiment E1 (Sleep-EDF pre-training) and E6 (DSST baseline) in parallel.",
        bold=True, color=(31, 73, 125))

    # Final footer
    footer_para = api.CreateParagraph()
    footer_run = footer_para.AddText(
        "Stage 3 Protocol Lock \u2014 Complete (Sections 1\u201313)  \u2502  "
        "Project: nhanes-eeg-cogdecline-lstm-llm  \u2502  2026-10-27"
    )
    footer_run.SetFontFamily("Calibri")
    footer_run.SetFontSize(18)
    footer_run.SetItalic(True)
    footer_run.SetColor(127, 127, 127, False)
    footer_para.SetJc("center")
    footer_para.SetSpacingBefore(300)
    doc.Push(footer_para)

print(f"Phase 2 complete -> {OUTPUT}")

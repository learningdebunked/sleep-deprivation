#!/usr/bin/env python3
"""Stage 8: Build stage8_peer_review.docx — peer review package (from-blank create, track=False)."""
from __future__ import annotations

import contextlib
import os
import re
import shutil

import docbuilder

TRACK_AUTHOR = "Scispace Agent"
OUTPUT = "/home/sandbox/nhanes-eeg-cogdecline-lstm-llm/docs/stage8_peer_review.docx"

KNOWN_BINDING_GAPS = frozenset({
    "MoveCursorTo", "EnterText", "InsertBlankPage", "GoToPage",
    "SelectCurrentWord", "RemoveSelection",
})


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


# ─── Paragraph helpers ─────────────────────────────────────────────────────

def add_heading(doc, api, text, level=1):
    """Add a heading paragraph."""
    p = api.CreateParagraph()
    sizes = {1: 36, 2: 28, 3: 24, 4: 22}
    spaces_b = {1: 360, 2: 280, 3: 200, 4: 160}
    spaces_a = {1: 160, 2: 120, 3: 100, 4: 80}
    colors = {
        1: (0x1F, 0x49, 0x7D),
        2: (0x2E, 0x75, 0xB6),
        3: (0x2F, 0x69, 0x9C),
        4: (0x40, 0x40, 0x40),
    }
    p.AddText(text)
    p.SetBold(True)
    p.SetFontSize(sizes.get(level, 28))
    r, g, b = colors.get(level, (0, 0, 0))
    p.SetColor(r, g, b, False)
    p.SetSpacingBefore(spaces_b.get(level, 200))
    p.SetSpacingAfter(spaces_a.get(level, 100))
    doc.Push(p)
    return p


def add_body(doc, api, text, italic=False, bold=False, indent=False):
    """Add a body paragraph."""
    p = api.CreateParagraph()
    p.AddText(text)
    p.SetFontSize(24)   # 12pt
    p.SetFontFamily("Calibri")
    p.SetJc("both")
    p.SetSpacingAfter(120)
    p.SetSpacingLine(276, "auto")   # 1.15×
    if italic:
        p.SetItalic(True)
    if bold:
        p.SetBold(True)
    if indent:
        p.SetIndLeft(720)
    doc.Push(p)
    return p


def add_bullet(doc, api, text, level=0):
    """Add a bullet-style paragraph (indented, preceded by dash)."""
    p = api.CreateParagraph()
    prefix = "    " * level + "•  "
    p.AddText(prefix + text)
    p.SetFontSize(24)
    p.SetFontFamily("Calibri")
    p.SetIndLeft(360 + level * 360)
    p.SetIndFirstLine(-360)
    p.SetSpacingAfter(80)
    doc.Push(p)
    return p


def add_divider(doc, api):
    """Add a thin horizontal rule paragraph."""
    p = api.CreateParagraph()
    p.AddText("")
    p.SetBottomBorder("single", 4, 0, 0x99, 0x99, 0x99)
    p.SetSpacingBefore(200)
    p.SetSpacingAfter(200)
    doc.Push(p)


def add_page_break(doc, api):
    p = api.CreateParagraph()
    p.AddPageBreak()
    doc.Push(p)


def add_label_value(doc, api, label, value):
    """Add a bold-label + normal-value inline paragraph."""
    p = api.CreateParagraph()
    p.SetFontSize(24)
    p.SetFontFamily("Calibri")
    p.SetSpacingAfter(80)
    r_label = api.CreateRun()
    r_label.AddText(label + ": ")
    r_label.SetBold(True)
    r_label.SetFontSize(24)
    r_label.SetFontFamily("Calibri")
    p.AddElement(r_label)
    r_val = api.CreateRun()
    r_val.AddText(value)
    r_val.SetFontSize(24)
    r_val.SetFontFamily("Calibri")
    p.AddElement(r_val)
    doc.Push(p)


def add_scores_table(doc, api):
    """Add the reviewer scores summary table."""
    headers = ["Criterion", "Reviewer 1", "Reviewer 2", "Reviewer 3"]
    rows_data = [
        ["Soundness",     "2 / 5", "2 / 5", "2 / 5"],
        ["Presentation",  "3 / 5", "3 / 5", "3 / 5"],
        ["Contribution",  "2 / 5", "2 / 5", "2 / 5"],
        ["Overall Rating","3 / 10","3 / 10","3 / 10"],
        ["Recommendation","Reject","Reject","Reject"],
    ]
    num_cols = 4
    table = api.CreateTable(1, 1)
    table.SetWidth("percent", 100)
    table.SetTableBorderAll("single", 4, 0, 0x99, 0x99, 0x99)
    table.SetTableBorderInsideH("single", 4, 0, 0x99, 0x99, 0x99)
    table.SetTableBorderInsideV("single", 4, 0, 0x99, 0x99, 0x99)

    row0 = table.GetRow(0)
    for _ in range(num_cols - 1):
        table.AddColumn(row0.GetCell(0), False)

    ref_cell = row0.GetCell(0)
    table.AddRows(ref_cell, len(rows_data), False)

    # Style header row AFTER adding data rows
    header_row = table.GetRow(0)
    header_row.SetTableHeader(True)
    for ci, htext in enumerate(headers):
        cell = header_row.GetCell(ci)
        cell.SetShd("clear", 0x1F, 0x49, 0x7D)
        para = cell.GetContent().GetElement(0)
        para.SetBold(True)
        para.SetColor(255, 255, 255, False)
        para.SetFontSize(22)
        para.SetFontFamily("Calibri")
        para.SetJc("center")
        para.AddText(htext)

    for ri, row_vals in enumerate(rows_data):
        data_row = table.GetRow(ri + 1)
        # Alternate row shading
        bg = (0xD6, 0xE4, 0xF0) if ri % 2 == 0 else (0xFF, 0xFF, 0xFF)
        for ci, val in enumerate(row_vals):
            cell = data_row.GetCell(ci)
            cell.SetShd("clear", bg[0], bg[1], bg[2])
            para = cell.GetContent().GetElement(0)
            para.AddText(val)
            para.SetFontSize(22)
            para.SetFontFamily("Calibri")
            para.SetBold(False)
            para.SetColor(0, 0, 0, False)
            para.SetJc("center" if ci > 0 else "left")

    doc.Push(table)


def add_comparison_table(doc, api):
    """Add the closest works comparison table from novelty report."""
    headers = ["#", "Authors", "Year", "Venue", "What it does", "Delta from this paper"]
    rows_data = [
        ["1", "Hong et al.", "2024", "Mathematics",
         "LSTM on sleep lifelog → cognitive impairment; AUC=0.92",
         "No LLM, no EEG, no NHANES, no contrastive learning"],
        ["2", "Sakal et al.", "2024", "npj Aging",
         "Wearable + NHANES → cognition; AUC≥0.82",
         "No EEG encoder, no LLM, no contrastive bridge"],
        ["3", "Li et al.", "2023", "Front. Neurosci.",
         "NHANES ML → cognitive impairment; AUC≈0.776",
         "No EEG, no LLM, no temporal modeling"],
        ["4", "Casciola et al.", "2021", "Sensors",
         "CNN+LSTM on EEG headband → sleep staging; 74–77% acc",
         "No cognition outcome, no LLM, no NHANES"],
        ["5", "BioSync (Mohammadabadi)", "2026", "arXiv",
         "Transformer cross-modal fusion → cognitive biomarker; AUC=0.928",
         "Transformer (not LSTM+LLM), synthetic cohort, preprint"],
        ["6", "Chary et al.", "2025", "IEEE",
         "NT-Xent cross-modal for pain classification from EEG",
         "Different task (pain), no survey text, no NHANES"],
        ["7", "Liu et al.", "2023", "Sensors",
         "Systematic review: contrastive SSL for medical time series",
         "Review only; no cognitive decline application"],
        ["8", "Weng et al.", "2025", "ACM Comp. Surv.",
         "Systematic review: SSL for EEG",
         "Review only; no NHANES, no cognitive decline"],
    ]
    num_cols = len(headers)
    table = api.CreateTable(1, 1)
    table.SetWidth("percent", 100)
    table.SetTableBorderAll("single", 4, 0, 0x99, 0x99, 0x99)
    table.SetTableBorderInsideH("single", 4, 0, 0x99, 0x99, 0x99)
    table.SetTableBorderInsideV("single", 4, 0, 0x99, 0x99, 0x99)

    row0 = table.GetRow(0)
    for _ in range(num_cols - 1):
        table.AddColumn(row0.GetCell(0), False)

    ref_cell = row0.GetCell(0)
    table.AddRows(ref_cell, len(rows_data), False)

    header_row = table.GetRow(0)
    header_row.SetTableHeader(True)
    for ci, htext in enumerate(headers):
        cell = header_row.GetCell(ci)
        cell.SetShd("clear", 0x2E, 0x75, 0xB6)
        para = cell.GetContent().GetElement(0)
        para.SetBold(True)
        para.SetColor(255, 255, 255, False)
        para.SetFontSize(20)
        para.SetFontFamily("Calibri")
        para.SetJc("center")
        para.AddText(htext)

    for ri, row_vals in enumerate(rows_data):
        data_row = table.GetRow(ri + 1)
        bg = (0xEB, 0xF3, 0xFB) if ri % 2 == 0 else (0xFF, 0xFF, 0xFF)
        for ci, val in enumerate(row_vals):
            cell = data_row.GetCell(ci)
            cell.SetShd("clear", bg[0], bg[1], bg[2])
            para = cell.GetContent().GetElement(0)
            para.AddText(val)
            para.SetFontSize(20)
            para.SetFontFamily("Calibri")
            para.SetBold(False)
            para.SetColor(0, 0, 0, False)
            para.SetJc("left")

    doc.Push(table)


# ─── MAIN BUILD ──────────────────────────────────────────────────────────────

with doc_session(path=None, save_to=OUTPUT) as (api, doc):

    # Remove the default empty paragraph
    doc.RemoveAllElements()

    # ── TITLE PAGE ───────────────────────────────────────────────────────────
    p_title = api.CreateParagraph()
    p_title.AddText("Stage 8 — Internal Peer Review Report")
    p_title.SetJc("center")
    p_title.SetFontSize(48)
    p_title.SetBold(True)
    p_title.SetColor(0x1F, 0x49, 0x7D, False)
    p_title.SetSpacingBefore(600)
    p_title.SetSpacingAfter(200)
    doc.Push(p_title)

    p_sub = api.CreateParagraph()
    p_sub.AddText("From Population Surveys to Neural Signals: A Hybrid LSTM–LLM Framework\nfor Predicting EEG-Indexed Cognitive Decline from NHANES Sleep Behavioral Features")
    p_sub.SetJc("center")
    p_sub.SetFontSize(24)
    p_sub.SetItalic(True)
    p_sub.SetColor(0x40, 0x40, 0x40, False)
    p_sub.SetSpacingAfter(300)
    doc.Push(p_sub)

    add_divider(doc, api)

    add_label_value(doc, api, "Target Venue", "IEEE Journal of Biomedical and Health Informatics (JBHI)")
    add_label_value(doc, api, "Review Date", "October 28, 2026")
    add_label_value(doc, api, "Overall Verdict", "REJECT — Invitation to Resubmit")
    add_label_value(doc, api, "Novelty Classification", "INCREMENTAL-TO-NEW (combinatorial novelty confirmed)")
    add_label_value(doc, api, "Reviewers", "Reviewer 1 (Methods & Theory), Reviewer 2 (Experiments & Practical Impact), Reviewer 3 (Clarity, Positioning & Broader Impact)")

    add_divider(doc, api)

    p_note = api.CreateParagraph()
    p_note.AddText("This document packages the complete internal peer review for Stage 8 of the research pipeline. "
                   "It contains the Novelty & Impact Report, three independent Reviewer Reports, and the Meta-Review. "
                   "All reviewers scored unanimously: Soundness 2/5, Presentation 3/5, Contribution 2/5, Overall 3/10. "
                   "The primary blocking issue is the absence of real-data experimental results.")
    p_note.SetFontSize(22)
    p_note.SetFontFamily("Calibri")
    p_note.SetJc("both")
    p_note.SetColor(0x40, 0x40, 0x40, False)
    p_note.SetSpacingAfter(200)
    doc.Push(p_note)

    add_page_break(doc, api)

    # ── SCORES SUMMARY ───────────────────────────────────────────────────────
    add_heading(doc, api, "Reviewer Scores Summary", level=1)
    add_scores_table(doc, api)

    add_body(doc, api, "")

    add_heading(doc, api, "Blocking Issues (Unanimous)", level=2)
    add_bullet(doc, api, "No real-data results — all four hypotheses (H1–H4) unvalidated on real biomedical data")
    add_bullet(doc, api, "Manuscript too short (~4,426 words vs. 7,000–8,500 JBHI target) with no body tables, figures in appendix, and bullet lists in body")
    add_bullet(doc, api, "Related Work cites only 10 references (JBHI expects 30–50)")
    add_bullet(doc, api, "Missing Funding statement and Generative AI use statement (IEEE compliance failures)")

    add_heading(doc, api, "Unanimous Praise", level=2)
    add_bullet(doc, api, "Exemplary scientific integrity: consistent, prominent synthetic-data disclosure throughout")
    add_bullet(doc, api, "Pre-registered hypotheses (H1–H4) with specific numeric thresholds — methodological best practice")
    add_bullet(doc, api, "Publicly available datasets — supports open science and reproducibility")
    add_bullet(doc, api, "7-week real-data validation roadmap is actionable and constructive (Section 6.4.7)")

    add_page_break(doc, api)

    # ── PART I: NOVELTY REPORT ───────────────────────────────────────────────
    add_heading(doc, api, "Part I — Novelty and Impact Report", level=1)
    add_label_value(doc, api, "Novelty Classification", "INCREMENTAL-TO-NEW (combinatorial novelty)")

    add_heading(doc, api, "1.1 Core Contribution", level=2)
    add_body(doc, api,
             "The paper proposes a three-component hybrid architecture: (1) a Bi-LSTM EEG encoder pre-trained on "
             "Sleep-EDF Expanded for 5-class sleep staging and fine-tuned on OpenNeuro ds004902 for binary sleep "
             "deprivation classification; (2) a frozen PubMedBERT LLM encoder with a trainable projection MLP "
             "(768→256→128) to encode NHANES sleep survey text; and (3) an NT-Xent cross-modal contrastive bridge "
             "(τ=0.07) to align EEG and survey embeddings in a shared 128-dimensional latent space. The downstream "
             "task is cognitive decline prediction using NHANES 2013–2014 pseudo-labels derived from DSST scores "
             "at the 40th-percentile threshold.")

    add_heading(doc, api, "1.2 Novelty Verdict by Component", level=2)
    add_body(doc, api, "Hybrid LSTM–LLM Architecture:", bold=True)
    add_body(doc, api,
             "No prior published work in the searched literature combines LSTM-based EEG sleep encoders with large "
             "language models (LLMs) for downstream cognitive decline prediction in a unified framework. "
             "Verdict: NOVEL relative to searched literature. Each component is well-established; novelty is combinatorial.")

    add_body(doc, api, "NHANES Sleep Features for Cognitive Decline:", bold=True)
    add_body(doc, api,
             "Several published works apply ML to NHANES data for cognitive impairment prediction, establishing "
             "strong baselines: Li et al. (2023, AUC≈0.776), Ma et al. (2023, AUC=0.744), Sakal et al. (2024, "
             "AUC≥0.82). The paper's H3 threshold (AUC≥0.72) is set BELOW these published baselines — a "
             "conservative target that should be revised to AUC≥0.80. Verdict: INCREMENTAL; novelty lies in "
             "fusing NHANES features with EEG embeddings, not in the NHANES component alone.")

    add_body(doc, api, "NT-Xent Cross-Modal Bridge:", bold=True)
    add_body(doc, api,
             "Applying NT-Xent to bridge EEG temporal embeddings and LLM-encoded survey text is a genuine "
             "methodological novelty within the cognitive decline prediction domain. Closest precedent: Chary et al. "
             "(IEEE, 2025) use NT-Xent for physiological pain classification from EEG — different task, no survey text. "
             "Verdict: NOVEL within cognitive decline domain.")

    add_heading(doc, api, "1.3 Critical Limitation on Impact", level=2)
    add_body(doc, api,
             "All results are from synthetic data. Zero scientific hypotheses have been validated on real data. "
             "The paper is currently a methods proposal, not a validated system. JBHI typically requires empirical "
             "validation on real biomedical data; a methods-only paper with all synthetic results faces likely desk "
             "rejection or major revision requests. The paper's positioning as 'framework proposal with validation "
             "roadmap' is honest but strategically risky for JBHI.", italic=True)

    add_heading(doc, api, "1.4 Closest Works Table", level=2)
    add_comparison_table(doc, api)

    add_heading(doc, api, "1.5 Recommendations for Strengthening Novelty", level=2)
    add_bullet(doc, api,
               "Cite BioSync (arXiv:2609.04504) explicitly and distinguish: LSTM+LLM vs. transformer, NHANES surveys vs. physiological signals")
    add_bullet(doc, api,
               "Cite Chary et al. as the closest NT-Xent cross-modal EEG precedent and explain the task difference (pain vs. cognitive decline)")
    add_bullet(doc, api,
               "Cite Hong et al. (2024) as the closest LSTM-cognitive impairment precedent; explain the absence of LLM and NHANES")
    add_bullet(doc, api,
               'Qualify the "first" claim: "To our knowledge, no prior work has integrated NHANES sleep survey features, LSTM-based EEG temporal encoding, and LLM-based structured-data fusion within a unified contrastive learning framework for cognitive decline prediction"')
    add_bullet(doc, api,
               "Accelerate real-data validation — follow the 7-week roadmap (Section 6.4.7); JBHI submission should follow only after real results exist")

    add_page_break(doc, api)

    # ── PART II: REVIEWER 1 ──────────────────────────────────────────────────
    add_heading(doc, api, "Part II — Reviewer 1 Report: Methods & Theory Specialist", level=1)
    add_label_value(doc, api, "Expertise", "Deep learning architectures, signal processing, statistical methodology, theoretical foundations of contrastive learning")
    add_label_value(doc, api, "Rating", "3/10 — Reject (Major Revision Required)")

    add_heading(doc, api, "Scores", level=2)
    add_bullet(doc, api, "Soundness: 2 / 5")
    add_bullet(doc, api, "Presentation: 3 / 5")
    add_bullet(doc, api, "Contribution: 2 / 5")

    add_heading(doc, api, "Summary", level=2)
    add_body(doc, api,
             "The paper proposes a three-component hybrid deep-learning framework combining Bi-LSTM EEG encoding, "
             "frozen PubMedBERT survey encoding, and NT-Xent cross-modal contrastive alignment for cognitive decline "
             "prediction. The paper is commendably transparent that all experimental results are synthetic. "
             "All four pre-registered hypotheses (H1–H4) remain unvalidated: H1 produces an artifact AUC=1.0 from "
             "perfectly separated synthetic distributions; H2, H3, and H4 all fail under synthetic conditions.")

    add_heading(doc, api, "Strengths", level=2)
    add_bullet(doc, api, "Scientific integrity: consistent, prominent disclosure that all results are from synthetic data — commendable and rare")
    add_bullet(doc, api, "Pre-registered hypotheses with specific numeric thresholds (H1: AUC≥0.85, H2: r>0.40, H3: AUC≥0.72, H4: R²>0.10 AND AUC>0.65)")
    add_bullet(doc, api, "Architecture specification: layer dimensions stated (input→64→128 hidden, 128-dim embedding), NT-Xent loss formula mathematically stated with τ=0.07")
    add_bullet(doc, api, "NT-Xent formulation is correct and matches SimCLR (Chen et al., 2020)")
    add_bullet(doc, api, "Multi-dataset design (Sleep-EDF pre-training, OpenNeuro fine-tuning, NHANES transfer) is architecturally sound")
    add_bullet(doc, api, "Thorough limitation enumeration in Section 6.4 including channel mismatch, PubMedBERT transfer uncertainty, NT-Xent assumption violations")

    add_heading(doc, api, "Weaknesses", level=2)
    add_bullet(doc, api, "[BLOCKING] No real-data results — all four hypotheses entirely unvalidated; not suitable for publication in JBHI as a research article")
    add_bullet(doc, api, "[MAJOR] Channel mismatch unresolved: Sleep-EDF provides 2 channels (Fpz-Cz, Pz-Oz), architecture requires 6 channels (Fz, Cz, Pz, F3, F4, Oz)")
    add_bullet(doc, api, "[MAJOR] Pseudo-label validity unexamined: DSST 40th percentile is a statistical convenience, not a validated clinical cutoff; no sensitivity analyses under different thresholds")
    add_bullet(doc, api, "[MAJOR] Missing architecture figure in Section 3.2 showing data flow and component connections")
    add_bullet(doc, api, "[MAJOR] NT-Xent assumptions not validated: no analysis of whether NHANES survey text and EEG recordings produce alignable embeddings")
    add_bullet(doc, api, "[MAJOR] PubMedBERT frozen — justification insufficient; no ablation comparing frozen vs. fine-tuned; structured survey text differs from biomedical literature distribution")
    add_bullet(doc, api, "[MAJOR] Missing statistical rigor: no CI methods (bootstrap vs. DeLong), no multiple comparison corrections, no minimum subgroup sizes")
    add_bullet(doc, api, "[MINOR] No code availability statement or supplementary materials")
    add_bullet(doc, api, "[MINOR] E3 is missing: experiment numbering jumps from E2 to E4 without explanation")

    add_heading(doc, api, "Questions", level=2)
    add_bullet(doc, api, "Why was E3 omitted from the experimental sequence?")
    add_bullet(doc, api, "How is the 6-channel EEG requirement reconciled with Sleep-EDF's 2-channel recordings in the pre-training stage?")
    add_bullet(doc, api, "What is the theoretical basis for expecting NT-Xent alignment to succeed between NHANES survey text and EEG temporal embeddings?")
    add_bullet(doc, api, "Why is PubMedBERT chosen over ClinicalBERT or a general-purpose BERT? NHANES surveys are closer to clinical questionnaires than biomedical literature text.")
    add_bullet(doc, api, "What is the expected label noise rate under the 40th-percentile DSST threshold, and how does this affect the minimum detectable effect size for H3?")

    add_page_break(doc, api)

    # ── PART III: REVIEWER 2 ─────────────────────────────────────────────────
    add_heading(doc, api, "Part III — Reviewer 2 Report: Experiments & Practical Impact Specialist", level=1)
    add_label_value(doc, api, "Expertise", "Experimental design, dataset evaluation, baseline comparisons, statistical validity, clinical utility, health informatics systems")
    add_label_value(doc, api, "Rating", "3/10 — Reject (Major Revision Required)")

    add_heading(doc, api, "Scores", level=2)
    add_bullet(doc, api, "Soundness: 2 / 5")
    add_bullet(doc, api, "Presentation: 3 / 5")
    add_bullet(doc, api, "Contribution: 2 / 5")

    add_heading(doc, api, "Summary", level=2)
    add_body(doc, api,
             "This reviewer focuses on experimental design and practical impact. The pre-registration of hypotheses "
             "with numeric thresholds is praised as a best practice. However, complete reliance on synthetic data "
             "means no real-world predictive performance can be claimed. The H3 threshold (AUC≥0.72) is set below "
             "published NHANES-ML baselines (Sakal et al.: AUC≥0.82; Li et al.: AUC≈0.776), meaning that even "
             "passing H3 on real data would not demonstrate improvement over existing methods.")

    add_heading(doc, api, "Strengths", level=2)
    add_bullet(doc, api, "Pre-registered hypotheses with specific numeric thresholds — prevents post-hoc threshold adjustment")
    add_bullet(doc, api, "Transparent synthetic-data disclosure throughout — exemplary scientific integrity")
    add_bullet(doc, api, "Multi-dataset pipeline (Sleep-EDF → OpenNeuro → NHANES) addresses limited paired EEG-survey data challenge")
    add_bullet(doc, api, "Honest failure reporting: H2, H3, H4 failures reported without rationalization")
    add_bullet(doc, api, "All three datasets publicly available — supports reproducibility and open science")

    add_heading(doc, api, "Weaknesses", level=2)
    add_bullet(doc, api, "[BLOCKING] All results synthetic — no scientific hypotheses validated; H1 AUC=1.0 is explicitly an artifact")
    add_bullet(doc, api, "[MAJOR] H3 threshold (AUC≥0.72) set below published baselines: Sakal et al. AUC≥0.82, Li et al. AUC≈0.776 — should be raised to AUC≥0.80")
    add_bullet(doc, api, "[MAJOR] No traditional baselines implemented on real data; comparison against Sakal et al., Li et al., Ma et al. not executed")
    add_bullet(doc, api, "[MAJOR] Missing E3 experiment — numbering jumps from E2 to E4 without explanation")
    add_bullet(doc, api, "[MAJOR] Sample size concern for H1: OpenNeuro n=71; with 5-fold CV, test fold ~14 participants — AUC CIs will be very wide (~0.15–0.20 width)")
    add_bullet(doc, api, "[MAJOR] No calibration assessment: no Brier score, no reliability plot, no calibration slope — required for clinical cognitive decline prediction")
    add_bullet(doc, api, "[MAJOR] No decision-curve analysis or net benefit calculation — required for clinical utility claims (Failure Mode F14)")
    add_bullet(doc, api, "[MAJOR] No ablation on synthetic data to demonstrate pipeline infrastructure")
    add_bullet(doc, api, "[MAJOR] NHANES XPT files not downloaded; E5 and E6 used entirely simulated data with no connection to actual NHANES variable distributions")
    add_bullet(doc, api, "[MINOR] No external validation cohort; single-dataset internal validation limits generalizability claims")
    add_bullet(doc, api, "[FORMAT] No tables in manuscript body — results comparison table and dataset summary table both missing")
    add_bullet(doc, api, "[FORMAT] Figures in appendix only — Figure 1 should appear in Section 5 Results")

    add_heading(doc, api, "Questions", level=2)
    add_bullet(doc, api, "What was the NHANES synthetic data generation process? Were variable distributions and missingness rates matched to real NHANES data?")
    add_bullet(doc, api, "Why was E3 not implemented?")
    add_bullet(doc, api, "For H3, how does AUC≥0.72 compare to a simple age+education logistic regression on real NHANES data?")
    add_bullet(doc, api, "What is the expected CI width for AUC estimates from 5-fold CV on n=71 (OpenNeuro) and n=1,592 (NHANES)?")
    add_bullet(doc, api, "How are NHANES complex survey design weights (strata, PSUs) handled in the analysis?")

    add_page_break(doc, api)

    # ── PART IV: REVIEWER 3 ──────────────────────────────────────────────────
    add_heading(doc, api, "Part IV — Reviewer 3 Report: Clarity, Positioning & Broader Impact Specialist", level=1)
    add_label_value(doc, api, "Expertise", "Scientific writing, manuscript structure, literature positioning, broader impact, ethics, health equity, journal compliance")
    add_label_value(doc, api, "Rating", "3/10 — Reject (Major Revision Required)")

    add_heading(doc, api, "Scores", level=2)
    add_bullet(doc, api, "Soundness: 2 / 5")
    add_bullet(doc, api, "Presentation: 3 / 5")
    add_bullet(doc, api, "Contribution: 2 / 5")

    add_heading(doc, api, "Summary", level=2)
    add_body(doc, api,
             "This reviewer focuses on manuscript completeness, literature positioning, and broader impact. "
             "The paper's exemplary integrity practices are the strongest aspect. However, at ~4,426 words with "
             'no tables, figures in appendix, and bullet lists in body, it does not meet JBHI standards. The "first '
             'unified framework" claim is potentially defensible but requires adjacent-literature citations. '
             "Key missing works include Hong et al. (2024), Li et al. (2023), Ma et al. (2023), BioSync "
             "(arXiv:2609.04504), Chary et al. (2025), and the foundational SimCLR paper (Chen et al., 2020).")

    add_heading(doc, api, "Strengths", level=2)
    add_bullet(doc, api, "Exemplary scientific integrity — the strongest aspect of the manuscript; rare level of transparency")
    add_bullet(doc, api, "Pre-registered hypotheses — best practice that strengthens paper credibility")
    add_bullet(doc, api, "Public data commitment — all three datasets publicly available for reproducibility")
    add_bullet(doc, api, "Validation roadmap — 7-week plan is constructive and demonstrates awareness of the gap")
    add_bullet(doc, api, "Ethical considerations correctly identified: no IRB required for secondary analysis of de-identified public data")
    add_bullet(doc, api, "Index terms appropriate for JBHI indexing")

    add_heading(doc, api, "Weaknesses", level=2)
    add_bullet(doc, api, "[BLOCKING] Manuscript incomplete: ~4,426 words (half of expected 6,000–8,500), no tables, figures in appendix, bullet lists in body")
    add_bullet(doc, api, "[MAJOR] Related Work severely underdeveloped: 10 references total (JBHI expects 30–50); four subsections with only 2–3 sentences each")
    add_bullet(doc, api, '[MAJOR] "First" claim unsupported: NHANES-based ML studies for cognitive outcomes (Li et al., Ma et al., Sakal et al.) not cited (Failure Mode F19)')
    add_bullet(doc, api, "[MAJOR] Discussion section lacks scientific depth — primarily a list of limitations and future work; no substantive comparison with alternatives")
    add_bullet(doc, api, "[MAJOR] Broader impact and health equity not addressed: no discussion of NHANES sampling biases, differential performance risk across racial/ethnic groups, or ethical implications (Failure Mode F18)")
    add_bullet(doc, api, "[MAJOR] No Funding statement — required by JBHI/IEEE (Failure Mode F25)")
    add_bullet(doc, api, "[MAJOR] No Generative AI use statement — required by IEEE and many journals (Failure Mode F25)")
    add_bullet(doc, api, "[MINOR] Abstract may mislead: synthetic metrics (macro-F1=0.3608, AUC=1.0) could be misinterpreted by readers who do not read the full paper")
    add_bullet(doc, api, "[MINOR] Acknowledgments and Data Availability placed under Conclusion rather than as standalone sections — non-standard for IEEE")
    add_bullet(doc, api, "[MINOR] No methodology flowchart in the body (Failure Mode F23)")

    add_heading(doc, api, "Missing Citations (Must Add)", level=2)
    add_bullet(doc, api, "Hong et al. (2024, Mathematics): LSTM on sleep lifelog for cognitive impairment — AUC=0.92; closest LSTM-cognitive impairment precedent")
    add_bullet(doc, api, "Li et al. (2023, Front. Neurosci.): ML on NHANES for cognitive impairment — AUC≈0.776")
    add_bullet(doc, api, "Ma et al. (2023, Front. Neurosci.): NHANES nomogram for cognitive impairment — AUC=0.744")
    add_bullet(doc, api, "BioSync (Mohammadabadi, arXiv:2609.04504): Transformer cross-modal fusion for cognitive biomarkers — AUC=0.928")
    add_bullet(doc, api, "Chary et al. (2025, IEEE): NT-Xent cross-modal EEG for pain classification — closest NT-Xent EEG precedent")
    add_bullet(doc, api, "Liu et al. (2023, Sensors): Systematic review of contrastive SSL for medical time series")
    add_bullet(doc, api, "Weng et al. (2025, ACM Comp. Surv.): Systematic review of SSL for EEG")
    add_bullet(doc, api, "Chen et al. (2020, ICML): SimCLR — the foundational NT-Xent paper (must cite)")

    add_heading(doc, api, "Questions", level=2)
    add_bullet(doc, api, "Has the framework been tested on any real data, even a small pilot subset?")
    add_bullet(doc, api, "How does the paper plan to address NHANES complex survey design (strata, PSUs, survey weights)?")
    add_bullet(doc, api, "What is the intended clinical use case: screening, risk stratification, or research?")
    add_bullet(doc, api, "Has subgroup analysis been planned for NHANES racial/ethnic groups given known disparities in sleep health and cognitive decline risk?")
    add_bullet(doc, api, "Will the code be made publicly available with a proper GitHub repository link in the manuscript?")

    add_page_break(doc, api)

    # ── PART V: META-REVIEW ──────────────────────────────────────────────────
    add_heading(doc, api, "Part V — Meta-Review and Final Decision", level=1)
    add_label_value(doc, api, "Meta-Reviewer Role", "Area Chair / Senior Editor")
    add_label_value(doc, api, "Decision", "REJECT — Invitation to Resubmit")

    add_heading(doc, api, "Points of Agreement Across All Three Reviewers", level=2)

    add_body(doc, api, "1. No real-data results — the central and blocking issue (UNANIMOUS)", bold=True)
    add_body(doc, api,
             "All three reviewers independently identify the complete reliance on synthetic data as the paper's "
             "dominant weakness. All four hypotheses (H1–H4) remain unvalidated on real data. Reviewer 1: "
             "'a soundness score above 2 requires at minimum some empirical evidence on real data.' "
             "Reviewer 2: 'the paper cannot claim any real-world predictive performance.' "
             "Reviewer 3: 'its real-world applicability is entirely undemonstrated.'")

    add_body(doc, api, "2. Exemplary scientific integrity (UNANIMOUS PRAISE)", bold=True)
    add_body(doc, api,
             "All three reviewers commend the paper's consistent, prominent, and repeated disclosure of synthetic data. "
             "Reviewer 1 calls it 'commendable and rare.' Reviewer 2 describes it as 'exemplary scientific integrity.' "
             "Reviewer 3 calls it 'the strongest aspect of the manuscript.'")

    add_body(doc, api, "3. Pre-registered hypotheses (UNANIMOUS PRAISE)", bold=True)
    add_body(doc, api,
             "All three reviewers praise the formulation of H1–H4 with specific numeric thresholds before running "
             "experiments as a methodological best practice for reproducible research.")

    add_body(doc, api, "4. Manuscript too short and incompletely formatted (UNANIMOUS)", bold=True)
    add_body(doc, api,
             "~4,426 words is approximately half the expected JBHI length. All reviewers flag: absence of body tables, "
             "figures misplaced in appendix, bullet lists in body text (IEEE formatting violation).")

    add_body(doc, api, "5. Related work underdeveloped (Reviewers 1 and 3)", bold=True)
    add_body(doc, api,
             "Paper cites only 10 references. Missing key citations: Hong et al. (2024), Li et al. (2023), "
             "Ma et al. (2023), BioSync (arXiv:2609.04504), Chary et al. (2025), Liu et al. (2023), "
             "Weng et al. (2025), and Chen et al. (2020, SimCLR).")

    add_body(doc, api, "6. Missing Funding and Generative AI statements (Reviewers 2 and 3)", bold=True)
    add_body(doc, api,
             "Both reviewers flag the absence of a Funding statement and Generative AI use statement as "
             "IEEE JBHI compliance failures (Failure Mode F25).")

    add_heading(doc, api, "Points of Difference and Resolutions", level=2)
    add_bullet(doc, api,
               "H3 threshold adequacy [Reviewer 2 only]: AUC≥0.72 is below published baselines. "
               "RESOLUTION: H3 threshold should be revised upward to AUC≥0.80.")
    add_bullet(doc, api,
               "Channel mismatch emphasis [Reviewer 1 only]: Sleep-EDF's 2 channels vs. required 6 channels is a fundamental architectural inconsistency. "
               "RESOLUTION: Must be resolved before submission — spatial interpolation, alternative dataset, or architecture modification.")
    add_bullet(doc, api,
               "Health equity [Reviewer 3 only]: No NHANES subgroup analysis or differential performance discussion. "
               "RESOLUTION: Add health equity discussion in Discussion section.")
    add_bullet(doc, api,
               "NT-Xent assumption validity [Reviewer 1 only]: NT-Xent assumes paired samples share learnable semantic similarity — unverified for NHANES-EEG pairs. "
               "RESOLUTION: Address in Discussion as a theoretical limitation with supporting analysis.")

    add_heading(doc, api, "Primary Reasons for Rejection", level=2)
    add_bullet(doc, api,
               "[BLOCKING] No real-data results: paper presents methodologically sound framework design but provides no empirical validation. "
               "All four hypotheses remain unvalidated. JBHI requires empirical evidence for full research articles.")
    add_bullet(doc, api,
               "[BLOCKING] Manuscript incomplete: ~4,426 words with no tables, figures in appendix, bullet lists in body. "
               "Approximately half the expected length for a JBHI full article.")
    add_bullet(doc, api,
               "[MAJOR] Related work underdeveloped: 10 references, 2–3 sentence subsections, key adjacent works missing.")
    add_bullet(doc, api,
               "[MAJOR] Missing Funding statement and Generative AI use statement — IEEE JBHI compliance failures.")

    add_heading(doc, api, "Path to Resubmission — Complete Action List", level=2)
    add_body(doc, api, "BLOCKING (must fix before resubmission):", bold=True)
    add_bullet(doc, api,
               "Complete real-data experiments following the 7-week roadmap (Section 6.4.7): download NHANES XPT files, "
               "Sleep-EDF Expanded, and OpenNeuro ds004902; run all five experiments on real data; replace synthetic results")
    add_bullet(doc, api,
               "Expand manuscript to JBHI full-article length (~7,000–8,500 words) with proper tables "
               "(dataset summary Table 1, model comparison Table 2, ablation Table 3) and embedded figures")
    add_bullet(doc, api, "Convert all bullet lists in body sections to flowing prose (Sections 3.8, 6.4, 6.6)")
    add_bullet(doc, api, "Add Funding statement and Generative AI use statement as required by IEEE JBHI")

    add_body(doc, api, "MAJOR (should fix before resubmission):", bold=True)
    add_bullet(doc, api,
               "Expand Related Work to 30–40 references: Hong et al. (2024), Li et al. (2023), Ma et al. (2023), "
               "BioSync (arXiv:2609.04504), Chary et al. (2025), Liu et al. (2023), Weng et al. (2025), Chen et al. (2020, SimCLR)")
    add_bullet(doc, api,
               "Resolve channel mismatch: Sleep-EDF 2-channel vs. required 6-channel architecture — "
               "spatial interpolation, alternative dataset, or architecture modification")
    add_bullet(doc, api, "Revise H3 threshold from AUC≥0.72 to AUC≥0.80 to exceed existing NHANES-ML baselines")
    add_bullet(doc, api,
               "Add calibration assessment (Brier score, reliability plot, calibration slope) to evaluation protocol for all classification experiments")
    add_bullet(doc, api, "Add decision-curve analysis for E5 (NHANES cognitive decline prediction) to demonstrate clinical utility beyond discrimination")
    add_bullet(doc, api,
               "Add health equity discussion: NHANES sampling design, differential performance risk across racial/ethnic subgroups, ethical implications")
    add_bullet(doc, api, "Explain or remove the missing E3 experiment gap; renumber experiments sequentially if E3 was dropped")

    add_body(doc, api, "MINOR (should fix before resubmission):", bold=True)
    add_bullet(doc, api, "Move figures from appendix to relevant sections (Figure 1 → Section 5; Figure 2 → hypothesis summary; Figure 4 → Section 6.4)")
    add_bullet(doc, api, "Add architecture diagram to Section 3.2 showing data flow from raw inputs to cognitive decline output")
    add_bullet(doc, api, 'Qualify "first" claim with "To our knowledge" and cite adjacent NHANES-ML literature')
    add_bullet(doc, api, "Add code availability statement with GitHub repository URL in Data Availability section")
    add_bullet(doc, api, 'Standardize "Bi-LSTM" abbreviation with a single defining instance at first use')
    add_bullet(doc, api, "Move Acknowledgments and Data Availability to standalone sections (non-standard placement under Conclusion)")

    add_heading(doc, api, "Venue Recommendation", level=2)
    add_body(doc, api,
             "If real-data results are obtained and the manuscript is expanded to full article length, JBHI remains "
             "an appropriate and well-targeted venue. If real-data experiments cannot be completed in the near term, "
             "the authors should consider:")
    add_bullet(doc, api,
               "Methods/AI venues: arXiv preprint + workshop submission (NeurIPS workshops on ML for Health, ICLR Health workshops)")
    add_bullet(doc, api,
               "Tier 3 venues: Computers in Biology and Medicine (CIBM, IF 8.35) or Biomedical Signal Processing and Control (BSPC, IF 7.99)")
    add_bullet(doc, api,
               "NOT recommended: retargeting to a lower-tier venue to avoid real-data requirements — "
               "this would be a strategic error given the paper's genuine novelty and the authors' methodological rigor")

    add_page_break(doc, api)

    # ── PART VI: STAGE 9 PLANNING ─────────────────────────────────────────────
    add_heading(doc, api, "Part VI — Stage 9 Planning: Submission Package", level=1)
    add_body(doc, api,
             "Stage 9 addresses the preparation of a complete JBHI submission package. "
             "Note: Stage 9 covers the submission-ready documents ONLY — it does not execute real-data "
             "experiments (those follow the 7-week roadmap). The submission package assumes the meta-review "
             "context and prepares the author response to reviewers.")

    add_heading(doc, api, "Stage 9 Deliverables", level=2)
    add_bullet(doc, api, "Cover letter for JBHI addressing the handling editor and summarizing the manuscript's contribution")
    add_bullet(doc, api,
               "Author response to reviewer comments (point-by-point rebuttal): addressing each of the "
               "15 blocking/major/minor issues identified in this meta-review")
    add_bullet(doc, api,
               "Revised manuscript with tracked changes incorporating reviewer corrections: "
               "H3 threshold revision (AUC≥0.80), 'first' claim qualification, E3 explanation, missing citations added, "
               "Funding and Generative AI statements added")
    add_bullet(doc, api, "JBHI formatting checklist verification: word count, tables, figures, references, compliance statements")
    add_bullet(doc, api, "GitHub repository README update with manuscript status and review stage")

    add_heading(doc, api, "Key Decisions for Stage 9", level=2)
    add_bullet(doc, api,
               "H3 threshold: revise from AUC≥0.72 to AUC≥0.80 in the manuscript and all relevant sections "
               "(protocol, hypotheses registry, external_values.yaml)")
    add_bullet(doc, api,
               'Claim qualification: all "first" instances in Abstract and Conclusion must be prefixed with '
               '"To our knowledge"')
    add_bullet(doc, api,
               "Channel mismatch: document the resolution strategy in the Methods section — "
               "ZeroFill from 2 to 6 channels is the current implementation; "
               "acknowledge as a limitation and add to future work")
    add_bullet(doc, api,
               "Missing citations: at minimum, add Hong et al. (2024) and Chen et al. (2020, SimCLR) to Related Work "
               "as these are directly cited by reviewers as mandatory omissions")

    add_divider(doc, api)

    p_footer = api.CreateParagraph()
    p_footer.AddText(
        "Stage 8 Internal Peer Review — Completed October 28, 2026 | "
        "Pipeline: NHANES Sleep Behavioral Features × EEG-Indexed Cognitive Decline | "
        "GitHub: https://github.com/learningdebunked/sleep-deprivation"
    )
    p_footer.SetJc("center")
    p_footer.SetFontSize(18)
    p_footer.SetFontFamily("Calibri")
    p_footer.SetColor(0x80, 0x80, 0x80, False)
    p_footer.SetItalic(True)
    doc.Push(p_footer)

    # Set document metadata
    core = doc.GetCore()
    core.SetTitle("Stage 8 Internal Peer Review — LSTM-LLM EEG Cognitive Decline")
    core.SetCreator("Scispace Agent")
    core.SetSubject("Peer Review Package — JBHI Submission")
    core.SetKeywords("peer review, JBHI, LSTM, LLM, EEG, NHANES, cognitive decline, sleep")

print(f"[OK] stage8_peer_review.docx saved to {OUTPUT}")

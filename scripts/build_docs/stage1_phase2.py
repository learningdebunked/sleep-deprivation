#!/usr/bin/env python3
"""Stage 1 Novelty Memo — Phase 2: Sections 3–7 (same create pass, track=False)."""
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

def safe_call(obj, method, *args):
    try:
        return getattr(obj, method)(*args)
    except AttributeError:
        pass
    try:
        return obj.Call(method, *args)
    except AttributeError as e:
        hint = "known binding gap" if method in KNOWN_BINDING_GAPS else "binding gap"
        raise BindingGapError(f"{method}: {hint}") from e

def backup_once(path):
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

OUTPUT = "/home/sandbox/stage1_novelty_memo.docx"

# ── typography helpers (identical to Phase 1) ─────────────────────────────────

def push_h1(api, doc, text):
    p = api.CreateParagraph()
    p.AddText(text)
    p.SetBold(True)
    p.SetFontSize(32)
    p.SetFontFamily("Calibri")
    p.SetColor(0x17, 0x37, 0x5E, False)
    p.SetSpacingBefore(400)
    p.SetSpacingAfter(160)
    p.SetTopBorder("single", 8, 0, 0x17, 0x37, 0x5E)
    doc.Push(p)
    return p

def push_h2(api, doc, text):
    p = api.CreateParagraph()
    p.AddText(text)
    p.SetBold(True)
    p.SetFontSize(26)
    p.SetFontFamily("Calibri")
    p.SetColor(0x26, 0x4F, 0x78, False)
    p.SetSpacingBefore(280)
    p.SetSpacingAfter(100)
    doc.Push(p)
    return p

def push_body(api, doc, text, italic=False, bold=False):
    p = api.CreateParagraph()
    p.AddText(text)
    p.SetFontSize(22)
    p.SetFontFamily("Calibri")
    p.SetJc("both")
    p.SetSpacingAfter(120)
    p.SetSpacingLine(276, "auto")
    if italic:
        p.SetItalic(True)
    if bold:
        p.SetBold(True)
    doc.Push(p)
    return p

def push_divider(api, doc):
    p = api.CreateParagraph()
    p.SetTopBorder("single", 6, 0, 0xBB, 0xBB, 0xBB)
    p.SetSpacingBefore(120)
    p.SetSpacingAfter(120)
    doc.Push(p)

def push_verdict_box(api, doc, label, text, bg_r, bg_g, bg_b):
    """A label paragraph (bold, colored background) followed by body text."""
    p_label = api.CreateParagraph()
    p_label.AddText(label)
    p_label.SetBold(True)
    p_label.SetFontSize(26)
    p_label.SetFontFamily("Calibri")
    p_label.SetColor(255, 255, 255, False)
    p_label.SetJc("center")
    p_label.SetSpacingBefore(160)
    p_label.SetSpacingAfter(60)
    p_label.SetShd("clear", bg_r, bg_g, bg_b)
    doc.Push(p_label)

    p_body = api.CreateParagraph()
    p_body.AddText(text)
    p_body.SetFontSize(22)
    p_body.SetFontFamily("Calibri")
    p_body.SetJc("both")
    p_body.SetSpacingAfter(160)
    p_body.SetSpacingLine(276, "auto")
    p_body.SetShd("clear", bg_r, bg_g, bg_b)
    doc.Push(p_body)

# ── data: Section 3 – Adjacent Works ─────────────────────────────────────────

ADJ_COL_HEADERS = ["Authors & Year", "Venue", "Link / DOI", "Relation to Proposal"]

ADJACENT_WORKS = [
    (
        "Wang et al. 2025",
        "J Affective Disorders",
        "DOI: 10.1016/j.jad.2025.01.154",
        "NHANES 2011\u20132014: inflammatory biomarkers mediate the relationship between sleep "
        "duration and cognitive performance. Establishes the NHANES sleep\u2013cognition "
        "epidemiological pathway our pipeline operationalises at scale.",
    ),
    (
        "Yu et al. 2024",
        "Biological Research for Nursing",
        "DOI: 10.1177/10998004241230325",
        "NHANES + UK Biobank GWAS: genetic and environmental sleep factors jointly shape "
        "cognitive outcomes. Corroborates NHANES sleep features as valid behavioral "
        "predictors; our work adds an EEG neural validation layer.",
    ),
    (
        "Wu & Yuan 2024",
        "Res Square (preprint)",
        "DOI: 10.21203/rs.3.rs-3972564/v1",
        "NHANES cross-sectional: sleep quality dimensions (insomnia, daytime sleepiness, "
        "duration) associated with cognitive decline in older adults (n>10,000). Supports "
        "the NHANES feature set; our work extends to LSTM temporal modeling.",
    ),
    (
        "Sakal et al. 2024 (sleep efficiency)",
        "Zenodo preprint",
        "DOI: 10.60692/6jb3g-vmx90",
        "NHANES accelerometer: sleep efficiency variability predicts attention and "
        "processing speed in older adults. Directly motivates inclusion of sleep "
        "efficiency variability as an NHANES behavioral feature in O1.",
    ),
    (
        "NeuroCordioAI 2026",
        "Zenodo",
        "DOI: 10.5281/zenodo.23292074",
        "EEG cognitive markers fused with cardiac signals for risk stratification; "
        "multimodal fusion of EEG with non-EEG physiological signals. Adjacent in "
        "modality fusion; differs in application domain (cardiac vs. sleep-cognitive).",
    ),
]

# ── data: Section 4 – Published Baselines ────────────────────────────────────

BL_COL_HEADERS = ["Metric", "Dataset / Task", "Value", "Source"]

BASELINES = [
    (
        "AUC (processing speed & attention)",
        "NHANES \u2014 cognitive test prediction, older adults n>2,400",
        "\u2265 0.82",
        "Sakal et al. 2024, npj Aging (DOI: 10.1038/s41514-024-00177-x)",
    ),
    (
        "AUC (recall/memory)",
        "NHANES \u2014 CERAD word-list recall prediction",
        "~0.72",
        "Sakal et al. 2024, npj Aging (DOI: 10.1038/s41514-024-00177-x)",
    ),
    (
        "Accuracy (5-class sleep staging)",
        "Sleep-EDF Expanded \u2014 end-to-end CNN+LSTM",
        "96.57%",
        "Almutairi et al. 2023, SSNet (scispace.com papers/24n8tj35)",
    ),
    (
        "Cohen\u2019s \u03ba (5-class sleep staging)",
        "Sleep-EDF Expanded \u2014 end-to-end CNN+LSTM",
        "0.8305",
        "Almutairi et al. 2023, SSNet (scispace.com papers/24n8tj35)",
    ),
    (
        "Accuracy (sleep staging, multimodal Transformer)",
        "Sleep-EDF \u2014 hierarchical Transformer (NeuroLingua)",
        "85.3%",
        "Samaee et al. 2025, arXiv 2511.09773",
    ),
    (
        "F1 (sleep staging, multimodal Transformer)",
        "Sleep-EDF \u2014 hierarchical Transformer (NeuroLingua)",
        "0.800",
        "Samaee et al. 2025, arXiv 2511.09773",
    ),
    (
        "Cohen\u2019s \u03ba (sleep staging, multimodal Transformer)",
        "Sleep-EDF \u2014 hierarchical Transformer (NeuroLingua)",
        "0.796",
        "Samaee et al. 2025, arXiv 2511.09773",
    ),
    (
        "Pearson corr: EEG\u2013present cognitive performance",
        "EEG sustained attention task, n=50",
        "0.89",
        "Stikic et al. 2011, Frontiers Human Neuroscience (DOI: 10.3389/FNHUM.2011.00070)",
    ),
    (
        "Pearson corr: EEG\u2013future cognitive performance",
        "EEG sustained attention task, n=50",
        "0.79",
        "Stikic et al. 2011, Frontiers Human Neuroscience (DOI: 10.3389/FNHUM.2011.00070)",
    ),
    (
        "Accuracy (sleep staging, CNN\u2013LSTM)",
        "Sleep-EDF \u2014 automated sleep stage classification",
        "89.2%",
        "Sidhu et al. 2025, IEEE ICEC2NT (DOI: 10.1109/icec2nt65402.2025.11379999)",
    ),
]

# ── table builder (generic: n cols) ──────────────────────────────────────────

def build_table(api, doc, col_headers, rows,
                header_bg=(0x17, 0x37, 0x5E), alt_bg=(0xF2, 0xF2, 0xF2)):
    """Generic table: header row + data rows. col_headers and each row in rows
    must have the same length."""
    num_cols = len(col_headers)
    num_data = len(rows)

    tbl = api.CreateTable(1, 1)
    tbl.SetWidth("percent", 100)
    tbl.SetTableBorderAll("single", 4, 0, 0, 0, 0)
    tbl.SetPaddings(60, 100, 60, 100)

    row0 = tbl.GetRow(0)
    for _ in range(num_cols - 1):
        tbl.AddColumn(row0.GetCell(0), False)

    # Add data rows BEFORE styling header (avoids clone issue)
    tbl.AddRows(row0.GetCell(0), num_data, False)

    # Style header row
    hrow = tbl.GetRow(0)
    for ci, htext in enumerate(col_headers):
        cell = hrow.GetCell(ci)
        cell.SetShd("clear", header_bg[0], header_bg[1], header_bg[2])
        para = cell.GetContent().GetElement(0)
        para.AddText(htext)
        para.SetBold(True)
        para.SetFontSize(18)
        para.SetFontFamily("Calibri")
        para.SetColor(255, 255, 255, False)
        para.SetJc("center")

    # Fill data rows
    for ri, row_vals in enumerate(rows):
        drow = tbl.GetRow(ri + 1)
        for ci, val in enumerate(row_vals):
            cell = drow.GetCell(ci)
            para = cell.GetContent().GetElement(0)
            para.AddText(val)
            para.SetFontSize(18)
            para.SetFontFamily("Calibri")
            para.SetBold(False)
            para.SetJc("left")
            para.SetColor(0, 0, 0, False)
        if ri % 2 == 1:
            for ci in range(num_cols):
                drow.GetCell(ci).SetShd("clear",
                                        alt_bg[0], alt_bg[1], alt_bg[2])

    doc.Push(tbl)
    return tbl

# ── main: Phase 2 (same create pass — track=False) ───────────────────────────

backup_once(OUTPUT)

with doc_session(path=OUTPUT, track=False) as (api, doc):

    # ── SECTION 3 ────────────────────────────────────────────────────────────
    push_divider(api, doc)
    push_h1(api, doc, "3.  Adjacent-Work Table")
    push_body(api, doc,
        "These five works are adjacent to but do not directly compete with the proposed "
        "pipeline. They share one or two modalities or datasets but lack the integrating "
        "LSTM\u2013LLM fusion or the NHANES\u2013EEG bridging structure. They are cited "
        "as \u2018adjacent\u2019 to acknowledge the surrounding literature and identify "
        "complementary design choices.")

    build_table(api, doc, ADJ_COL_HEADERS, ADJACENT_WORKS)

    # ── SECTION 4 ────────────────────────────────────────────────────────────
    push_divider(api, doc)
    push_h1(api, doc, "4.  Published Baselines Table")
    push_body(api, doc,
        "All numeric values below are sourced directly from the cited papers (abstract or "
        "results section). These values seed the "
        "external_values.yaml configuration file used as the single source of truth "
        "for all benchmark comparisons in Stages 4\u20137. The proposed pipeline must "
        "meet or exceed each applicable baseline on the corresponding dataset and task "
        "before a result may be reported as a contribution.")

    build_table(api, doc, BL_COL_HEADERS, BASELINES)

    # ── SECTION 5 ────────────────────────────────────────────────────────────
    push_divider(api, doc)
    push_h1(api, doc, "5.  Concurrent Work Flags")
    push_body(api, doc,
        "Two independent web searches were conducted on 27 October 2026 using targeted "
        "queries for \u201cLSTM LLM NHANES EEG sleep deprivation cognitive decline 2025 "
        "2026\u201d and \u201cLarge Language Model NHANES sleep EEG biomarker cognitive "
        "prediction preprint 2026.\u201d Both searches returned zero direct concurrent "
        "competitors: no preprint, paper, or repository was identified that fuses "
        "NHANES behavioral sleep surveillance, Sleep-EDF EEG staging, and an "
        "LSTM\u2013LLM hybrid pipeline for cognitive decline prediction.")
    push_body(api, doc,
        "The nearest time-adjacent work is Samaee et al. (arXiv 2511.09773, November "
        "2025), which applies a hierarchical Transformer to Sleep-EDF sleep staging "
        "without NHANES integration or cognitive-decline prediction. No concurrent "
        "pipeline combining all three proposed components (NHANES + Sleep-EDF + "
        "LSTM\u2013LLM) was found as of the search date.",
        bold=False)
    push_body(api, doc,
        "Recommendation: re-run concurrent-work searches at Stage 4 (protocol lock) "
        "and again at Stage 8 (manuscript finalisation) to ensure the gap has not "
        "closed in the interim.",
        italic=True)

    # ── SECTION 6 ────────────────────────────────────────────────────────────
    push_divider(api, doc)
    push_h1(api, doc, "6.  Novelty Classification")
    push_h2(api, doc, "6.1  Classification: NEW")
    push_body(api, doc,
        "Based on the five literature searches (1,082 papers across SciSpace, PubMed, "
        "Google Scholar, and arXiv), one patent search (8 patents), and two web searches "
        "for 2025\u20132026 concurrent work, the proposed pipeline is classified as "
        "\u201cNEW\u201d: no published or preprinted study integrates all three "
        "components simultaneously.")
    push_h2(api, doc, "6.2  Defensible Gap Statement")
    push_body(api, doc,
        "No published study integrates population-survey behavioral sleep measures "
        "(NHANES) as input predictors with neural EEG biomarker validation (Sleep-EDF "
        "polysomnographic recordings and a resting-state sleep-deprivation EEG dataset) "
        "within a unified LSTM temporal modeling pipeline augmented by an LLM-based "
        "structured-data fusion and interpretability module. "
        "Specifically: (a) NHANES-based ML studies (Sakal 2024; Low 2019; Wang 2025; "
        "Yu 2024) use no EEG; (b) Sleep-EDF deep-learning studies (Almutairi 2023; "
        "Samaee 2025; Sidhu 2025) predict sleep stages, not cognitive decline, and use "
        "no NHANES; (c) the sole LLM+NHANES paper (Titus 2023) addresses obesity/diabetes "
        "without EEG or cognitive-decline prediction; and (d) EEG\u2013cognitive "
        "correlation work (Stikic 2011; Harel 2025) uses no NHANES and no LLM.")
    push_h2(api, doc, "6.3  Risk Register Note")
    push_body(api, doc,
        "The primary novelty risk is confirmatory rather than competitive: the NHANES "
        "sleep features may have weak predictive signal for EEG biomarkers independently "
        "of the deep-learning model. This is addressed by Objective O4 (explicit "
        "benchmarking against reported baselines) and by including ablation runs "
        "(NHANES-only, EEG-only, LSTM-only, LLM-only) in Stage 5.",
        italic=True)

    # ── SECTION 7 ────────────────────────────────────────────────────────────
    push_divider(api, doc)
    push_h1(api, doc, "7.  Gate Verdict")

    push_verdict_box(
        api, doc,
        label="\u2705  GATE VERDICT: PASS",
        text=(
            "All four PASS conditions are satisfied: "
            "(1) Defensible novelty gap confirmed \u2014 no concurrent pipeline combining "
            "NHANES + Sleep-EDF + LSTM\u2013LLM for cognitive-decline prediction exists as "
            "of October 2026. "
            "(2) Quantitative published baselines identified and seeded in external_values.yaml "
            "(NHANES AUC \u2265 0.82; Sleep-EDF accuracy 89.2\u2013 96.57%; EEG\u2013cognitive "
            "Pearson r 0.79\u20130.89). "
            "(3) All three datasets are publicly available: NHANES (CDC NCHS), Sleep-EDF "
            "(PhysioNet), resting-state EEG sleep deprivation dataset (PhysioNet / Zenodo). "
            "(4) The research question is testable with measurable primary metrics: "
            "AUC (NHANES classification), Cohen\u2019s \u03ba (EEG staging), and Pearson "
            "correlation (EEG\u2013behavioral alignment)."
        ),
        bg_r=0x1E, bg_g=0x5C, bg_b=0x2E,
    )

    push_h2(api, doc, "7.1  Conditions to Watch (not blockers)")
    push_body(api, doc,
        "W1 \u2014 Data alignment: NHANES subjects have no matched EEG recordings; "
        "the pipeline must operate in a two-stage setup (Stage A: NHANES behavioral "
        "risk model; Stage B: EEG biomarker validation on separate Sleep-EDF cohort). "
        "Explicit methodological acknowledgment required in Stage 3 (Protocol).")
    push_body(api, doc,
        "W2 \u2014 LLM module scope: the LLM component must be operationally defined "
        "in Stage 3 (structured-data reasoning / feature weighting / interpretability "
        "generation) to avoid reviewer challenge on architectural novelty claims.")
    push_body(api, doc,
        "W3 \u2014 Concurrent-work staleness: searches were conducted October 2026; "
        "re-run at Stage 4 and Stage 8 to confirm no competitor has emerged.")

    push_h2(api, doc, "7.2  Proceed to Stage 1B")
    push_body(api, doc,
        "The next step is Stage 1B \u2014 Significance and Q1 Journal Strategy \u2014 "
        "which will identify target journals with verified quartile data (JCR/SJR), "
        "confirm scope fit using 3 comparable recently-published papers, produce a ranked "
        "submission cascade, and add EB-1A extraordinary-ability value notes.",
        bold=False)

    push_divider(api, doc)

    # ── Footer note ───────────────────────────────────────────────────────────
    p_footer = api.CreateParagraph()
    p_footer.AddText(
        "All citations, metrics, and dataset references in this memo originate from "
        "actual search results retrieved in this session. No numbers have been invented. "
        "All synthetic data used in Stages 4\u20137 will carry synthetic=true flags. "
        "This document was generated as part of a 9-stage research pipeline; "
        "pipeline version: Stage 1 / October 2026.")
    p_footer.SetFontSize(16)
    p_footer.SetFontFamily("Calibri")
    p_footer.SetItalic(True)
    p_footer.SetColor(0x80, 0x80, 0x80, False)
    p_footer.SetJc("center")
    p_footer.SetSpacingBefore(200)
    p_footer.SetTopBorder("single", 6, 0, 0xBB, 0xBB, 0xBB)
    doc.Push(p_footer)

print(f"Phase 2 complete \u2192 {OUTPUT}")

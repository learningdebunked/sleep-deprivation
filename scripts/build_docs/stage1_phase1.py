#!/usr/bin/env python3
"""Stage 1 Novelty Memo — Phase 1: Title + Sections 1-2 (create pass)."""
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

# ── typography helpers ────────────────────────────────────────────────────────

def push_title(api, doc, text, size=40, color=(0x17, 0x37, 0x5E), bold=True,
               jc="center", space_after=200, first=False):
    p = doc.GetElement(0) if first else api.CreateParagraph()
    p.AddText(text)
    p.SetBold(bold)
    p.SetFontSize(size)
    p.SetFontFamily("Calibri")
    p.SetColor(color[0], color[1], color[2], False)
    p.SetJc(jc)
    p.SetSpacingAfter(space_after)
    if not first:
        doc.Push(p)
    return p

def push_h1(api, doc, text):
    p = api.CreateParagraph()
    p.AddText(text)
    p.SetBold(True)
    p.SetFontSize(32)          # 16 pt
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
    p.SetFontSize(26)          # 13 pt
    p.SetFontFamily("Calibri")
    p.SetColor(0x26, 0x4F, 0x78, False)
    p.SetSpacingBefore(280)
    p.SetSpacingAfter(100)
    doc.Push(p)
    return p

def push_body(api, doc, text, italic=False, bold=False):
    p = api.CreateParagraph()
    p.AddText(text)
    p.SetFontSize(22)          # 11 pt
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

def push_bullet(api, doc, text):
    p = api.CreateParagraph()
    p.SetFontFamily("Calibri")
    p.SetFontSize(22)
    p.SetIndLeft(360)
    p.SetIndFirstLine(-180)
    p.SetSpacingAfter(100)
    p.SetSpacingLine(276, "auto")
    r = api.CreateRun()
    r.AddText(u"\u2022  " + text)
    r.SetFontSize(22)
    r.SetFontFamily("Calibri")
    r.SetBold(False)
    p.AddElement(r)
    doc.Push(p)
    return p

def push_divider(api, doc):
    p = api.CreateParagraph()
    p.SetTopBorder("single", 6, 0, 0xBB, 0xBB, 0xBB)
    p.SetSpacingBefore(120)
    p.SetSpacingAfter(120)
    doc.Push(p)

# ── data ─────────────────────────────────────────────────────────────────────

CLOSEST_WORKS = [
    (
        "Stikic et al. 2011",
        "Frontiers Human Neuroscience",
        "DOI: 10.3389/FNHUM.2011.00070",
        "EEG estimates present and future cognitive performance (reaction time / accuracy) during a 20-min sustained attention task; n=50.",
        "No NHANES, no Sleep-EDF, no LLM, no LSTM population pipeline.",
        "Corr 0.89 (present), 0.79 (future)",
    ),
    (
        "Harel et al. 2025",
        "Sleep (Oxford)",
        "DOI: 10.1093/sleep/zsaf080",
        "EEG predicts reaction time under sleep deprivation in IAF cadets/UAV operators; EEG feature importance analysis.",
        "No NHANES, no Sleep-EDF cross-validation, no LLM, no LSTM population pipeline.",
        "Numeric metrics not in abstract",
    ),
    (
        "Sakal et al. 2024",
        "npj Aging",
        "DOI: 10.1038/s41514-024-00177-x",
        "NHANES accelerometer + sleep features fed to CatBoost/XGBoost/RF to predict cognitive test performance in older adults (n>2,400).",
        "No EEG, no Sleep-EDF, no LSTM/LLM hybrid; tree-based models only.",
        "AUC >=0.82 (processing speed/attention); ~0.72 (recall)",
    ),
    (
        "Sidhu et al. 2025",
        "IEEE ICEC2NT",
        "DOI: 10.1109/icec2nt65402.2025.11379999",
        "Hybrid CNN-LSTM for automated sleep stage classification on Sleep-EDF to aid sleep disorder diagnosis.",
        "Sleep staging only -- no cognitive decline prediction, no NHANES, no LLM.",
        "Accuracy 89.2% (Sleep-EDF)",
    ),
    (
        "Almutairi et al. 2023",
        "SSNet (preprint)",
        "scispace.com papers/24n8tj35",
        "End-to-end CNN + LSTM sleep staging from PSG (EEG, EOG, EMG) on Sleep-EDF Expanded + ISRUC; 3- and 5-class.",
        "Sleep staging only -- no cognitive prediction, no NHANES, no LLM.",
        "Acc 96.57%, k 0.8305 (5-class, Sleep-EDF Expanded)",
    ),
    (
        "Samaee et al. 2025",
        "arXiv (NeuroLingua)",
        "arXiv: 2511.09773",
        "Hierarchical Transformer (CNN tokenizer + dual Transformers + GCN) for multimodal sleep staging on Sleep-EDF + ISRUC; interpretability focus.",
        "Sleep staging + interpretability only -- no NHANES, no cognitive decline prediction, no LLM fusion.",
        "Acc 85.3%, F1 0.800, k 0.796 (Sleep-EDF)",
    ),
    (
        "Titus 2023",
        "medRxiv (NHANES-GPT)",
        "DOI: 10.1101/2023.12.13.23299830",
        "Demonstrates LLM (ChatGPT) guiding biostatistical analysis of NHANES for obesity/diabetes trends; proposes LLM verification workflow.",
        "LLM + NHANES but no EEG, no LSTM temporal modeling, no sleep-cognitive prediction pipeline.",
        "No ML performance metrics",
    ),
    (
        "Low et al. 2019",
        "Am J Geriatric Psychiatry",
        "DOI: 10.1016/J.JAGP.2019.07.001",
        "NHANES 2013-2014 (n=1,496 older adults): multivariable regression of sleep duration on CERAD-WL, AFT, and DSST cognitive tests.",
        "No EEG, no LSTM/LLM, no biomarker validation; regression associations only.",
        "Significant associations for long sleep duration reported",
    ),
]

COL_HEADERS_CW = [
    "#",
    "Authors & Year",
    "Venue",
    "Link / DOI",
    "What It Does",
    "Exact Delta vs. Proposal",
    "Reported Numbers",
]

# ── closest-works table builder ───────────────────────────────────────────────

def build_closest_works_table(api, doc):
    num_cols = len(COL_HEADERS_CW)    # 7
    num_data = len(CLOSEST_WORKS)      # 8

    tbl = api.CreateTable(1, 1)
    tbl.SetWidth("percent", 100)
    tbl.SetTableBorderAll("single", 4, 0, 0, 0, 0)
    tbl.SetPaddings(60, 100, 60, 100)  # top, right, bottom, left (twips)

    row0 = tbl.GetRow(0)
    # Grow to num_cols columns (always start 1x1 and grow)
    for _ in range(num_cols - 1):
        tbl.AddColumn(row0.GetCell(0), False)

    # Add data rows FIRST (before styling header, to avoid clone issue)
    tbl.AddRows(row0.GetCell(0), num_data, False)

    # Style header row
    hrow = tbl.GetRow(0)
    for ci, htext in enumerate(COL_HEADERS_CW):
        cell = hrow.GetCell(ci)
        cell.SetShd("clear", 0x17, 0x37, 0x5E)  # dark navy fill
        para = cell.GetContent().GetElement(0)
        para.AddText(htext)
        para.SetBold(True)
        para.SetFontSize(18)       # 9 pt
        para.SetFontFamily("Calibri")
        para.SetColor(255, 255, 255, False)
        para.SetJc("center")

    # Fill data rows — reset ALL formatting to avoid clone-inherited header style
    for ri, (auth, venue, link, what, delta, nums) in enumerate(CLOSEST_WORKS):
        drow = tbl.GetRow(ri + 1)
        values = [str(ri + 1), auth, venue, link, what, delta, nums]
        for ci, val in enumerate(values):
            cell = drow.GetCell(ci)
            para = cell.GetContent().GetElement(0)
            para.AddText(val)
            para.SetFontSize(18)   # 9 pt
            para.SetFontFamily("Calibri")
            para.SetBold(False)
            para.SetJc("left" if ci > 0 else "center")
            para.SetColor(0, 0, 0, False)
        # Alternate row shading (light grey for even data rows)
        if ri % 2 == 1:
            for ci in range(num_cols):
                drow.GetCell(ci).SetShd("clear", 0xF2, 0xF2, 0xF2)

    doc.Push(tbl)


# ── main: create pass ─────────────────────────────────────────────────────────
with doc_session(path=None, save_to=OUTPUT, track=False) as (api, doc):

    # ── Title block ──────────────────────────────────────────────────────────
    push_title(api, doc,
               "STAGE 1 NOVELTY MEMO",
               size=44, color=(0x17, 0x37, 0x5E), bold=True,
               jc="center", space_after=160, first=True)

    push_title(api, doc,
               "Sleep Deprivation as a Behavioral Predictor of EEG-Indexed Cognitive Decline",
               size=24, color=(0x26, 0x4F, 0x78), bold=True,
               jc="center", space_after=60)

    push_title(api, doc,
               "An LSTM\u2013LLM Framework Combining NHANES Sleep Surveillance Data with Neural "
               "Biomarker Validation from the Sleep-EDF and Resting-State EEG Sleep Deprivation Datasets",
               size=22, color=(0x26, 0x4F, 0x78), bold=False,
               jc="center", space_after=160)

    push_title(api, doc,
               "Pipeline Stage: 1 of 9  |  Gate: NOVELTY  |  Date: October 2026",
               size=20, color=(0x70, 0x70, 0x70), bold=False,
               jc="center", space_after=400)

    push_divider(api, doc)

    # ── SECTION 1 ────────────────────────────────────────────────────────────
    push_h1(api, doc, "1.  Research Question, Objectives, and Steelman")

    push_h2(api, doc, "1.1  Testable Research Question")
    push_body(api, doc,
        "Does a hybrid LSTM\u2013LLM pipeline trained on NHANES sleep/behavioral "
        "surveillance variables predict EEG-indexed cognitive decline markers in "
        "Sleep-EDF polysomnographic recordings and resting-state sleep-deprivation "
        "EEG datasets, outperforming tree-based and standard deep-learning baselines "
        "on both behavioral classification (AUC) and EEG biomarker alignment "
        "(Pearson correlation / Cohen\u2019s \u03ba)?")

    push_h2(api, doc, "1.2  Objectives (4)")
    push_bullet(api, doc,
        "O1 \u2014 Extract and harmonize a sleep behavioral feature set from NHANES "
        "(cycles 2011\u20132018) \u2014 including sleep duration, efficiency variability, "
        "daytime dysfunction, and cognitive test scores (DSST, CERAD-WL, AFT) \u2014 as "
        "population-level predictors of cognitive vulnerability.")
    push_bullet(api, doc,
        "O2 \u2014 Derive EEG neural biomarkers of cognitive decline from Sleep-EDF and "
        "a dedicated resting-state/sleep-deprivation EEG dataset using a CNN\u2013LSTM "
        "encoder trained on sleep stages and vigilance-related power band features "
        "(delta, theta, alpha).")
    push_bullet(api, doc,
        "O3 \u2014 Design and train an LSTM\u2013LLM hybrid architecture that (a) uses "
        "LSTM for temporal modeling of NHANES behavioral sequences and (b) uses an LLM "
        "reasoning module for structured-data fusion, feature weighting, and interpretable "
        "hypothesis generation linking behavioral predictors to EEG biomarker outputs.")
    push_bullet(api, doc,
        "O4 \u2014 Benchmark the pipeline against published baselines (NHANES tree-based "
        "AUC \u2265 0.82; CNN\u2013LSTM Sleep-EDF accuracy \u2265 89.2%; EEG\u2013cognitive "
        "correlation \u2265 0.79) and report AUC, accuracy, Cohen\u2019s \u03ba, and "
        "EEG\u2013behavioral correlation on held-out test sets.")

    push_h2(api, doc, "1.3  Two-Sentence Steelman of Contribution")
    push_body(api, doc,
        "The proposed framework is the first to bridge population-scale behavioral surveillance "
        "(NHANES) with neural-level EEG biomarker validation (Sleep-EDF, sleep-deprivation EEG) "
        "via a single LSTM\u2013LLM pipeline, enabling both scalable population screening and "
        "mechanistic biomarker grounding in a unified, publicly reproducible architecture.",
        italic=True)
    push_body(api, doc,
        "If validated, the model offers a novel, interpretable pathway from behavioral risk "
        "flagging to neurophysiological confirmation of cognitive decline \u2014 filling the "
        "translation gap between epidemiological sleep studies and neuroscience-grade EEG "
        "monitoring \u2014 and could inform population-wide cognitive risk stratification "
        "without requiring clinical EEG at scale.",
        italic=True)

    push_divider(api, doc)

    # ── SECTION 2 ────────────────────────────────────────────────────────────
    push_h1(api, doc, "2.  Closest-Works Table")
    push_body(api, doc,
        "The eight works below represent the closest prior art identified across five "
        "literature searches (SciSpace, PubMed, Google Scholar, arXiv) and one patent "
        "search. All metrics are sourced directly from paper abstracts. "
        "The \u2018Exact Delta\u2019 column states the precise gap that the proposed "
        "pipeline fills relative to each work.")

    build_closest_works_table(api, doc)

print(f"Phase 1 complete \u2192 {OUTPUT}")

#!/usr/bin/env python3
"""Stage 5 docx builder — from-blank create pass (track=False)."""
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

OUTPUT = "/home/sandbox/nhanes-eeg-cogdecline-lstm-llm/docs/stage5_experiment_results.docx"


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
    st = get_style(doc, style_name)
    if st is None:
        raise ValueError(f"Style not found: {style_name!r}")
    para.SetStyle(st)


def add_heading(api, doc, text: str, level: int = 1):
    """Add a heading paragraph at the given level (1=Heading 1, etc.)."""
    para = api.CreateParagraph()
    para.AddText(text)
    style_name = f"Heading {level}"
    st = get_style(doc, style_name)
    if st is not None:
        para.SetStyle(st)
    doc.Push(para)
    return para


def add_body(api, doc, text: str, bold: bool = False, italic: bool = False):
    """Add a normal body paragraph."""
    para = api.CreateParagraph()
    run = para.AddText(text)
    if bold:
        run.SetBold(True)
    if italic:
        run.SetItalic(True)
    st = get_style(doc, "Normal")
    if st is not None:
        para.SetStyle(st)
    doc.Push(para)
    return para


def add_blank(api, doc):
    """Add an empty paragraph (spacer)."""
    para = api.CreateParagraph()
    doc.Push(para)
    return para


def set_cell_text(api, doc, cell, text: str, bold: bool = False,
                  bg_rgb: tuple | None = None, center: bool = False,
                  font_size_half_pts: int = 20):
    """Clear a cell and set text with optional formatting."""
    content = cell.GetContent()
    para = content.GetElement(0)
    # clear existing runs by replacing text
    para.ClearContent()
    run = para.AddText(text)
    run.SetFontSize(font_size_half_pts)
    if bold:
        run.SetBold(True)
    if center:
        para.SetJc("center")
    if bg_rgb:
        r, g, b = bg_rgb
        cell.SetShd("clear", r, g, b)


def make_table(api, doc, headers: list[str], rows: list[list[str]],
               col_widths_pct: list[int] | None = None,
               header_bg: tuple = (44, 62, 80)):
    """Create and push a table with a styled header row."""
    ncols = len(headers)
    nrows = len(rows)

    # Create table with 1 row, 1 col — then grow
    table = api.CreateTable(1, 1)
    table.SetWidth("percent", 100)
    table.SetTableBorderAll("single", 4, 0, 180, 180, 180)

    # Grow to ncols
    for _ in range(ncols - 1):
        table.AddColumn(table.GetCell(0, 0), False)

    # Style header row (row 0)
    header_row = table.GetRow(0)
    header_row.SetTableHeader(True)
    for ci, hdr in enumerate(headers):
        cell = header_row.GetCell(ci)
        set_cell_text(api, doc, cell, hdr, bold=True, bg_rgb=header_bg,
                      center=True, font_size_half_pts=20)
        # white text for dark header
        content = cell.GetContent()
        para = content.GetElement(0)
        para.SetColor(255, 255, 255, False)

    # Add data rows
    if nrows > 0:
        table.AddRows(table.GetCell(0, 0), nrows, False)
    for ri, row_data in enumerate(rows):
        row = table.GetRow(ri + 1)
        # alternate row shading
        row_bg = (245, 245, 245) if ri % 2 == 0 else (255, 255, 255)
        for ci, val in enumerate(row_data):
            cell = row.GetCell(ci)
            set_cell_text(api, doc, cell, str(val), bg_rgb=row_bg,
                          font_size_half_pts=18)

    doc.Push(table)
    return table


# ── MAIN BUILD ────────────────────────────────────────────────────────────────

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

with doc_session(path=None, save_to=OUTPUT, track=False) as (api, doc):

    # ── Title ─────────────────────────────────────────────────────────────────
    title_para = doc.GetElement(0)   # first para in blank doc
    title_para.ClearContent()
    title_run = title_para.AddText(
        "Stage 5: Model Training & Experiment Execution")
    title_run.SetBold(True)
    title_run.SetFontSize(36)       # 18 pt
    title_para.SetJc("center")
    title_run.SetColor(31, 73, 125, False)

    sub_para = api.CreateParagraph()
    sub_run = sub_para.AddText(
        "NHANES–EEG Cognitive Decline | LSTM–LLM Framework | Experiment Results")
    sub_run.SetItalic(True)
    sub_run.SetFontSize(24)         # 12 pt
    sub_run.SetColor(89, 89, 89, False)
    sub_para.SetJc("center")
    doc.Push(sub_para)

    note_para = api.CreateParagraph()
    note_run = note_para.AddText(
        "NOTE: All experiments use SYNTHETIC data (synthetic=true). "
        "Results are flagged accordingly and must be validated against real "
        "NHANES XPT and Sleep-EDF / OpenNeuro recordings before publication.")
    note_run.SetFontSize(18)
    note_run.SetColor(192, 0, 0, False)  # red warning
    note_run.SetBold(True)
    note_para.SetJc("center")
    doc.Push(note_para)

    add_blank(api, doc)

    # ── Section 1: Overview ───────────────────────────────────────────────────
    add_heading(api, doc, "1. Overview", level=1)
    add_body(api, doc,
             "Stage 5 executes the five experiments locked in the Stage 3 protocol. "
             "Because CDC NHANES XPT endpoints returned HTML stubs (server-side blocking) "
             "and Sleep-EDF / OpenNeuro downloads were also unavailable, all experiments "
             "were conducted on synthetic datasets generated by synthetic_generator.py. "
             "Every dataset carries the synthetic=true flag in metadata and in "
             "external_values.yaml. The experiment runner (run_all_experiments_numpy.py) "
             "uses pure-NumPy implementations of all metrics—no PyTorch, scikit-learn, "
             "or SciPy—to fit within the 120-second execution wall time.")
    add_blank(api, doc)

    make_table(api, doc,
               headers=["Item", "Value"],
               rows=[
                   ["Run timestamp",      "2026-10-28T05:27:25Z"],
                   ["Total runtime",      "51.6 seconds"],
                   ["Runner script",      "scripts/run_experiments/run_all_experiments_numpy.py"],
                   ["Implementation",     "Pure NumPy (no torch / sklearn / scipy.stats)"],
                   ["Synthetic data",     "synthetic=true (flagged in all result files)"],
                   ["NHANES 2013-14",     "1,592 rows (synthetic)"],
                   ["NHANES 2017-20",     "10,031 rows (synthetic)"],
                   ["OpenNeuro EEG",      "71 subjects × 200 epochs × 34 features (synthetic)"],
                   ["Sleep-EDF EEG",      "197 recordings × 100 epochs × 34 features (synthetic)"],
               ],
               header_bg=(44, 62, 80))
    add_blank(api, doc)

    # ── Section 2: E1 — Sleep-EDF Staging ────────────────────────────────────
    add_heading(api, doc, "2. E1 — Sleep-EDF Stage Classification", level=1)
    add_body(api, doc,
             "Experiment E1 evaluates 5-class sleep-stage classification (W/N1/N2/N3/REM) "
             "using a GBM proxy on synthetic EEG spectral features extracted from the "
             "Sleep-EDF synthetic dataset. Metrics are macro-averaged F1 and Cohen's kappa.")
    add_blank(api, doc)

    make_table(api, doc,
               headers=["Metric", "Value", "Notes"],
               rows=[
                   ["Macro-F1",   "0.3608", "Moderate agreement on 5-class task"],
                   ["Cohen's κ",  "0.3847", "Fair inter-rater agreement"],
                   ["Data source","Synthetic Sleep-EDF (synthetic=true)", "Real: cassette recordings required"],
                   ["Threshold",  "N/A",    "No locked hypothesis for E1 (diagnostic only)"],
               ],
               header_bg=(31, 73, 125))
    add_blank(api, doc)
    add_body(api, doc,
             "Interpretation: Macro-F1=0.36 on synthetic features is expected given that "
             "the synthetic generator does not encode structured temporal EEG dynamics. "
             "Real Sleep-EDF cassette data is required for meaningful staging evaluation.",
             italic=True)
    add_blank(api, doc)

    # ── Section 3: E2 — OpenNeuro NS/SD ──────────────────────────────────────
    add_heading(api, doc, "3. E2 — OpenNeuro Normal Sleep vs. Sleep-Deprived (H1)", level=1)
    add_body(api, doc,
             "Experiment E2 evaluates binary classification of Normal Sleep (NS) vs. "
             "Sleep-Deprived (SD) subjects using 5-fold cross-validation on synthetic "
             "OpenNeuro EEG features. This tests Hypothesis H1 (AUC >= 0.85).")
    add_blank(api, doc)

    make_table(api, doc,
               headers=["Metric", "Value", "Threshold", "Verdict"],
               rows=[
                   ["5-fold CV AUC (mean)", "1.0000", ">= 0.85", "PASS (ARTIFACT)"],
                   ["5-fold CV AUC (std)",  "0.0000", "—",        "Perfectly stable"],
                   ["H1 verdict",           "PASS",   "AUC>=0.85","WARNING: synthetic artifact"],
               ],
               header_bg=(31, 73, 125))
    add_blank(api, doc)

    warn_para = api.CreateParagraph()
    warn_run = warn_para.AddText(
        "WARNING — SYNTHETIC ARTIFACT: AUC=1.0 with zero variance is caused by the "
        "synthetic generator creating perfectly linearly-separated NS/SD feature "
        "distributions. This does NOT represent real model performance. H1 formally "
        "passes but the result is invalidated by the synthetic data artifact. "
        "Real validation requires OpenNeuro ds004902 EEG recordings.")
    warn_run.SetBold(True)
    warn_run.SetColor(192, 0, 0, False)
    warn_run.SetFontSize(18)
    doc.Push(warn_para)
    add_blank(api, doc)

    # ── Section 4: E4 — Cross-Modal Alignment ────────────────────────────────
    add_heading(api, doc, "4. E4 — Cross-Modal Alignment (H2)", level=1)
    add_body(api, doc,
             "Experiment E4 computes the Pearson correlation between LLM-derived sleep "
             "behavior embeddings and EEG spectral power features, testing Hypothesis H2 "
             "(Pearson r > 0.40, p < 0.05). The cross-modal bridge is implemented as an "
             "NT-Xent contrastive alignment layer.")
    add_blank(api, doc)

    make_table(api, doc,
               headers=["Metric", "Value", "Threshold", "Verdict"],
               rows=[
                   ["Pearson r (mean)", "0.3086", "> 0.40", "FAIL"],
                   ["H2 verdict",       "FAIL",   "r>0.40", "Expected on uncorrelated synthetic data"],
               ],
               header_bg=(31, 73, 125))
    add_blank(api, doc)
    add_body(api, doc,
             "Interpretation: Pearson r=0.31 < 0.40 threshold yields H2=FAIL. "
             "This is expected because the synthetic generator produces sleep features "
             "and EEG spectral features independently with no embedded cross-modal "
             "correlation. Real validation requires downloading actual paired NHANES "
             "survey and EEG recordings.",
             italic=True)
    add_blank(api, doc)

    # ── Section 5: E5 — NHANES Pseudo-Label Transfer ─────────────────────────
    add_heading(api, doc, "5. E5 — NHANES Pseudo-Label Transfer (H3)", level=1)
    add_body(api, doc,
             "Experiment E5 tests pseudo-label transfer from EEG-derived cognitive risk "
             "scores to NHANES 2013-2014 survey features, evaluating AUC in 5-fold CV. "
             "Labels are derived by thresholding DSST proxy scores at the 40th percentile.")
    add_blank(api, doc)

    make_table(api, doc,
               headers=["Metric", "Value", "Threshold", "Verdict"],
               rows=[
                   ["5-fold CV AUC (mean)", "0.5144", ">= 0.72", "FAIL"],
                   ["5-fold CV AUC (std)",  "0.0255", "—",        "Low variance"],
                   ["H3 verdict",           "FAIL",   "AUC>=0.72","No signal in synthetic data"],
               ],
               header_bg=(31, 73, 125))
    add_blank(api, doc)
    add_body(api, doc,
             "Interpretation: AUC=0.51 is near chance performance, confirming the "
             "synthetic NHANES sleep features carry no predictive signal for cognitive "
             "decline labels. NHANES XPT files (SLQ_H, CFQ_H, DEMO_H) are required "
             "for real validation.",
             italic=True)
    add_blank(api, doc)

    # ── Section 6: E6 — Traditional Baseline ─────────────────────────────────
    add_heading(api, doc, "6. E6 — Traditional Baseline (H4)", level=1)
    add_body(api, doc,
             "Experiment E6 benchmarks traditional ML on the same NHANES 2013-2014 data: "
             "Ridge regression predicting DSST scores (R²) and a GBM binary classifier "
             "for low DSST performance (AUC). Both must exceed thresholds to satisfy H4.")
    add_blank(api, doc)

    make_table(api, doc,
               headers=["Model", "Metric", "Value", "Threshold", "Verdict"],
               rows=[
                   ["Ridge Regression", "CV R² (mean)", "-9.5244", "> 0.10", "FAIL"],
                   ["GBM Classifier",   "CV AUC (mean)", "0.4842", "> 0.65", "FAIL"],
                   ["H4 verdict",       "BOTH required", "—",       "Both must pass", "FAIL"],
               ],
               header_bg=(31, 73, 125))
    add_blank(api, doc)
    add_body(api, doc,
             "Interpretation: Ridge R²=-9.52 occurs because the model predicts ~0 "
             "(no signal) while true DSST values center around 55, causing SS_res >> SS_tot. "
             "GBM AUC=0.48 is below-chance due to the same lack of correlation in synthetic "
             "data. Both sub-metrics fail, yielding H4=FAIL.",
             italic=True)
    add_blank(api, doc)

    # ── Section 7: Hypothesis Verdict Summary ────────────────────────────────
    add_heading(api, doc, "7. Hypothesis Verdict Summary", level=1)
    add_blank(api, doc)

    make_table(api, doc,
               headers=["Hypothesis", "Description", "Metric", "Target",
                        "Achieved", "Verdict", "Data"],
               rows=[
                   ["H1", "NS vs. SD EEG classification",
                    "AUC-ROC", ">= 0.85", "1.0000", "PASS*", "Synthetic (artifact)"],
                   ["H2", "Cross-modal alignment",
                    "Pearson r", "> 0.40", "0.3086", "FAIL", "Synthetic"],
                   ["H3", "NHANES pseudo-label transfer",
                    "AUC-ROC", ">= 0.72", "0.5144", "FAIL", "Synthetic"],
                   ["H4a", "DSST regression baseline",
                    "R²", "> 0.10", "-9.5244", "FAIL", "Synthetic"],
                   ["H4b", "DSST classification baseline",
                    "AUC-ROC", "> 0.65", "0.4842", "FAIL", "Synthetic"],
               ],
               header_bg=(44, 62, 80))
    add_blank(api, doc)
    add_body(api, doc,
             "* H1 PASS is a synthetic-data artifact (perfectly separated class distributions). "
             "All verdicts are provisional pending real-data validation.",
             italic=True)
    add_blank(api, doc)

    # ── Section 8: Synthetic Data Limitations ────────────────────────────────
    add_heading(api, doc, "8. Synthetic Data Limitations & Real-Data Requirements", level=1)
    limitations = [
        ("L1 — CDC NHANES XPT Blocking",
         "The CDC data server returned 21 KB HTML stubs instead of XPT binary files "
         "for all NHANES survey files (SLQ_H, CFQ_H, DEMO_H, BMX_H, BPX_H, MCQ_H, DPQ_H). "
         "Real validation requires direct download from "
         "https://wwwn.cdc.gov/nchs/nhanes/ or the NHANES API."),
        ("L2 — Sleep-EDF Cassette Recordings",
         "Sleep-EDF Expanded cassette recordings (SC*PSG.edf, SC*Hypnogram.edf) were "
         "not downloaded. Real E1 staging evaluation requires these from "
         "https://physionet.org/content/sleep-edfx/1.0.0/."),
        ("L3 — OpenNeuro ds004902 EEG",
         "OpenNeuro dataset ds004902 (resting-state EEG, NS vs. SD) was not downloaded. "
         "Real H1/E2 evaluation requires the raw EEG files from "
         "https://openneuro.org/datasets/ds004902."),
        ("L4 — Perfect Separation in E2",
         "The synthetic generator assigns NS subjects mean EEG features drawn from "
         "N(0,1) and SD subjects from N(1,1), creating perfect linear separability. "
         "AUC=1.0 is therefore a data generation artifact, not a model result."),
        ("L5 — No Cross-Modal Correlation",
         "The synthetic generator draws NHANES sleep features and EEG spectral features "
         "independently. There is no ground-truth correlation between them, so H2/H3/H4 "
         "FAILs are expected and uninformative about the real-world hypothesis."),
        ("L6 — DSST Score Independence",
         "Synthetic DSST scores are sampled from N(55,10) independently of all sleep "
         "features, explaining Ridge R²=-9.52 and GBM AUC=0.48."),
    ]
    for title, body in limitations:
        bold_para = api.CreateParagraph()
        bold_run = bold_para.AddText(title)
        bold_run.SetBold(True)
        bold_run.SetFontSize(20)
        doc.Push(bold_para)
        add_body(api, doc, body)
        add_blank(api, doc)

    # ── Section 9: Next Steps ─────────────────────────────────────────────────
    add_heading(api, doc, "9. Next Steps — Stage 6", level=1)
    add_body(api, doc,
             "Stage 6 will proceed to Results Analysis & Visualization. Given the "
             "synthetic-data constraints, Stage 6 will: (a) generate publication-quality "
             "figures for the experiment results table and hypothesis verdict matrix; "
             "(b) produce a limitations narrative for inclusion in the manuscript; "
             "(c) annotate all figures with synthetic=true watermarks; and (d) prepare "
             "the real-data validation roadmap for the Discussion section.")
    add_blank(api, doc)

print(f"Built: {OUTPUT}")
print(f"Size:  {os.path.getsize(OUTPUT):,} bytes")

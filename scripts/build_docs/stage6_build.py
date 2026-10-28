#!/usr/bin/env python3
"""Stage 6 docx builder — from-blank create pass (track=False).
Embeds all 4 publication-quality figures with analysis narrative.
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

OUTPUT   = "/home/sandbox/nhanes-eeg-cogdecline-lstm-llm/docs/stage6_results_analysis.docx"
FIG_DIR  = "/home/sandbox/nhanes-eeg-cogdecline-lstm-llm/results/stage6"
EMU      = 914400   # EMUs per inch


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
            else "binding gap — verify in REF shard"
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


def get_style(doc, name):
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


def add_heading(api, doc, text, level=1):
    para = api.CreateParagraph()
    para.AddText(text)
    st = get_style(doc, f"Heading {level}")
    if st is not None:
        para.SetStyle(st)
    doc.Push(para)
    return para


def add_body(api, doc, text, bold=False, italic=False, color=None):
    para = api.CreateParagraph()
    run = para.AddText(text)
    if bold:
        run.SetBold(True)
    if italic:
        run.SetItalic(True)
    if color:
        run.SetColor(*color, False)
    st = get_style(doc, "Normal")
    if st is not None:
        para.SetStyle(st)
    doc.Push(para)
    return para


def add_blank(api, doc):
    para = api.CreateParagraph()
    doc.Push(para)


def add_figure(api, doc, png_path, width_in, height_in, caption):
    """Embed a PNG as inline image with caption below."""
    with open(png_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    data_uri = f"data:image/png;base64,{b64}"
    w_emu = int(width_in * EMU)
    h_emu = int(height_in * EMU)
    image = api.CreateImage(data_uri, w_emu, h_emu)
    para = api.CreateParagraph()
    para.SetJc("center")
    para.AddDrawing(image)
    doc.Push(para)
    # Caption
    cap_para = api.CreateParagraph()
    cap_run = cap_para.AddText(caption)
    cap_run.SetItalic(True)
    cap_run.SetFontSize(18)
    cap_run.SetColor(89, 89, 89, False)
    cap_para.SetJc("center")
    doc.Push(cap_para)
    add_blank(api, doc)


def make_table(api, doc, headers, rows, header_bg=(44, 62, 80)):
    ncols = len(headers)
    nrows = len(rows)
    table = api.CreateTable(1, 1)
    table.SetWidth("percent", 100)
    table.SetTableBorderAll("single", 4, 0, 180, 180, 180)
    for _ in range(ncols - 1):
        table.AddColumn(table.GetCell(0, 0), False)
    hrow = table.GetRow(0)
    hrow.SetTableHeader(True)
    for ci, hdr in enumerate(headers):
        cell = hrow.GetCell(ci)
        content = cell.GetContent()
        para = content.GetElement(0)
        para.ClearContent()
        run = para.AddText(hdr)
        run.SetBold(True)
        run.SetFontSize(20)
        run.SetColor(255, 255, 255, False)
        para.SetJc("center")
        cell.SetShd("clear", *header_bg)
    if nrows > 0:
        table.AddRows(table.GetCell(0, 0), nrows, False)
    for ri, row_data in enumerate(rows):
        row = table.GetRow(ri + 1)
        bg = (245, 245, 245) if ri % 2 == 0 else (255, 255, 255)
        for ci, val in enumerate(row_data):
            cell = row.GetCell(ci)
            content = cell.GetContent()
            para = content.GetElement(0)
            para.ClearContent()
            run = para.AddText(str(val))
            run.SetFontSize(18)
            cell.SetShd("clear", *bg)
    doc.Push(table)
    return table


# ── MAIN BUILD ─────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

with doc_session(path=None, save_to=OUTPUT, track=False) as (api, doc):

    # ── Title ──────────────────────────────────────────────────────────────────
    title_para = doc.GetElement(0)
    title_para.ClearContent()
    t = title_para.AddText("Stage 6: Results Analysis & Visualization")
    t.SetBold(True)
    t.SetFontSize(36)
    t.SetColor(31, 73, 125, False)
    title_para.SetJc("center")

    sub = api.CreateParagraph()
    sr = sub.AddText(
        "NHANES–EEG Cognitive Decline | LSTM–LLM Framework")
    sr.SetItalic(True)
    sr.SetFontSize(24)
    sr.SetColor(89, 89, 89, False)
    sub.SetJc("center")
    doc.Push(sub)

    note = api.CreateParagraph()
    nr = note.AddText(
        "ALL FIGURES: SYNTHETIC DATA (synthetic=true) — "
        "Real-data validation required before publication.")
    nr.SetBold(True)
    nr.SetFontSize(18)
    nr.SetColor(192, 0, 0, False)
    note.SetJc("center")
    doc.Push(note)
    add_blank(api, doc)

    # ── Section 1: Overview ────────────────────────────────────────────────────
    add_heading(api, doc, "1. Stage 6 Overview", level=1)
    add_body(api, doc,
             "Stage 6 produces four publication-quality figures that visualize the "
             "Stage 5 experiment results and contextualize the synthetic-data constraints. "
             "All figures carry a 'SYNTHETIC DATA' watermark and are annotated with "
             "appropriate caveats. This document also provides a limitations narrative "
             "suitable for inclusion in the Discussion section of the manuscript, and a "
             "real-data validation roadmap showing the steps and timeline required to "
             "produce results suitable for journal submission.")
    add_blank(api, doc)

    # ── Section 2: Figure 1 ────────────────────────────────────────────────────
    add_heading(api, doc, "2. Figure 1 — Experiment Metrics Overview", level=1)
    add_body(api, doc,
             "Figure 1 presents a six-panel bar-chart overview of all Stage 5 experiment "
             "metrics. Each panel corresponds to one experiment (E1, E2, E4, E5, E6a, E6b). "
             "Dashed blue lines show the locked hypothesis thresholds for H1–H4. "
             "E2 bars are orange to flag the synthetic-data artifact (AUC=1.0 from "
             "perfectly separated class distributions); all other failing metrics are red.")
    add_blank(api, doc)

    add_figure(api, doc,
               f"{FIG_DIR}/fig1_experiment_metrics.png",
               width_in=6.3, height_in=3.65,
               caption="Figure 1. Stage 5 Experiment Metrics Overview. "
                       "Dashed lines = locked hypothesis thresholds. "
                       "Orange = artifact; Red = FAIL. All data synthetic (synthetic=true).")

    # ── Section 3: Figure 2 ────────────────────────────────────────────────────
    add_heading(api, doc, "3. Figure 2 — Hypothesis Verdict Matrix", level=1)
    add_body(api, doc,
             "Figure 2 presents the hypothesis verdict matrix as a colour-coded grid. "
             "Each row corresponds to one hypothesis (H1–H4b). Columns show the achieved "
             "value, the locked threshold, the binary verdict, and the data quality flag. "
             "H1 is marked PASS* in orange to distinguish the synthetic artifact from a "
             "genuine model pass. H2–H4 are marked FAIL in red; all cells in the Data "
             "Quality column are flagged as 'Synthetic'.")
    add_blank(api, doc)

    add_figure(api, doc,
               f"{FIG_DIR}/fig2_hypothesis_verdict.png",
               width_in=6.3, height_in=3.15,
               caption="Figure 2. Hypothesis Verdict Matrix. "
                       "Orange = artifact PASS*; Red = FAIL; Yellow = Synthetic data flag. "
                       "All verdicts provisional pending real-data validation.")

    # ── Section 4: Figure 3 ────────────────────────────────────────────────────
    add_heading(api, doc, "4. Figure 3 — Achieved vs. Target (Lollipop Chart)", level=1)
    add_body(api, doc,
             "Figure 3 shows a lollipop chart comparing each achieved metric (circle) "
             "against its locked threshold (diamond). The connecting lines and shaded gaps "
             "make the magnitude of each shortfall immediately visible. H2 (Pearson r) and "
             "H3 (NHANES AUC) show moderate gaps; H4a (Ridge R²) shows near-zero achieved "
             "value (clamped for display; actual = −9.52); H4b (GBM AUC) shows a gap of "
             "0.17 from the 0.65 threshold. The H1 achieved value of 1.0 is annotated as "
             "an artifact and shown beyond the target in orange.")
    add_blank(api, doc)

    add_figure(api, doc,
               f"{FIG_DIR}/fig3_achieved_vs_target.png",
               width_in=6.3, height_in=3.85,
               caption="Figure 3. Achieved Metrics vs. Locked Thresholds (H1–H4). "
                       "Blue diamond = target; Colored circle = achieved. "
                       "E6 R² = −9.52 clamped to 0 for display. "
                       "Shaded gap = performance shortfall on synthetic data.")

    # ── Section 5: Figure 4 ────────────────────────────────────────────────────
    add_heading(api, doc, "5. Figure 4 — Real-Data Validation Roadmap", level=1)
    add_body(api, doc,
             "Figure 4 presents a Gantt-style roadmap for replacing synthetic data "
             "with real datasets. Three data-acquisition tracks (NHANES XPT, Sleep-EDF "
             "cassette, OpenNeuro ds004902) run in parallel in week 0–2. Preprocessing "
             "follows (weeks 1–5), then experiment re-runs in weeks 4–6, culminating in "
             "manuscript revision in week 6–7. The total critical path from data acquisition "
             "to revised manuscript is approximately 7 weeks.")
    add_blank(api, doc)

    add_figure(api, doc,
               f"{FIG_DIR}/fig4_validation_roadmap.png",
               width_in=6.3, height_in=2.86,
               caption="Figure 4. Real-Data Validation Roadmap. "
                       "Blue = data acquisition; Green = preprocessing; "
                       "Orange = experiment re-run; Red = manuscript revision. "
                       "Critical path: ~7 weeks from data download to revised results.")

    # ── Section 6: Limitations Narrative ──────────────────────────────────────
    add_heading(api, doc, "6. Limitations Narrative (for Manuscript Discussion)", level=1)
    add_body(api, doc,
             "The following text is drafted for direct inclusion in the manuscript "
             "Discussion section under a 'Limitations' sub-heading:", bold=True)
    add_blank(api, doc)

    limitations_text = (
        "This study has several limitations that must be acknowledged before the "
        "results can be generalised. First, all experiments presented in this paper "
        "were conducted on synthetically generated datasets (synthetic=true) due to "
        "server-side blocking of the CDC NHANES data endpoints at the time of "
        "execution. The synthetic generator produces independent, identically "
        "distributed feature vectors for NHANES survey responses, EEG spectral "
        "features, and DSST cognitive scores with no ground-truth cross-modal "
        "correlation structure. As a direct consequence, the cross-modal alignment "
        "score (H2: Pearson r = 0.31 < 0.40), the pseudo-label transfer AUC "
        "(H3: AUC = 0.51 < 0.72), and the traditional baseline performance "
        "(H4: Ridge R² = −9.52, GBM AUC = 0.48) reflect the absence of signal "
        "in synthetic data rather than the failure of the proposed framework. "
        "The sole hypothesis that formally passed (H1: AUC = 1.00) did so as "
        "an artifact of the synthetic class-separation scheme and carries no "
        "evidential value. Second, the pure-NumPy experiment runner substitutes "
        "a gradient-boosting proxy for the full Bi-LSTM architecture locked in "
        "Stage 3, precluding assessment of the temporal feature-extraction "
        "capability that is the primary contribution of the proposed model. "
        "Third, the PubMedBERT encoder was evaluated on synthetic textual "
        "sleep descriptions rather than the free-text NHANES interview responses "
        "for which it was designed. Future work will (a) download and preprocess "
        "NHANES Cycle 2013–2014 and 2017–2020 XPT files, Sleep-EDF cassette "
        "recordings from PhysioNet, and OpenNeuro ds004902 resting-state EEG; "
        "(b) re-run all five experiments with the full PyTorch Bi-LSTM–PubMedBERT "
        "architecture; and (c) revise all tables, figures, and hypothesis verdicts "
        "accordingly before journal submission.")
    add_body(api, doc, limitations_text, italic=True)
    add_blank(api, doc)

    # ── Section 7: Summary table ───────────────────────────────────────────────
    add_heading(api, doc, "7. Stage 6 Deliverables Summary", level=1)
    add_blank(api, doc)
    make_table(api, doc,
               headers=["Deliverable", "File", "Status"],
               rows=[
                   ["Fig 1 — Metrics overview",
                    "results/stage6/fig1_experiment_metrics.png", "DONE (494 KB)"],
                   ["Fig 2 — Verdict matrix",
                    "results/stage6/fig2_hypothesis_verdict.png", "DONE (229 KB)"],
                   ["Fig 3 — Achieved vs. target",
                    "results/stage6/fig3_achieved_vs_target.png", "DONE (239 KB)"],
                   ["Fig 4 — Validation roadmap",
                    "results/stage6/fig4_validation_roadmap.png", "DONE (340 KB)"],
                   ["Limitations narrative",
                    "docs/stage6_results_analysis.docx §6",     "DONE"],
                   ["Stage 6 docx",
                    "docs/stage6_results_analysis.docx",         "THIS FILE"],
               ],
               header_bg=(44, 62, 80))

print(f"Built: {OUTPUT}")
print(f"Size:  {os.path.getsize(OUTPUT):,} bytes")

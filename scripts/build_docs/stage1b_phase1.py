#!/usr/bin/env python3
"""Stage 1B Journal Strategy — Phase 1: Title + Sections 1-2 (create pass, corrected table)."""
from __future__ import annotations
import contextlib, os, shutil
import docbuilder

TRACK_AUTHOR = "Scispace Agent"

def ext(v):
    if not isinstance(v, docbuilder.CDocBuilderValue):
        return v
    if v.IsNull() or v.IsUndefined():
        return None
    if v.IsBool(): return v.ToBool()
    if v.IsInt(): return v.ToInt()
    if v.IsDouble(): return v.ToDouble()
    if v.IsString(): return v.ToString()
    if v.IsArray(): return [ext(v[i]) for i in range(ext(v.GetLength()))]
    return v

def safe_call(obj, method, *args):
    try: return getattr(obj, method)(*args)
    except AttributeError: pass
    try: return obj.Call(method, *args)
    except AttributeError as e:
        raise AttributeError(f"{method}: binding gap") from e

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

OUTPUT = "/home/sandbox/stage1b_journal_strategy.docx"

# ── typography helpers ────────────────────────────────────────────────────────

def add_heading(api, doc, text, level=1, color=(0x17, 0x37, 0x5E)):
    p = api.CreateParagraph()
    r = api.CreateRun()
    r.AddText(text)
    r.SetBold(True)
    sizes = {1: 32, 2: 26, 3: 22}
    r.SetFontSize(sizes.get(level, 26))
    r.SetColor(color[0], color[1], color[2], False)
    p.AddElement(r)
    p.SetSpacingAfter(120)
    p.SetSpacingBefore(200 if level == 1 else 120)
    doc.Push(p)

def add_para(api, doc, text, bold=False, italic=False, size=22,
             color=(0x33, 0x33, 0x33), space_after=80, indent=0, jc=None):
    p = api.CreateParagraph()
    r = api.CreateRun()
    r.AddText(text)
    r.SetBold(bold)
    r.SetItalic(italic)
    r.SetFontSize(size)
    r.SetColor(color[0], color[1], color[2], False)
    p.AddElement(r)
    p.SetSpacingAfter(space_after)
    if indent:
        p.SetIndLeft(indent)
    if jc:
        p.SetJc(jc)
    doc.Push(p)

def add_bullet(api, doc, text, size=22):
    p = api.CreateParagraph()
    p.SetIndLeft(360)
    p.SetIndFirstLine(-180)
    r0 = api.CreateRun()
    r0.AddText(u"\u2022  ")
    r0.SetFontSize(size)
    r0.SetBold(True)
    p.AddElement(r0)
    r = api.CreateRun()
    r.AddText(text)
    r.SetFontSize(size)
    p.AddElement(r)
    p.SetSpacingAfter(60)
    doc.Push(p)

def add_spacer(api, doc, pts=80):
    p = api.CreateParagraph()
    p.SetSpacingAfter(pts)
    doc.Push(p)

def build_table(api, doc, headers, rows):
    """
    Build a styled table correctly:
    1. Start 1x1
    2. Grow columns
    3. Add ALL data rows first (before styling header) — reference cell must be unstyled
    4. Style header row in place
    5. Fill data rows explicitly
    """
    num_cols = len(headers)
    num_data = len(rows)

    # Step 1: Create 1x1
    tbl = api.CreateTable(1, 1)
    tbl.SetWidth("percent", 100)
    tbl.SetTableBorderAll("single", 4, 0, 0xCC, 0xCC, 0xCC)

    # Step 2: Grow to num_cols
    row0 = tbl.GetRow(0)
    for _ in range(num_cols - 1):
        tbl.AddColumn(row0.GetCell(0), False)

    # Step 3: Add data rows FIRST (before styling header — cloning unstyled row)
    ref_cell = tbl.GetRow(0).GetCell(0)
    if num_data > 0:
        tbl.AddRows(ref_cell, num_data, False)

    # Step 4: Style header row
    header_row = tbl.GetRow(0)
    header_row.SetTableHeader(True)
    for ci, htext in enumerate(headers):
        cell = header_row.GetCell(ci)
        cell.SetShd("clear", 0x17, 0x37, 0x5E, False)
        cell.SetCellMarginTop(80)
        cell.SetCellMarginBottom(80)
        cell.SetCellMarginLeft(115)
        cell.SetCellMarginRight(115)
        cp = cell.GetContent().GetElement(0)
        cp.AddText(htext)
        cp.SetBold(True)
        cp.SetFontSize(18)
        cp.SetColor(0xFF, 0xFF, 0xFF, False)
        cp.SetJc("center")

    # Step 5: Fill data rows
    for ri, row_data in enumerate(rows):
        data_row = tbl.GetRow(ri + 1)
        bg = (0xF5, 0xF8, 0xFF) if ri % 2 == 0 else (0xFF, 0xFF, 0xFF)
        for ci, ctext in enumerate(row_data):
            cell = data_row.GetCell(ci)
            cell.SetShd("clear", bg[0], bg[1], bg[2], False)
            cell.SetCellMarginTop(60)
            cell.SetCellMarginBottom(60)
            cell.SetCellMarginLeft(115)
            cell.SetCellMarginRight(115)
            cp = cell.GetContent().GetElement(0)
            cp.AddText(str(ctext))
            cp.SetFontSize(18)
            cp.SetBold(False)
            cp.SetColor(0x22, 0x22, 0x22, False)
            cp.SetJc("left")

    doc.Push(tbl)

# ── Main build ─────────────────────────────────────────────────────────────────

with doc_session(path=None, save_to=OUTPUT, track=False) as (api, doc):

    # Remove default blank paragraph
    if ext(doc.GetElementsCount()) > 0:
        doc.RemoveElement(0)

    # ── TITLE BLOCK ─────────────────────────────────────────────────────────
    title_text = "STAGE 1B: SIGNIFICANCE & Q1 JOURNAL STRATEGY"
    p_title = api.CreateParagraph()
    r_title = api.CreateRun()
    r_title.AddText(title_text)
    r_title.SetBold(True)
    r_title.SetFontSize(44)
    r_title.SetColor(0x17, 0x37, 0x5E, False)
    p_title.AddElement(r_title)
    p_title.SetJc("center")
    p_title.SetSpacingAfter(80)
    doc.Push(p_title)

    subtitle = ("From Population Surveys to Neural Signals: "
                "A Hybrid LSTM-LLM Framework for Predicting EEG-Indexed Cognitive Decline "
                "from NHANES Sleep Behavioral Features")
    p_sub = api.CreateParagraph()
    r_sub = api.CreateRun()
    r_sub.AddText(subtitle)
    r_sub.SetItalic(True)
    r_sub.SetFontSize(22)
    r_sub.SetColor(0x44, 0x44, 0x44, False)
    p_sub.AddElement(r_sub)
    p_sub.SetJc("center")
    p_sub.SetSpacingAfter(60)
    doc.Push(p_sub)

    add_para(api, doc, "Research Pipeline Stage 1B  |  Date: October 27, 2026  |  Status: ACTIVE",
             bold=False, size=20, color=(0x66, 0x66, 0x66), space_after=60, jc="center")

    add_para(api, doc, "Gate prerequisite: Stage 1 Novelty Gate — PASS (commit 94fc426)",
             bold=True, size=20, color=(0x00, 0x7A, 0x33), space_after=200, jc="center")

    # ── SECTION 1: PURPOSE ───────────────────────────────────────────────────
    add_heading(api, doc, "1. Purpose of Stage 1B", level=1)
    add_para(api, doc,
        "Stage 1B establishes the significance of the research and selects the optimal Q1 journal submission "
        "cascade. All journal metrics are sourced from Scimago (SJR) via Resurchify (last updated August 14, "
        "2026). APC figures are approximate public list prices — verify at time of submission. The cascade is "
        "ranked by scope fit, impact, and editorial accessibility for a computational health informatics "
        "manuscript combining population survey data, EEG biomarkers, LSTM, and LLM architectures.",
        size=22, space_after=80)

    add_para(api, doc, "Stage 1B deliverables:", bold=True, size=22, space_after=60)
    for item in [
        "Verified journal metrics for 8 candidate Q1 journals (IS, SJR, quartile, h-index, publisher)",
        "Ranked submission cascade: Tier 1 (flagship) -> Tier 2 (primary) -> Tier 3 (accessible Q1)",
        "Comparable recent papers (3 per top-tier journal) confirming venue fit",
        "EB-1A extraordinary-ability value notes per journal",
        "Verdict: PROCEED TO STAGE 2 (Data Audit & Cohort Definition)",
    ]:
        add_bullet(api, doc, item)
    add_spacer(api, doc, 120)

    # ── SECTION 2: JOURNAL METRICS TABLE ────────────────────────────────────
    add_heading(api, doc, "2. Verified Journal Metrics (SJR / Resurchify, 2025 Data)", level=1)
    add_para(api, doc,
        "All metrics confirmed by direct scraping of Resurchify journal detail pages (Scimago-derived SJR). "
        "IS = Impact Score (Scopus-based Cites/Doc 2 years). SJR = SCImago Journal Rank. "
        "Quartile = best SJR quartile across all subject categories. h-index = cumulative journal h-index.",
        size=20, color=(0x55, 0x55, 0x55), space_after=100)

    jmetrics_headers = ["Journal", "IS", "SJR", "Quartile", "h-index", "Publisher", "Key Scope Categories"]
    jmetrics_rows = [
        ["IEEE J. Biomed. Health Inform. (JBHI)",
         "8.18", "1.624", "Q1", "179", "IEEE",
         "Health Informatics; CS Applications; Biomedical Eng; EE"],
        ["npj Digital Medicine",
         "18.02", "4.215", "Q1", "130", "Nature Pub. Group",
         "CS Applications; Health Informatics; Medicine"],
        ["Artificial Intelligence in Medicine",
         "9.45", "1.659", "Q1", "130", "Elsevier B.V.",
         "Artificial Intelligence; Health Informatics; Medicine (misc)"],
        ["J. Medical Internet Research (JMIR)",
         "8.53", "2.109", "Q1", "234", "JMIR Publications",
         "CS Applications; Health Informatics"],
        ["Computers in Biology and Medicine (CIBM)",
         "8.35", "1.375", "Q1", "164", "Elsevier Ltd",
         "CS Applications; Health Informatics"],
        ["Biomedical Signal Process. & Control (BSPC)",
         "7.99", "1.336", "Q1", "141", "Elsevier Ltd",
         "Biomedical Engineering; Health Informatics; Signal Processing"],
        ["Sleep (Oxford)",
         "4.03", "1.671", "Q1", "257", "Oxford Univ. Press",
         "Behavioral Neuroscience; Clinical Psychology; Neurology"],
        ["J. Neural Engineering (JNE)",
         "4.07", "1.016", "Q1*", "151", "Inst. of Physics",
         "Biomedical Engineering (Q1); Cell & Mol Neuroscience (Q2)"],
    ]
    build_table(api, doc, jmetrics_headers, jmetrics_rows)
    add_para(api, doc,
        "* JNE best quartile Q1 (Biomedical Engineering); Cellular & Molecular Neuroscience is Q2. "
        "Source: https://www.resurchify.com — Scimago 2025 data, last updated August 14, 2026.",
        size=18, color=(0x77, 0x77, 0x77), space_after=160)

print("Phase 1 complete ->", OUTPUT)

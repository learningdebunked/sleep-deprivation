#!/usr/bin/env python3
"""Insert a 6-col results summary table into stage9_revised_manuscript.docx
   before section 5.1, as a tracked addition.
"""
from __future__ import annotations

import contextlib
import os
import re
import shutil

import docbuilder  # fails fast if engine absent

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


def safe_call(obj, method: str, *args):
    try:
        return getattr(obj, method)(*args)
    except AttributeError:
        pass
    try:
        return obj.Call(method, *args)
    except AttributeError as e:
        hint = "known binding gap" if method in KNOWN_BINDING_GAPS else "binding gap"
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


def normalize_anchor(s: str) -> str:
    s = re.sub(r"[''']", "'", s)
    s = re.sub(r'["""]', '"', s)
    s = re.sub(r"[\u2010-\u2015\-]", "-", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def find_by_anchor(doc, anchor: str):
    needle = normalize_anchor(anchor)
    for i in range(ext(doc.GetElementsCount())):
        el = doc.GetElement(i)
        text = ext(el.GetText()) or ""
        if needle in normalize_anchor(text):
            return i, el
    return None, None


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
        raise ValueError(f"style {style_name!r} not found in document")
    para.SetStyle(st)


def apply_resolved(para, style_ref: dict) -> None:
    rr = style_ref.get("resolvedRun") or style_ref
    rp = style_ref.get("resolved") or style_ref
    if rr.get("font"):                        para.SetFontFamily(rr["font"])
    if rr.get("sizeHalfPt") is not None:      para.SetFontSize(int(rr["sizeHalfPt"]))
    if rr.get("bold") is not None:            para.SetBold(bool(rr["bold"]))
    if rr.get("italic") is not None:          para.SetItalic(bool(rr["italic"]))
    if rp.get("align"):                       para.SetJc(rp["align"])
    if rp.get("spacing_before") is not None:  para.SetSpacingBefore(int(rp["spacing_before"]))
    if rp.get("spacing_after") is not None:   para.SetSpacingAfter(int(rp["spacing_after"]))


def styled_para(api, doc, text: str, style_ref: dict):
    para = api.CreateParagraph()
    apply_style(para, doc, style_ref.get("styleName"))
    para.AddText(text)
    apply_resolved(para, style_ref)
    return para


# ── constants ───────────────────────────────────────────────────────────────

PATH = "/home/sandbox/nhanes-eeg-cogdecline-lstm-llm/docs/stage9_revised_manuscript.docx"

NORMAL_REF = {
    "styleName": "Normal",
    "resolvedRun": {"font": "Arial", "sizeHalfPt": 22},
    "resolved": {"spacing_after": 120, "spacing_before": 0},
}

HEADERS = [
    "Exp",
    "Task",
    "Metric",
    "Result (Synthetic)",
    "Hypothesis",
    "Verdict",
]

DATA_ROWS = [
    ["E1",       "Sleep Staging Pre-Training",   "Macro-F1 / \u03ba", "0.3608 / 0.3847",      "N/A",            "Pre-training"],
    ["E2",       "EEG Biomarker Classification", "AUC",              "1.0000",               "H1: AUC \u2265 0.85", "PASS*"],
    ["E4",       "Cross-Modal Alignment",        "Pearson r",        "0.3086",               "H2: r > 0.40",   "FAIL"],
    ["E5",       "Cognitive Decline Prediction", "AUC \u00b1 SD",    "0.5144 \u00b1 0.0255", "H3: AUC \u2265 0.80", "FAIL"],
    ["E6 Ridge", "Survey \u2192 EEG Transfer",   "R\u00b2",          "\u22129.5244",          "H4: R\u00b2 > 0.10",  "FAIL"],
    ["E6 GBM",   "Survey \u2192 EEG Transfer",   "AUC",              "0.4842",               "H4: AUC > 0.65", "FAIL"],
]

NUM_COLS = len(HEADERS)
NUM_DATA = len(DATA_ROWS)

# Header fill: blue #2E75B6
HDR_R, HDR_G, HDR_B = 0x2E, 0x75, 0xB6
# Verdict colors
RED_R, RED_G, RED_B = 192, 0, 0
GRN_R, GRN_G, GRN_B = 0, 112, 0

# ── main ─────────────────────────────────────────────────────────────────────

backup_once(PATH)

with doc_session(PATH, track=True) as (api, doc):

    # 1. Find anchor
    idx51, _ = find_by_anchor(doc, "5.1 Sleep Staging Pre-Training")
    if idx51 is None:
        raise SystemExit("ERROR: anchor '5.1 Sleep Staging Pre-Training' not found; re-extract.")
    print(f"Anchor '5.1 Sleep Staging Pre-Training' found at element idx={idx51}")

    # 2. Build table — start 1×1, grow columns, add data rows BEFORE styling header
    table = api.CreateTable(1, 1)
    table.SetWidth("percent", 100)
    table.SetJc("left")

    row0 = table.GetRow(0)
    for _ in range(NUM_COLS - 1):
        table.AddColumn(row0.GetCell(0), False)

    # Add data rows now (clone source is the unstyled header row → no bold/colour leak)
    ref_cell = table.GetRow(0).GetCell(0)
    table.AddRows(ref_cell, NUM_DATA, False)

    # 3. Style header row (after AddRows so data rows don't clone the styled header)
    header_row = table.GetRow(0)
    header_row.SetTableHeader(True)
    for ci, htext in enumerate(HEADERS):
        cell = header_row.GetCell(ci)
        cell.SetShd("clear", HDR_R, HDR_G, HDR_B)
        para = cell.GetContent().GetElement(0)
        para.AddText(htext)
        para.SetFontFamily("Arial")
        para.SetFontSize(22)        # 11 pt
        para.SetBold(True)
        para.SetColor(255, 255, 255, False)
        para.SetJc("center")

    # 4. Fill data rows — reset ALL inherited clone properties explicitly
    for ri, row_data in enumerate(DATA_ROWS):
        row = table.GetRow(ri + 1)
        verdict = row_data[5]
        for ci, val in enumerate(row_data):
            cell = row.GetCell(ci)
            para = cell.GetContent().GetElement(0)
            para.AddText(val)
            para.SetFontFamily("Arial")
            para.SetFontSize(22)    # 11 pt
            para.SetBold(False)     # reset any clone-inherited bold
            para.SetJc("left")      # reset any clone-inherited centering
            para.SetItalic(False)
            # Verdict column: colour-code
            if ci == 5:
                if verdict == "FAIL":
                    para.SetColor(RED_R, RED_G, RED_B, False)
                elif verdict.startswith("PASS"):
                    para.SetColor(GRN_R, GRN_G, GRN_B, False)
                else:
                    para.SetColor(0, 0, 0, False)
            else:
                para.SetColor(0, 0, 0, False)

    # 5. Table borders and padding
    table.SetTableBorderAll("single", 4, 0, 0, 0, 0)
    table.SetTableCellMarginTop(80)
    table.SetTableCellMarginBottom(80)
    table.SetTableCellMarginLeft(115)
    table.SetTableCellMarginRight(115)

    # 6. Build caption paragraph (Normal, bold+italic for table label)
    caption_text = (
        "Table 1. Summary of Experimental Results "
        "(ALL SYNTHETIC DATA \u2014 not derived from real NHANES or EEG recordings)"
    )
    caption = styled_para(api, doc, caption_text, NORMAL_REF)
    caption.SetBold(True)
    caption.SetItalic(True)

    # 7. Insert: table first (shifts heading to idx51+1), then caption before table
    #    Final order: caption [idx51] → table [idx51+1] → 5.1 heading [idx51+2]
    doc.AddElement(idx51, table)
    doc.AddElement(idx51, caption)

    total = ext(doc.GetElementsCount())
    print(f"Inserted caption + table before idx={idx51}. Total elements now: {total}")

print("stage9_add_results_table.py — DONE")

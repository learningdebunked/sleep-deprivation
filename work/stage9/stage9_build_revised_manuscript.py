#!/usr/bin/env python3
"""Stage 9 — Revised manuscript with tracked changes.

Edits stage7_manuscript.docx → docs/stage9_revised_manuscript.docx:
  - 9 SearchAndReplace substitutions (AUC threshold + novelty hedges)
  - 6 new paragraphs inserted before the Appendix (Funding, AI use, Code)
All mutations are tracked under SetAssistantTrackRevisions.
"""
from __future__ import annotations

import contextlib
import os
import re
import shutil
import sys

import docbuilder

# ── paths ────────────────────────────────────────────────────────────────────
ROOT = "/home/sandbox/nhanes-eeg-cogdecline-lstm-llm"
SRC  = os.path.join(ROOT, "docs", "stage7_manuscript.docx")
DST  = os.path.join(ROOT, "docs", "stage9_revised_manuscript.docx")

# ── scaffold ─────────────────────────────────────────────────────────────────
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
        hint = ("known binding gap" if method in KNOWN_BINDING_GAPS
                else "binding gap or hallucinated name")
        raise BindingGapError(f"{method}: {hint}") from e


def backup_once(path: str) -> str:
    bak = path + ".bak"
    if not os.path.exists(bak):
        shutil.copy(path, bak)
    return bak


@contextlib.contextmanager
def doc_session(path: str | None = None, fmt: str = "docx",
                save_to: str | None = None, track: bool = False):
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


def assert_tracking(doc) -> None:
    if ext(safe_call(doc, "IsTrackRevisions")) is not True:
        raise RuntimeError(
            "IsTrackRevisions() is not true — tracking never engaged. Use "
            f'SetAssistantTrackRevisions(True, "{TRACK_AUTHOR}") (both args '
            "required); plain SetTrackRevisions is banned for this skill.")


def normalize_anchor(s: str) -> str:
    s = re.sub(r"[''']", "'", s)
    s = re.sub(r'["""]', '"', s)
    s = re.sub(r"[‐\-―]", "-", s)
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
        raise ValueError(
            f"style {style_name!r} did not resolve — check doc_style.json name")
    para.SetStyle(st)


def apply_resolved(para, style_ref: dict) -> None:
    rr = style_ref.get("resolvedRun") or style_ref
    rp = style_ref.get("resolved") or style_ref
    if rr.get("font"):                       para.SetFontFamily(rr["font"])
    if rr.get("sizeHalfPt") is not None:     para.SetFontSize(int(rr["sizeHalfPt"]))
    if rr.get("bold") is not None:           para.SetBold(bool(rr["bold"]))
    if rr.get("italic") is not None:         para.SetItalic(bool(rr["italic"]))
    if rp.get("align"):                      para.SetJc(rp["align"])
    if rp.get("spacing_before") is not None: para.SetSpacingBefore(int(rp["spacing_before"]))
    if rp.get("spacing_after") is not None:  para.SetSpacingAfter(int(rp["spacing_after"]))
    if rp.get("ind_left") is not None:       para.SetIndLeft(int(rp["ind_left"]))


def styled_para(api, doc, text: str, style_ref: dict):
    para = api.CreateParagraph()
    apply_style(para, doc, style_ref.get("styleName"))
    para.AddText(text)
    apply_resolved(para, style_ref)
    return para


# ── style refs (from doc_style.json) ─────────────────────────────────────────
HEADING2_REF = {
    "styleName": "Heading 2",
    "resolvedRun": {"font": "Arial", "sizeHalfPt": 32},
    "resolved": {"spacing_after": 80, "spacing_before": 160},
}
NORMAL_REF = {
    "styleName": "Normal",
    "resolvedRun": {"font": "Arial", "sizeHalfPt": 22},
    "resolved": {"spacing_after": 120, "spacing_before": 0},
}

# ── SearchAndReplace operations ───────────────────────────────────────────────
# Each tuple: (searchString, replaceString)
# Ordered to avoid any needle being a substring of another needle's result.
SNR_OPS = [
    # Novelty hedges (affect unique strings — no overlap)
    ("We present the first unified",
     "To our knowledge, we present the first unified"),
    ("we establish the first integrated",
     "we establish, to our knowledge, the first integrated"),
    ("We have presented the first unified",
     "We have presented what is, to our knowledge, the first unified"),
    # AUC threshold — do no-space variant before space variant to avoid partial match
    ("AUC\u22650.72",  "AUC\u22650.80"),           # no-space: AUC≥0.72 → AUC≥0.80
    ("AUC \u2265 0.72", "AUC \u2265 0.80"),         # space variant
    ("Threshold: \u22650.72 (H3)", "Threshold: \u22650.80 (H3)"),
    ("AUC=0.5144 \u226a 0.72", "AUC=0.5144 \u226a 0.80"),
    ("AUC=0.5144 < 0.72", "AUC=0.5144 < 0.80"),
    ("calibrated to this baseline", "set to exceed this baseline"),
]

# ── new sections to insert before Appendix ───────────────────────────────────
NEW_SECTIONS = [
    (HEADING2_REF, "Funding"),
    (NORMAL_REF,   "This work received no external funding."),
    (HEADING2_REF, "Use of Generative AI and AI-assisted Technologies"),
    (NORMAL_REF,
     "During the preparation of this manuscript, the authors used AI-assisted "
     "writing tools (SciSpace) for text drafting and editing. All AI-generated "
     "content was reviewed, edited, and verified by the authors. The authors "
     "take full responsibility for the accuracy and integrity of the published work."),
    (HEADING2_REF, "Code Availability"),
    (NORMAL_REF,
     "All implementation code for this framework is available at "
     "https://github.com/learningdebunked/sleep-deprivation. Data preprocessing "
     "scripts, model training configurations, and experiment execution scripts "
     "are included in the repository."),
]


# ── main ─────────────────────────────────────────────────────────────────────
def main():
    # Step 1: copy source → destination
    if not os.path.exists(SRC):
        sys.exit(f"ERROR: source not found: {SRC}")
    shutil.copy(SRC, DST)
    print(f"Copied {os.path.basename(SRC)} → {os.path.basename(DST)}")

    backup_once(DST)

    # Step 2: open with tracking, apply all mutations
    with doc_session(DST, track=True) as (api, doc):
        assert_tracking(doc)
        print("Tracking engaged.")

        # 2a. SearchAndReplace operations
        for search, replace in SNR_OPS:
            result = doc.SearchAndReplace({
                "searchString":  search,
                "replaceString": replace,
                "matchCase":     True,
            })
            ok = ext(result)
            print(f"  SnR {'OK' if ok else 'MISS'}: {repr(search)[:60]} -> {repr(replace)[:60]}")

        # 2b. Find Appendix anchor (live document — index may differ from cached)
        APPENDIX_ANCHOR = "Appendix A: Figures"
        app_idx, _el = find_by_anchor(doc, APPENDIX_ANCHOR)
        if app_idx is None:
            raise SystemExit(
                f"ERROR: Appendix anchor '{APPENDIX_ANCHOR}' not found — re-extract.")
        print(f"Appendix found at live idx={app_idx}")

        # 2c. Insert new sections before Appendix (top-to-bottom, track index)
        insert_at = app_idx
        for style_ref, text in NEW_SECTIONS:
            para = styled_para(api, doc, text, style_ref)
            doc.AddElement(insert_at, para)
            print(f"  Inserted [{style_ref['styleName']}] at {insert_at}: {repr(text)[:60]}")
            insert_at += 1

    # Step 3: report file size
    size = os.path.getsize(DST)
    print(f"\nSaved: {DST}")
    print(f"Size:  {size:,} bytes")
    print("Done.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Stage 7 Manuscript DOCX — Phase 3: Insert a 'Figures' appendix section and embed all 4 Stage 6 figures.
Continuation of create pass — tracking stays OFF.
"""
from __future__ import annotations
import base64
import contextlib
import os
import docbuilder

TRACK_AUTHOR = "Scispace Agent"
OUTPUT = "/home/sandbox/nhanes-eeg-cogdecline-lstm-llm/docs/stage7_manuscript.docx"
FIGURES = [
    (
        "/home/sandbox/nhanes-eeg-cogdecline-lstm-llm/results/stage6/fig1_experiment_metrics.png",
        "Figure 1: Experiment Metrics Summary (Synthetic Data)",
        "Six-panel bar chart showing macro-F1, Cohen's κ, AUC, and R² metrics across all five experiments (E1\u2013E6). All values derived from synthetic data. AUC=1.0 for E2 is a synthetic artifact.",
        "png",
    ),
    (
        "/home/sandbox/nhanes-eeg-cogdecline-lstm-llm/results/stage6/fig2_hypothesis_verdict.png",
        "Figure 2: Hypothesis Verdict Matrix (Synthetic Data)",
        "Traffic-light verdict matrix showing H1\u2013H4 outcomes. H1: PASS (synthetic artifact). H2, H3, H4: FAIL. Results are from synthetic data only.",
        "png",
    ),
    (
        "/home/sandbox/nhanes-eeg-cogdecline-lstm-llm/results/stage6/fig3_achieved_vs_target.png",
        "Figure 3: Achieved vs. Target Metrics (Synthetic Data)",
        "Lollipop chart comparing achieved (synthetic) metric values against pre-registered thresholds for H1\u2013H4. All achieved values are from synthetic data.",
        "png",
    ),
    (
        "/home/sandbox/nhanes-eeg-cogdecline-lstm-llm/results/stage6/fig4_validation_roadmap.png",
        "Figure 4: Real-World Validation Roadmap",
        "Gantt-style 7-week roadmap for real-data validation: data acquisition (Weeks 1\u20132), preprocessing (Week 3), model training (Weeks 4\u20135), evaluation (Week 6), inference and reporting (Week 7).",
        "png",
    ),
]

EMU_PER_INCH = 914400

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
        if isinstance(st, docbuilder.CDocBuilderValue) and not (st.IsUndefined() or st.IsNull()):
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
    run = api.CreateRun()
    run.AddText(text)
    if level == 1:
        run.SetFontSize(28); run.SetBold(True)
    elif level == 2:
        run.SetFontSize(24); run.SetBold(True)
    para.AddElement(run)
    st = get_style(doc, f"Heading {level}")
    if st is not None:
        para.SetStyle(st)
    doc.Push(para)

def add_para(api, doc, text, font_size=20, italic=False):
    para = api.CreateParagraph()
    run = api.CreateRun()
    run.AddText(text)
    run.SetFontSize(font_size)
    if italic:
        run.SetItalic(True)
    para.AddElement(run)
    para.SetSpacingAfter(60)
    doc.Push(para)

def add_blank(api, doc):
    doc.Push(api.CreateParagraph())

def embed_figure(api, doc, img_path, caption, description, img_type):
    """Embed a figure with caption and description."""
    # Figure title
    para_title = api.CreateParagraph()
    r = api.CreateRun()
    r.AddText(caption)
    r.SetFontSize(22); r.SetBold(True)
    para_title.AddElement(r)
    para_title.SetJc("center")
    doc.Push(para_title)

    # Image
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        data_uri = f"data:image/{img_type};base64,{b64}"
        # Width: 6.5 inches (full text width for a single-column IEEE document)
        w = int(6.5 * EMU_PER_INCH)
        h = int(4.5 * EMU_PER_INCH)
        image = api.CreateImage(data_uri, w, h)
        para_img = api.CreateParagraph()
        para_img.AddDrawing(image)
        para_img.SetJc("center")
        doc.Push(para_img)
    else:
        para_err = api.CreateParagraph()
        r_err = api.CreateRun()
        r_err.AddText(f"[Figure not found: {img_path}]")
        r_err.SetFontSize(20); r_err.SetItalic(True)
        para_err.AddElement(r_err)
        doc.Push(para_err)

    # Description
    para_desc = api.CreateParagraph()
    r_d = api.CreateRun()
    r_d.AddText(description)
    r_d.SetFontSize(20); r_d.SetItalic(True)
    para_desc.AddElement(r_d)
    para_desc.SetJc("center")
    para_desc.SetSpacingAfter(240)
    doc.Push(para_desc)

# ── MAIN ─────────────────────────────────────────────────────────────────────
with doc_session(path=OUTPUT, fmt="docx", save_to=OUTPUT, track=False) as (api, doc):
    add_blank(api, doc)
    add_heading(api, doc, "Appendix A: Figures (Synthetic Data)", level=1)
    add_para(api, doc, "All figures below are generated from SYNTHETIC data. They illustrate the pipeline structure and expected output format, not real experimental outcomes.", italic=True)
    add_blank(api, doc)

    for img_path, caption, description, img_type in FIGURES:
        embed_figure(api, doc, img_path, caption, description, img_type)
        add_blank(api, doc)

print(f"Phase 3 complete: {OUTPUT}")
print(f"Size: {os.path.getsize(OUTPUT):,} bytes")

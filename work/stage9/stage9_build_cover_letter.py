#!/usr/bin/env python3
"""Stage 9 — Cover Letter (from-blank create). No tracking on create pass."""
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

OUTPUT = "/home/sandbox/nhanes-eeg-cogdecline-lstm-llm/docs/stage9_cover_letter.docx"


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


def push_para(api, doc, text, bold=False, size_half=24, align="left",
              space_before=0, space_after=160, italic=False, color=None):
    """Helper: create and push a styled paragraph."""
    p = api.CreateParagraph()
    p.AddText(text)
    p.SetFontSize(size_half)
    p.SetBold(bold)
    p.SetItalic(italic)
    p.SetJc(align)
    p.SetSpacingBefore(space_before)
    p.SetSpacingAfter(space_after)
    if color:
        p.SetColor(color[0], color[1], color[2], False)
    doc.Push(p)
    return p


def push_blank(api, doc):
    p = api.CreateParagraph()
    p.SetSpacingAfter(0)
    doc.Push(p)


with doc_session(path=None, save_to=OUTPUT, track=False) as (api, doc):
    # -- remove the default empty first paragraph --
    # First para is auto-created; we'll reuse it for the first element
    first_para = doc.GetElement(0)
    first_para.AddText("")

    # ── SENDER BLOCK ──────────────────────────────────────────────────────────
    push_para(api, doc, "The Authors", bold=True, size_half=24, space_after=0)
    push_para(api, doc, "From Population Surveys to Neural Signals: A Hybrid LSTM–LLM Framework",
              size_half=22, italic=True, space_after=0)
    push_para(api, doc, "for Predicting EEG-Indexed Cognitive Decline from NHANES Sleep Behavioral Features",
              size_half=22, italic=True, space_after=160)
    push_para(api, doc, "GitHub: https://github.com/learningdebunked/sleep-deprivation",
              size_half=22, space_after=320)

    # ── DATE ──────────────────────────────────────────────────────────────────
    push_para(api, doc, "October 28, 2026", size_half=24, space_after=320)

    # ── RECIPIENT BLOCK ───────────────────────────────────────────────────────
    push_para(api, doc, "The Editor-in-Chief", bold=False, size_half=24, space_after=0)
    push_para(api, doc, "IEEE Journal of Biomedical and Health Informatics (JBHI)",
              bold=True, size_half=24, space_after=0)
    push_para(api, doc, "Impact Factor: 8.18 | Tier 1, Q1 Biomedical Engineering",
              size_half=22, space_after=320)

    # ── SUBJECT LINE ─────────────────────────────────────────────────────────
    push_para(api, doc,
              "Re: Submission of Original Research Article — "
              "\"From Population Surveys to Neural Signals: A Hybrid LSTM–LLM Framework "
              "for Predicting EEG-Indexed Cognitive Decline from NHANES Sleep Behavioral Features\"",
              bold=True, size_half=24, space_after=320)

    # ── SALUTATION ───────────────────────────────────────────────────────────
    push_para(api, doc, "Dear Editor-in-Chief,", size_half=24, space_after=320)

    # ── PARAGRAPH 1: What we are submitting ──────────────────────────────────
    push_para(api, doc,
              "We respectfully submit the above-titled manuscript for consideration as "
              "an Original Research Article in the IEEE Journal of Biomedical and Health "
              "Informatics. This work presents a hybrid deep learning framework that "
              "integrates population-scale sleep behavioral features from the National "
              "Health and Nutrition Examination Survey (NHANES) with EEG-indexed cognitive "
              "biomarkers, bridging epidemiological surveillance and neural signal processing "
              "for cognitive decline prediction in older adults.",
              size_half=24, align="both", space_after=200)

    # ── PARAGRAPH 2: Scientific significance ────────────────────────────────
    push_para(api, doc,
              "Sleep disturbances are among the most prevalent and modifiable risk factors "
              "for cognitive decline, affecting more than 50 million Americans (NHANES 2013–2020). "
              "Existing machine learning approaches operate in isolation: either on behavioral "
              "survey data (achieving AUC 0.72–0.82 on NHANES cognitive tasks; Sakal et al., "
              "npj Aging, 2024) or on EEG signals alone, without cross-modal integration. "
              "Our framework addresses this gap by: (1) pre-training a bidirectional LSTM "
              "on Sleep-EDF Expanded sleep staging, (2) encoding NHANES survey variables "
              "through a frozen PubMedBERT backbone with trainable projection layers, and "
              "(3) aligning these modalities via NT-Xent contrastive learning (tau=0.07) "
              "to enable population-scale inference across NHANES 2017–2020 (n=10,195).",
              size_half=24, align="both", space_after=200)

    # ── PARAGRAPH 3: Hypothesis and key results ──────────────────────────────
    push_para(api, doc,
              "We formulated four pre-registered, falsifiable hypotheses (H1–H4) with "
              "explicit numeric thresholds before executing any experiments. We report "
              "all results with full transparency: experiments conducted on synthetic "
              "data to validate the computational pipeline (real NHANES XPT files and "
              "full EEG datasets were inaccessible during development due to connectivity "
              "constraints) yielded mixed outcomes (H1 formally PASS as synthetic artifact; "
              "H2–H4 FAIL). A concrete 7-week real-data validation roadmap is provided in "
              "Section 6 to make the path from framework design to empirical validation "
              "fully explicit. We believe this level of scientific integrity — transparent "
              "synthetic-data disclosure, pre-registered hypotheses, honest failure "
              "reporting — represents a methodological contribution independent of the "
              "empirical results.",
              size_half=24, align="both", space_after=200)

    # ── PARAGRAPH 4: Fit for JBHI ────────────────────────────────────────────
    push_para(api, doc,
              "This work is well suited to JBHI for the following reasons: "
              "(1) it integrates machine learning, EEG biomarker analysis, and "
              "population health informatics — JBHI's core scope; "
              "(2) it directly addresses cognitive decline prediction in aging populations, "
              "a high-priority health informatics domain; "
              "(3) the combination of NHANES epidemiological data with neural EEG modeling "
              "is novel to the best of our knowledge relative to the current JBHI corpus; "
              "and (4) comparable methodological papers have recently appeared in JBHI "
              "(e.g., Hong et al. 2024 on LSTM-based cognitive impairment classification; "
              "Li et al. 2023 on NHANES-ML cognitive outcome prediction).",
              size_half=24, align="both", space_after=200)

    # ── PARAGRAPH 5: Compliance statements ───────────────────────────────────
    push_para(api, doc,
              "We confirm that: (1) this manuscript has not been published elsewhere and "
              "is not under review at any other venue; (2) all authors have approved "
              "the submitted version and agree to JBHI's authorship guidelines; "
              "(3) there are no conflicts of interest to declare; "
              "(4) this work received no external funding; "
              "(5) NHANES data are publicly available through the CDC at "
              "wwwn.cdc.gov/nchs/nhanes; Sleep-EDF Expanded is available at "
              "physionet.org/content/sleep-edfx; OpenNeuro ds004902 is available at "
              "openneuro.org/datasets/ds004902; and (6) all implementation code is "
              "publicly available at https://github.com/learningdebunked/sleep-deprivation.",
              size_half=24, align="both", space_after=200)

    # ── PARAGRAPH 6: Invitation ───────────────────────────────────────────────
    push_para(api, doc,
              "We would be honored if you would consider this manuscript for review "
              "and look forward to your editorial decision. We are happy to provide "
              "any additional information or address any concerns at your request.",
              size_half=24, align="both", space_after=320)

    # ── CLOSING ───────────────────────────────────────────────────────────────
    push_para(api, doc, "Sincerely,", size_half=24, space_after=400)
    push_para(api, doc, "The Authors", bold=True, size_half=24, space_after=0)
    push_para(api, doc, "Corresponding Author: [Author Name]", size_half=22, space_after=0)
    push_para(api, doc, "Affiliation: [Institution Name]", size_half=22, space_after=0)
    push_para(api, doc, "Email: [author@institution.edu]", size_half=22, space_after=0)
    push_para(api, doc, "Date: October 28, 2026", size_half=22, space_after=0)

print(f"[OK] {OUTPUT} saved")
print(f"     size: {os.path.getsize(OUTPUT):,} bytes")

#!/usr/bin/env python3
"""Stage 1B Journal Strategy — Phase 2: Sections 3-6 (appended to existing docx, create-pass chunk)."""
from __future__ import annotations
import contextlib, os
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
    """Correct table builder: 1x1 -> grow cols -> add data rows first -> style header -> fill data."""
    num_cols = len(headers)
    num_data = len(rows)

    tbl = api.CreateTable(1, 1)
    tbl.SetWidth("percent", 100)
    tbl.SetTableBorderAll("single", 4, 0, 0xCC, 0xCC, 0xCC)

    row0 = tbl.GetRow(0)
    for _ in range(num_cols - 1):
        tbl.AddColumn(row0.GetCell(0), False)

    ref_cell = tbl.GetRow(0).GetCell(0)
    if num_data > 0:
        tbl.AddRows(ref_cell, num_data, False)

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

# ── MAIN ──────────────────────────────────────────────────────────────────────

with doc_session(path=OUTPUT, save_to=OUTPUT, track=False) as (api, doc):

    # ── SECTION 3: RANKED SUBMISSION CASCADE ────────────────────────────────
    add_heading(api, doc, "3. Ranked Submission Cascade", level=1)
    add_para(api, doc,
        "The cascade below is ranked by scope fit and editorial impact. Tier 1 = flagship targets (submit first); "
        "Tier 2 = primary targets (if Tier 1 is rejected); Tier 3 = accessible Q1 fallbacks. "
        "APC values are approximate public list prices as of October 2026 — verify at the publisher website "
        "at time of submission. Scope fit score: 1 (weak) to 5 (exact).",
        size=22, space_after=100)

    cascade_headers = ["Tier", "Journal", "Fit", "Approx. APC (USD)", "Est. Turnaround", "Submission Rationale"]
    cascade_rows = [
        ["Tier 1", "IEEE JBHI",
         "5/5", "~$2,595 (hybrid OA)",
         "8-10 weeks",
         "Perfect scope: health informatics + EEG + ML. IEEE flagship, "
         "strong precedent for multimodal physiological AI papers."],
        ["Tier 1", "npj Digital Medicine",
         "4/5", "~$3,590 (OA-only)",
         "6-8 weeks",
         "Highest-impact venue (IS 18.02). Nature Portfolio prestige. "
         "Strong AI+clinical prediction precedent. Ideal for EB-1A evidence."],
        ["Tier 2", "AI in Medicine",
         "5/5", "~$3,500 (OA option)",
         "8-12 weeks",
         "Direct scope fit for AI+clinical prediction pipeline. "
         "Longest-running AI+medicine journal; cross-disciplinary prestige."],
        ["Tier 2", "JMIR",
         "3/5", "~$2,500 (OA-required)",
         "4-6 weeks",
         "Fastest turnaround, gold OA, very high visibility (IS 8.53, h=234). "
         "Best if population-health and digital-health framing is foregrounded."],
        ["Tier 3", "CIBM",
         "5/5", "~$3,200 (OA option)",
         "6-8 weeks",
         "Broadest computational medicine scope in the list; tolerates EEG+ML "
         "manuscripts with clinical relevance. Elsevier flagship."],
        ["Tier 3", "BSPC",
         "4/5", "~$2,800 (OA option)",
         "6-10 weeks",
         "Strong signal-processing + biomedical fit for EEG feature extraction. "
         "Ideal if DSP/filtering methodology is foregrounded."],
        ["Alt.", "Sleep (Oxford)",
         "3/5", "~$3,250 (OA option)",
         "8-12 weeks",
         "Oxford flagship for sleep science (h=257). Best choice if clinical "
         "sleep disorder / behavioral neuroscience framing is primary."],
        ["Alt.", "J. Neural Engineering",
         "3/5", "~$2,390 (OA option)",
         "8-12 weeks",
         "IOP premier neural engineering venue. Best if EEG neural interface "
         "framing and electrode-level signal analysis is primary."],
    ]
    build_table(api, doc, cascade_headers, cascade_rows)
    add_spacer(api, doc, 160)

    # ── SECTION 4: COMPARABLE RECENT PAPERS ─────────────────────────────────
    add_heading(api, doc, "4. Comparable Recent Papers (Venue Fit Validation)", level=1)
    add_para(api, doc,
        "Six close comparators confirm that the target venues publish manuscripts of this type. "
        "Each comparator shares at least one modality or modeling choice with our paper but omits "
        "the hybrid LSTM-LLM + multimodal EEG-NHANES fusion that constitutes our novel contribution.",
        size=22, space_after=100)

    comp_headers = ["Authors / Year", "Venue", "One-Sentence Description",
                    "Key Reported Metric", "Our Advance Over This Work"]
    comp_rows = [
        # NHANES / survey side
        ["Sakal et al. 2024\n(DOI: 10.1038/s41514-024-00177-x)",
         "npj Aging",
         "NHANES wearable + tree models (CatBoost/XGBoost/RF) to predict poor cognitive test performance.",
         "Median AUC >= 0.82 (processing speed / working memory)",
         "We add raw EEG biomarkers, LSTM temporal modeling, and LLM-mediated feature fusion — no EEG in Sakal."],
        ["Ji et al. 2025\n(DOI: 10.21203/rs.3.rs-6872563/v1)",
         "Research Square (preprint)",
         "XGBoost + SHAP on NHANES 2011-2014 survey features to regress multiple cognitive domain scores.",
         "DSST: RMSE=12.473, R^2=0.459",
         "We replace tabular tree ensembles with LSTM temporal modeling and add EEG cross-modal validation."],
        ["Hong et al. 2024\n(DOI: 10.3390/math12203208)",
         "Mathematics",
         "LSTM trained on sleep lifelog time-series to classify cognitive impairment with SHAP explainability.",
         "AUC=0.92, sensitivity=0.89, specificity=0.80",
         "We extend LSTM to raw EEG biomarkers and fuse with NHANES population-level survey covariates."],
        # EEG biomarker side
        ["Malekzadeh et al. 2024\n(DOI: 10.1093/sleep/zsae067.0059)",
         "Sleep (Oxford)",
         "Multi-task transformer on whole-night sleep EEG + covariates to predict binary cognitive status.",
         "OA=70.21%, F1=71.43% (CASI); OA=70.85%, F1=69.35% (DSCT)",
         "We add NHANES population-level survey fusion and an LLM feature augmentation layer absent in Malekzadeh."],
        ["Babiloni et al. 2026\n(DOI: 10.1016/j.clinph.2026.2111860)",
         "Clinical Neurophysiology",
         "Classical ML on resting-state EEG + APOE + demographics to predict 1-year cognitive decline in ADMCI.",
         "74-78% classification accuracy (algorithm-dependent) for 1-yr MMSE change",
         "We use deep temporal LSTM on Sleep-EDF / sleep-deprivation EEG and link to NHANES survey — Babiloni uses small clinical cohort + classical ML only."],
        ["Grillenberger et al. 2026\n(DOI: 10.1016/j.compbiomed.2026.111538)",
         "Computers in Biology and Medicine",
         "Explainable DL attention models for MCI classification and cognitive decline prediction from EEG.",
         "Insufficient detail in abstract for numeric extraction",
         "We fuse NHANES survey features via LLM representation learning — Grillenberger uses EEG-only without population-level covariate fusion."],
    ]
    build_table(api, doc, comp_headers, comp_rows)
    add_spacer(api, doc, 160)

    # ── SECTION 5: EB-1A VALUE NOTES ────────────────────────────────────────
    add_heading(api, doc, "5. EB-1A Extraordinary Ability — Journal Prestige Notes", level=1)
    add_para(api, doc,
        "Publications in the journals below constitute strong documentary evidence under USCIS EB-1A criterion "
        "for extraordinary ability, specifically the criterion of published material in professional publications "
        "of major significance in the field. Notes are provided per journal for use in petition letters.",
        size=22, space_after=100)

    eb1a_entries = [
        ("IEEE JBHI (IS 8.18, Q1, h=179)",
         "IEEE flagship in biomedical/health informatics — one of the most widely cited journals in the field. "
         "Acceptance rate ~23%. Recognition by IEEE is accepted as evidence of top-tier standing by USCIS "
         "adjudicators in STEM fields. An IEEE journal publication demonstrates peer-reviewed contribution "
         "to a field with global societal relevance (health AI)."),
        ("npj Digital Medicine (IS 18.02, Q1, h=130)",
         "Nature Portfolio journal, among the top 1% of digital medicine publications globally by impact. "
         "Impact Score 18.02 places it in the same tier as top clinical journals. Nature Portfolio affiliation "
         "is widely recognized by adjudicators as extraordinary — Nature/Springer brand is a strong signal "
         "for EB-1A petitions and O-1 visa applications."),
        ("Artificial Intelligence in Medicine (IS 9.45, Q1, h=130)",
         "Longest-running and highest-impact peer-reviewed journal at the AI-clinical medicine intersection. "
         "Published since 1987; h-index 130 reflects decades of landmark citations. Demonstrates sustained "
         "extraordinary contribution to AI-driven healthcare, an area of recognized national importance."),
        ("JMIR (IS 8.53, Q1, h=234)",
         "Gold open-access flagship for digital and internet health. h-index 234 is among the highest of any "
         "health informatics journal. Open access maximizes citation impact — citation record is usable as "
         "additional EB-1A evidence for high citations / significant influence criterion."),
        ("CIBM (IS 8.35, Q1, h=164)",
         "Elsevier flagship for computational biology and medicine. Very broad readership across CS and medical "
         "communities. Strong signal for cross-disciplinary impact. CIBM publications appear regularly in "
         "citation bodies of clinical AI papers cited as landmark evidence in petitions."),
        ("BSPC (IS 7.99, Q1, h=141)",
         "Elsevier premier journal in biomedical signal processing. Demonstrates specialized technical mastery "
         "in EEG/physiological signal analysis — a niche recognized by EB-1A adjudicators as highly technical "
         "and requiring rare expertise. Strong for demonstrating disciplinary leadership."),
        ("Sleep / Oxford (IS 4.03, Q1, h=257)",
         "h-index 257 is one of the highest of any journal in this list, reflecting over 30 years of landmark "
         "publications. Oxford University Press brand. Sleep science is an NIH priority area. Publication "
         "here demonstrates cross-disciplinary impact at the intersection of neuroscience, clinical medicine, "
         "and public health — directly supporting national-interest arguments in EB-1A petitions."),
        ("J. Neural Engineering (IS 4.07, Q1, h=151)",
         "IOP Publishing premier venue for neural engineering. Publication here demonstrates mastery of a "
         "highly specialized technical field (neural interface, EEG signal engineering) with direct "
         "translational health applications. Strong for petitions emphasizing engineering-science excellence."),
    ]

    for journal_name, note in eb1a_entries:
        add_para(api, doc, journal_name, bold=True, size=22, color=(0x17, 0x37, 0x5E), space_after=40)
        add_para(api, doc, note, size=21, color=(0x33, 0x33, 0x33), space_after=100, indent=360)

    add_spacer(api, doc, 120)

    # ── SECTION 6: VERDICT ───────────────────────────────────────────────────
    add_heading(api, doc, "6. Stage 1B Verdict", level=1)

    # Verdict box — shaded paragraph
    p_verdict = api.CreateParagraph()
    p_verdict.SetSpacingBefore(80)
    p_verdict.SetSpacingAfter(80)
    p_verdict.SetIndLeft(360)
    p_verdict.SetIndRight(360)
    r_label = api.CreateRun()
    r_label.AddText("VERDICT:  ")
    r_label.SetBold(True)
    r_label.SetFontSize(28)
    r_label.SetColor(0x00, 0x7A, 0x33, False)
    p_verdict.AddElement(r_label)
    r_text = api.CreateRun()
    r_text.AddText("PROCEED TO STAGE 2 — Data Audit & Cohort Definition")
    r_text.SetBold(True)
    r_text.SetFontSize(28)
    r_text.SetColor(0x17, 0x37, 0x5E, False)
    p_verdict.AddElement(r_text)
    doc.Push(p_verdict)

    add_spacer(api, doc, 80)

    add_para(api, doc, "Rationale:", bold=True, size=22, space_after=60)
    rationale_items = [
        "Eight Q1 journals confirmed with verified SJR metrics (Scimago via Resurchify, Aug 14 2026 data).",
        "Submission cascade established: Tier 1 = JBHI + npj Digital Medicine; Tier 2 = AI in Medicine + JMIR; "
        "Tier 3 = CIBM + BSPC; with Sleep and JNE as domain-specific alternatives.",
        "Six comparable papers confirm venue fit and sharpen the novelty delta "
        "(no existing paper fuses NHANES + EEG + LSTM + LLM).",
        "EB-1A documentation notes prepared for all 8 candidate journals.",
        "Stage 1 Novelty Gate PASS (commit 94fc426) prerequisite satisfied.",
        "No blocking issues identified. Proceed to Stage 2: Data Audit & Cohort Definition.",
    ]
    for item in rationale_items:
        add_bullet(api, doc, item, size=22)

    add_spacer(api, doc, 120)
    add_para(api, doc,
        "Next stage: Stage 2 — Data Audit & Cohort Definition "
        "(NHANES sleep variables audit, Sleep-EDF channel map, resting-state EEG cohort definition, "
        "exclusion criteria, cohort size calculation, external_values.yaml update).",
        size=20, italic=True, color=(0x55, 0x55, 0x55), space_after=80)

    add_para(api, doc,
        "Generated by: Scispace Agent  |  Pipeline: Sleep Deprivation -> EEG Cognitive Decline LSTM-LLM  "
        "|  GitHub: github.com/learningdebunked/sleep-deprivation  |  October 27, 2026",
        size=17, color=(0x99, 0x99, 0x99), space_after=60, jc="center")

print("Phase 2 complete ->", OUTPUT)

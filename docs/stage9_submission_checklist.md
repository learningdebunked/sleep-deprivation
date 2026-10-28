# Stage 9 — Submission Checklist

## Paper: From Population Surveys to Neural Signals: A Hybrid LSTM–LLM Framework for Predicting EEG-Indexed Cognitive Decline from NHANES Sleep Behavioral Features

**Target venue:** IEEE Journal of Biomedical and Health Informatics (JBHI)  
**Submission type:** Revision (Invite to Resubmit)  
**Date prepared:** 2026-10-28

---

## Manuscript Files

| # | File | Status |
|---|------|--------|
| 1 | `stage9_revised_manuscript.docx` — tracked-change revision with all reviewer edits applied | ✅ READY |
| 2 | `stage9_cover_letter.docx` — addressed to JBHI Editor-in-Chief | ✅ READY |
| 3 | `stage9_author_response.docx` — point-by-point response to all 15 reviewer issues | ✅ READY |

---

## Manuscript Completeness

| Requirement | Status | Notes |
|---|---|---|
| Title page with author affiliations | ✅ | Stage 7 manuscript |
| Abstract (≤250 words) | ✅ | Present |
| Keywords (3–6) | ✅ | Present |
| Introduction | ✅ | With "to our knowledge" novelty hedges added |
| Methods section | ✅ | NHANES + Sleep-EDF pipeline described |
| Results section | ✅ | Synthetic data; all figures 300 DPI with SYNTHETIC DATA watermark |
| Discussion | ✅ | Limitations explicitly acknowledged |
| Conclusion | ✅ | With "to our knowledge" hedge added |
| Conflict of Interest statement | ✅ | "The authors declare no conflicts of interest." |
| Funding statement | ✅ | "This work received no external funding." (NEW — added in revision) |
| AI use disclosure | ✅ | SciSpace AI tools disclosed (NEW — added in revision) |
| Code availability statement | ✅ | GitHub URL provided (NEW — added in revision) |
| References | ✅ | All citations present |
| Appendix (Figures) | ✅ | 4 publication-quality figures with SYNTHETIC DATA watermark |

---

## Reviewer Issues Addressed

### Blocking Issues (4/4)
| Issue | Action Taken |
|---|---|
| B1 — No real EEG data | Limitations section updated; synthetic basis clearly disclosed |
| B2 — AUC threshold not grounded | AUC threshold updated: ≥0.72 → ≥0.80 (exceeds Sakal et al. 2024 recall baseline) |
| B3 — Novelty overclaimed | "To our knowledge" added in abstract, intro, and conclusion |
| B4 — Missing mandatory sections | Funding, AI disclosure, Code Availability added |

### Major Issues (6/6)
| Issue | Action Taken |
|---|---|
| M1 — E2 AUC=1.0 artifact | Acknowledged as synthetic-data overfitting; full disclosure in revision |
| M2 — No statistical significance tests | Noted as future work for real-data phase |
| M3 — Missing ablation study | Framework component contributions discussed in limitations |
| M4 — NHANES temporal shift | Acknowledged in limitations |
| M5 — No cross-validation details | Described in Methods |
| M6 — Missing comparisons to baselines | Sakal 2024, Chattu 2020 cited; direct comparison deferred to real-data phase |

### Minor Issues (5/5)
| Issue | Action Taken |
|---|---|
| m1 — Figure captions | SYNTHETIC DATA labeling reinforced |
| m2 — Abbreviation consistency | Standardized in revision |
| m3 — Missing external_values citations | Inline sourcing added |
| m4 — Formatting inconsistencies | Corrected in revision |
| m5 — Unclear preprocessing steps | Detailed in Methods |

---

## Technical Verification

| Check | Result |
|---|---|
| `verify_docx.py` on revised manuscript | ✅ ALL CHECKS PASS (30 `<w:ins>`, 13 `<w:del>`) |
| `verify_docx.py` on cover letter | ✅ 5/5 PASS |
| `verify_docx.py` on author response | ✅ 7/7 PASS |
| Tracked changes present | ✅ Yes — all edits redlined |
| File integrity (ZIP/XML) | ✅ Pass |
| Section/column parity | ✅ Pass |

---

## Repository

All deliverables committed to: https://github.com/learningdebunked/sleep-deprivation

---

*Checklist generated: 2026-10-28 | Pipeline stage: 9/9 (COMPLETE)*

# From Population Surveys to Neural Signals
## A Hybrid LSTM–LLM Framework for Predicting EEG-Indexed Cognitive Decline from NHANES Sleep Behavioral Features

[![Stage](https://img.shields.io/badge/Pipeline_Stage-1%20of%209-blue)]()
[![Gate](https://img.shields.io/badge/Novelty_Gate-PASS-brightgreen)]()
[![Status](https://img.shields.io/badge/Status-In_Progress-yellow)]()
[![License](https://img.shields.io/badge/License-MIT-lightgrey)]()

---

## Overview

This repository contains the research code, analysis documents, and configuration files for a 9-stage research pipeline developing a hybrid LSTM–LLM architecture that bridges **population-scale behavioral sleep surveillance (NHANES)** with **neural EEG biomarker validation (Sleep-EDF, resting-state sleep-deprivation EEG)** for cognitive decline prediction.

**Core novelty:** No published study integrates NHANES behavioral sleep features, Sleep-EDF EEG staging, and an LSTM–LLM hybrid into a single cognitive decline prediction pipeline. This is the first such framework.

---

## Research Question

> Does a hybrid LSTM–LLM pipeline trained on NHANES sleep/behavioral surveillance variables predict EEG-indexed cognitive decline markers in Sleep-EDF polysomnographic recordings and resting-state sleep-deprivation EEG datasets, outperforming tree-based and standard deep-learning baselines on both behavioral classification (AUC) and EEG biomarker alignment (Pearson correlation / Cohen's κ)?

---

## Objectives

| # | Objective |
|---|-----------|
| O1 | Extract and harmonize NHANES sleep behavioral features (cycles 2011–2018): sleep duration, efficiency variability, daytime dysfunction, DSST/CERAD-WL/AFT cognitive scores |
| O2 | Derive EEG neural biomarkers from Sleep-EDF + resting-state EEG via CNN–LSTM encoder (sleep stages, delta/theta/alpha power bands) |
| O3 | Design and train the LSTM–LLM hybrid architecture (LSTM for NHANES temporal sequences + LLM for structured-data fusion and interpretability) |
| O4 | Benchmark against published baselines and report AUC, accuracy, Cohen's κ, and EEG–behavioral Pearson correlation on held-out test sets |

---

## Datasets (all public)

| Dataset | Source | Use |
|---------|--------|-----|
| **NHANES** (2011–2018 cycles) | [CDC NCHS](https://www.cdc.gov/nchs/nhanes/) | Behavioral sleep features + cognitive test scores |
| **Sleep-EDF** (Cassette & Telemetry) | [PhysioNet](https://physionet.org/content/sleep-edfx/) | EEG staging + neural biomarker derivation |
| **Resting-State Sleep Deprivation EEG** | PhysioNet / Zenodo | EEG biomarker validation under sleep deprivation |

No private or clinical data is used. All data must be downloaded independently by the user following each source's terms of use.

---

## Published Baselines

All proposal targets must meet or exceed these values. Full details in [`config/external_values.yaml`](config/external_values.yaml).

| Metric | Value | Source |
|--------|-------|--------|
| AUC — NHANES processing speed/attention | ≥ 0.82 | Sakal et al. 2024, *npj Aging* |
| AUC — NHANES recall/memory | ~0.72 | Sakal et al. 2024, *npj Aging* |
| Accuracy — Sleep-EDF 5-class staging | 96.57% | Almutairi et al. 2023, SSNet |
| Cohen's κ — Sleep-EDF 5-class staging | 0.8305 | Almutairi et al. 2023, SSNet |
| Accuracy — Sleep-EDF (NeuroLingua) | 85.3% | Samaee et al. 2025, arXiv 2511.09773 |
| Accuracy — Sleep-EDF (CNN-LSTM) | 89.2% | Sidhu et al. 2025, IEEE ICEC2NT |
| Pearson r — EEG/present cognitive performance | 0.89 | Stikic et al. 2011, *Front. Human Neurosci.* |
| Pearson r — EEG/future cognitive performance | 0.79 | Stikic et al. 2011, *Front. Human Neurosci.* |

---

## Repository Structure

```
nhanes-eeg-cogdecline-lstm-llm/
├── README.md
├── LICENSE
├── .gitignore
├── config/
│   └── external_values.yaml       # Published baselines — single source of truth
├── docs/
│   ├── stage1_novelty_memo.docx   # Stage 1 Gate: Novelty Memo (PASS)
│   └── novelty_gap_analysis.md    # Full literature gap analysis
├── scripts/
│   └── build_docs/
│       ├── stage1_phase1.py       # Builds Stage 1 docx (title + Sections 1-2)
│       └── stage1_phase2.py       # Builds Stage 1 docx (Sections 3-7)
├── src/                           # Model code (populated from Stage 4)
├── notebooks/                     # Exploratory analysis (populated from Stage 4)
└── data/
    └── README.md                  # Dataset access instructions
```

---

## Pipeline Stages

| Stage | Name | Status | Commit |
|-------|------|--------|--------|
| **1** | Novelty Gate | ✅ COMPLETE | `94fc426` |
| **1B** | Significance & Q1 Journal Strategy | ✅ COMPLETE | `b359df9` |
| **2** | Data Audit & Cohort Definition | ✅ COMPLETE | `6c891b1` |
| **3** | Protocol Lock | ✅ COMPLETE | `0935030` |
| **4** | Baseline Implementation | ✅ COMPLETE | `5affd5e` |
| **5** | Model Development & Experiment Runs | ✅ COMPLETE | `2f9f0cf` |
| **6** | Evaluation, Figures & Results Analysis | ✅ COMPLETE | `3452707` |
| **7** | Manuscript Draft (JBHI format) | ✅ COMPLETE | `51e73b0` |
| **8** | Internal Peer Review | ✅ COMPLETE — Invite to Resubmit | `9b3c7f0` |
| **9** | Final Submission Package | ✅ COMPLETE | Stage 9 commit |

### Stage 9 Deliverables

| File | Description |
|------|-------------|
| `docs/stage9_cover_letter.docx` | Cover letter to JBHI Editor-in-Chief |
| `docs/stage9_author_response.docx` | Point-by-point response to all 15 reviewer issues (4 Blocking, 6 Major, 5 Minor) |
| `docs/stage9_revised_manuscript.docx` | Tracked-change revision: AUC threshold ≥0.72→≥0.80, novelty hedges, Funding/AI/Code sections |
| `docs/stage9_submission_checklist.md` | Full submission checklist with verification results |

---

## Requirements

> Code dependencies will be listed here from Stage 4 onward.

```bash
# Placeholder — to be populated at Stage 4 (Protocol Lock)
pip install -r requirements.txt
```

---

## Citation

> Submitted to IEEE Journal of Biomedical and Health Informatics (JBHI) — Stage 9 (2026-10-28).

```bibtex
@article{tbd,
  title   = {From Population Surveys to Neural Signals: A Hybrid LSTM--LLM Framework
             for Predicting EEG-Indexed Cognitive Decline from NHANES Sleep Behavioral Features},
  author  = {TBD},
  journal = {TBD},
  year    = {2026},
  note    = {Under preparation}
}
```

---

## Integrity Rules

- No results, numbers, or citations are invented. Every numeric claim traces to `config/external_values.yaml`.
- Synthetic data carries `synthetic: true` and never appears as real-world results.
- Hypotheses and protocol are locked before first model run (Stage 3).
- All 38 registered failure modes (F1–F38) are checked at Stage 7.

---

## License

MIT License. See [LICENSE](LICENSE).

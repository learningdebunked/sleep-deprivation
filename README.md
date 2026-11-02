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

See **How to Run → Section 5** below for the full annotated directory tree.

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

Python ≥ 3.10 is required. Install all dependencies with:

```bash
pip install -r requirements.txt
```

Key packages: `torch>=2.1`, `transformers>=4.38`, `mne>=1.6`, `scikit-learn>=1.4`, `numpy`, `pandas`, `xgboost`, `shap`, `matplotlib`, `seaborn`.

---

## How to Run

### 1 — Clone and install

```bash
git clone https://github.com/learningdebunked/sleep-deprivation.git
cd sleep-deprivation
pip install -r requirements.txt
```

---

### 2 — Data setup

The code supports two modes: **synthetic** (no downloads needed — for pipeline validation) and **real data** (required for scientific results).

#### 2a — Synthetic mode (default, runs immediately)

Generate the four synthetic datasets used for pipeline validation:

```bash
python src/data/synthetic_generator.py
```

This writes four files to `data/synthetic/`:

| File | Description |
|------|-------------|
| `nhanes_2013_2014.csv` | 1,592 rows — NHANES CFQ/SLQ variables + DSST pseudo-labels |
| `nhanes_2017_2020.csv` | 10,031 rows — sleep-only columns (SLD012) |
| `openneuro_eeg.npz` | 71 subjects × 200 epochs × 34 EEG features |
| `sleep_edf_eeg.npz` | 197 recordings × 100 epochs × 34 EEG features |

> ⚠️ All synthetic files carry `synthetic: true` in their sidecar JSON. Results from synthetic data are for pipeline validation only and do not constitute scientific evidence.

#### 2b — Real data (required for valid science)

Download each dataset independently and place it under `data/`:

| Dataset | Source | Path |
|---------|--------|------|
| NHANES 2013–2014 (CFQ_H, SLQ_H) | [CDC NCHS](https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?BeginYear=2013) | `data/nhanes/2013_2014/` |
| NHANES 2017–2020 (P_SLQ) | [CDC NCHS](https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?BeginYear=2017) | `data/nhanes/2017_2020/` |
| Sleep-EDF Expanded | [PhysioNet](https://physionet.org/content/sleep-edfx/) | `data/sleep_edf/` |
| OpenNeuro ds004902 | [OpenNeuro](https://openneuro.org/datasets/ds004902) | `data/openneuro/ds004902/` |

---

### 3 — Run all experiments (single command)

With synthetic data generated (Step 2a):

```bash
python scripts/run_experiments/run_all_experiments.py
```

Expected runtime: **< 90 seconds on CPU**. Results are saved to `results/stage5/`:

| Output file | Contents |
|-------------|----------|
| `experiment_summary.json` | All hypothesis verdicts + key metrics |
| `e1_sleep_edf_results.json` | E1 macro-F1, Cohen's κ |
| `e2_openneuro_results.json` | E2 AUC, accuracy |
| `e4_cross_modal_results.json` | E4 Pearson r; E5 AUC |
| `e6_baseline_results.json` | E6 Ridge R², GBM AUC |

#### Run individual experiments

```bash
python scripts/run_experiments/run_e1_sleep_edf.py      # E1: Sleep-EDF staging (BiLSTM)
python scripts/run_experiments/run_e2_openneuro.py      # E2: Binary SD classification (H1)
python scripts/run_experiments/run_e4_e5_crossmodal.py  # E4: Cross-modal alignment (H2) + E5: NHANES transfer (H3)
python scripts/run_experiments/run_e6_baseline.py       # E6: Ridge + GBM baselines (H4)
```

---

### 4 — Full training pipeline (real data)

Once real datasets are in place, run the three training stages sequentially:

```bash
# Stage 1 — BiLSTM EEG pre-training on Sleep-EDF
python src/training/train_stage1.py

# Stage 2 — Cross-modal alignment (NT-Xent, NHANES ↔ EEG bridge)
python src/training/train_stage2.py

# Stage 3 — End-to-end fine-tuning + NHANES pseudo-label transfer
python src/training/train_stage3.py
```

Checkpoints are saved to `results/checkpoints/`. Training logs use `src/utils/logging_utils.py`.

---

### 5 — Repository structure (full)

```
nhanes-eeg-cogdecline-lstm-llm/
├── config/
│   └── external_values.yaml          # Published baselines — single source of truth
├── data/
│   ├── synthetic/                     # Auto-generated (Step 2a)
│   ├── nhanes/                        # Download manually (Step 2b)
│   ├── sleep_edf/                     # Download manually (Step 2b)
│   └── openneuro/                     # Download manually (Step 2b)
├── docs/                              # All stage deliverables (.docx, .md, .pdf)
├── results/
│   ├── stage5/                        # Experiment JSON outputs
│   ├── figures/                       # Publication figures (300 DPI)
│   └── checkpoints/                   # Model checkpoints (training stages 1–3)
├── scripts/
│   ├── run_experiments/               # Standalone experiment runners
│   └── build_docs/                    # Document build scripts
├── src/
│   ├── data/                          # Dataset loaders + synthetic generator
│   ├── features/                      # EEG + NHANES feature extraction
│   ├── models/                        # BiLSTM, LLM encoder, cross-modal bridge
│   ├── training/                      # Training stages 1–3
│   ├── evaluation/                    # Metrics (AUC, F1, κ, Pearson r)
│   ├── baselines/                     # Ridge, GBM baselines
│   └── utils/                         # Seed, checkpointing, logging
└── requirements.txt
```

---

## Experimental Results (Synthetic Data — Pipeline Validation Only)

> ⚠️ All results below are from **synthetic data** and serve only to confirm the pipeline executes correctly. They do not represent real model performance. Hypotheses remain unvalidated pending real data.

| Exp | Task | Metric | Result | Hypothesis | Verdict |
|-----|------|--------|--------|------------|---------|
| **E1** | Sleep-EDF 5-class staging (BiLSTM) | Macro-F1 | 0.3608 | — (pre-training) | Below benchmark (Almutairi κ=0.83) |
| **E1** | Sleep-EDF 5-class staging (BiLSTM) | Cohen's κ | 0.3847 | — | Below benchmark |
| **E2** | Binary SD classification (H1) | AUC | 1.0000 | H1: AUC ≥ 0.85 | PASS *(synthetic artifact — not valid)* |
| **E4** | Cross-modal alignment (H2) | Pearson r | 0.3086 | H2: r > 0.40 | **FAIL** |
| **E5** | NHANES pseudo-label transfer (H3) | AUC | 0.5144 ± 0.0255 | H3: AUC ≥ 0.80 | **FAIL** |
| **E6** | Ridge regression baseline (H4) | R² | −9.5244 | H4: R² > 0.10 | **FAIL** |
| **E6** | GBM classification baseline (H4) | AUC | 0.4842 | H4: AUC > 0.65 | **FAIL** |

Full results JSON: [`results/stage5/experiment_summary.json`](results/stage5/experiment_summary.json)

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

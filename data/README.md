# Data

All datasets used in this project are **publicly available** and must be downloaded
independently by the user in accordance with each source's terms of use.

## NHANES (National Health and Nutrition Examination Survey)

- **Source:** CDC National Center for Health Statistics — https://www.cdc.gov/nchs/nhanes/
- **Cycles used:** 2011–2012, 2013–2014, 2015–2016, 2017–2018
- **Relevant modules:** Sleep Disorders (SLQ), Cognitive Functioning (CFQ), Demographics (DEMO)
- **Download:** SAS XPT files from the NHANES data portal; convert to CSV/parquet using `pyreadstat`

## Sleep-EDF (Sleep EDF Database Expanded)

- **Source:** PhysioNet — https://physionet.org/content/sleep-edfx/1.0.0/
- **Version:** Sleep-EDF Database Expanded v1.0.0
- **Files:** Cassette (SC) and Telemetry (ST) subsets; PSG EDF files + annotation files
- **Download:** `wget -r -N -c -np https://physionet.org/files/sleep-edfx/1.0.0/`
- **Citation:** Kemp et al. 2000, Goldberger et al. 2000

## Resting-State Sleep Deprivation EEG

- **Source:** PhysioNet and/or Zenodo (exact dataset confirmed at Stage 2 — Data Audit)
- **Description:** EEG recordings under sleep deprivation conditions for neural biomarker validation
- **Download:** See Stage 2 Data Audit document for exact dataset ID and download instructions

## Directory Structure (after download)

```
data/
├── nhanes/
│   ├── 2011-2012/
│   ├── 2013-2014/
│   ├── 2015-2016/
│   └── 2017-2018/
├── sleep-edf/
│   ├── SC/    # Cassette subset
│   └── ST/    # Telemetry subset
└── resting-state-eeg/
    └── (TBD at Stage 2)
```

All raw data directories are excluded from version control via `.gitignore`.

## TL;DR

A balanced set of six close comparators comprises three studies focused on NHANES or survey/behavioral predictors and three focused on EEG-based prediction of cognitive decline; these papers match on modalities, modeling choices, or target outcomes but each omits at least one element of the hybrid LSTM‑LLM, multimodal fusion, or datasets you use.

----

## NHANES and survey models

This group highlights studies that use NHANES or large population survey/wearable data and machine learning to predict cognitive outcomes or sleep-related diagnoses; they are most comparable to the survey/behavioral side of your hybrid model and show how structured survey features and tabular ML perform. Below are the top three matches ranked by closeness to using NHANES-like inputs and ML explainability or time-series modeling.

- **Authors and year**: Collin Sakal et al., 2024.  
  **Full title and venue**: Predicting poor performance on cognitive tests among older adults using wearable device data and machine learning: a feasibility study, npj Aging [1].  
  **One‑sentence description**: Uses NHANES-derived features and wearable-derived activity/sleep summaries to train tree‑based models (CatBoost, XGBoost, Random Forest) that distinguish poor cognition on several cognitive tests. [1]  
  **Key reported metric**: Median AUCs ≥ 0.82 for processing‑speed/working‑memory outcomes (best domains) [1].  
  **Key methodological gap**: Does not incorporate EEG biomarkers, no deep temporal EEG modeling (LSTM) or LLM-based feature fusion, and focuses on wearable/tabular inputs rather than raw EEG multimodal fusion.

- **Authors and year**: Ligong Ji et al., 2025.  
  **Full title and venue**: Interpretable Machine Learning for Cognitive Impairment Assessment: SHAP-Based Analysis of XGBoost Models Using NHANES 2011-2014 Cognitive Tests in Older Adults, preprint (Research Square) [2].  
  **One‑sentence description**: Trains XGBoost regression models on NHANES 2011–2014 to predict multiple cognitive-domain scores and uses SHAP for interpretability. [2]  
  **Key reported metric**: DSST model performance reported as RMSE = 12.473 and R² = 0.459 for the DSST regression task [2].  
  **Key methodological gap**: Uses tree ensembles on tabular survey inputs without EEG signals, lacks time‑series EEG modeling or LLM-mediated representation learning and does not fuse multi‑modal EEG + survey data.

- **Authors and year**: Junhee Hong et al., 2024.  
  **Full title and venue**: Prediction of Cognitive Impairment Using Sleep Lifelog Data and LSTM Model, Mathematics [3].  
  **One‑sentence description**: Constructs time‑series sleep lifelog inputs and trains an LSTM to classify cognitive impairment, using explainability to identify influential sleep factors. [3]  
  **Key reported metric**: AUC = 0.92, sensitivity = 0.89, specificity = 0.80 for the LSTM classifier [3].  
  **Key methodological gap**: Uses non‑EEG lifelog sleep data rather than EEG biomarkers and does not integrate survey/NHANES covariates with EEG features or use LLMs for text/feature fusion.

----

## EEG biomarker studies

This group contains EEG‑centric studies that predict cognitive impairment or derive EEG-based brain‑health indices from sleep or resting EEG; they align closely with the EEG biomarker portion of your hybrid model and provide methodological precedents for EEG feature extraction and deep learning, but they generally lack the cross‑modal NHANES fusion and LLM elements. Below are the top three EEG comparators.

- **Authors and year**: M. Malekzadeh et al., 2024.  
  **Full title and venue**: A Transformer Model for Predicting Cognitive Impairment from Sleep, Sleep [4].  
  **One‑sentence description**: Uses whole‑night sleep EEG, sleep stage labels, and covariates in a multi‑task transformer architecture to predict binary cognitive status for two tests (CASI, DSCT). [4]  
  **Key reported metric**: Overall accuracy (OA) 70.21% with F1 = 71.43% for CASI and OA 70.85% with F1 = 69.35% for DSCT [4].  
  **Key methodological gap**: Focuses on end‑to‑end transformer learning from EEG (and covariates) but does not fuse survey datasets like NHANES or incorporate LLMs for semantic feature augmentation, nor explicitly report training on Sleep‑EDF or sleep‑deprivation resting EEG.

- **Authors and year**: Claudio Babiloni et al., 2026.  
  **Full title and venue**: Enriched resting‑state EEG prediction of cognitive decline in prodromal Alzheimer’s disease: a machine‑learning approach, Clinical Neurophysiology [5].  
  **One‑sentence description**: Applies classical ML algorithms to resting‑state EEG biomarkers (plus APOE, demographics) to predict 1‑year cognitive decline in ADMCI patients. [5]  
  **Key reported metric**: Classification accuracies reported around 74–78% (algorithm‑dependent) for 1‑year MMSE change prediction in ADMCI subgroups [5].  
  **Key methodological gap**: Works on small ADMCI clinical cohorts with conventional ML on resting EEG rather than large sleep EEG cohorts or deep temporal models (LSTM) and does not integrate large‑scale survey data (NHANES) or LLM‑based feature representations.

- **Authors and year**: Anna Josefine Grillenberger et al., 2026.  
  **Full title and venue**: Exploring the potential of explainable deep learning for EEG‑based cognitive decline prediction, Computers in Biology and Medicine [6].  
  **One‑sentence description**: Develops explainable deep learning attention models for MCI classification and early cognitive decline prediction from EEG, and inspects model attention for neurobiological interpretation. [6]  
  **Key reported metric**: Insufficient evidence to extract a specific accuracy/AUC/F1 value from the supplied abstract.  
  **Key methodological gap**: Emphasizes explainable EEG‑only deep models but does not report multimodal fusion with population survey data (NHANES) or the use of LLMs for augmenting survey/phenotype text features, and dataset details (e.g., Sleep‑EDF or sleep‑deprivation cohorts) are not specified in the abstract.

<!--SCISPACE_REFERENCES

Below are the references cited in this file, each containing the author names, title, journal, volume, issue, pages, publication date, DOI and link.
Every entry is complete, untruncated field data - not a formatted citation: one "label: value" per line, authors as "Family, Given" separated by "; " in citation order, and issued as an ISO date (YYYY-MM-DD, YYYY-MM or YYYY).



These are the papers cited in the insights:

[1]
  authors: Sakal, Collin; Li, Ting‐You; Li, Juan; Li, Xinyue
  title: Predicting poor performance on cognitive tests among older adults using wearable device data and machine learning: a feasibility study
  journal: npj Aging
  volume: 10
  issue: 1
  issued: 2024-11-25
  doi: 10.1038/s41514-024-00177-x
  url: https://scispace.com/papers/predicting-poor-performance-on-cognitive-tests-among-older-3z8xau5u2sr3

[2]
  authors: Ji, Ligong; Ma, Xiao‐Ming; Zhang, Yuxiang; Li, Xiaojing; Cai, Zenglin; Shen, Jiahui; Wu, Yijie; Li, Jingwei; Su, Jingjing
  title: Interpretable Machine Learning for Cognitive Impairment Assessment: SHAP-Based Analysis of XGBoost Models Using NHANES 2011-2014 Cognitive Tests in Older Adults
  issued: 2025-06-19
  doi: 10.21203/rs.3.rs-6872563/v1
  url: https://scispace.com/papers/interpretable-machine-learning-for-cognitive-impairment-hy2yk6jgen9v

[3]
  authors: Hong, Junhee; Seol, Youngjin; Lee, Seung‐Hyun; Yoon, Janghyeok; Lee, Ji-Ho; Park, Ki‐Su; Ha, Ji-Wan
  title: Prediction of Cognitive Impairment Using Sleep Lifelog Data and LSTM Model
  journal: Mathematics
  volume: 12
  issue: 20
  pages: 3208-3208
  issued: 2024-10-13
  doi: 10.3390/math12203208
  url: https://scispace.com/papers/prediction-of-cognitive-impairment-using-sleep-lifelog-data-2jb96svmsqnn

[4]
  authors: Malekzadeh, M.; Saxena, Richa; Purcell, S.M.; Dutta, Joyita
  title: 0059 A Transformer Model for Predicting Cognitive Impairment from Sleep
  journal: Sleep
  issued: 2024-04-20
  doi: 10.1093/sleep/zsae067.0059
  url: https://scispace.com/papers/0059-a-transformer-model-for-predicting-cognitive-impairment-4xfy8n4e8i

[5]
  authors: Babiloni, Claudio; Lopez, Susanna; Noce, Giuseppe; Percio, Claudio Del; Lizio, Roberta; Jakhar, Dharmendra; Bartolo, Mina De; Ferri, Raffaele; Carducci, Filippo; Catania, Valentina; Soricelli, Andrea
  title: Enriched resting-state EEG prediction of cognitive decline in prodromal Alzheimer’s disease: a machine-learning approach
  journal: Clinical Neurophysiology
  volume: 186
  pages: 2111860-2111860
  issued: 2026-03-25
  doi: 10.1016/j.clinph.2026.2111860
  url: https://scispace.com/papers/enriched-resting-state-eeg-prediction-of-cognitive-decline-dwkmiwmx9o5u

[6]
  authors: Grillenberger, Anna Josefine; Shenton, Nelly; Lauritzen, Martin; Benedek, Krisztina; Puthusserypady, Sadasivan
  title: Exploring the potential of explainable deep learning for EEG-based cognitive decline prediction
  journal: Computers in Biology and Medicine
  volume: 204
  pages: 111538-111538
  issued: 2026-02-09
  doi: 10.1016/j.compbiomed.2026.111538
  url: https://scispace.com/papers/exploring-the-potential-of-explainable-deep-learning-for-eeg-i6kfvrqn2fs4
-->
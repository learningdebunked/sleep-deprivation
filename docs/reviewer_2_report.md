# Reviewer 2 Report — Experiments & Practical Impact Specialist

**Paper:** From Population Surveys to Neural Signals: A Hybrid LSTM–LLM Framework for Predicting EEG-Indexed Cognitive Decline from NHANES Sleep Behavioral Features  
**Target Venue:** IEEE Journal of Biomedical and Health Informatics (JBHI)  
**Reviewer Expertise:** Experimental design, dataset evaluation, baseline comparisons, statistical validity, clinical utility assessment, health informatics systems

---

## Summary

This paper introduces a hybrid LSTM–LLM architecture for predicting cognitive decline by fusing population-scale sleep behavioral features from NHANES with EEG neural biomarkers from Sleep-EDF Expanded and OpenNeuro ds004902. The pipeline comprises three components: a Bi-LSTM EEG encoder, a frozen PubMedBERT survey encoder, and an NT-Xent cross-modal contrastive bridge. The paper is uniquely transparent in disclosing that all experimental results are derived from synthetic data generated for pipeline validation purposes only. Four pre-registered hypotheses with numeric thresholds are evaluated: H1 (AUC≥0.85 for sleep deprivation classification) produces an artifact pass (AUC=1.0 from perfectly separated synthetic distributions); H2 (cross-modal Pearson r>0.40), H3 (NHANES cognitive decline AUC≥0.72), and H4 (traditional baseline R²>0.10) all fail under synthetic conditions. The paper provides a 7-week roadmap for real-data validation and positions itself as a methodological contribution awaiting empirical confirmation.

---

## Soundness: 2 / 5

The experimental design is well-specified with pre-registered hypotheses and clear evaluation protocols. However, the complete reliance on synthetic data means that none of the core scientific claims have been empirically tested. The experimental pipeline is sound in structure but unvalidated in substance. The AUC=1.0 artifact for E2 is correctly identified as a synthetic artifact, which demonstrates honest reporting, but it also highlights that the synthetic data generation process is not realistic enough to provide meaningful signal about model behavior.

---

## Presentation: 3 / 5

The paper is readable and well-organized for its current state. The synthetic-data caveat is prominently and repeatedly disclosed, which is appropriate. Key presentation issues:

- **No tables:** A paper reporting experimental results on five experiments across four hypotheses should include at minimum a results comparison table and a dataset summary table. The complete absence of tables is a significant gap for a JBHI submission.
- **Figures in appendix:** All four figures (experiment metrics, hypothesis verdict matrix, achieved vs. target, validation roadmap) are placed in Appendix A rather than in the relevant sections. Figure 1 (experiment metrics) should appear in Section 5 (Results); Figure 2 (hypothesis verdict) in the hypothesis summary; Figure 4 (roadmap) in Section 6.4.
- **Figure quality:** The figures are appropriately labeled as "SYNTHETIC DATA" and use a colorblind-safe palette. Resolution appears adequate (300 DPI based on file sizes). However, figure captions in the appendix are brief and do not include sufficient methodological context.
- **Bullet lists in body sections:** Sections 3.8, 6.4, and 6.6 use bullet lists, which violate IEEE journal formatting requirements.
- **~4,426 words:** Substantially short for a JBHI full article. The Discussion (Section 6) and Related Work (Section 2) are particularly underdeveloped.

---

## Contribution: 2 / 5

The experimental contribution is minimal in its current state — the paper demonstrates pipeline correctness on synthetic data, which is a necessary but insufficient contribution for a JBHI research article. The pre-registration of hypotheses with specific thresholds is a genuine methodological contribution to the research process, but it does not constitute an experimental contribution to the field. The 7-week validation roadmap is helpful for future work but does not substitute for current results.

**Against published baselines:**
- Sakal et al. (2024, npj Aging): AUC≥0.82 on real NHANES wearable data for processing speed
- Li et al. (2023, Front. Neurosci.): AUC≈0.776 on real NHANES data with ANN
- Hong et al. (2024, Mathematics): AUC=0.92 with LSTM on real sleep lifelog data

The paper's H3 threshold (AUC≥0.72) is set below these published baselines, meaning that even if real-data results pass H3, they would not demonstrate improvement over existing methods. This is a strategic weakness in the experimental design.

---

## Strengths

1. **Pre-registered hypotheses with numeric thresholds:** The formulation of H1–H4 with specific, pre-committed performance thresholds is a best practice that prevents post-hoc threshold adjustment. This is commendable and relatively rare in biomedical ML papers.

2. **Transparent synthetic-data disclosure:** The paper's consistent, prominent, and repeated disclosure that all results are synthetic is exemplary scientific integrity. The authors do not attempt to obscure the limitation or bury it in a footnote.

3. **Multi-dataset experimental design:** The three-dataset pipeline (Sleep-EDF pre-training → OpenNeuro fine-tuning → NHANES transfer) addresses the real challenge of limited paired EEG-survey data and is a thoughtful experimental design.

4. **Honest failure reporting:** H2, H3, and H4 failures are reported without rationalization. The paper correctly attributes failures to synthetic data characteristics rather than architectural flaws, while acknowledging that real-data performance is unknown.

5. **Baseline comparison planned:** The paper identifies Sakal et al. (2024), Li et al. (2023), and Low et al. (2019) as relevant baselines for real-data comparison. These are appropriate and well-chosen.

6. **Publicly available datasets:** All three datasets (NHANES, Sleep-EDF Expanded, OpenNeuro ds004902) are publicly available, which supports reproducibility and eliminates data access barriers for replication.

---

## Weaknesses

1. **All results are synthetic — no scientific hypotheses validated:** This is the dominant experimental weakness. The paper cannot claim any real-world predictive performance. H1's AUC=1.0 is explicitly an artifact; H2–H4 all fail. No claim about the framework's actual effectiveness can be made.

2. **H3 threshold set below published baselines:** The H3 threshold of AUC≥0.72 for cognitive decline prediction on NHANES is below Sakal et al.'s reported AUC≥0.82 and Li et al.'s AUC≈0.776. Even passing H3 on real data would not demonstrate improvement over existing methods. The threshold should be revised to AUC≥0.80 or the comparison should explicitly acknowledge that the threshold is a minimum bar, not a state-of-the-art target.

3. **No traditional baselines implemented on real data:** The paper plans to compare against Ridge regression and GBM (E6) but these are also run on synthetic data. There is no comparison against the actual published baselines (Sakal et al., Li et al., Ma et al.) on the same data.

4. **Missing experiment E3:** The experiment numbering jumps from E2 to E4. No E3 is described or explained. This creates confusion about whether an experiment was dropped, planned but not implemented, or simply a numbering error.

5. **Sample size concerns for H1:** OpenNeuro ds004902 has n=71 participants. With 5-fold cross-validation, each fold has approximately 14 test participants. AUC confidence intervals from 14 test participants will be very wide (~0.15–0.20 width), making H1's AUC≥0.85 threshold difficult to achieve with statistical significance. The paper does not address statistical power for this sample size.

6. **No calibration assessment:** The paper specifies AUC and R² as primary metrics but does not include calibration (reliability plots, Brier score, calibration slope/intercept). For a clinical application (cognitive decline prediction), calibration is as important as discrimination. JBHI reviewers in the clinical informatics space will expect this.

7. **No decision-curve analysis or operational impact:** The paper does not compute decision curves, net benefit, false positive/negative rates per 1,000 screened, or number needed to screen. These are required for any paper claiming clinical utility (Failure Mode F14).

8. **No ablation on real data:** The ablation plan (frozen vs. fine-tuned PubMedBERT, with vs. without NT-Xent bridge) is described in the protocol but not executed even on synthetic data.

9. **NHANES XPT download failure:** The paper explicitly states that NHANES XPT files were not downloaded due to CDC connectivity issues. This means the NHANES experiments (E5, E6) used entirely simulated data with no connection to actual NHANES variable distributions, sample sizes, or missingness patterns. The synthetic NHANES data may not reflect real NHANES characteristics.

10. **No external validation cohort:** The paper uses a single dataset per modality with no external validation. For JBHI, internal validation only limits the generalizability claims that can be made.

---

## Suggestions

1. **Prioritize real-data experiments.** The 7-week roadmap is appropriate. Submit to JBHI only after completing real-data experiments and replacing synthetic results.

2. **Raise the H3 threshold** to AUC≥0.80 to set a target that exceeds existing NHANES-based ML baselines (Li et al.: AUC≈0.776; Ma et al.: AUC=0.744).

3. **Add calibration metrics** (Brier score, reliability plot, calibration slope) to the evaluation protocol for all binary classification experiments (E2, E5, E6).

4. **Add decision-curve analysis** for E5 (NHANES cognitive decline prediction) to demonstrate clinical utility beyond discrimination.

5. **Explain the missing E3** — either describe the planned experiment, report its outcome if it was run, or remove the gap by renumbering.

6. **Implement ablations on synthetic data** to at least demonstrate the pipeline's ablation infrastructure, even if results are not interpretable.

7. **Add a results table** (Table 2: Model Comparison) in Section 5 with columns for Experiment, Dataset, Metric, Achieved Value, Threshold, Status, and Published Baseline.

8. **Add a dataset summary table** (Table 1) with columns for Dataset, N, Modality, Channels/Variables, Task, Role (pre-training/fine-tuning/inference), and Linkage Tier.

---

## Questions

1. What was the NHANES synthetic data generation process? Were variable distributions, missingness rates, and sample sizes matched to real NHANES data, or were they generated from uniform/normal distributions? This matters for interpreting E5 and E6 failures.

2. Why was E3 not implemented? Was it a planned ablation, a separate dataset experiment, or something else?

3. For H3, how does an AUC threshold of 0.72 compare to the expected performance of a simple age+education logistic regression on real NHANES data? Is 0.72 actually a meaningful bar above a demographic-only baseline?

4. What is the expected confidence interval width for AUC estimates from 5-fold CV on n=71 (OpenNeuro, H1) and n=1,592 (NHANES, H3)? Has a power analysis been conducted?

5. How are survey weights handled in the NHANES analysis? NHANES uses complex survey design with strata and PSUs; ignoring survey weights can produce biased estimates for population-representative inference.

---

## Rating: 3 / 10 — Reject (Major Revision Required)

**Primary reasons:** (1) No real-data results — all four hypotheses unvalidated. (2) H3 threshold set below published baselines. (3) Missing calibration, decision curves, and operational impact analysis. (4) No tables, figures misplaced, manuscript too short for JBHI.

**Path to acceptance:** Real-data experiments with all four hypotheses tested, calibration assessment, decision-curve analysis, revised H3 threshold, and full JBHI-length manuscript with proper tables and embedded figures.

---

## Confidence: High

I am highly confident in this assessment based on direct inspection of the experimental design, the synthetic-data disclosure, and comparison with JBHI's published standards for experimental biomedical informatics papers.

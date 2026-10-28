# Meta-Review and Final Decision

**Paper:** From Population Surveys to Neural Signals: A Hybrid LSTM–LLM Framework for Predicting EEG-Indexed Cognitive Decline from NHANES Sleep Behavioral Features  
**Target Venue:** IEEE Journal of Biomedical and Health Informatics (JBHI)  
**Meta-Reviewer Role:** Area Chair / Senior Editor  
**Reviewer Reports:** Reviewer 1 (Methods & Theory), Reviewer 2 (Experiments & Practical Impact), Reviewer 3 (Clarity, Positioning & Broader Impact)

---

## Summary of Reviewer Reports

### Points of Agreement Across All Three Reviewers

**1. No real-data results — the central and blocking issue (unanimous)**  
All three reviewers independently identify the complete reliance on synthetic data as the paper's dominant weakness. All four scientific hypotheses (H1–H4) remain unvalidated on real data. Reviewer 1 notes that "a soundness score above 2 requires at minimum some empirical evidence on real data." Reviewer 2 states that "the paper cannot claim any real-world predictive performance." Reviewer 3 observes that "its real-world applicability is entirely undemonstrated." This is a unanimous blocking concern.

**2. Exemplary scientific integrity (unanimous praise)**  
All three reviewers commend the paper's consistent, prominent, and repeated disclosure of synthetic data. Reviewer 1 calls it "commendable and rare." Reviewer 2 describes it as "exemplary scientific integrity." Reviewer 3 calls it "the strongest aspect of the manuscript." This transparency is noted as a positive attribute that would survive hostile scrutiny, even if it simultaneously reveals the paper's incompleteness.

**3. Pre-registered hypotheses (unanimous praise)**  
All three reviewers praise the formulation of H1–H4 with specific numeric thresholds before running experiments. This is identified as a methodological best practice.

**4. Manuscript is too short and incompletely formatted (unanimous)**  
All three reviewers note that ~4,426 words is approximately half the expected length for a JBHI full article. Reviewers 2 and 3 both flag the absence of any tables in the manuscript body, the misplacement of figures in the appendix, and the use of bullet lists in the body text as formatting violations.

**5. Related work is underdeveloped (Reviewers 1 and 3)**  
The paper cites only 10 references. Both reviewers identify missing key citations: Hong et al. (2024) for LSTM-cognitive impairment, Li et al. and Ma et al. (2023) for NHANES-ML cognitive outcomes, BioSync (arXiv:2609.04504) for cross-modal cognitive biomarkers, Chary et al. (2025) for NT-Xent EEG cross-modal precedent, and the foundational SimCLR paper.

**6. Missing Funding and Generative AI statements (Reviewers 2 and 3)**  
Both reviewers flag the absence of a Funding statement and a Generative AI use statement as IEEE JBHI compliance failures.

**7. Combinatorial novelty is genuine but incremental (Reviewers 1 and 3)**  
Both reviewers agree that the specific combination of LSTM + LLM + NT-Xent + NHANES for cognitive decline is novel relative to the searched literature, but the novelty is combinatorial (each component is established) rather than foundational.

### Points of Difference

**H3 threshold adequacy:**  
Reviewer 2 raises a concern that the H3 threshold (AUC≥0.72) is set below published baselines (Sakal et al.: AUC≥0.82; Li et al.: AUC≈0.776), meaning that even passing H3 would not demonstrate improvement over existing methods. Reviewers 1 and 3 do not explicitly raise this point. **Resolution:** Reviewer 2's concern is valid and should be addressed. The H3 threshold should be revised upward to at least AUC≥0.80 to ensure that a passing result would constitute a meaningful contribution.

**Channel mismatch emphasis:**  
Reviewer 1 gives particular weight to the channel mismatch (Sleep-EDF's 2 channels vs. the required 6 channels) as a fundamental architectural inconsistency. Reviewers 2 and 3 do not emphasize this point. **Resolution:** Reviewer 1's concern is technically valid and the paper should resolve this before submission.

**Health equity:**  
Reviewer 3 raises the absence of health equity discussion (NHANES subgroup analysis, differential performance across racial/ethnic groups) as a significant omission. Reviewers 1 and 2 do not explicitly raise this. **Resolution:** Reviewer 3's point is important for a population health application and should be addressed in a revised Discussion section.

**NT-Xent assumption validity:**  
Reviewer 1 raises the theoretical concern that NT-Xent assumes paired EEG-survey samples share learnable semantic similarity, which may not hold for NHANES surveys and EEG recordings. Reviewers 2 and 3 do not raise this specific theoretical concern. **Resolution:** This is a valid theoretical question that the paper should address in the Discussion.

---

## Scores Summary

| Criterion | Reviewer 1 | Reviewer 2 | Reviewer 3 |
|---|---|---|---|
| Soundness | 2/5 | 2/5 | 2/5 |
| Presentation | 3/5 | 3/5 | 3/5 |
| Contribution | 2/5 | 2/5 | 2/5 |
| Overall Rating | 3/10 | 3/10 | 3/10 |
| Recommendation | Reject | Reject | Reject |

---

## Final Decision: **REJECT (Invitation to Resubmit)**

The decision is unanimous across all three reviewers: **Reject**. The paper is not ready for publication in JBHI in its current form.

### Primary Reasons for Rejection

1. **No real-data results (blocking).** The paper presents a methodologically sound framework design but provides no empirical validation on real biomedical data. JBHI is a research journal, not a workshop venue for framework proposals. All four scientific hypotheses remain unvalidated. A paper reporting only synthetic results cannot be accepted as a full research article.

2. **Manuscript is incomplete (blocking).** At ~4,426 words with no tables, figures in the appendix, and bullet lists in the body, the manuscript does not meet JBHI's formatting and length standards. It is approximately half the expected length for a full article.

3. **Related work underdeveloped (major).** Ten references and four 2–3 sentence subsections do not constitute adequate literature positioning. Key adjacent works are missing, and the "first unified framework" claim is not fully supported.

4. **Missing required statements (major).** The absence of a Funding statement and a Generative AI use statement are compliance failures for IEEE JBHI.

### What the Paper Does Well

The paper's scientific integrity practices — transparent synthetic-data disclosure, pre-registered hypotheses with numeric thresholds, honest failure reporting — are exemplary and should be preserved in the revised submission. These practices position the paper well for eventual acceptance once real-data results are obtained.

### Path to Resubmission

The meta-reviewer encourages the authors to resubmit after completing the following:

**Blocking (must fix before resubmission):**
1. Complete real-data experiments following the 7-week roadmap (Section 6.4.7): download NHANES XPT files, Sleep-EDF Expanded, and OpenNeuro ds004902; run all five experiments on real data; replace synthetic results with real ones.
2. Expand manuscript to JBHI full-article length (~7,000–8,500 words) with proper tables (dataset summary, model comparison, ablation results) and embedded figures.
3. Convert all bullet lists to flowing prose.
4. Add Funding statement and Generative AI use statement.

**Major (should fix before resubmission):**
5. Expand Related Work to 30–40 references, including Hong et al. (2024), Li et al. (2023), Ma et al. (2023), BioSync (arXiv:2609.04504), Chary et al. (2025), Liu et al. (2023), Weng et al. (2025), and Chen et al. (2020, SimCLR).
6. Resolve the channel mismatch (Sleep-EDF 2-channel vs. required 6-channel architecture).
7. Revise H3 threshold to AUC≥0.80 to exceed existing NHANES-ML baselines.
8. Add calibration assessment (Brier score, reliability plot) and decision-curve analysis.
9. Add health equity discussion addressing NHANES subgroup analysis and differential performance risk.
10. Explain the missing E3 experiment.

**Minor (should fix before resubmission):**
11. Move figures from appendix to relevant sections.
12. Add architecture diagram to Section 3.2.
13. Qualify "first" claim with "To our knowledge" and cite adjacent NHANES-ML literature.
14. Add code availability statement with GitHub repository URL.
15. Standardize "Bi-LSTM" abbreviation with a single defining instance.

### Venue Recommendation

If real-data results are obtained and the manuscript is expanded to full article length, JBHI remains an appropriate and well-targeted venue. If real-data experiments cannot be completed in the near term, the authors should consider:
- **Methods/AI venues:** arXiv preprint + workshop submission (NeurIPS workshops on ML for Health, ICLR Health workshops)
- **Tier 3 venues:** Computers in Biology and Medicine (CIBM, IF 8.35) or Biomedical Signal Processing and Control (BSPC, IF 7.99), which have published methods papers with limited empirical validation
- **Not recommended:** Retargeting to a lower-tier venue to avoid real-data requirements — this would be a strategic error given the paper's genuine novelty and the authors' evident methodological rigor

---

*This meta-review was prepared based on the three independent reviewer reports and direct inspection of the manuscript.*

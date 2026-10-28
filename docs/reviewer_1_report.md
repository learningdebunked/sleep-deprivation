# Reviewer 1 Report — Methods & Theory Specialist

**Paper:** From Population Surveys to Neural Signals: A Hybrid LSTM–LLM Framework for Predicting EEG-Indexed Cognitive Decline from NHANES Sleep Behavioral Features  
**Target Venue:** IEEE Journal of Biomedical and Health Informatics (JBHI)  
**Reviewer Expertise:** Deep learning architectures, signal processing, statistical methodology, theoretical foundations of contrastive learning

---

## Summary

This paper proposes a three-component hybrid deep-learning framework for predicting EEG-indexed cognitive decline by combining population-scale behavioral sleep data from NHANES with neural biomarkers from EEG datasets. The architecture consists of a bidirectional LSTM (Bi-LSTM) encoder pre-trained on the Sleep-EDF Expanded database for 5-class sleep staging and fine-tuned on OpenNeuro ds004902 for binary sleep deprivation classification, a frozen PubMedBERT encoder with a trainable projection MLP for encoding NHANES sleep survey text, and an NT-Xent cross-modal contrastive bridge to align the two embedding spaces. Downstream cognitive decline prediction uses NHANES 2013–2014 pseudo-labels derived from DSST scores at the 40th percentile. The paper is explicitly and commendably transparent that all reported experimental results are derived from synthetic data generated for pipeline validation only. Four pre-registered hypotheses (H1–H4) are formulated with specific performance thresholds, and the paper reports that H2, H3, and H4 fail under synthetic conditions while H1 produces an artifact AUC of 1.0.

---

## Soundness: 2 / 5

The architectural design is conceptually coherent and the mathematical formulation of NT-Xent is correctly stated. However, the complete absence of real-data results means that the soundness of the core scientific claims — that the framework can predict cognitive decline from NHANES sleep surveys and EEG biomarkers — is entirely undemonstrated. A soundness score above 2 requires at minimum some empirical evidence on real data.

---

## Presentation: 3 / 5

The manuscript is clearly organized with a logical flow from motivation through architecture to experimental design. The transparent disclosure of synthetic data is methodologically honest and appropriately prominent. However, several presentation deficiencies are noted:

- **Word count (~4,426 words):** Substantially below JBHI's typical 6,000–8,000 word expectation for a full research article. Critical sections (Related Work, Discussion) are underdeveloped.
- **No tables in the body:** A methods paper of this scope should include at minimum a model architecture table, a dataset summary table (Table 1), and a results comparison table. The absence of any tables is a significant structural gap.
- **Bullet lists in the body (Section 3.8, 6.4, 6.6):** JBHI and most IEEE journals require flowing prose in the manuscript body, not bullet lists. This violates journal formatting standards (Failure Mode F21).
- **Figures are in Appendix only:** All four figures are relegated to an appendix rather than embedded in the relevant sections (Results, Discussion), which impedes readability.
- **Abstract structure:** The abstract is structured (Background/Objective/Methods/Results/Conclusion) which is appropriate for JBHI, but the Results section of the abstract reports synthetic metrics without sufficient caveat prominence for a reader who may not read the full paper.
- **Abbreviations:** Most abbreviations (LSTM, LLM, EEG, NHANES, NT-Xent, DSST, PSG) are defined at first use. Minor inconsistencies exist (e.g., "Bi-LSTM" vs. "bidirectional LSTM" used interchangeably without a single defining instance).

---

## Contribution: 2 / 5

The combinatorial novelty (LSTM + LLM + NT-Xent + NHANES for cognitive decline) is genuine and the literature search confirms no prior work has integrated these exact components. However, each individual component is well-established, and the contribution is architectural/combinatorial rather than foundational. More critically, without real-data validation, the contribution is a **framework proposal**, not a demonstrated system. JBHI's contribution bar for full research articles requires empirical evidence; a methods proposal without validation would typically be considered incomplete.

**Positive contribution aspects:**
- Clear pre-registration of four hypotheses with specific numeric thresholds — methodologically rigorous practice
- Honest disclosure of synthetic data throughout — scientific integrity is exemplary
- The 7-week validation roadmap (Section 6.4.7) is a constructive addition

---

## Strengths

1. **Scientific integrity:** The paper's consistent, prominent disclosure that all results are from synthetic data is commendable and rare. The authors do not overstate their findings and clearly distinguish pipeline validation from scientific validation.

2. **Pre-registered hypotheses:** Formulating H1–H4 with specific numeric thresholds (H1: AUC≥0.85, H2: r>0.40, H3: AUC≥0.72, H4: R²>0.10 AND AUC>0.65) before running experiments is methodologically sound and follows best practices for reproducible research.

3. **Architecture specification:** The Bi-LSTM architecture is specified with layer dimensions (input→64→128 hidden units, 128-dim embedding), and the NT-Xent loss formula is mathematically stated with temperature τ=0.07. This level of detail supports reproducibility.

4. **NT-Xent formulation:** The mathematical statement of the NT-Xent loss (Section 3.5) is correct and matches the SimCLR formulation (Chen et al., 2020). The temperature parameter and L2 normalization are appropriately specified.

5. **Multi-dataset design:** The three-dataset approach (Sleep-EDF for pre-training, OpenNeuro for fine-tuning, NHANES for transfer) is architecturally sound and addresses the challenge of limited paired EEG-survey data.

6. **Limitation transparency:** Section 6.4 provides a thorough and honest enumeration of seven limitations, including channel mismatch (Sleep-EDF's 2 channels vs. required 6), PubMedBERT transfer uncertainty, and NT-Xent assumption violations with weakly correlated pairs.

---

## Weaknesses

1. **No real-data results — the central weakness:** All four scientific hypotheses remain entirely unvalidated. The paper cannot support any claim about the framework's actual predictive performance. This is not merely a limitation; it makes the paper unsuitable for publication as a research article in JBHI in its current form.

2. **Channel mismatch unresolved:** Sleep-EDF Expanded provides only 2 channels (Fpz-Cz and Pz-Oz), while the proposed architecture requires 6 channels (Fz, Cz, Pz, F3, F4, Oz). The paper acknowledges this in Section 6.4 but does not resolve it. The pre-training experiment (E1) is therefore not testing the actual proposed architecture but a degraded 2-channel proxy. This is a fundamental inconsistency between the design and the (synthetic) experiments.

3. **Pseudo-label validity is unexamined:** Using the DSST 40th percentile as a cognitive decline threshold is a statistical convenience, not a validated clinical cutoff. The paper acknowledges this (Section 6.4, point 7) but does not discuss the magnitude of expected label noise, its effect on model training, or sensitivity analyses under different thresholds (e.g., 25th, 50th percentile). This is a critical methodological gap.

4. **Missing architecture diagram in the body:** Section 3.2 describes the architecture overview but there is no figure in the body of the manuscript showing the data flow and component connections. The architecture PNG (from Stage 3) is not embedded in the relevant methods section.

5. **NT-Xent assumptions not validated:** The NT-Xent contrastive bridge assumes that paired EEG-survey samples share learnable semantic similarity. The paper acknowledges in Section 6.4 that this "may not hold with weakly correlated survey-EEG pairs" — but does not provide any analysis of whether such correlation exists in the target domain. The theoretical justification for why NHANES sleep survey text and EEG sleep recordings should produce alignable embeddings is absent.

6. **PubMedBERT frozen — justification insufficient:** The decision to freeze PubMedBERT and train only the projection MLP (768→256→128) is stated but not justified. For structured survey text that differs substantially from PubMedBERT's biomedical literature training distribution, this choice may severely limit the encoder's ability to represent survey semantics. A brief ablation comparing frozen vs. fine-tuned PubMedBERT would strengthen the design rationale.

7. **Missing statistical rigor:** The paper does not specify confidence interval methods (bootstrap vs. DeLong), multiple comparison corrections, or minimum subgroup sizes for interpretation. For a JBHI submission, these are required.

8. **Missing supplementary materials and code repository:** No code repository is linked (only the GitHub repo for the pipeline). No supplementary material is provided. JBHI increasingly requires code availability statements.

9. **E3 is missing:** The experiment numbering jumps from E2 to E4, with no E3 described. This gap is unexplained and may confuse readers.

---

## Suggestions

1. **Conduct real-data experiments before submission to JBHI.** Download NHANES XPT files, Sleep-EDF Expanded, and OpenNeuro ds004902 as described in the 7-week roadmap and replace synthetic results with real ones. Without this, the paper should be retargeted to a methods/workshop venue.

2. **Resolve the channel mismatch** by either (a) modifying the architecture to use 2-channel input matching Sleep-EDF, (b) implementing spatial interpolation to synthesize 6-channel data from 2-channel recordings, or (c) using a different pre-training dataset with 6+ channels.

3. **Add an architecture figure** to Section 3.2 showing the data flow from raw EEG/survey inputs through each component to the cognitive decline output.

4. **Justify or ablate the PubMedBERT freezing decision** and discuss alternative LLM backbones (e.g., BioBERT, ClinicalBERT, or a general-purpose BERT fine-tuned on survey text).

5. **Add sensitivity analyses for the DSST threshold** (25th, 40th, 50th percentile) to assess robustness of pseudo-label generation.

6. **Explain the missing E3** or renumber experiments sequentially.

7. **Add a model architecture table** specifying all layer dimensions, parameter counts, activation functions, and regularization for both the Bi-LSTM and the projection MLP.

---

## Questions

1. Why was E3 omitted from the experimental sequence? What was the originally planned E3 experiment?

2. How is the 6-channel EEG requirement (Fz, Cz, Pz, F3, F4, Oz) reconciled with Sleep-EDF's 2-channel recordings (Fpz-Cz, Pz-Oz) in the pre-training stage? Does the model pre-train on 2 channels and fine-tune on 6, or is spatial interpolation applied?

3. What is the theoretical basis for expecting NT-Xent alignment to succeed between NHANES survey text embeddings and EEG temporal embeddings? Is there prior evidence of semantic correspondence between these modalities?

4. Why is PubMedBERT chosen over ClinicalBERT or a general-purpose BERT? NHANES surveys are closer to clinical questionnaires than biomedical literature text.

5. What is the expected label noise rate under the 40th-percentile DSST threshold, and how does this affect the minimum detectable effect size for H3?

---

## Rating: 3 / 10 — Reject (Major Revision Required)

**Primary reason for rejection:** The paper presents a methodologically sound framework design but provides no real-data validation. All four scientific hypotheses remain unvalidated. JBHI requires empirical evidence on real biomedical data for a full research article. The paper is not ready for submission to JBHI in its current form.

**Path to acceptance:** Real-data experiments replacing synthetic results, resolution of the channel mismatch, and expansion of the manuscript to full JBHI length (~7,000 words with proper tables and figures).

---

## Confidence: High

I am highly confident in this assessment based on direct inspection of the manuscript content, the explicit synthetic-data disclosure, and familiarity with JBHI's publication standards for full research articles.

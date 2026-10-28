# Reviewer 3 Report — Clarity, Positioning & Broader Impact Specialist

**Paper:** From Population Surveys to Neural Signals: A Hybrid LSTM–LLM Framework for Predicting EEG-Indexed Cognitive Decline from NHANES Sleep Behavioral Features  
**Target Venue:** IEEE Journal of Biomedical and Health Informatics (JBHI)  
**Reviewer Expertise:** Scientific writing, manuscript structure, literature positioning, broader impact, ethics, health equity, journal compliance

---

## Summary

The paper presents a hybrid deep-learning framework combining NHANES population sleep survey data with EEG neural biomarkers for cognitive decline prediction. The architecture integrates a Bi-LSTM EEG encoder, a frozen PubMedBERT survey text encoder, and an NT-Xent cross-modal contrastive bridge. The paper is explicitly transparent that all experimental results are from synthetic data generated for pipeline validation, with real-data validation deferred to a 7-week roadmap. Four pre-registered hypotheses are evaluated: H1 passes as a synthetic artifact (AUC=1.0), while H2, H3, and H4 all fail under synthetic conditions. The paper positions itself as a methodological contribution establishing the first integrated framework for NHANES-EEG-LLM cognitive decline prediction.

---

## Soundness: 2 / 5

While the paper's integrity practices (synthetic data disclosure, pre-registered hypotheses) are commendable, the absence of real-data results means the core scientific soundness cannot be assessed. The framework design is internally consistent, but its real-world applicability is entirely undemonstrated.

---

## Presentation: 3 / 5

**Positive aspects:**
- Clear section structure with numbered headings
- Consistent use of SYNTHETIC DATA warnings throughout
- Index terms are appropriate for JBHI
- References are properly formatted (IEEE style)

**Significant issues:**

*Length and completeness:*
- ~4,426 words is approximately half the expected length for a JBHI full article (typically 6,000–8,500 words). The manuscript is underdeveloped across multiple sections.
- Related Work (Section 2) covers four subsections but each is only 2–3 sentences. A JBHI paper should provide substantive engagement with at least 20–30 relevant works, not 10 references total.
- Discussion (Section 6) is largely a list of limitations and future work rather than a substantive scientific discussion.

*Formatting violations (JBHI/IEEE standards):*
- **Bullet lists in the body** (Sections 3.8, 6.4, 6.6): IEEE journals require flowing prose. This is a clear formatting violation (Failure Mode F21).
- **No tables in the manuscript body:** JBHI papers at this scope require at minimum a demographics table (Table 1), a results comparison table (Table 2), and an architecture specification table.
- **Figures in appendix only:** Figures should be embedded in the relevant sections (Results, Discussion), not relegated to an appendix.
- **Abstract length:** The abstract appears within JBHI's word limit, but the Results subsection of the abstract ("macro-F1=0.3608 and Cohen's κ=0.3847 [synthetic]") may mislead readers who do not read the full paper.

*Structural issues:*
- Section 3.8 (Evaluation Metrics and Hypotheses) uses bullet points to list hypotheses; these should be presented as a proper hypothesis registry table or integrated prose.
- The Appendix contains figures that belong in the main text.
- The "Acknowledgments" and "Data Availability" subsections are placed under Section 7 (Conclusion) rather than as standalone sections, which is non-standard for IEEE.

---

## Contribution: 2 / 5

**Positioning assessment:**
The paper's "first unified framework" claim (Introduction, Conclusion) is potentially defensible based on the literature search (no prior work combines LSTM EEG encoder + LLM survey encoder + NT-Xent + NHANES for cognitive decline), but it is stated too broadly. The claim must be qualified:
1. Adjacent work (BioSync, arXiv:2609.04504) uses a transformer-based cross-modal fusion for cognitive biomarkers — this should be cited and distinguished.
2. The "first" claim requires the adjacent-literature qualification: "To our knowledge, no prior work has integrated..."
3. Without real-data validation, the "first framework" claim is a design contribution, not a performance contribution.

**Related work gaps:**
- The paper cites only 10 references, which is sparse for a JBHI submission (typical: 30–50 references).
- Missing citations that should be included based on the literature search:
  - Hong et al. (2024, Mathematics): LSTM on sleep lifelog for cognitive impairment (AUC=0.92) — the closest LSTM-cognitive impairment precedent
  - Li et al. (2023, Front. Neurosci.): ML on NHANES for cognitive impairment (AUC≈0.776)
  - Ma et al. (2023, Front. Neurosci.): NHANES nomogram for cognitive impairment (AUC=0.744)
  - BioSync (Mohammadabadi, arXiv:2609.04504): Transformer cross-modal fusion for cognitive biomarkers
  - Liu et al. (2023, Sensors): Systematic review of contrastive SSL for medical time series
  - Weng et al. (2025, ACM Comp. Surv.): Systematic review of SSL for EEG
  - Chary et al. (2025, IEEE): NT-Xent cross-modal for physiological pain classification — closest NT-Xent EEG precedent
  - Chen et al. (2020, ICML): SimCLR — the foundational NT-Xent paper that should be cited

**Failure Mode F19 (adjacent literature):** The paper does not cite NHANES-based ML studies that used the same data source for cognitive outcomes (Li et al., Ma et al.). The "first" claim is not defensible without citing and distinguishing these adjacent uses of NHANES.

---

## Strengths

1. **Exemplary scientific integrity:** The paper's consistent and prominent disclosure of synthetic data is the strongest aspect of the manuscript. This level of transparency is rare and should be recognized. The authors clearly distinguish between pipeline validation and scientific validation throughout.

2. **Pre-registered hypotheses:** The explicit formulation of H1–H4 with numeric thresholds before running experiments is a best practice that strengthens the paper's credibility.

3. **Public data commitment:** All three datasets are publicly available, which supports reproducibility and open science principles.

4. **Validation roadmap:** The 7-week real-data validation roadmap (Section 6.4.7) is a constructive and actionable plan that demonstrates the authors' awareness of the gap between the current state and a publication-ready result.

5. **Ethical considerations:** Section 6.5 correctly identifies that no IRB approval is required for secondary analysis of de-identified public data and notes the CC0 license for OpenNeuro ds004902.

6. **Index terms:** The index terms (cognitive decline, EEG, NHANES, LSTM, large language models, contrastive learning, sleep deprivation, population health) are appropriate and comprehensive for JBHI indexing.

---

## Weaknesses

1. **Manuscript is incomplete for JBHI submission:** At ~4,426 words with no tables, figures in appendix only, and bullet lists in the body, this manuscript does not meet JBHI's formatting and length standards for a full research article. It reads more like a technical report or workshop paper than a journal submission.

2. **Related work is severely underdeveloped:** Ten references and four 2–3 sentence subsections do not constitute adequate literature positioning for JBHI. Key adjacent works are missing (see Contribution section above), and the gap statement is not fully supported by the cited literature.

3. **"First" claim unsupported by adjacent-literature check (Failure Mode F19):** The paper claims to present "the first unified framework" without citing NHANES-based ML studies for cognitive outcomes (Li et al., Ma et al., Sakal et al.). The claim is potentially defensible but requires these citations and explicit distinctions.

4. **Discussion section lacks scientific depth:** Section 6 is primarily a list of limitations (Section 6.4) and future directions (Section 6.6), with minimal substantive discussion of what the synthetic results mean for the field, why the architectural choices are expected to work on real data, or how the framework compares to alternatives beyond the brief Section 6.2.

5. **Broader impact and health equity not addressed:** The paper does not discuss potential biases in NHANES sampling (e.g., underrepresentation of certain racial/ethnic groups, socioeconomic strata), the risk of differential performance across demographic subgroups, or the ethical implications of cognitive decline prediction from behavioral surveys. NHANES oversamples certain minority populations; model performance may vary across these groups. This is a significant omission for a JBHI submission targeting clinical/population health applications (Failure Mode F18).

6. **No Funding statement:** The paper lacks a Funding section. JBHI requires a Funding or "no financial support" statement (Failure Mode F25). The Acknowledgments section does not substitute for a proper Funding statement.

7. **No Generative AI use statement:** The paper lacks a Generative AI use statement, which is now required by IEEE and many journals (Failure Mode F25). The pipeline was developed with AI assistance (as noted in the project context), and this must be disclosed.

8. **Abstract may mislead:** The abstract reports synthetic metrics (macro-F1=0.3608, AUC=1.0000) that could be misinterpreted by readers who do not read the full paper. The abstract should more prominently state that these are synthetic-data results, not real-world performance.

9. **Conflict of Interest statement placement:** The Conflict of Interest statement is placed as a subsection under Section 7 (Conclusion) rather than as a standalone statement, which is non-standard for IEEE JBHI.

10. **No methodology flowchart in the body:** The paper references a Stage 3 architecture diagram but does not embed it in the manuscript body. A methodology flowchart is required for clarity (Failure Mode F23).

---

## Suggestions

1. **Expand the Related Work section** to 30–40 references covering: NHANES-based cognitive ML studies (Li et al., Ma et al., Sakal et al.), LSTM for cognitive prediction (Hong et al.), EEG sleep staging deep learning (Almutairi et al., Samaee et al., Sidhu et al.), LLMs for health data (NHANES-GPT, ClinicalBERT), contrastive learning for biomedical signals (Liu et al., Weng et al., Chary et al.), and the foundational SimCLR paper (Chen et al., 2020).

2. **Add a health equity discussion** addressing NHANES sampling design, potential differential model performance across racial/ethnic and SES subgroups, and the ethical implications of cognitive decline prediction from behavioral surveys.

3. **Add Funding and Generative AI use statements** as required by IEEE JBHI.

4. **Convert bullet lists to prose** throughout the manuscript body.

5. **Move figures to relevant sections** (Figure 1 → Section 5; Figure 2 → Hypothesis Summary; Figure 4 → Section 6.4).

6. **Add a methodology flowchart** (architecture diagram) to Section 3.2.

7. **Qualify the "first" claim** with "To our knowledge" and cite the adjacent NHANES-ML literature.

8. **Expand the Discussion** to include: comparison with published baselines on real data (expected), architectural design rationale with literature support, implications for clinical deployment (if real-data results are obtained), and field significance.

---

## Questions

1. Has the framework been tested on any real data, even a small pilot subset? Even preliminary real-data results (e.g., Sleep-EDF pre-training on real EEG) would substantially strengthen the submission.

2. How does the paper plan to address NHANES complex survey design (strata, PSUs, survey weights) in the statistical analysis? Ignoring these can produce biased population estimates.

3. What is the intended clinical use case? Is the framework intended for screening, risk stratification, or research? The clinical utility framing affects which metrics and thresholds are appropriate.

4. Has any subgroup analysis been planned for NHANES racial/ethnic groups (Non-Hispanic White, Non-Hispanic Black, Hispanic, Asian) given the known disparities in both sleep health and cognitive decline risk?

5. Will the code be made publicly available? A GitHub repository is mentioned in the project context but not in the manuscript's Data Availability statement.

---

## Rating: 3 / 10 — Reject (Major Revision Required)

**Primary reasons:** (1) Manuscript is incomplete — too short, no tables, figures misplaced, bullet lists in body. (2) Related work underdeveloped with missing key citations. (3) No real-data results. (4) Missing Funding and Generative AI statements. (5) Health equity and broader impact not addressed.

**Path to acceptance:** Full manuscript expansion to JBHI length standards, real-data experiments, expanded related work with proper citation of adjacent NHANES-ML and contrastive-learning literature, health equity discussion, and compliance with all IEEE formatting requirements.

---

## Confidence: High

I am highly confident in this assessment based on direct inspection of the manuscript structure, content, and comparison with JBHI's published formatting guidelines and recent comparable papers.

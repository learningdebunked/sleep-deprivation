#!/usr/bin/env python3
"""
Stage 6: Publication-quality figures for experiment results.
All figures annotated with SYNTHETIC DATA watermark.
Output: results/stage6/fig*.png  (300 DPI, ≤ 3200×2400 px)
"""
import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap

OUT = "/home/sandbox/nhanes-eeg-cogdecline-lstm-llm/results/stage6"
os.makedirs(OUT, exist_ok=True)

# ── Palette (colorblind-safe) ──────────────────────────────────────────────────
C_PASS   = "#2ca02c"   # green
C_FAIL   = "#d62728"   # red
C_WARN   = "#ff7f0e"   # orange (artifact)
C_TARG   = "#1f77b4"   # blue  (target line)
C_BG     = "#f7f7f7"
DARK     = "#2c3e50"

# ── Shared watermark helper ────────────────────────────────────────────────────
def add_watermark(ax_or_fig):
    """Add SYNTHETIC DATA diagonal watermark."""
    if isinstance(ax_or_fig, plt.Figure):
        fig = ax_or_fig
        fig.text(0.5, 0.5, "SYNTHETIC DATA",
                 fontsize=38, color="gray", alpha=0.12,
                 ha="center", va="center", rotation=30,
                 fontweight="bold", transform=fig.transFigure)
    else:
        ax = ax_or_fig
        ax.text(0.5, 0.5, "SYNTHETIC DATA",
                fontsize=20, color="gray", alpha=0.15,
                ha="center", va="center", rotation=30,
                fontweight="bold", transform=ax.transAxes)


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 1  –  Experiment Metrics Overview (multi-panel bar chart)
# ═══════════════════════════════════════════════════════════════════════════════
fig1, axes = plt.subplots(2, 3, figsize=(13, 7.5), facecolor=C_BG)
fig1.suptitle(
    "Stage 5 Experiment Metrics Overview\n(LSTM–LLM | NHANES–EEG Cognitive Decline)",
    fontsize=13, fontweight="bold", color=DARK, y=0.98)

# Panel data: (title, metric_labels, values, thresholds, colors, units)
panels = [
    # E1
    ("E1 — Sleep-EDF Staging\n(5-class, GBM proxy)",
     ["Macro-F1", "Cohen's κ"],
     [0.3608, 0.3847],
     [None, None],
     ["#5b9bd5", "#5b9bd5"],
     "Score"),
    # E2
    ("E2 — OpenNeuro NS/SD\n(Binary, 5-fold CV)",
     ["AUC-ROC"],
     [1.0000],
     [0.85],
     [C_WARN],     # orange = artifact
     "AUC-ROC"),
    # E4
    ("E4 — Cross-Modal\nAlignment (H2)",
     ["Pearson r"],
     [0.3086],
     [0.40],
     [C_FAIL],
     "Pearson r"),
    # E5
    ("E5 — NHANES Pseudo-\nLabel Transfer (H3)",
     ["AUC-ROC"],
     [0.5144],
     [0.72],
     [C_FAIL],
     "AUC-ROC"),
    # E6a
    ("E6a — Ridge Regression\n(DSST R², H4)",
     ["CV R²"],
     [-9.5244],
     [0.10],
     [C_FAIL],
     "R²"),
    # E6b
    ("E6b — GBM Classifier\n(DSST AUC, H4)",
     ["AUC-ROC"],
     [0.4842],
     [0.65],
     [C_FAIL],
     "AUC-ROC"),
]

for ax, (title, labels, values, thresholds, colors, unit) in zip(axes.flat, panels):
    ax.set_facecolor("white")
    x = np.arange(len(labels))
    bars = ax.bar(x, values, color=colors, width=0.5, edgecolor="white", linewidth=0.8,
                  zorder=3)
    # Draw threshold line(s)
    for i, (thr, val) in enumerate(zip(thresholds, values)):
        if thr is not None:
            ax.axhline(thr, color=C_TARG, linewidth=1.8, linestyle="--",
                       label=f"Target: {thr}", zorder=4)
            ax.text(len(labels) - 0.05, thr + 0.03 * abs(thr if thr != 0 else 0.5),
                    f"target={thr}", color=C_TARG, fontsize=7.5, ha="right")
    # Value labels on bars
    for bar, val in zip(bars, values):
        ypos = bar.get_height()
        va = "bottom" if ypos >= 0 else "top"
        offset = 0.015 if ypos >= 0 else -0.015
        ax.text(bar.get_x() + bar.get_width()/2,
                ypos + offset, f"{val:.4f}",
                ha="center", va=va, fontsize=8.5, fontweight="bold", color=DARK)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel(unit, fontsize=9)
    ax.set_title(title, fontsize=9.5, fontweight="bold", color=DARK, pad=6)
    ax.grid(axis="y", alpha=0.35, linewidth=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    # Special: E6a R² goes very negative — clamp y-axis for readability
    if "R²" in unit:
        ax.set_ylim(-1.5, 0.5)
        ax.text(0.5, 0.6, f"Actual: {values[0]:.2f}", transform=ax.transAxes,
                ha="center", fontsize=8.5, color=C_FAIL, fontweight="bold")
    else:
        ax.set_ylim(0, 1.12)
    add_watermark(ax)

add_watermark(fig1)
plt.tight_layout(rect=[0, 0, 1, 0.95])
fig1.savefig(f"{OUT}/fig1_experiment_metrics.png", dpi=300, bbox_inches="tight",
             facecolor=C_BG)
plt.close(fig1)
print("Saved fig1_experiment_metrics.png")


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 2  –  Hypothesis Verdict Matrix (traffic-light heatmap)
# ═══════════════════════════════════════════════════════════════════════════════
fig2, ax2 = plt.subplots(figsize=(9, 4.5), facecolor=C_BG)
ax2.set_facecolor("white")
ax2.set_title(
    "Hypothesis Verdict Matrix — Stage 5 (Synthetic Data)",
    fontsize=12, fontweight="bold", color=DARK, pad=10)

hyps   = ["H1\n(E2 AUC≥0.85)", "H2\n(E4 r>0.40)", "H3\n(E5 AUC≥0.72)",
          "H4a\n(E6 R²>0.10)", "H4b\n(E6 AUC>0.65)"]
dims   = ["Achieved\nValue", "Target\nThreshold", "Verdict", "Data\nQuality"]

# Values for colour map
# Columns: achieved (normalized 0-1), target (norm), verdict (1=PASS,0=FAIL), quality (1=real,0=synthetic)
achieved = [1.0000, 0.3086, 0.5144, -9.5244, 0.4842]  # raw
targets  = [0.85,   0.40,   0.72,    0.10,    0.65]
verdicts = [1,      0,      0,       0,       0]      # 1=PASS(artifact), 0=FAIL
quality  = [0,      0,      0,       0,       0]      # all synthetic

# We'll draw coloured rectangles manually
cell_colors = []
cell_text   = []

for i, (h, av, tg, vd, qq) in enumerate(
        zip(hyps, achieved, targets, verdicts, quality)):
    row_colors = []
    row_text   = []
    # col 0: achieved value
    if vd == 1:
        row_colors.append(C_WARN)   # orange = suspicious pass
        row_text.append(f"{av:.4f}\n(artifact)" if av == 1.0 else f"{av:.4f}")
    elif av < 0:
        row_colors.append(C_FAIL)
        row_text.append(f"{av:.2f}")
    else:
        norm = max(0, min(1, av / tg)) if tg != 0 else 0
        r = int(215 + (1-norm)*40)
        g = int(48 + norm*160)
        b = int(39 + (1-norm)*10)
        row_colors.append(C_FAIL)
        row_text.append(f"{av:.4f}")
    # col 1: target threshold
    row_colors.append("#5b9bd5")
    row_text.append(f"{'≥' if tg > 0 else '>'}{tg}")
    # col 2: verdict
    row_colors.append(C_WARN if (vd==1 and av==1.0) else (C_PASS if vd==1 else C_FAIL))
    row_text.append("PASS*" if (vd==1 and av==1.0) else ("PASS" if vd==1 else "FAIL"))
    # col 3: data quality
    row_colors.append("#e8a838")
    row_text.append("Synthetic")
    cell_colors.append(row_colors)
    cell_text.append(row_text)

ax2.set_xlim(0, len(dims))
ax2.set_ylim(0, len(hyps))
ax2.set_xticks(np.arange(len(dims)) + 0.5)
ax2.set_xticklabels(dims, fontsize=10, fontweight="bold")
ax2.set_yticks(np.arange(len(hyps)) + 0.5)
ax2.set_yticklabels(reversed(hyps), fontsize=10)
ax2.tick_params(length=0)
ax2.spines[:].set_visible(False)

for row_i, (row_c, row_t) in enumerate(zip(cell_colors, cell_text)):
    y = len(hyps) - 1 - row_i
    for col_j, (c, t) in enumerate(zip(row_c, row_t)):
        rect = mpatches.FancyBboxPatch(
            (col_j + 0.04, y + 0.08), 0.92, 0.84,
            boxstyle="round,pad=0.02", linewidth=0,
            facecolor=c, alpha=0.88)
        ax2.add_patch(rect)
        ax2.text(col_j + 0.5, y + 0.5, t,
                 ha="center", va="center", fontsize=9.5,
                 fontweight="bold", color="white")

# Legend note
ax2.text(0, -0.6,
         "* H1 PASS is a synthetic-data artifact (perfectly separated class distributions). "
         "All verdicts provisional — real NHANES/EEG data required.",
         fontsize=8, color="#555", style="italic",
         transform=ax2.transData, va="top")

add_watermark(ax2)
plt.tight_layout()
fig2.savefig(f"{OUT}/fig2_hypothesis_verdict.png", dpi=300, bbox_inches="tight",
             facecolor=C_BG)
plt.close(fig2)
print("Saved fig2_hypothesis_verdict.png")


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 3  –  Achieved vs. Target (lollipop chart for H1-H4)
# ═══════════════════════════════════════════════════════════════════════════════
fig3, ax3 = plt.subplots(figsize=(9, 5.5), facecolor=C_BG)
ax3.set_facecolor("white")
ax3.set_title(
    "Achieved Metrics vs. Locked Thresholds (H1–H4)\n(Synthetic-data run — real-data gap visible)",
    fontsize=11, fontweight="bold", color=DARK, pad=10)

lollipop_labels = ["H1: E2 AUC\n(ArtifACT)", "H2: E4 Pearson r", "H3: E5 AUC",
                   "H4a: E6 R²\n(clamped at 0)", "H4b: E6 AUC"]
lollipop_achieved = [1.000,  0.3086, 0.5144, 0.0,    0.4842]   # R² clamped for plot
lollipop_targets  = [0.85,   0.40,   0.72,   0.10,   0.65]
lollipop_verdicts = ["PASS*","FAIL",  "FAIL", "FAIL", "FAIL"]
lollipop_colors   = [C_WARN, C_FAIL, C_FAIL, C_FAIL, C_FAIL]

y_pos = np.arange(len(lollipop_labels))[::-1]

for yp, lbl, av, tg, vd, col in zip(
        y_pos, lollipop_labels,
        lollipop_achieved, lollipop_targets,
        lollipop_verdicts, lollipop_colors):
    # target marker (blue diamond)
    ax3.plot(tg, yp, marker="D", markersize=10, color=C_TARG, zorder=5)
    # achieved marker
    ax3.plot(av, yp, marker="o", markersize=12, color=col, zorder=5)
    # connecting line
    x_start, x_end = (min(av, tg), max(av, tg))
    ax3.plot([x_start, x_end], [yp, yp], color="#aaa", linewidth=1.8, zorder=3)
    # gap shading
    ax3.fill_betweenx([yp-0.18, yp+0.18], x_start, x_end,
                      color=C_FAIL if vd != "PASS*" else C_WARN, alpha=0.12)
    # value labels
    ax3.text(av + 0.015, yp + 0.22, f"{av:.3f}", color=col,
             fontsize=9, fontweight="bold", va="bottom")
    ax3.text(tg + 0.015, yp - 0.28, f"target={tg}", color=C_TARG,
             fontsize=8.5, va="top")
    # verdict badge
    badge_color = C_WARN if vd == "PASS*" else C_FAIL
    ax3.text(1.03, yp, vd, color="white", fontsize=9, fontweight="bold",
             ha="left", va="center",
             bbox=dict(facecolor=badge_color, edgecolor="none",
                       boxstyle="round,pad=0.3", alpha=0.9))

ax3.set_yticks(y_pos)
ax3.set_yticklabels(lollipop_labels, fontsize=10)
ax3.set_xlabel("Metric Value", fontsize=10)
ax3.set_xlim(-0.05, 1.22)
ax3.set_ylim(-0.7, len(lollipop_labels) - 0.3)
ax3.axvline(0, color="#ccc", linewidth=0.8, linestyle=":")
ax3.grid(axis="x", alpha=0.3, linewidth=0.7)
ax3.spines[["top", "right"]].set_visible(False)

# Legend
legend_elements = [
    mpatches.Patch(facecolor=C_WARN, label="PASS (artifact)"),
    mpatches.Patch(facecolor=C_FAIL, label="FAIL"),
    plt.Line2D([0],[0], marker="D", color="w", markerfacecolor=C_TARG,
               markersize=9, label="Target threshold"),
    plt.Line2D([0],[0], marker="o", color="w", markerfacecolor=C_WARN,
               markersize=9, label="Achieved (synthetic)"),
]
ax3.legend(handles=legend_elements, loc="lower right", fontsize=8.5,
           framealpha=0.9)

ax3.text(0.5, -0.62,
         "Note: E6 Ridge R² = −9.52 is clamped to 0 for plot visibility. "
         "H1 AUC=1.0 is a class-separation artifact in synthetic data.",
         ha="center", va="top", fontsize=8, color="#555", style="italic",
         transform=ax3.transAxes)

add_watermark(ax3)
plt.tight_layout()
fig3.savefig(f"{OUT}/fig3_achieved_vs_target.png", dpi=300, bbox_inches="tight",
             facecolor=C_BG)
plt.close(fig3)
print("Saved fig3_achieved_vs_target.png")


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 4  –  Real-Data Validation Roadmap (Gantt-style)
# ═══════════════════════════════════════════════════════════════════════════════
fig4, ax4 = plt.subplots(figsize=(11, 5), facecolor=C_BG)
ax4.set_facecolor("white")
ax4.set_title(
    "Real-Data Validation Roadmap\n(Steps Required to Replace Synthetic Data)",
    fontsize=11, fontweight="bold", color=DARK, pad=10)

roadmap = [
    # (label, start_wk, dur_wk, color, datasets)
    ("Download NHANES XPT files\n(SLQ_H, CFQ_H, DEMO_H…)",    0, 1, "#5b9bd5",
     "Enables: E5, E6 (H3, H4)"),
    ("Download Sleep-EDF cassette EEG\n(Physionet)",           0, 2, "#5b9bd5",
     "Enables: E1"),
    ("Download OpenNeuro ds004902\n(Resting-state EEG)",        0, 2, "#5b9bd5",
     "Enables: E2 (H1)"),
    ("NHANES preprocessing\n(merge, QC, pseudo-label)",         1, 2, "#70ad47",
     "Feeds: E5, E6"),
    ("EEG preprocessing\n(filter, epoch, feature extract)",    2, 3, "#70ad47",
     "Feeds: E1, E2, E4"),
    ("Re-run E1: Sleep-EDF staging",                            4, 1, "#ff7f0e",
     "Updates: Table 3, Fig 1 Panel A"),
    ("Re-run E2: OpenNeuro NS/SD (H1)",                         4, 1, "#ff7f0e",
     "Updates: H1 verdict"),
    ("Re-run E4/E5: Cross-modal + NHANES",                      5, 1, "#ff7f0e",
     "Updates: H2, H3 verdicts"),
    ("Re-run E6: Traditional baselines (H4)",                   5, 1, "#ff7f0e",
     "Updates: H4 verdict"),
    ("Revise manuscript with real results",                      6, 1, "#c00000",
     "Manuscript Sections 4-5"),
]

y_ticks = []
y_labels = []
for i, (lbl, start, dur, col, note) in enumerate(roadmap):
    y = len(roadmap) - 1 - i
    ax4.barh(y, dur, left=start, height=0.55,
             color=col, edgecolor="white", linewidth=0.7, alpha=0.88)
    ax4.text(start + dur + 0.08, y, note,
             va="center", fontsize=7.5, color="#555", style="italic")
    y_ticks.append(y)
    y_labels.append(lbl)

ax4.set_yticks(y_ticks)
ax4.set_yticklabels(y_labels, fontsize=8.5)
ax4.set_xlabel("Weeks from start", fontsize=10)
ax4.set_xlim(0, 12)
ax4.set_xticks(range(8))
ax4.grid(axis="x", alpha=0.3, linewidth=0.7)
ax4.spines[["top", "right"]].set_visible(False)

legend_patches = [
    mpatches.Patch(facecolor="#5b9bd5", label="Data acquisition"),
    mpatches.Patch(facecolor="#70ad47", label="Preprocessing"),
    mpatches.Patch(facecolor="#ff7f0e", label="Experiment re-run"),
    mpatches.Patch(facecolor="#c00000", label="Manuscript revision"),
]
ax4.legend(handles=legend_patches, loc="lower right", fontsize=8.5,
           framealpha=0.9)

add_watermark(ax4)
plt.tight_layout()
fig4.savefig(f"{OUT}/fig4_validation_roadmap.png", dpi=300, bbox_inches="tight",
             facecolor=C_BG)
plt.close(fig4)
print("Saved fig4_validation_roadmap.png")

# ── Summary sizes ──────────────────────────────────────────────────────────────
for fn in ["fig1_experiment_metrics.png", "fig2_hypothesis_verdict.png",
           "fig3_achieved_vs_target.png", "fig4_validation_roadmap.png"]:
    path = f"{OUT}/{fn}"
    kb = os.path.getsize(path) // 1024
    print(f"  {fn}: {kb} KB")

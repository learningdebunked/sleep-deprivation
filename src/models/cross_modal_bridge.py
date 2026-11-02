#!/usr/bin/env python3
"""
Module 3 — Cross-Modal Alignment Bridge (Stage 3 spec).

Architecture (locked):
  Input: LLM behavioral embedding (128-dim) + EEG cognitive embedding (128-dim)
  Loss:  NT-Xent contrastive loss (InfoNCE), temperature τ = 0.07
  Classification head: Linear(128→64) → ReLU → Dropout(0.3) → Linear(64→1) → Sigmoid
  Output: P(cognitive decline risk) ∈ [0, 1]

The bridge aligns the two 128-dim embedding spaces via contrastive learning.
After alignment the head classifies NHANES-only embeddings against DSST pseudo-labels.

Positive pairs: same sleep condition (both NS or both SD)
Negative pairs: opposite conditions
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


EMBED_DIM = 128
HEAD_MID = 64
HEAD_DROPOUT = 0.3
NT_XENT_TEMPERATURE = 0.07


class NTXentLoss(nn.Module):
    """Normalized Temperature-scaled Cross Entropy (NT-Xent / InfoNCE) loss.

    Expects two batches of L2-normalized embeddings: z_a and z_b.
    Positive pairs: (z_a[i], z_b[i]) for i in [0, N).
    Negative pairs: all other cross-batch combinations.

    Reference: Chen et al. 2020 (SimCLR), Oord et al. 2019 (CPC/InfoNCE).
    """

    def __init__(self, temperature: float = NT_XENT_TEMPERATURE):
        super().__init__()
        self.temperature = temperature

    def forward(self, z_a: torch.Tensor, z_b: torch.Tensor) -> torch.Tensor:
        """
        Args:
            z_a: (N, D) L2-normalized embeddings from source A (e.g., LLM)
            z_b: (N, D) L2-normalized embeddings from source B (e.g., EEG)

        Returns:
            loss: scalar NT-Xent loss averaged over all N samples
        """
        N = z_a.size(0)
        assert z_b.size(0) == N, "z_a and z_b must have the same batch size"

        # Concatenate: (2N, D)
        z = torch.cat([z_a, z_b], dim=0)

        # Similarity matrix: (2N, 2N)
        sim = F.cosine_similarity(z.unsqueeze(1), z.unsqueeze(0), dim=2) / self.temperature

        # Mask self-similarity
        mask = torch.eye(2 * N, dtype=torch.bool, device=z.device)
        sim = sim.masked_fill(mask, float("-inf"))

        # Labels: positive pair for z_a[i] is z_b[i] (at index i+N in z), and vice versa
        labels = torch.cat([
            torch.arange(N, 2 * N, device=z.device),
            torch.arange(0, N, device=z.device),
        ])  # (2N,)

        loss = F.cross_entropy(sim, labels)
        return loss


class CognitiveDeclinesHead(nn.Module):
    """Binary classification head: 128-dim embed → P(cognitive decline risk).

    Architecture: FC(128→64) → ReLU → Dropout(0.3) → FC(64→1) → Sigmoid
    """

    def __init__(
        self,
        input_dim: int = EMBED_DIM,
        mid_dim: int = HEAD_MID,
        dropout: float = HEAD_DROPOUT,
    ):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, mid_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(mid_dim, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch, 128) L2-normalized embedding

        Returns:
            prob: (batch, 1) P(cognitive decline risk)
        """
        return self.net(x)


class CrossModalBridge(nn.Module):
    """Cross-modal alignment bridge: aligns LLM ↔ EEG embeddings + classification.

    Usage:
        bridge = CrossModalBridge()

        # Contrastive training (Stage 3 training step)
        loss_contrastive = bridge.contrastive_loss(llm_embeds, eeg_embeds)

        # Classification (NHANES inference)
        prob = bridge.classify(llm_embeds)
    """

    def __init__(
        self,
        embed_dim: int = EMBED_DIM,
        temperature: float = NT_XENT_TEMPERATURE,
        head_mid: int = HEAD_MID,
        head_dropout: float = HEAD_DROPOUT,
    ):
        super().__init__()
        self.embed_dim = embed_dim

        # NT-Xent contrastive loss
        self.nt_xent = NTXentLoss(temperature=temperature)

        # Classification head
        self.head = CognitiveDeclinesHead(embed_dim, head_mid, head_dropout)

    def contrastive_loss(
        self,
        llm_embeds: torch.Tensor,
        eeg_embeds: torch.Tensor,
    ) -> torch.Tensor:
        """Compute NT-Xent loss between LLM and EEG embeddings.

        Embeddings should already be L2-normalized (LLMSurveyEncoder ensures this;
        EEG embeds are passed through F.normalize before calling this).

        Args:
            llm_embeds: (N, 128) L2-normalized behavioral embeddings
            eeg_embeds: (N, 128) L2-normalized cognitive state embeddings

        Returns:
            scalar NT-Xent loss
        """
        # Ensure unit sphere
        z_llm = F.normalize(llm_embeds, p=2, dim=-1)
        z_eeg = F.normalize(eeg_embeds, p=2, dim=-1)
        return self.nt_xent(z_llm, z_eeg)

    def classify(self, llm_embeds: torch.Tensor) -> torch.Tensor:
        """Predict cognitive decline risk from NHANES behavioral embeddings.

        Args:
            llm_embeds: (batch, 128) L2-normalized behavioral embeddings

        Returns:
            prob: (batch, 1) P(cognitive decline risk)
        """
        z = F.normalize(llm_embeds, p=2, dim=-1)
        return self.head(z)

    def forward(
        self,
        llm_embeds: torch.Tensor,
        eeg_embeds: torch.Tensor | None = None,
        labels: torch.Tensor | None = None,
        alpha_contrastive: float = 0.5,
    ) -> dict:
        """Combined forward pass for Stage 3 bridge training.

        Args:
            llm_embeds:        (batch, 128) LLM behavioral embeddings
            eeg_embeds:        (batch, 128) EEG cognitive embeddings (optional)
            labels:            (batch, 1) binary pseudo-labels (optional)
            alpha_contrastive: weight for contrastive loss vs. BCE loss

        Returns:
            dict with keys: loss, loss_contrastive, loss_bce, prob
        """
        prob = self.classify(llm_embeds)
        result = {"prob": prob}

        loss_bce = torch.tensor(0.0, device=llm_embeds.device)
        loss_contrastive = torch.tensor(0.0, device=llm_embeds.device)

        if labels is not None:
            loss_bce = F.binary_cross_entropy(prob, labels.float())
            result["loss_bce"] = loss_bce

        if eeg_embeds is not None:
            loss_contrastive = self.contrastive_loss(llm_embeds, eeg_embeds)
            result["loss_contrastive"] = loss_contrastive

        total_loss = alpha_contrastive * loss_contrastive + (1 - alpha_contrastive) * loss_bce
        result["loss"] = total_loss
        return result

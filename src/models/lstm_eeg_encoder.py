#!/usr/bin/env python3
"""
Module 2 — Bi-LSTM Temporal EEG Encoder (Stage 3 spec).

Architecture (locked):
  Input:  (batch, T, 34) — T variable-length epoch sequences, 34 features each
  Layer 1: Bidirectional LSTM, 128 units × 2 dirs → (batch, T, 256), dropout 0.3
  Layer 2: Bidirectional LSTM,  64 units × 2 dirs → (batch, T, 128), dropout 0.3
  Attention pooling: learned scalar weights over T → (batch, 128)
  Classification head: Linear(128→1) + Sigmoid → P(Sleep Deprived)

Two output modes:
  - encode(x, lengths):  returns 128-dim cognitive state embedding
  - forward(x, lengths): returns (embedding, probability) tuple

Pre-training (Stage 1):  add 5-class staging head → swap back for Stage 2/3
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence


class TemporalAttentionPool(nn.Module):
    """Learnable attention pooling over the time dimension.

    Computes a weighted mean of T hidden states, where weights are
    softmax-normalized scalar scores produced by a single linear layer.
    """

    def __init__(self, hidden_dim: int):
        super().__init__()
        self.score = nn.Linear(hidden_dim, 1, bias=True)

    def forward(self, hidden: torch.Tensor, mask: torch.Tensor | None = None) -> torch.Tensor:
        """
        Args:
            hidden: (batch, T, hidden_dim)
            mask:   (batch, T) bool — True for valid positions, False for padding

        Returns:
            pooled: (batch, hidden_dim)
        """
        scores = self.score(hidden).squeeze(-1)        # (batch, T)
        if mask is not None:
            scores = scores.masked_fill(~mask, float("-inf"))
        weights = F.softmax(scores, dim=1).unsqueeze(2)  # (batch, T, 1)
        pooled = (hidden * weights).sum(dim=1)            # (batch, hidden_dim)
        return pooled


class BiLSTMEEGEncoder(nn.Module):
    """Bidirectional LSTM encoder for EEG epoch sequences.

    Input feature dimension: 34 (30 band-power + 4 connectivity).
    Output embedding dimension: 128.
    """

    INPUT_DIM = 34
    HIDDEN_DIM_1 = 128   # units per direction, layer 1
    HIDDEN_DIM_2 = 64    # units per direction, layer 2
    EMBED_DIM = 128      # output embedding (64 × 2 dirs)
    DROPOUT = 0.3

    def __init__(
        self,
        input_dim: int = INPUT_DIM,
        hidden_dim_1: int = HIDDEN_DIM_1,
        hidden_dim_2: int = HIDDEN_DIM_2,
        dropout: float = DROPOUT,
        n_staging_classes: int = 5,
    ):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim_1 = hidden_dim_1
        self.hidden_dim_2 = hidden_dim_2
        self.embed_dim = hidden_dim_2 * 2  # 128

        # Layer 1: Bi-LSTM
        self.lstm1 = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim_1,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
            dropout=0.0,  # dropout between layers via nn.Dropout below
        )
        self.drop1 = nn.Dropout(dropout)

        # Layer 2: Bi-LSTM
        self.lstm2 = nn.LSTM(
            input_size=hidden_dim_1 * 2,
            hidden_size=hidden_dim_2,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
            dropout=0.0,
        )
        self.drop2 = nn.Dropout(dropout)

        # Attention pooling
        self.attention = TemporalAttentionPool(self.embed_dim)

        # ── Classification heads ──────────────────────────────────────────────
        # Stage 1 pre-training: 5-class sleep staging
        self.staging_head = nn.Linear(self.embed_dim, n_staging_classes)

        # Stage 2 fine-tuning: binary SD classification
        self.binary_head = nn.Sequential(
            nn.Linear(self.embed_dim, 1),
            nn.Sigmoid(),
        )

        # Current mode: "staging" | "binary" | "embed_only"
        self.mode = "staging"

    def encode(
        self,
        x: torch.Tensor,
        lengths: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Encode a batch of EEG sequences to 128-dim embeddings.

        Args:
            x:       (batch, T, 34) — padded epoch sequences
            lengths: (batch,) int64 — actual sequence lengths (for packing)

        Returns:
            embed: (batch, 128) — cognitive state embedding
        """
        # Pack for efficiency if lengths provided
        if lengths is not None:
            packed = pack_padded_sequence(
                x, lengths.cpu(), batch_first=True, enforce_sorted=False
            )
            packed_out1, _ = self.lstm1(packed)
            out1, _ = pad_packed_sequence(packed_out1, batch_first=True)
        else:
            out1, _ = self.lstm1(x)

        out1 = self.drop1(out1)         # (batch, T, 256)

        if lengths is not None:
            packed2 = pack_padded_sequence(
                out1, lengths.cpu(), batch_first=True, enforce_sorted=False
            )
            packed_out2, _ = self.lstm2(packed2)
            out2, _ = pad_packed_sequence(packed_out2, batch_first=True)
        else:
            out2, _ = self.lstm2(out1)

        out2 = self.drop2(out2)         # (batch, T, 128)

        # Build padding mask for attention
        if lengths is not None:
            max_len = out2.size(1)
            mask = torch.arange(max_len, device=x.device).unsqueeze(0) < lengths.unsqueeze(1)
        else:
            mask = None

        embed = self.attention(out2, mask)   # (batch, 128)
        return embed

    def forward(
        self,
        x: torch.Tensor,
        lengths: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Forward pass.

        Returns:
            (embed, logits_or_prob) where:
              - embed:          (batch, 128)
              - logits_or_prob: staging logits (batch, 5) or binary prob (batch, 1)
        """
        embed = self.encode(x, lengths)

        if self.mode == "staging":
            out = self.staging_head(embed)   # (batch, 5) logits
        elif self.mode == "binary":
            out = self.binary_head(embed)    # (batch, 1) probability
        else:
            out = embed                      # embed_only mode

        return embed, out

    def set_mode(self, mode: str) -> None:
        """Switch between 'staging', 'binary', 'embed_only' modes."""
        assert mode in ("staging", "binary", "embed_only"), \
            f"mode must be 'staging', 'binary', or 'embed_only', got '{mode}'"
        self.mode = mode

    def freeze_lstm(self) -> None:
        """Freeze LSTM layers and attention (keep heads trainable)."""
        for param in self.lstm1.parameters():
            param.requires_grad = False
        for param in self.lstm2.parameters():
            param.requires_grad = False
        for param in self.attention.parameters():
            param.requires_grad = False

    def unfreeze_all(self) -> None:
        """Unfreeze all parameters."""
        for param in self.parameters():
            param.requires_grad = True

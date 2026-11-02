#!/usr/bin/env python3
"""
Module 1 — LLM Behavioral Survey Encoder (Stage 3 spec).

Architecture (locked):
  Input:  Tokenized NHANES text template (from nhanes_features.py)
  Backbone: PubMedBERT (microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext) — FROZEN
  [CLS] token: 768-dim
  Projection MLP:
    Linear(768 → 256) → ReLU → Dropout(0.2) → Linear(256 → 128) → L2-normalize
  Output: 128-dim unit-sphere behavioral embedding

The backbone is always frozen. Only the projection MLP is trained.
Fallback backbone: dmis-lab/biobert-v1.1

Usage:
    from src.models.llm_survey_encoder import LLMSurveyEncoder
    encoder = LLMSurveyEncoder()
    embed = encoder(input_ids, attention_mask)   # (batch, 128)
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


PRIMARY_MODEL = "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext"
FALLBACK_MODEL = "dmis-lab/biobert-v1.1"
BERT_DIM = 768
PROJ_MID = 256
EMBED_DIM = 128
PROJ_DROPOUT = 0.2


class ProjectionMLP(nn.Module):
    """Two-layer projection head: 768 → 256 → 128, L2-normalized output."""

    def __init__(
        self,
        input_dim: int = BERT_DIM,
        mid_dim: int = PROJ_MID,
        output_dim: int = EMBED_DIM,
        dropout: float = PROJ_DROPOUT,
    ):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, mid_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(mid_dim, output_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch, 768) [CLS] token embeddings

        Returns:
            (batch, 128) L2-normalized embeddings
        """
        projected = self.net(x)
        return F.normalize(projected, p=2, dim=-1)


class LLMSurveyEncoder(nn.Module):
    """NHANES survey text → 128-dim behavioral embedding.

    The BERT backbone is loaded from HuggingFace and immediately frozen.
    Only the ProjectionMLP is trained.
    """

    def __init__(
        self,
        model_name: str = PRIMARY_MODEL,
        embed_dim: int = EMBED_DIM,
        proj_dropout: float = PROJ_DROPOUT,
    ):
        super().__init__()
        self.model_name = model_name

        # Lazy import to avoid hard dependency at module load time
        from transformers import AutoModel
        try:
            self.bert = AutoModel.from_pretrained(model_name)
            print(f"[LLMSurveyEncoder] Loaded backbone: {model_name}")
        except Exception as e:
            print(f"[LLMSurveyEncoder] Primary model failed ({e}), trying fallback: {FALLBACK_MODEL}")
            self.bert = AutoModel.from_pretrained(FALLBACK_MODEL)
            self.model_name = FALLBACK_MODEL

        # Freeze backbone — this is ALWAYS frozen (Stage 3 spec)
        for param in self.bert.parameters():
            param.requires_grad = False

        self.projection = ProjectionMLP(
            input_dim=BERT_DIM,
            mid_dim=PROJ_MID,
            output_dim=embed_dim,
            dropout=proj_dropout,
        )

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        token_type_ids: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Encode tokenized NHANES text to 128-dim embedding.

        Args:
            input_ids:      (batch, seq_len) token IDs
            attention_mask: (batch, seq_len) 1 for real tokens, 0 for padding
            token_type_ids: optional (batch, seq_len)

        Returns:
            embed: (batch, 128) L2-normalized behavioral embedding
        """
        with torch.no_grad():  # Backbone always frozen
            outputs = self.bert(
                input_ids=input_ids,
                attention_mask=attention_mask,
                token_type_ids=token_type_ids,
            )
            cls_embedding = outputs.last_hidden_state[:, 0, :]  # (batch, 768) [CLS] token

        embed = self.projection(cls_embedding)   # (batch, 128)
        return embed

    def trainable_parameters(self):
        """Iterator over trainable parameters (projection MLP only)."""
        return self.projection.parameters()

    @staticmethod
    def get_tokenizer(model_name: str = PRIMARY_MODEL):
        """Convenience method to load the matching tokenizer."""
        from transformers import AutoTokenizer
        return AutoTokenizer.from_pretrained(model_name)

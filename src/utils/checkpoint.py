"""
checkpoint.py — Save and load model checkpoints.
"""

from __future__ import annotations
import torch
from pathlib import Path


def save_checkpoint(state: dict, path: str) -> None:
    """
    Save a checkpoint dictionary to `path`.
    Creates parent directories if needed.

    Args:
        state:  dict with model state_dicts and any metadata.
        path:   destination .pt file path.
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    torch.save(state, path)


def load_checkpoint(model: torch.nn.Module, path: str,
                    device: torch.device | str = "cpu") -> dict:
    """
    Load a single model from a checkpoint.

    If `path` contains a raw state_dict (OrderedDict), loads it directly.
    If `path` is a wrapper dict, looks for the key matching `type(model).__name__.lower()`
    or falls back to trying the first value that is an OrderedDict.

    Returns the full checkpoint dict for any additional metadata.
    """
    ckpt = torch.load(path, map_location=device)

    if isinstance(ckpt, dict):
        # Try direct state_dict load
        try:
            model.load_state_dict(ckpt, strict=False)
            return ckpt
        except Exception:
            pass

        # Try keyed lookup (e.g. {"eeg_enc": <sd>, "bridge": <sd>})
        key = type(model).__name__.lower()
        for k, v in ckpt.items():
            if key in k.lower() and hasattr(v, "keys"):
                model.load_state_dict(v, strict=False)
                return ckpt

        # Last resort: first OrderedDict value
        for v in ckpt.values():
            if hasattr(v, "keys"):
                model.load_state_dict(v, strict=False)
                return ckpt

    raise ValueError(f"Could not load model from checkpoint: {path}")


def load_full_checkpoint(path: str, device: torch.device | str = "cpu") -> dict:
    """Return the raw checkpoint dict without loading into any model."""
    return torch.load(path, map_location=device)

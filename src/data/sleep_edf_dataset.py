#!/usr/bin/env python3
"""
Sleep-EDF Expanded Dataset Loader — Stage 1 pre-training.

Expects Sleep-EDF Expanded data downloaded from PhysioNet:
  https://physionet.org/content/sleep-edfx/1.0.0/

File structure expected:
  data/sleep_edf/
    SC4001E0-PSG.edf   (Cassette subjects)
    SC4001E0-Hypnogram.edf
    ST7011J0-PSG.edf   (Telemetry subjects)
    ...

Labels (5 classes):
  0=Wake, 1=N1, 2=N2, 3=N3/N4 (merged), 4=REM

Features: 34-dim EEG feature vector per 30-second epoch.
  Note: Sleep-EDF uses 30-sec epochs; OpenNeuro uses 2-sec. Feature extraction
  is adapted accordingly (same bands, same channels where available).

Usage:
    dataset = SleepEDFDataset(data_dir="data/sleep_edf/", split="train")
    loader = DataLoader(dataset, batch_size=64, shuffle=True)
"""
from __future__ import annotations

import os
import glob
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

# Sleep stage label map (AASM / Sleep-EDF annotation codes)
SLEEP_STAGE_MAP = {
    "Sleep stage W":   0,
    "Sleep stage 1":   1,
    "Sleep stage 2":   2,
    "Sleep stage 3":   3,
    "Sleep stage 4":   3,   # N3/N4 merged per modern AASM
    "Sleep stage R":   4,
    "Movement time":   0,   # Treat as Wake for classification
    "Sleep stage ?":   -1,  # Excluded
}
N_CLASSES = 5
SLEEP_EDF_SFREQ = 100      # Hz (Sleep-EDF Expanded EEG channels)
EPOCH_SEC = 30             # Standard sleep scoring epoch


class SleepEDFDataset(Dataset):
    """PyTorch Dataset for Sleep-EDF Expanded sleep staging.

    Each sample: (features, label) where
      features: (T, 34) float32 — epochs in one recording, 34 EEG features
      label:    int in {0,1,2,3,4}

    For the pre-training task, samples are individual epochs, not recordings.
    """

    def __init__(
        self,
        data_dir: str,
        split: str = "train",
        split_seed: int = 42,
        train_frac: float = 0.70,
        val_frac: float = 0.15,
        cache_dir: str | None = None,
        ch_names: list[str] | None = None,
    ):
        """
        Args:
            data_dir:   Directory containing *-PSG.edf and *-Hypnogram.edf files.
            split:      "train" | "val" | "test"
            split_seed: Random seed for reproducible subject-level split.
            train_frac, val_frac: Fractions; test = 1 - train - val.
            cache_dir:  Optional directory to cache extracted features as .npy.
            ch_names:   EEG channel names if known (else default positional mapping).
        """
        self.data_dir = data_dir
        self.split = split
        self.cache_dir = cache_dir
        self.ch_names = ch_names

        # Discover recording pairs
        self.psg_files = sorted(glob.glob(os.path.join(data_dir, "*-PSG.edf")))
        assert len(self.psg_files) > 0, (
            f"No *-PSG.edf files found in {data_dir}. "
            "Download Sleep-EDF Expanded from PhysioNet first."
        )

        # Subject-level split (recordings, not epochs — prevents data leakage)
        rng = np.random.default_rng(split_seed)
        n = len(self.psg_files)
        idx = rng.permutation(n)
        n_train = int(n * train_frac)
        n_val = int(n * val_frac)

        if split == "train":
            self.selected = [self.psg_files[i] for i in idx[:n_train]]
        elif split == "val":
            self.selected = [self.psg_files[i] for i in idx[n_train:n_train + n_val]]
        else:
            self.selected = [self.psg_files[i] for i in idx[n_train + n_val:]]

        # Load or compute features
        self.samples: list[tuple[np.ndarray, int]] = []
        self._load_all()

    def _hypnogram_path(self, psg_path: str) -> str:
        """Derive the hypnogram path from PSG path."""
        base = psg_path.replace("-PSG.edf", "")
        # Try both common naming conventions
        for suffix in ["-Hypnogram.edf", "-Annotations.edf"]:
            candidate = base + suffix
            if os.path.exists(candidate):
                return candidate
        raise FileNotFoundError(f"No hypnogram found for {psg_path}")

    def _cache_path(self, psg_path: str) -> str | None:
        if self.cache_dir is None:
            return None
        base = os.path.splitext(os.path.basename(psg_path))[0]
        return os.path.join(self.cache_dir, f"{base}_features.npz")

    def _load_recording(self, psg_path: str) -> tuple[np.ndarray, np.ndarray]:
        """Load one EDF recording and extract (features, labels).

        Returns:
            features: (n_epochs, 34) float32
            labels:   (n_epochs,) int32, -1 for excluded epochs
        """
        import mne
        from src.features.eeg_features import EEGFeatureExtractor

        # Load PSG (EEG channels only)
        raw = mne.io.read_raw_edf(psg_path, preload=True, verbose=False)
        hypno_path = self._hypnogram_path(psg_path)
        annots = mne.read_annotations(hypno_path)
        raw.set_annotations(annots)

        # Bandpass filter (Stage 3 spec: 0.5–100 Hz)
        raw.filter(0.5, 80.0, verbose=False)

        # Create 30-sec epochs
        events, event_id = mne.events_from_annotations(raw, chunk_duration=EPOCH_SEC, verbose=False)
        epochs = mne.Epochs(
            raw, events, event_id=None,
            tmin=0.0, tmax=EPOCH_SEC - 1.0 / SLEEP_EDF_SFREQ,
            baseline=None, preload=True, verbose=False,
            reject=dict(eeg=150e-6),
        )
        data = epochs.get_data()             # (n_epochs, n_ch, n_samples)
        event_labels_raw = events[:, 2]

        # Map event codes to stage labels
        id2label = {v: k for k, v in event_id.items()}
        labels = np.array([
            SLEEP_STAGE_MAP.get(id2label.get(code, "?"), -1)
            for code in event_labels_raw[:len(data)]
        ], dtype=np.int32)

        # Extract features
        extractor = EEGFeatureExtractor(sfreq=SLEEP_EDF_SFREQ, ch_names=list(raw.ch_names))
        features = extractor.extract_recording(data)   # (n_epochs, 34)

        return features, labels

    def _load_all(self) -> None:
        """Load all recordings in the split, using cache when available."""
        os.makedirs(self.cache_dir or ".", exist_ok=True) if self.cache_dir else None

        for psg_path in self.selected:
            cp = self._cache_path(psg_path)
            if cp and os.path.exists(cp):
                loaded = np.load(cp)
                features, labels = loaded["features"], loaded["labels"]
            else:
                features, labels = self._load_recording(psg_path)
                if cp:
                    np.savez_compressed(cp, features=features, labels=labels)

            # Exclude invalid epochs (label == -1)
            valid = labels != -1
            for feat, lbl in zip(features[valid], labels[valid]):
                self.samples.append((feat.astype(np.float32), int(lbl)))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        features, label = self.samples[idx]
        return torch.from_numpy(features), torch.tensor(label, dtype=torch.long)


def build_sleep_edf_loaders(
    data_dir: str,
    batch_size: int = 64,
    num_workers: int = 4,
    cache_dir: str | None = None,
) -> tuple[DataLoader, DataLoader, DataLoader]:
    """Build train/val/test DataLoaders for Sleep-EDF Expanded.

    Returns: (train_loader, val_loader, test_loader)
    """
    train_ds = SleepEDFDataset(data_dir, split="train", cache_dir=cache_dir)
    val_ds   = SleepEDFDataset(data_dir, split="val",   cache_dir=cache_dir)
    test_ds  = SleepEDFDataset(data_dir, split="test",  cache_dir=cache_dir)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,
                              num_workers=num_workers, pin_memory=True)
    val_loader   = DataLoader(val_ds,   batch_size=batch_size, shuffle=False,
                              num_workers=num_workers, pin_memory=True)
    test_loader  = DataLoader(test_ds,  batch_size=batch_size, shuffle=False,
                              num_workers=num_workers, pin_memory=True)
    return train_loader, val_loader, test_loader

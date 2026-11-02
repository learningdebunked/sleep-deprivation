#!/usr/bin/env python3
"""
OpenNeuro ds004902 Dataset Loader — Stage 2 fine-tuning.

Dataset: EEG During Mental Arithmetic Tasks (Normal Sleep vs. Sleep Deprived)
DOI: 10.1038/s41597-024-03268-2
URL: https://openneuro.org/datasets/ds004902
71 participants × 2 sessions = up to 142 recordings
61 EEG channels, 500 Hz, impedance <5 kΩ
Binary classification: 0 = Normal Sleep (NS), 1 = Sleep Deprived (SD)

Expected BIDS directory structure:
  data/openneuro_ds004902/
    participants.tsv        (subject metadata including condition)
    sub-001/ses-01/eeg/sub-001_ses-01_task-MentalArithmetic_eeg.set
    ...

Usage:
    dataset = OpenNeuroEEGDataset(data_dir="data/openneuro_ds004902/")
    loader  = DataLoader(dataset, batch_size=32, shuffle=True)
"""
from __future__ import annotations

import os
import glob
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence

SFREQ = 500         # Hz (OpenNeuro ds004902)
EPOCH_SEC = 2.0     # seconds (Stage 3 spec)
N_CHANNELS = 61
LABEL_MAP = {"NS": 0, "SD": 1, "normal": 0, "deprived": 1}


class OpenNeuroEEGDataset(Dataset):
    """PyTorch Dataset for OpenNeuro ds004902 binary NS/SD classification.

    Each sample: (features, label) where
      features: (T, 34) float32 — variable-length epoch sequence for one recording
      label:    int {0=NS, 1=SD}

    Variable-length sequences are collated with pad_collate_fn.
    """

    def __init__(
        self,
        data_dir: str,
        subjects: list[str] | None = None,
        cache_dir: str | None = None,
        reject_amplitude_uv: float = 150.0,
    ):
        """
        Args:
            data_dir:             Root BIDS directory of ds004902.
            subjects:             Optional list of subject IDs to restrict to.
            cache_dir:            Optional feature cache directory.
            reject_amplitude_uv:  Epoch rejection threshold (µV).
        """
        self.data_dir = data_dir
        self.cache_dir = cache_dir
        self.reject_amplitude_uv = reject_amplitude_uv

        # Load participant metadata
        participants_tsv = os.path.join(data_dir, "participants.tsv")
        if os.path.exists(participants_tsv):
            self.meta = pd.read_csv(participants_tsv, sep="\t")
        else:
            # Build from directory structure
            self.meta = self._build_meta_from_dirs()

        if subjects:
            self.meta = self.meta[self.meta["participant_id"].isin(subjects)]

        self.samples: list[tuple[np.ndarray, int]] = []
        self._load_all()

    def _build_meta_from_dirs(self) -> pd.DataFrame:
        """Fallback: infer subject list and condition from directory names."""
        sub_dirs = sorted(glob.glob(os.path.join(self.data_dir, "sub-*")))
        rows = []
        for sd in sub_dirs:
            sub_id = os.path.basename(sd)
            # Condition from session metadata or directory name convention
            rows.append({"participant_id": sub_id, "condition": "unknown"})
        return pd.DataFrame(rows)

    def _get_label(self, row: pd.Series) -> int | None:
        """Return binary label from participant metadata row."""
        for col in ["condition", "group", "sleep_condition"]:
            val = str(row.get(col, "")).lower().strip()
            for k, v in LABEL_MAP.items():
                if k in val:
                    return v
        return None   # Exclude if condition unknown

    def _find_eeg_files(self, sub_id: str) -> list[str]:
        """Find all EEG files for a subject (any session)."""
        pattern = os.path.join(
            self.data_dir, sub_id, "ses-*", "eeg",
            f"{sub_id}_ses-*_task-*_eeg.*"
        )
        files = glob.glob(pattern)
        # Also try without session level
        if not files:
            files = glob.glob(os.path.join(self.data_dir, sub_id, "eeg", "*.set"))
            files += glob.glob(os.path.join(self.data_dir, sub_id, "eeg", "*.edf"))
        return files

    def _cache_path(self, sub_id: str, ses: str = "ses-01") -> str | None:
        if self.cache_dir is None:
            return None
        return os.path.join(self.cache_dir, f"{sub_id}_{ses}_features.npz")

    def _load_recording(self, eeg_path: str) -> np.ndarray | None:
        """Load EEG file, preprocess, and extract (T, 34) feature array."""
        import mne
        from src.features.eeg_features import EEGFeatureExtractor

        # Load raw EEG (handle .set / .edf / .fif)
        ext = os.path.splitext(eeg_path)[1].lower()
        try:
            if ext == ".set":
                raw = mne.io.read_raw_eeglab(eeg_path, preload=True, verbose=False)
            elif ext == ".edf":
                raw = mne.io.read_raw_edf(eeg_path, preload=True, verbose=False)
            elif ext in (".fif", ".fif.gz"):
                raw = mne.io.read_raw_fif(eeg_path, preload=True, verbose=False)
            else:
                print(f"[OpenNeuroDataset] Unsupported format: {eeg_path}")
                return None
        except Exception as e:
            print(f"[OpenNeuroDataset] Failed to load {eeg_path}: {e}")
            return None

        # Stage 3 preprocessing pipeline
        raw.filter(0.5, 100.0, verbose=False)                    # Step 2: bandpass
        raw.notch_filter([50.0, 60.0], verbose=False)            # Step 3: notch
        raw.set_eeg_reference("average", verbose=False)          # Step 4: re-reference

        # Step 5: ICA artifact removal (automated)
        try:
            from mne.preprocessing import ICA
            ica = ICA(n_components=20, random_state=42, verbose=False)
            ica.fit(raw, verbose=False)
            # Auto-detect ocular components by correlation with EOG (if EOG channel exists)
            eog_chs = [c for c in raw.ch_names if "EOG" in c.upper() or "VEOG" in c.upper()]
            if eog_chs:
                eog_inds, _ = ica.find_bads_eog(raw, ch_name=eog_chs[0], verbose=False)
                ica.exclude = eog_inds[:2]   # Exclude at most 2 components
            ica.apply(raw, verbose=False)
        except Exception as e:
            print(f"[OpenNeuroDataset] ICA failed for {eeg_path}: {e} — skipping ICA")

        # Step 6: Epoch extraction — 2-sec fixed-length
        epoch_len = int(SFREQ * EPOCH_SEC)
        try:
            epochs = mne.make_fixed_length_epochs(
                raw, duration=EPOCH_SEC, overlap=EPOCH_SEC / 2,
                preload=True, verbose=False,
            )
            epochs.drop_bad(reject={"eeg": self.reject_amplitude_uv * 1e-6}, verbose=False)
            data = epochs.get_data()   # (n_epochs, n_ch, n_samples)
        except Exception as e:
            print(f"[OpenNeuroDataset] Epoch extraction failed for {eeg_path}: {e}")
            return None

        if data.shape[0] == 0:
            return None

        # Step 7: Baseline correction
        data -= data.mean(axis=2, keepdims=True)

        # Step 8: Feature extraction
        extractor = EEGFeatureExtractor(sfreq=SFREQ, ch_names=list(raw.ch_names))
        features = extractor.extract_recording(data)   # (n_epochs, 34)

        return features.astype(np.float32)

    def _load_all(self) -> None:
        os.makedirs(self.cache_dir, exist_ok=True) if self.cache_dir else None

        for _, row in self.meta.iterrows():
            sub_id = str(row["participant_id"])
            label = self._get_label(row)
            if label is None:
                continue

            eeg_files = self._find_eeg_files(sub_id)
            for eeg_path in eeg_files:
                ses = os.path.basename(os.path.dirname(os.path.dirname(eeg_path)))
                cp = self._cache_path(sub_id, ses)

                if cp and os.path.exists(cp):
                    features = np.load(cp)["features"]
                else:
                    features = self._load_recording(eeg_path)
                    if features is None:
                        continue
                    if cp:
                        np.savez_compressed(cp, features=features)

                self.samples.append((features, label))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        features, label = self.samples[idx]
        length = torch.tensor(features.shape[0], dtype=torch.long)
        return (
            torch.from_numpy(features),
            torch.tensor(label, dtype=torch.long),
            length,
        )


def pad_collate_fn(batch):
    """Collate variable-length epoch sequences into a padded batch.

    Returns:
        features:  (batch, T_max, 34) padded tensor
        labels:    (batch,) long tensor
        lengths:   (batch,) long tensor — actual sequence lengths
    """
    features_list, labels, lengths = zip(*batch)
    features_padded = pad_sequence(features_list, batch_first=True, padding_value=0.0)
    return (
        features_padded,
        torch.stack(labels),
        torch.stack(lengths),
    )


def build_openneuro_loaders(
    data_dir: str,
    batch_size: int = 32,
    num_workers: int = 4,
    cache_dir: str | None = None,
    n_folds: int = 5,
    fold: int = 0,
    seed: int = 42,
) -> tuple[DataLoader, DataLoader]:
    """Build one train/val fold for OpenNeuro ds004902 cross-validation.

    Returns: (train_loader, val_loader)
    """
    full_ds = OpenNeuroEEGDataset(data_dir, cache_dir=cache_dir)
    n = len(full_ds)
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n)
    fold_size = n // n_folds
    val_idx = idx[fold * fold_size:(fold + 1) * fold_size].tolist()
    train_idx = [i for i in idx if i not in set(val_idx)]

    from torch.utils.data import Subset
    train_loader = DataLoader(
        Subset(full_ds, train_idx), batch_size=batch_size,
        shuffle=True, num_workers=num_workers, collate_fn=pad_collate_fn,
    )
    val_loader = DataLoader(
        Subset(full_ds, val_idx), batch_size=batch_size,
        shuffle=False, num_workers=num_workers, collate_fn=pad_collate_fn,
    )
    return train_loader, val_loader

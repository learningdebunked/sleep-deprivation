#!/usr/bin/env python3
"""
EEG Feature Extraction — Stage 3 spec implementation.
Extracts 34-dimensional feature vector per 2-second epoch:
  - 6 channels × 5 bands = 30 band-power features (Welch PSD)
  - 4 connectivity features (theta/alpha ratio, FAA, PLV, coherence)

Usage:
    from src.features.eeg_features import EEGFeatureExtractor
    extractor = EEGFeatureExtractor(sfreq=500)
    features = extractor.extract(epochs_array)  # (n_epochs, T) -> (n_epochs, 34)
"""
from __future__ import annotations

import numpy as np
from typing import Tuple

# ── Constants ─────────────────────────────────────────────────────────────────
SFREQ_DEFAULT = 500          # OpenNeuro ds004902 sampling frequency (Hz)
EPOCH_DURATION = 2.0         # Seconds per epoch (Stage 3 spec)
BANDS = {
    "delta": (0.5, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 12.0),
    "beta":  (12.0, 30.0),
    "gamma": (30.0, 80.0),
}
FEATURE_CHANNELS = ["Fz", "Cz", "Pz", "F3", "F4", "Oz"]  # 6 channels for band power
N_BAND_POWER_FEATURES = len(FEATURE_CHANNELS) * len(BANDS)  # 6 × 5 = 30
N_CONNECTIVITY_FEATURES = 4                                   # theta/alpha, FAA, PLV, coherence
N_TOTAL_FEATURES = N_BAND_POWER_FEATURES + N_CONNECTIVITY_FEATURES  # 34


def bandpower_welch(
    signal: np.ndarray,
    sfreq: float,
    fmin: float,
    fmax: float,
    nperseg: int = 256,
) -> float:
    """Compute mean band power using Welch's method.

    Args:
        signal: 1-D array, single-channel epoch.
        sfreq: Sampling frequency (Hz).
        fmin: Lower band edge (Hz).
        fmax: Upper band edge (Hz).
        nperseg: FFT window length.

    Returns:
        Mean power spectral density in [fmin, fmax].
    """
    from scipy.signal import welch
    freqs, psd = welch(signal, fs=sfreq, nperseg=min(nperseg, len(signal)))
    freq_mask = (freqs >= fmin) & (freqs <= fmax)
    if not np.any(freq_mask):
        return 0.0
    return float(np.mean(psd[freq_mask]))


def phase_locking_value(sig1: np.ndarray, sig2: np.ndarray, fmin: float, fmax: float,
                        sfreq: float) -> float:
    """Compute Phase Locking Value (PLV) between two signals in a frequency band.

    Args:
        sig1, sig2: 1-D arrays, same length.
        fmin, fmax: Frequency band (Hz).
        sfreq: Sampling frequency (Hz).

    Returns:
        PLV in [0, 1].
    """
    from scipy.signal import butter, filtfilt
    nyq = sfreq / 2.0
    b, a = butter(4, [fmin / nyq, fmax / nyq], btype="band")
    f1 = filtfilt(b, a, sig1)
    f2 = filtfilt(b, a, sig2)
    phase1 = np.angle(hilbert_analytic(f1))
    phase2 = np.angle(hilbert_analytic(f2))
    plv = np.abs(np.mean(np.exp(1j * (phase1 - phase2))))
    return float(plv)


def hilbert_analytic(signal: np.ndarray) -> np.ndarray:
    """Return the analytic signal via the Hilbert transform."""
    from scipy.signal import hilbert
    return hilbert(signal)


def magnitude_squared_coherence(sig1: np.ndarray, sig2: np.ndarray,
                                fmin: float, fmax: float,
                                sfreq: float, nperseg: int = 256) -> float:
    """Mean magnitude-squared coherence in a frequency band.

    Args:
        sig1, sig2: 1-D signals.
        fmin, fmax: Frequency band (Hz).
        sfreq: Sampling frequency (Hz).
        nperseg: FFT window.

    Returns:
        Mean MSC in [0, 1].
    """
    from scipy.signal import coherence
    freqs, cxy = coherence(sig1, sig2, fs=sfreq, nperseg=min(nperseg, len(sig1)))
    freq_mask = (freqs >= fmin) & (freqs <= fmax)
    if not np.any(freq_mask):
        return 0.0
    return float(np.mean(cxy[freq_mask]))


class EEGFeatureExtractor:
    """Extract 34-dim EEG feature vectors per epoch.

    Usage:
        extractor = EEGFeatureExtractor(sfreq=500, ch_names=[...])
        features = extractor.extract_epoch(epoch_data)
            epoch_data: (n_channels, n_samples) array for one 2-sec epoch
            returns: (34,) feature vector

    The feature vector layout (34 dims):
        [0:30]  Band power: 6 channels × 5 bands (delta, theta, alpha, beta, gamma)
                  order: Fz_delta, Fz_theta, ..., Fz_gamma,
                         Cz_delta, ..., Oz_gamma
        [30]    Theta/alpha ratio (Fz)
        [31]    Frontal alpha asymmetry: ln(F4_alpha) - ln(F3_alpha)
        [32]    PLV Fz-Pz (theta band 4-8 Hz)
        [33]    MSC coherence Fz-Oz (theta band 4-8 Hz)
    """

    def __init__(self, sfreq: float = SFREQ_DEFAULT, ch_names: list[str] | None = None):
        self.sfreq = sfreq
        self.ch_names = ch_names  # Full channel list from recording
        # Indices resolved lazily in extract_epoch
        self._ch_idx: dict[str, int] = {}

    def _resolve_indices(self, n_channels: int) -> None:
        """Build channel-name → index map.

        Falls back to positional defaults if ch_names not provided.
        Default order assumes standard 61-ch layout: Fz=11, Cz=20, Pz=29,
        F3=10, F4=12, Oz=30 (approximate; overridden by ch_names when available).
        """
        if self.ch_names is not None:
            self._ch_idx = {name.upper(): i for i, name in enumerate(self.ch_names)}
        else:
            # Fallback positional defaults for 61-channel caps
            defaults = {"FZ": 11, "CZ": 20, "PZ": 29, "F3": 10, "F4": 12, "OZ": 30}
            self._ch_idx = {k: min(v, n_channels - 1) for k, v in defaults.items()}

    def _get_ch(self, epoch: np.ndarray, name: str) -> np.ndarray:
        """Return signal for a named channel from epoch array."""
        idx = self._ch_idx.get(name.upper())
        if idx is None:
            raise KeyError(f"Channel '{name}' not found. Available: {list(self._ch_idx.keys())}")
        return epoch[idx]

    def extract_epoch(self, epoch: np.ndarray) -> np.ndarray:
        """Extract 34-dim feature vector from a single epoch.

        Args:
            epoch: (n_channels, n_samples) array, float64, already filtered/cleaned.

        Returns:
            features: (34,) float32 array.
        """
        n_channels, n_samples = epoch.shape
        if not self._ch_idx:
            self._resolve_indices(n_channels)

        features = np.zeros(N_TOTAL_FEATURES, dtype=np.float32)
        idx = 0

        # ── Band-power features (30 dims) ─────────────────────────────────────
        for ch_name in FEATURE_CHANNELS:
            sig = self._get_ch(epoch, ch_name)
            for band_name, (fmin, fmax) in BANDS.items():
                features[idx] = bandpower_welch(sig, self.sfreq, fmin, fmax)
                idx += 1

        # ── Connectivity features (4 dims) ────────────────────────────────────
        fz = self._get_ch(epoch, "Fz")
        pz = self._get_ch(epoch, "Pz")
        f3 = self._get_ch(epoch, "F3")
        f4 = self._get_ch(epoch, "F4")
        oz = self._get_ch(epoch, "Oz")

        # [30] Theta/alpha ratio (Fz)
        theta_fz = bandpower_welch(fz, self.sfreq, *BANDS["theta"])
        alpha_fz = bandpower_welch(fz, self.sfreq, *BANDS["alpha"])
        features[30] = theta_fz / (alpha_fz + 1e-10)

        # [31] Frontal Alpha Asymmetry: ln(F4_alpha) - ln(F3_alpha)
        alpha_f3 = bandpower_welch(f3, self.sfreq, *BANDS["alpha"])
        alpha_f4 = bandpower_welch(f4, self.sfreq, *BANDS["alpha"])
        features[31] = np.log(alpha_f4 + 1e-10) - np.log(alpha_f3 + 1e-10)

        # [32] PLV Fz-Pz (theta 4-8 Hz)
        features[32] = phase_locking_value(fz, pz, *BANDS["theta"], self.sfreq)

        # [33] MSC coherence Fz-Oz (theta 4-8 Hz)
        features[33] = magnitude_squared_coherence(fz, oz, *BANDS["theta"], self.sfreq)

        return features

    def extract_recording(self, recording: np.ndarray) -> np.ndarray:
        """Extract features from all epochs in a recording.

        Args:
            recording: (n_epochs, n_channels, n_samples) array.

        Returns:
            features: (n_epochs, 34) float32 array.
        """
        n_epochs = recording.shape[0]
        features = np.zeros((n_epochs, N_TOTAL_FEATURES), dtype=np.float32)
        for i in range(n_epochs):
            features[i] = self.extract_epoch(recording[i])
        return features

    def get_feature_names(self) -> list[str]:
        """Return ordered list of feature names (for SHAP interpretability)."""
        names = []
        for ch_name in FEATURE_CHANNELS:
            for band_name in BANDS:
                names.append(f"{ch_name}_{band_name}_power")
        names += [
            "Fz_theta_alpha_ratio",
            "frontal_alpha_asymmetry_F3F4",
            "PLV_Fz_Pz_theta",
            "MSC_Fz_Oz_theta",
        ]
        assert len(names) == N_TOTAL_FEATURES, f"Expected {N_TOTAL_FEATURES}, got {len(names)}"
        return names

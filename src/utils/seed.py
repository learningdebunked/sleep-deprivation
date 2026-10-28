"""
seed.py — Reproducible random seed fixation for PyTorch + NumPy + Python.
"""

import os
import random
import numpy as np
import torch


def set_seed(seed: int = 42) -> None:
    """
    Fix all random seeds for reproducible runs.
    Sets Python, NumPy, PyTorch (CPU + CUDA) seeds and disables
    non-deterministic cuDNN algorithms.
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

"""DNG loader: thin Python wrapper around the C++ dngparse extension.

Returns plain numpy arrays and Python primitives — no torch dependency.
Convert to torch tensors at the call site if needed:

    import torch
    from dngparse import load_dng
    d = load_dng("photo.dng")
    raw = torch.from_numpy(d["raw"])
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

# The compiled extension is installed alongside this package by scikit-build-core.
import dngparse._dng as _dng_ext


def load_dng(path: str | Path) -> dict[str, Any]:
    """Load a DNG file and return structured metadata + raw pixel array.

    Returns a dict with keys including:
        raw: np.ndarray (H, W) uint16
        cfa_pattern: list[int]
        black_level: list[float]
        white_level: int
        color_matrix_1: np.ndarray (3, 3) float32
        color_matrix_2: np.ndarray (3, 3) float32 | None
        as_shot_neutral: list[float]
        noise_profile: dict
        ...
    """
    return _dng_ext.load_dng(str(path))


def load_dng_raw_only(path: str | Path) -> np.ndarray:
    """Load only the raw pixel array from a DNG file.

    Returns
    -------
    np.ndarray (H, W) uint16
    """
    return _dng_ext.load_dng_raw_only(str(path))

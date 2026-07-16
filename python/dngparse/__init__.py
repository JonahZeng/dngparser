"""dngparse: Fast DNG parser for PyTorch datasets (DJI Pocket 4 specialized).

This package provides:
  - DNG loading via the C++ extension (dngparse._dng)
  - Numpy-based metadata + raw pixel extraction
  - Optional PyTorch Dataset wrapper (requires torch)
"""

__version__ = "0.1.0"

from dngparse.dng_loader import load_dng, load_dng_raw_only

__all__ = ["load_dng", "load_dng_raw_only"]

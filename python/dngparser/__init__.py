"""dngparser: Fast DNG parser for machine learning datasets (DJI + Apple ProRAW).

This package provides:
  - DNG loading via the C++ extension (dngparser._dng)
  - Numpy-based metadata + raw pixel extraction
  - Optional PyTorch Dataset wrapper (requires torch)
"""

__version__ = "0.1.0"

from dngparser.dng_loader import load_dng, load_dng_raw_only

__all__ = ["load_dng", "load_dng_raw_only"]

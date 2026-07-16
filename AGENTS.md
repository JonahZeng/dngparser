# Repository Guidelines

## Project Structure & Module Organization

```
dngparse/
├── CMakeLists.txt              # CMake build for the C++ extension
├── pyproject.toml              # scikit-build-core wheel build config
├── cpp/
│   ├── pybind11/               # Vendored pybind11 (C++ Python bindings)
│   ├── include/dng/            # Headers: tiff_reader.h, dng_image.h, dng_parser.h, ljpeg_decoder.h
│   ├── src/                    # Sources: tiff_reader.cpp, dng_parser.cpp, ljpeg_decoder.cpp
│   └── binding/pybind_module.cpp  # pybind11 module that exposes load_dng()
├── python/dngparse/            # Python package installed into the wheel
│   ├── __init__.py             # Re-exports load_dng, load_dng_raw_only
│   ├── dng_loader.py           # Thin wrapper: returns numpy arrays
│   └── _dng.pyi                # Type stubs (generated, do not hand-edit)
├── tests/test_dng_parse.py     # End-to-end DNG parse verification (DJI + Apple)
└── *.DNG                       # Sample DNG files: IMG_5063/5064 (DJI), IMG_5070 (Apple)
```

## Build, Test, and Development Commands

All commands assume the venv at `.venv/`. Create it once:

```powershell
python -m venv .venv
.\.venv\Scripts\pip install scikit-build-core build pybind11 pybind11-stubgen numpy
```

Build the wheel and install into the venv:

```powershell
Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m build --wheel
.\.venv\Scripts\pip.exe install --force-reinstall --no-deps dist\dngparse-0.1.0-cp310-cp310-win_amd64.whl
```

Regenerate type stubs after changing the pybind11 binding:

```powershell
.\.venv\Scripts\python.exe -m pybind11_stubgen dngparse._dng --output-dir stubs
Copy-Item stubs\dngparse\_dng.pyi python\dngparse\_dng.pyi -Force
```

Run tests:

```powershell
.\.venv\Scripts\python.exe tests\test_dng_parse.py
```

## Coding Style & Naming Conventions

- C++17, no extensions (`CMAKE_CXX_EXTENSIONS OFF`). MSVC `/W4 /utf-8`, GCC/Clang `-Wall -Wextra -Wpedantic`.
- Headers use `#pragma once`. All C++ lives in `namespace dng`.
- Python follows PEP 8. Type hints required on public functions. Use `from __future__ import annotations`.
- Source files are UTF-8 **without BOM** (PowerShell `Set-Content -Encoding utf8` adds BOM — use `[System.IO.File]::WriteAllText` with `UTF8Encoding($false)` instead).

## Testing Guidelines

Tests are plain scripts under `tests/`. `test_dng_parse.py` loads real DNG files (DJI Pocket 4 + Apple ProRAW), asserts vendor-specific key metadata values (dimensions, CFA pattern, compression type, bit depth, tile layout, linearization table), and prints a full metadata dump. Run it after every C++ or binding change. Single-channel CFA data is exported as `.raw`; multi-channel RGB data is exported as `.pnm` (P6 PPM).

## Commit & Pull Request Guidelines

No commit history yet (empty repo). Suggested conventions:

- Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`.
- Keep C++ changes and Python wrapper changes in separate commits when possible.
- PRs must pass `test_dng_parse.py` on at least one sample DNG (DJI or Apple).

## Architecture Overview

The pipeline is: DNG file -> C++ `TiffReader` (TIFF container parse, both LE/BE) -> `DngParser` (tag interpretation, raw IFD selection for CFA/LinearRaw, pixel read) -> optional `LjpegDecoder` (SOF3 lossless JPEG tile decompression for Apple ProRAW) -> pybind11 -> Python dict of numpy arrays. The parser only reads and structures data — no linearization, black-level subtraction, or color conversion is applied. Those transforms belong to the differentiable ISP pipeline (planned, separate project).

### Multi-Vendor Support

- **DJI Pocket 4**: little-endian, uncompressed CFA Bayer (1ch uint16, strip-based). Main IFD holds global metadata; SubIFD[0] holds the raw CFA data.
- **Apple ProRAW**: big-endian, LJPEG-compressed LinearRaw (3ch uint16, tile-based). SubIFD[0] holds tiled 12-bit LJPEG data with a 4096-entry LinearizationTable. NoiseProfile and levels live on the raw SubIFD rather than the main IFD. The `LjpegDecoder` class handles SOF3 frame parsing, Huffman table construction (16-bit flat lookup), and predictor-based lossless reconstruction.

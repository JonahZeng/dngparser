"""Test script: parse a DNG file and verify all metadata fields.

Usage:
    python tests/test_dng_parse.py [path/to/file.dng]

Does NOT require torch — uses numpy only.
"""

import os
import sys

import numpy as np

from dngparse import load_dng


def export_raw(raw: np.ndarray, dng_path: str, out_dir: str | None = None) -> str:
    """Export the raw pixel array to local disk.

    For single-channel (CFA) data: exported as raw binary (.raw).
    For multi-channel (RGB) data: exported as PNM/PPM (.pnm).

    Parameters
    ----------
    raw : np.ndarray
        Raw pixel array (H, W) or (H, W, C) uint16.
    dng_path : str
        Source DNG file path — used to derive the output filename.
    out_dir : str | None
        Output directory. Defaults to the same directory as the DNG file.

    Returns
    -------
    str
        Path to the exported file.
    """
    stem = os.path.splitext(os.path.basename(dng_path))[0]
    out_dir = out_dir or os.path.dirname(os.path.abspath(dng_path))
    os.makedirs(out_dir, exist_ok=True)

    if raw.ndim == 3 and raw.shape[2] == 3:
        # RGB data → PNM (PPM binary, P6)
        out_path = os.path.join(out_dir, f"{stem}_raw.pnm")
        h, w, _ = raw.shape
        max_val = int(raw.max())
        with open(out_path, "wb") as f:
            header = f"P6\n{w} {h}\n{max_val}\n".encode("ascii")
            f.write(header)
            if raw.dtype == np.uint16:
                # PNM big-endian 16-bit: need to byteswap on little-endian host
                raw.astype(">u2").tofile(f)
            else:
                raw.tofile(f)
        out_size = os.path.getsize(out_path)
        print(f"  Exported .pnm:  {out_path}  ({out_size:,} bytes)")
    else:
        # Single-channel CFA data → raw binary
        out_path = os.path.join(out_dir, f"{stem}_raw.raw")
        raw.tofile(out_path)
        out_size = os.path.getsize(out_path)
        print(f"  Exported .raw:  {out_path}  ({out_size:,} bytes)")
    return out_path


def test_dng(path: str):
    print(f"Loading: {path}")
    dng = load_dng(path)

    make = dng["make"]
    is_apple = "apple" in make.lower()
    print(f"  Vendor: {make}")

    # --- Pixel data ---
    raw = dng["raw"]
    print(f"\n=== Pixel Data ===")
    print(f"  Shape: {raw.shape}  dtype: {raw.dtype}")
    print(f"  Min: {raw.min()}  Max: {raw.max()}  Mean: {raw.astype(np.float64).mean():.1f}")
    print(f"  Width x Height: {dng['width']} x {dng['height']}")
    print(f"  BitsPerSample: {dng['bits_per_sample']}")
    print(f"  Compression: {dng['compression']}")
    print(f"  PhotometricInterpretation: {dng['photometric_interpretation']}")
    print(f"  SamplesPerPixel: {dng['samples_per_pixel']}")
    print(f"  IsTiled: {dng['is_tiled']}")

    # --- CFA ---
    print(f"\n=== CFA ===")
    print(f"  Pattern: {dng['cfa_pattern']}  (0=R, 1=G, 2=B)")
    print(f"  Repeat: {dng['cfa_repeat_rows']}x{dng['cfa_repeat_cols']}")
    print(f"  Layout: {dng['cfa_layout']}")

    # --- Levels ---
    print(f"\n=== Levels ===")
    print(f"  BlackLevel: {dng['black_level']}")
    print(f"  WhiteLevel: {dng['white_level']}")
    wlps = dng.get("white_level_per_sample")
    if wlps is not None:
        print(f"  WhiteLevelPerSample: {wlps}")
    lt = dng['linearization_table']
    print(f"  LinearizationTable: {'present' if lt is not None else 'absent'}")
    if lt is not None:
        print(f"    length: {len(lt)}, first 10: {list(lt[:10])}")

    # --- Color ---
    print(f"\n=== Color ===")
    print(f"  ColorMatrix1:\n{dng['color_matrix_1']}")
    if dng["color_matrix_2"] is not None:
        print(f"  ColorMatrix2:\n{dng['color_matrix_2']}")
    else:
        print(f"  ColorMatrix2: None")
    print(f"  CalibrationIlluminant: {dng['calibration_illuminant_1']}, {dng['calibration_illuminant_2']}")
    print(f"  AsShotNeutral: {dng['as_shot_neutral']}")
    fm1 = dng["forward_matrix_1"]
    print(f"  ForwardMatrix1: {'present' if fm1 is not None else 'None'}")

    # --- Crop ---
    print(f"\n=== Crop ===")
    print(f"  ActiveArea: {dng['active_area']}")
    print(f"  DefaultCropOrigin: {dng['default_crop_origin']}")
    print(f"  DefaultCropSize: {dng['default_crop_size']}")

    # --- Exposure ---
    print(f"\n=== Exposure ===")
    print(f"  ISO: {dng['iso_speed']}")
    print(f"  ExposureTime: {dng['exposure_time']}s")
    print(f"  FNumber: f/{dng['f_number']}")
    print(f"  FocalLength: {dng['focal_length']}mm")
    print(f"  BaselineExposure: {dng['baseline_exposure']}")

    # --- Noise ---
    print(f"\n=== Noise ===")
    np_profile = dng["noise_profile"]
    print(f"  Present: {np_profile['present']}")
    print(f"  Slope: {np_profile['slope']}")
    print(f"  Offset: {np_profile['offset']}")

    # --- Opcodes ---
    print(f"\n=== Opcodes ===")
    print(f"  OpcodeList1: {'present' if dng['opcode_list_1'] is not None else 'absent'}")
    print(f"  OpcodeList2: {'present' if dng['opcode_list_2'] is not None else 'absent'}")
    print(f"  OpcodeList3: {'present' if dng['opcode_list_3'] is not None else 'absent'}")
    if dng["opcode_list_2"] is not None:
        print(f"  OpcodeList2 size: {len(dng['opcode_list_2'])} bytes")

    # --- Camera ---
    print(f"\n=== Camera ===")
    print(f"  Make: {dng['make']}")
    print(f"  Model: {dng['model']}")
    print(f"  UniqueCameraModel: {dng['unique_camera_model']}")
    print(f"  SerialNumber: {dng['serial_number']}")
    print(f"  DNGVersion: {dng['dng_version']}")

    # --- Sanity checks ---
    print(f"\n=== Sanity Checks ===")

    if is_apple:
        _assert_apple(dng, raw)
    else:
        _assert_dji(dng, raw)

    print("  All assertions passed!")

    # --- Export raw data ---
    print(f"\n=== Export Raw ===")
    out_path = export_raw(raw, path)

    print(f"\nDone. File parsed successfully.")


def _assert_dji(dng, raw):
    """Assertions specific to DJI Pocket 4 DNG files."""
    expected_w, expected_h = 3840, 2160
    assert raw.shape == (expected_h, expected_w), f"Expected ({expected_h}, {expected_w}), got {raw.shape}"
    assert dng["compression"] == 1, f"Expected uncompressed (1), got {dng['compression']}"
    assert dng["bits_per_sample"] == 16, f"Expected 16-bit, got {dng['bits_per_sample']}"
    assert dng["photometric_interpretation"] == 32803, f"Expected CFA (32803), got {dng['photometric_interpretation']}"
    assert dng["samples_per_pixel"] == 1, f"Expected 1 sample, got {dng['samples_per_pixel']}"
    assert dng["cfa_pattern"] == [0, 1, 1, 2], f"Expected RGGB, got {dng['cfa_pattern']}"
    assert dng["black_level"] == [1024.0, 1024.0, 1024.0, 1024.0], f"BL mismatch: {dng['black_level']}"
    assert dng["white_level"] == 62400, f"WL mismatch: {dng['white_level']}"
    assert dng["noise_profile"]["present"], "NoiseProfile should be present"
    assert dng["color_matrix_1"][0, 1] < 0, "ColorMatrix1[0,1] should be negative"
    assert dng["is_tiled"] == False, "DJI DNG should not be tiled"


def _assert_apple(dng, raw):
    """Assertions specific to Apple ProRAW DNG files."""
    expected_w, expected_h = 4032, 3024
    assert raw.shape == (expected_h, expected_w, 3), f"Expected ({expected_h}, {expected_w}, 3), got {raw.shape}"
    assert dng["compression"] == 7, f"Expected LJPEG (7), got {dng['compression']}"
    assert dng["bits_per_sample"] == 12, f"Expected 12-bit, got {dng['bits_per_sample']}"
    assert dng["photometric_interpretation"] == 34892, f"Expected LinearRaw (34892), got {dng['photometric_interpretation']}"
    assert dng["samples_per_pixel"] == 3, f"Expected 3 samples, got {dng['samples_per_pixel']}"
    assert dng["is_tiled"] == True, "Apple DNG should be tiled"
    assert dng["tile_width"] == 504, f"Expected tile_width=504, got {dng['tile_width']}"
    assert dng["tile_length"] == 504, f"Expected tile_length=504, got {dng['tile_length']}"
    assert dng["noise_profile"]["present"], "NoiseProfile should be present"
    assert dng["color_matrix_1"][0, 1] < 0, "ColorMatrix1[0,1] should be negative"
    assert dng["linearization_table"] is not None, "LinearizationTable should be present"
    assert len(dng["linearization_table"]) == 4096, f"Expected 4096-entry LUT, got {len(dng['linearization_table'])}"
    assert dng["white_level"] == 65535, f"Expected white_level=65535, got {dng['white_level']}"
    assert dng["as_shot_neutral"] == [1.0, 1.0, 1.0], f"AsShotNeutral mismatch: {dng['as_shot_neutral']}"
    # Pixel value range: 12-bit LJPEG-decoded values (pre-linearization)
    assert raw.min() >= 0, f"Min pixel value should be >= 0, got {raw.min()}"
    assert raw.max() <= 4095, f"Max pixel value should be <= 4095 (12-bit), got {raw.max()}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Try all known DNG files
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root = os.path.dirname(script_dir)
        candidates = [
            os.path.join(root, "IMG_5063.DNG"),
            os.path.join(root, "IMG_5064.DNG"),
            os.path.join(root, "IMG_5070.DNG"),
        ]
        found = [p for p in candidates if os.path.exists(p)]
        if not found:
            print("Usage: python test_dng_parse.py <path/to/file.dng>")
            sys.exit(1)
        for p in found:
            test_dng(p)
            print()
    else:
        test_dng(sys.argv[1])

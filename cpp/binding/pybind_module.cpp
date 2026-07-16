#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include "dng/dng_parser.h"

namespace py = pybind11;

using namespace dng;

// Convert a Matrix3x3 to a numpy array (3x3 float32)
static py::array_t<float> matrix_to_numpy(const Matrix3x3& mat) {
    py::array_t<float> arr({3, 3});
    auto buf = arr.mutable_unchecked<2>();
    for (int r = 0; r < 3; ++r) {
        for (int c = 0; c < 3; ++c) {
            buf(r, c) = mat(r, c);
        }
    }
    return arr;
}

// Convert raw pixel buffer (uint8) to numpy uint16 array.
// For single-channel (CFA): shape (H, W)
// For multi-channel (LinearRaw): shape (H, W, C)
static py::array_t<uint16_t> pixels_to_numpy(const std::vector<uint8_t>& raw,
                                             uint32_t width, uint32_t height,
                                             uint16_t samples_per_pixel) {
    uint16_t spp = samples_per_pixel > 0 ? samples_per_pixel : 1;
    size_t num_pixels = static_cast<size_t>(width) * height * spp;
    const uint16_t* src = reinterpret_cast<const uint16_t*>(raw.data());

    if (spp == 1) {
        py::array_t<uint16_t> arr({static_cast<py::ssize_t>(height),
                                    static_cast<py::ssize_t>(width)});
        auto buf = arr.mutable_unchecked<2>();
        for (size_t i = 0; i < num_pixels; ++i) {
            buf(static_cast<py::ssize_t>(i / width),
                static_cast<py::ssize_t>(i % width)) = src[i];
        }
        return arr;
    } else {
        py::array_t<uint16_t> arr({static_cast<py::ssize_t>(height),
                                    static_cast<py::ssize_t>(width),
                                    static_cast<py::ssize_t>(spp)});
        auto buf = arr.mutable_unchecked<3>();
        for (size_t row = 0; row < height; ++row) {
            for (size_t col = 0; col < width; ++col) {
                for (uint16_t c = 0; c < spp; ++c) {
                    buf(static_cast<py::ssize_t>(row),
                        static_cast<py::ssize_t>(col),
                        static_cast<py::ssize_t>(c)) =
                        src[(row * width + col) * spp + c];
                }
            }
        }
        return arr;
    }
}

static py::dict dng_image_to_dict(const DngImage& img) {
    py::dict result;

    // --- Raw pixel data ---
    result["raw"] = pixels_to_numpy(img.raw_pixels, img.width, img.height,
                                    img.samples_per_pixel);
    result["width"] = img.width;
    result["height"] = img.height;
    result["bits_per_sample"] = img.bits_per_sample;
    result["compression"] = img.compression;
    result["photometric_interpretation"] = img.photometric_interpretation;
    result["samples_per_pixel"] = img.samples_per_pixel;
    result["is_tiled"] = img.is_tiled;
    result["tile_width"] = img.tile_width;
    result["tile_length"] = img.tile_length;

    // --- CFA ---
    result["cfa_pattern"] = py::cast(img.cfa_pattern);
    result["cfa_repeat_rows"] = img.cfa_repeat_rows;
    result["cfa_repeat_cols"] = img.cfa_repeat_cols;
    result["cfa_layout"] = img.cfa_layout;

    // --- Levels ---
    result["black_level"] = py::cast(img.black_level);
    result["white_level"] = img.white_level;
    if (!img.white_level_per_sample.empty()) {
        result["white_level_per_sample"] = py::cast(img.white_level_per_sample);
    } else {
        result["white_level_per_sample"] = py::none();
    }
    if (!img.linearization_table.empty()) {
        result["linearization_table"] = py::cast(img.linearization_table);
    } else {
        result["linearization_table"] = py::none();
    }
    result["black_level_repeat_rows"] = img.black_level_repeat_rows;
    result["black_level_repeat_cols"] = img.black_level_repeat_cols;

    // --- Color matrices ---
    result["color_matrix_1"] = matrix_to_numpy(img.color_matrix_1);
    if (img.has_color_matrix_2) {
        result["color_matrix_2"] = matrix_to_numpy(img.color_matrix_2);
    } else {
        result["color_matrix_2"] = py::none();
    }
    result["calibration_illuminant_1"] = static_cast<int>(img.calibration_illuminant_1);
    result["calibration_illuminant_2"] = static_cast<int>(img.calibration_illuminant_2);

    if (img.has_forward_matrix_1) {
        result["forward_matrix_1"] = matrix_to_numpy(img.forward_matrix_1);
    } else {
        result["forward_matrix_1"] = py::none();
    }
    if (img.has_forward_matrix_2) {
        result["forward_matrix_2"] = matrix_to_numpy(img.forward_matrix_2);
    } else {
        result["forward_matrix_2"] = py::none();
    }

    // --- White balance ---
    result["as_shot_neutral"] = py::cast(img.as_shot_neutral);

    // --- Active area & crop ---
    py::list aa;
    aa.append(img.active_area[0]);
    aa.append(img.active_area[1]);
    aa.append(img.active_area[2]);
    aa.append(img.active_area[3]);
    result["active_area"] = aa;
    result["has_active_area"] = img.has_active_area;

    py::list dco;
    dco.append(img.default_crop_origin[0]);
    dco.append(img.default_crop_origin[1]);
    result["default_crop_origin"] = dco;

    py::list dcs;
    dcs.append(img.default_crop_size[0]);
    dcs.append(img.default_crop_size[1]);
    result["default_crop_size"] = dcs;

    // --- Exposure ---
    result["baseline_exposure"] = img.baseline_exposure;
    result["iso_speed"] = img.iso_speed;
    result["exposure_time"] = img.exposure_time;
    result["f_number"] = img.f_number;
    result["focal_length"] = img.focal_length;

    // --- Noise ---
    py::dict noise;
    noise["present"] = img.noise_profile.present;
    noise["slope"] = img.noise_profile.slope;
    noise["offset"] = img.noise_profile.offset;
    result["noise_profile"] = noise;

    // --- Opcodes (raw bytes) ---
    if (!img.opcode_list_1.empty()) {
        result["opcode_list_1"] = py::bytes(reinterpret_cast<const char*>(img.opcode_list_1.data()),
                                             img.opcode_list_1.size());
    } else {
        result["opcode_list_1"] = py::none();
    }
    if (!img.opcode_list_2.empty()) {
        result["opcode_list_2"] = py::bytes(reinterpret_cast<const char*>(img.opcode_list_2.data()),
                                             img.opcode_list_2.size());
    } else {
        result["opcode_list_2"] = py::none();
    }
    if (!img.opcode_list_3.empty()) {
        result["opcode_list_3"] = py::bytes(reinterpret_cast<const char*>(img.opcode_list_3.data()),
                                             img.opcode_list_3.size());
    } else {
        result["opcode_list_3"] = py::none();
    }

    // --- Camera info ---
    result["make"] = img.make;
    result["model"] = img.model;
    result["unique_camera_model"] = img.unique_camera_model;
    result["serial_number"] = img.serial_number;

    // --- DNG version ---
    py::list ver;
    for (int i = 0; i < 4; ++i) ver.append(img.dng_version[i]);
    result["dng_version"] = ver;

    return result;
}

PYBIND11_MODULE(_dng, m) {
    m.doc() = "DNG parser for next-isp project (multi-vendor: DJI, Apple ProRAW)";

    m.def("load_dng", [](const std::string& path) {
        DngImage img = DngParser::parse(path);
        return dng_image_to_dict(img);
    }, py::arg("path"),
    "Parse a DNG file and return a dict of metadata + raw pixel array.\n\n"
    "Args:\n"
    "    path: Path to the .dng file.\n\n"
    "Returns:\n"
    "    dict with keys: raw (HxW uint16), width, height, bits_per_sample,\n"
    "    compression, cfa_pattern, black_level, white_level, color_matrix_1/2,\n"
    "    as_shot_neutral, active_area, noise_profile, exposure metadata, etc.");

    m.def("load_dng_raw_only", [](const std::string& path) {
        DngImage img = DngParser::parse(path);
        return pixels_to_numpy(img.raw_pixels, img.width, img.height,
                                img.samples_per_pixel);
    }, py::arg("path"),
    "Parse a DNG file and return only the raw pixel array.\n"
    "For CFA data: (H, W) uint16.\n"
    "For LinearRaw data: (H, W, C) uint16.");

    m.attr("__version__") = "0.1.0";
}

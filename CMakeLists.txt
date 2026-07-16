cmake_minimum_required(VERSION 3.18)
project(_dng LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

# --- pybind11 (from pip install in the build environment) --------------------
set(CMAKE_POLICY_DEFAULT_CMP0148 OLD)
find_package(pybind11 CONFIG REQUIRED)

# --- Sources ----------------------------------------------------------------
set(DNG_SOURCES
    cpp/src/tiff_reader.cpp
    cpp/src/dng_parser.cpp
    cpp/src/ljpeg_decoder.cpp
)

pybind11_add_module(_dng cpp/binding/pybind_module.cpp ${DNG_SOURCES})

target_include_directories(_dng PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/cpp/include
)

target_compile_features(_dng PRIVATE cxx_std_17)

if(MSVC)
    target_compile_options(_dng PRIVATE /W4 /utf-8 /wd4127)
else()
    target_compile_options(_dng PRIVATE -Wall -Wextra -Wpedantic)
endif()

# --- Generate type stubs after compilation -----------------------------------
# Runs pybind11-stubgen on the built .pyd, producing _dng.pyi next to the
# Python package sources so that install(DIRECTORY) picks it up automatically.
# Made optional: if pybind11_stubgen is not installed, the build still succeeds.
execute_process(
    COMMAND ${PYTHON_EXECUTABLE} -c "import pybind11_stubgen"
    RESULT_VARIABLE STUBGEN_AVAILABLE
    OUTPUT_QUIET ERROR_QUIET
)
if(STUBGEN_AVAILABLE EQUAL 0)
    add_custom_command(TARGET _dng POST_BUILD
        COMMAND ${PYTHON_EXECUTABLE} -m pybind11_stubgen _dng
            --output-dir ${CMAKE_CURRENT_SOURCE_DIR}/python/dngparser
        WORKING_DIRECTORY $<TARGET_FILE_DIR:_dng>
        COMMENT "Generating type stubs for _dng"
        VERBATIM
    )
else()
    message(STATUS "pybind11_stubgen not found, skipping type stub generation")
endif()

# --- Install rules (scikit-build-core) ---------------------------------------
if(DEFINED SKBUILD_PLATLIB_DIR)
    install(TARGETS _dng LIBRARY DESTINATION dngparser)
    install(DIRECTORY python/dngparser/
            DESTINATION dngparser
            FILES_MATCHING
              PATTERN "*.py"
              PATTERN "*.pyi"
            PATTERN "__pycache__" EXCLUDE)
else()
    install(TARGETS _dng
            LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/python/dngparser
            RUNTIME DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/python/dngparser)
endif()

cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(TumorLensAI)

find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

set(EXTENSION_HOMEPAGE "https://github.com/example/TumorLensAI")
set(EXTENSION_CATEGORY "Segmentation")
set(EXTENSION_CONTRIBUTORS "Tarun")
set(EXTENSION_DESCRIPTION "AI-assisted brain tumor MRI segmentation, 3D reconstruction, and quantitative analysis for research and education workflows.")
set(EXTENSION_ICONURL "")
set(EXTENSION_SCREENSHOTURLS "")
set(EXTENSION_DEPENDS "NA")

add_subdirectory(TumorLensAI)

include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})


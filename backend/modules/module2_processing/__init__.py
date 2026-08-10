"""
Module 2: Image Processing — Package Init
IEEE M.Tech Project
"""

from backend.modules.module2_processing.processor       import (
    process_single_image, process_levir_pair, process_batch,
    compute_difference_map, detect_edges, compute_lbp,
    apply_gabor_bank, extract_color_spaces,
)
from backend.modules.module2_processing.levir_loader    import (
    scan_levir_dataset, get_preview_pairs, load_pair,
)
from backend.modules.module2_processing.roboflow_loader import (
    scan_roboflow_dataset, compute_class_distribution, get_images_paginated,
)

__all__ = [
    "process_single_image", "process_levir_pair", "process_batch",
    "compute_difference_map", "detect_edges", "compute_lbp",
    "apply_gabor_bank", "extract_color_spaces",
    "scan_levir_dataset", "get_preview_pairs", "load_pair",
    "scan_roboflow_dataset", "compute_class_distribution", "get_images_paginated",
]

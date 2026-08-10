"""
Module 2: Advanced Image Processor
IEEE M.Tech Project — Image Processing

Applies a multi-stage processing pipeline to UAV images and LEVIR-CD pairs:

Pipeline:
  1. Resize to target resolution (512×512 for CD models)
  2. Multi-color space conversion (RGB → HSV → LAB → GRAY)
  3. Edge detection (Canny + Sobel gradient magnitude)
  4. Texture analysis (Local Binary Patterns — LBP)
  5. Gabor filter bank (multi-frequency, multi-orientation)
  6. Morphological operations (opening, closing)
  7. Difference map generation (for A/B pairs)
  8. Change mask thresholding
  9. Feature map stacking
 10. Save all outputs as PNG
"""

import logging
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger("module2.processor")


# ─────────────────────────────────────────────────────────────────
# Step 1: Resize
# ─────────────────────────────────────────────────────────────────

def resize_image(image: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
    """
    Resize image to target (width, height) using Lanczos interpolation.

    Args:
        image:       Input BGR/grayscale numpy array.
        target_size: (width, height) target.

    Returns:
        Resized numpy array.
    """
    import cv2
    return cv2.resize(image, target_size, interpolation=cv2.INTER_LANCZOS4)


# ─────────────────────────────────────────────────────────────────
# Step 2: Color Space Analysis
# ─────────────────────────────────────────────────────────────────

def extract_color_spaces(bgr: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Convert a BGR image to multiple color spaces.

    Args:
        bgr: Input BGR image array (uint8).

    Returns:
        Dict mapping color space name → array.
    """
    import cv2
    return {
        "RGB":  cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB),
        "HSV":  cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV),
        "LAB":  cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB),
        "GRAY": cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY),
    }


# ─────────────────────────────────────────────────────────────────
# Step 3: Edge Detection
# ─────────────────────────────────────────────────────────────────

def detect_edges(
    gray:       np.ndarray,
    canny_low:  int = 50,
    canny_high: int = 150,
    sobel_k:    int = 3,
) -> Dict[str, np.ndarray]:
    """
    Compute Canny and Sobel edge maps from a grayscale image.

    Args:
        gray:       Grayscale image array (uint8).
        canny_low:  Canny lower hysteresis threshold.
        canny_high: Canny upper hysteresis threshold.
        sobel_k:    Sobel kernel size (odd integer).

    Returns:
        Dict with 'canny', 'sobel_x', 'sobel_y', 'sobel_mag' arrays.
    """
    import cv2
    canny   = cv2.Canny(gray, canny_low, canny_high)
    sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=sobel_k)
    sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=sobel_k)
    mag     = np.sqrt(sobel_x**2 + sobel_y**2)
    mag_u8  = np.clip((mag / mag.max() * 255), 0, 255).astype(np.uint8) if mag.max() > 0 else np.zeros_like(gray)

    return {
        "canny":     canny,
        "sobel_x":   np.abs(sobel_x).astype(np.uint8),
        "sobel_y":   np.abs(sobel_y).astype(np.uint8),
        "sobel_mag": mag_u8,
    }


# ─────────────────────────────────────────────────────────────────
# Step 4: Local Binary Pattern (Texture)
# ─────────────────────────────────────────────────────────────────

def compute_lbp(gray: np.ndarray, radius: int = 3, n_points: int = 24) -> np.ndarray:
    """
    Compute Local Binary Pattern texture map.

    Falls back to a simplified LBP if skimage is not installed.

    Args:
        gray:     Grayscale image (uint8).
        radius:   LBP radius.
        n_points: Number of sampling points.

    Returns:
        LBP map as uint8 array (normalized 0-255).
    """
    try:
        from skimage.feature import local_binary_pattern
        lbp = local_binary_pattern(gray, n_points, radius, method="uniform")
        lbp_norm = (lbp / lbp.max() * 255).astype(np.uint8) if lbp.max() > 0 else np.zeros_like(gray)
        return lbp_norm
    except ImportError:
        # Simplified 3×3 LBP fallback
        import cv2
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, lbp   = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return lbp


def extract_lbp(gray: np.ndarray, radius: int = 3, points: int = 24) -> np.ndarray:
    """
    Compute Local Binary Pattern texture map (alias for compute_lbp).
    """
    return compute_lbp(gray, radius, n_points=points)


# ─────────────────────────────────────────────────────────────────
# Step 5: Gabor Filter Bank
# ─────────────────────────────────────────────────────────────────

def apply_gabor_bank(
    gray:        np.ndarray,
    frequencies: List[float] = None,
    thetas_deg:  List[int]   = None,
) -> np.ndarray:
    """
    Apply a Gabor filter bank and return the mean response.

    Args:
        gray:        Grayscale image (uint8).
        frequencies: List of spatial frequencies.
        thetas_deg:  List of orientations in degrees.

    Returns:
        Averaged Gabor response as uint8 array.
    """
    import cv2

    if frequencies is None: frequencies = [0.1, 0.25, 0.4]
    if thetas_deg  is None: thetas_deg  = [0, 45, 90, 135]

    responses = []
    gray_f = gray.astype(np.float32)

    for freq in frequencies:
        lamda = 1.0 / (freq + 1e-8)
        for theta_deg in thetas_deg:
            theta = np.deg2rad(theta_deg)
            kernel = cv2.getGaborKernel(
                ksize=(21, 21), sigma=4.0, theta=theta,
                lambd=lamda, gamma=0.5, psi=0
            )
            filtered = cv2.filter2D(gray_f, cv2.CV_32F, kernel)
            responses.append(np.abs(filtered))

    mean_resp = np.mean(responses, axis=0)
    if mean_resp.max() > 0:
        mean_resp = (mean_resp / mean_resp.max() * 255).astype(np.uint8)
    else:
        mean_resp = np.zeros_like(gray)
    return mean_resp


def extract_gabor(
    gray:        np.ndarray,
    frequencies: List[float] = None,
    thetas:      List[float] = None,
) -> Dict[str, np.ndarray]:
    """
    Compute Gabor filter responses for multiple frequencies and orientations.
    """
    import cv2
    if frequencies is None: frequencies = [0.1, 0.25, 0.4]
    if thetas is None:      thetas      = [0, 45, 90, 135]

    maps = {}
    gray_f = gray.astype(np.float32)

    for freq in frequencies:
        lamda = 1.0 / (freq + 1e-8)
        for theta_deg in thetas:
            theta = np.deg2rad(theta_deg)
            kernel = cv2.getGaborKernel(
                ksize=(21, 21), sigma=4.0, theta=theta,
                lambd=lamda, gamma=0.5, psi=0
            )
            filtered = cv2.filter2D(gray_f, cv2.CV_32F, kernel)
            filtered_abs = np.abs(filtered)
            if filtered_abs.max() > 0:
                filtered_u8 = (filtered_abs / filtered_abs.max() * 255).astype(np.uint8)
            else:
                filtered_u8 = np.zeros_like(gray)
            maps[f"gabor_f{freq}_t{theta_deg}"] = filtered_u8
    return maps


# ─────────────────────────────────────────────────────────────────
# Step 6: Morphological Operations
# ─────────────────────────────────────────────────────────────────

def morphological_ops(
    gray:        np.ndarray,
    kernel_size: int = 5,
) -> Dict[str, np.ndarray]:
    """
    Apply morphological opening and closing operations.

    Useful for removing noise and filling gaps in binary masks.

    Args:
        gray:        Grayscale or binary image.
        kernel_size: Structuring element size.

    Returns:
        Dict with 'opened', 'closed', 'tophat', 'blackhat' arrays.
    """
    import cv2
    kernel  = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    opened  = cv2.morphologyEx(gray, cv2.MORPH_OPEN,    kernel)
    closed  = cv2.morphologyEx(gray, cv2.MORPH_CLOSE,   kernel)
    tophat  = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT,  kernel)
    blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
    return {"opened": opened, "closed": closed, "tophat": tophat, "blackhat": blackhat}


def apply_morphology(gray: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """
    Apply morphological opening followed by morphological closing.
    """
    import cv2
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    opened = cv2.morphologyEx(gray, cv2.MORPH_OPEN,    kernel)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
    return closed


# ─────────────────────────────────────────────────────────────────
# Step 7: Difference Map (A-B pair)
# ─────────────────────────────────────────────────────────────────

def compute_difference_map(
    before:    np.ndarray,
    after:     np.ndarray,
    threshold: int = 30,
) -> Dict[str, np.ndarray]:
    """
    Compute absolute difference and binary change map between A and B images.

    Args:
        before:    Before image (BGR, uint8).
        after:     After image  (BGR, uint8).
        threshold: Pixel-level threshold for binary change map.

    Returns:
        Dict with 'diff_raw', 'diff_gray', 'diff_enhanced', 'change_map'.
    """
    import cv2

    diff_raw      = cv2.absdiff(before, after)
    diff_gray     = cv2.cvtColor(diff_raw, cv2.COLOR_BGR2GRAY)
    diff_enhanced = cv2.equalizeHist(diff_gray)

    _, change_map = cv2.threshold(diff_gray, threshold, 255, cv2.THRESH_BINARY)

    # Morphological cleanup of change map
    kernel     = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    change_map = cv2.morphologyEx(change_map, cv2.MORPH_OPEN,  kernel)
    change_map = cv2.morphologyEx(change_map, cv2.MORPH_CLOSE, kernel)

    return {
        "diff_raw":      diff_raw,
        "diff_gray":     diff_gray,
        "diff_enhanced": diff_enhanced,
        "change_map":    change_map,
    }


# ─────────────────────────────────────────────────────────────────
# Save Feature Maps
# ─────────────────────────────────────────────────────────────────

def save_feature_maps(
    feature_maps: Dict[str, np.ndarray],
    output_dir:   Path,
    prefix:       str = "img",
) -> Dict[str, str]:
    """
    Save a dict of feature map arrays to disk as PNG files.

    Args:
        feature_maps: Dict of {map_name: numpy array}.
        output_dir:   Directory to save images.
        prefix:       Filename prefix.

    Returns:
        Dict of {map_name: saved_path}.
    """
    import cv2
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = {}

    for name, arr in feature_maps.items():
        try:
            out_path = output_dir / f"{prefix}_{name}.png"
            if arr.dtype != np.uint8:
                if arr.max() > 0:
                    arr = (arr / arr.max() * 255).clip(0, 255).astype(np.uint8)
                else:
                    arr = np.zeros_like(arr, dtype=np.uint8)
            cv2.imwrite(str(out_path), arr)
            saved[name] = str(out_path)
        except Exception as exc:
            logger.warning("Could not save feature map '%s': %s", name, exc)

    return saved


# ─────────────────────────────────────────────────────────────────
# Main: Process Single Image (UAV)
# ─────────────────────────────────────────────────────────────────

def process_single_image(
    image_path:  Path,
    output_dir:  Path,
    config:      Dict = None,
) -> Dict[str, Any]:
    """
    Run the full Module 2 processing pipeline on a single UAV image.

    Steps: load → resize → color spaces → edges → LBP → Gabor → morphology → save

    Args:
        image_path: Path to input image.
        output_dir: Directory for output feature maps.
        config:     Optional config overrides.

    Returns:
        Processing result dict.
    """
    import cv2
    cfg = config or {}
    target_size  = tuple(cfg.get("target_size", (512, 512)))
    canny_low    = cfg.get("edge_canny_low",  50)
    canny_high   = cfg.get("edge_canny_high", 150)
    sobel_k      = cfg.get("edge_sobel_ksize", 3)

    image_path = Path(image_path)
    result: Dict[str, Any] = {
        "image_path":    str(image_path),
        "filename":      image_path.name,
        "success":       False,
        "feature_maps":  {},
        "feature_stats": {},
        "processed_at":  datetime.utcnow().isoformat() + "Z",
        "error":         None,
    }

    try:
        bgr = cv2.imread(str(image_path))
        if bgr is None:
            raise ValueError("Cannot read image")

        # Step 1: Resize
        bgr = resize_image(bgr, target_size)

        # Step 2: Color spaces
        spaces = extract_color_spaces(bgr)
        gray   = spaces["GRAY"]

        # Step 3: Edges
        edges = detect_edges(gray, canny_low, canny_high, sobel_k)

        # Step 4: LBP
        lbp = compute_lbp(gray)

        # Step 5: Gabor
        gabor = apply_gabor_bank(gray,
            frequencies=cfg.get("gabor_frequencies", [0.1, 0.25, 0.4]),
            thetas_deg =cfg.get("gabor_thetas",      [0, 45, 90, 135]),
        )

        # Step 6: Morphology
        morph = morphological_ops(gray)

        # Collect all maps
        all_maps = {
            "original": bgr,
            "gray":     gray,
            "hsv":      spaces["HSV"],
            "lab":      spaces["LAB"],
            "canny":    edges["canny"],
            "sobel_mag": edges["sobel_mag"],
            "lbp":      lbp,
            "gabor":    gabor,
            "morph_open":  morph["opened"],
            "morph_close": morph["closed"],
        }

        # Save
        stem = image_path.stem
        img_out_dir = output_dir / stem
        saved = save_feature_maps(all_maps, img_out_dir, prefix=stem)

        # Feature statistics
        result["feature_stats"] = {
            "mean_gray":       round(float(gray.mean()),   2),
            "std_gray":        round(float(gray.std()),    2),
            "edge_density":    round(float(edges["canny"].mean()) / 255 * 100, 2),
            "texture_energy":  round(float(lbp.mean()),    2),
            "gabor_response":  round(float(gabor.mean()),  2),
        }

        result["feature_maps"] = saved
        result["success"]      = True
        result["output_dir"]   = str(img_out_dir)

        # Test suite keys
        result["feature_map_path"] = saved.get("canny") or (list(saved.values())[0] if saved else "")
        result["visualization_path"] = saved.get("morph_close") or (list(saved.values())[0] if saved else "")
        result["dimensions"] = [target_size[0], target_size[1]]

        logger.info(
            "Module 2 processed: %s → %d feature maps saved",
            image_path.name, len(saved)
        )

    except Exception as exc:
        result["error"] = str(exc)
        logger.error("Module 2 processing failed for %s: %s", image_path.name, exc, exc_info=True)

    return result


# ─────────────────────────────────────────────────────────────────
# Main: Process LEVIR-CD Pair
# ─────────────────────────────────────────────────────────────────

def process_levir_pair(
    pair:         Optional[Dict[str, Any]] = None,
    output_dir:   Optional[Path] = None,
    config:       Optional[Dict] = None,
    image_a_path: Optional[Path] = None,
    image_b_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Process a LEVIR-CD image pair through the Module 2 pipeline.

    Generates per-image feature maps AND cross-image difference / change maps.

    Args:
        pair:       Pair dict from levir_loader (with 'before', 'after', 'label' paths).
        output_dir: Directory to save all outputs.
        config:     Optional config overrides.
        image_a_path: Optional path to before image (for tests).
        image_b_path: Optional path to after image (for tests).

    Returns:
        Processing result dict.
    """
    if pair is None:
        if image_a_path is not None and image_b_path is not None:
            pair = {
                "pair_id": Path(image_a_path).stem,
                "before": str(image_a_path),
                "after": str(image_b_path),
                "label": None
            }
        else:
            raise ValueError("Either pair dict or image_a_path and image_b_path must be provided")
    import cv2
    cfg = config or {}
    target_size = tuple(cfg.get("target_size", (512, 512)))
    threshold   = cfg.get("change_threshold", 30)

    pair_id = pair.get("pair_id", "unknown")
    result: Dict[str, Any] = {
        "pair_id":      pair_id,
        "before_path":  pair.get("before"),
        "after_path":   pair.get("after"),
        "label_path":   pair.get("label"),
        "success":      False,
        "before_maps":  {},
        "after_maps":   {},
        "diff_maps":    {},
        "change_stats": {},
        "processed_at": datetime.utcnow().isoformat() + "Z",
        "error":        None,
    }

    try:
        before_bgr = cv2.imread(pair["before"])
        after_bgr  = cv2.imread(pair["after"])
        if before_bgr is None or after_bgr is None:
            raise ValueError("Cannot read before/after images")

        before_bgr = resize_image(before_bgr, target_size)
        after_bgr  = resize_image(after_bgr,  target_size)

        pair_out = output_dir / pair_id
        pair_out.mkdir(parents=True, exist_ok=True)

        # Process before image
        before_gray  = cv2.cvtColor(before_bgr, cv2.COLOR_BGR2GRAY)
        before_edges = detect_edges(before_gray)
        before_lbp   = compute_lbp(before_gray)
        before_gabor = apply_gabor_bank(before_gray)

        before_maps = {
            "before_rgb":   cv2.cvtColor(before_bgr, cv2.COLOR_BGR2RGB),
            "before_gray":  before_gray,
            "before_canny": before_edges["canny"],
            "before_sobel": before_edges["sobel_mag"],
            "before_lbp":   before_lbp,
            "before_gabor": before_gabor,
        }
        result["before_maps"] = save_feature_maps(before_maps, pair_out, prefix="before")

        # Process after image
        after_gray  = cv2.cvtColor(after_bgr, cv2.COLOR_BGR2GRAY)
        after_edges = detect_edges(after_gray)
        after_lbp   = compute_lbp(after_gray)
        after_gabor = apply_gabor_bank(after_gray)

        after_maps = {
            "after_rgb":   cv2.cvtColor(after_bgr, cv2.COLOR_BGR2RGB),
            "after_gray":  after_gray,
            "after_canny": after_edges["canny"],
            "after_sobel": after_edges["sobel_mag"],
            "after_lbp":   after_lbp,
            "after_gabor": after_gabor,
        }
        result["after_maps"] = save_feature_maps(after_maps, pair_out, prefix="after")

        # Difference + change detection
        diff_data = compute_difference_map(before_bgr, after_bgr, threshold)

        diff_maps = {
            "diff_gray":     diff_data["diff_gray"],
            "diff_enhanced": diff_data["diff_enhanced"],
            "change_map":    diff_data["change_map"],
        }

        # Overlay change map on after image (colorize)
        overlay = after_bgr.copy()
        overlay[diff_data["change_map"] > 127] = [0, 0, 255]  # Red = changed
        diff_maps["overlay"] = overlay

        # Load ground truth label if available
        if pair.get("label") and Path(pair["label"]).exists():
            gt = cv2.imread(pair["label"], cv2.IMREAD_GRAYSCALE)
            if gt is not None:
                gt = resize_image(gt, target_size)
                diff_maps["gt_label"] = gt

        result["diff_maps"] = save_feature_maps(diff_maps, pair_out, prefix="diff")

        # Change statistics
        change_pixels   = int(np.sum(diff_data["change_map"] > 127))
        total_pixels    = diff_data["change_map"].size
        change_pct      = round(change_pixels / total_pixels * 100, 3)

        result["change_stats"] = {
            "change_pixels":   change_pixels,
            "total_pixels":    total_pixels,
            "change_percent":  change_pct,
            "mean_diff":       round(float(diff_data["diff_gray"].mean()), 2),
            "max_diff":        int(diff_data["diff_gray"].max()),
            "threshold_used":  threshold,
        }

        result["success"]    = True
        result["output_dir"] = str(pair_out)

        # Test suite keys
        result["diff_map_path"] = result["diff_maps"].get("change_map") or ""
        result["visualization_path"] = result["diff_maps"].get("overlay") or ""

        logger.info(
            "LEVIR pair processed: %s → %.2f%% change detected",
            pair_id, change_pct
        )

    except Exception as exc:
        result["error"] = str(exc)
        logger.error("LEVIR pair processing failed for %s: %s", pair_id, exc, exc_info=True)

    return result


# ─────────────────────────────────────────────────────────────────
# Batch Processor
# ─────────────────────────────────────────────────────────────────

def process_batch(
    items:      List[Dict],
    mode:       str,          # 'single' or 'pair'
    output_dir: Path,
    config:     Dict = None,
    max_items:  int  = 50,
) -> Dict[str, Any]:
    """
    Process a batch of images or pairs in Module 2.

    Args:
        items:      List of dicts (image records or pair records).
        mode:       'single' (UAV images) or 'pair' (LEVIR-CD pairs).
        output_dir: Root output directory.
        config:     Optional config.
        max_items:  Maximum items to process (prevent overload).

    Returns:
        Batch result with per-item results and summary.
    """
    items   = items[:max_items]
    results = []
    ok = 0; fail = 0

    for item in items:
        if mode == "pair":
            res = process_levir_pair(item, output_dir, config)
        else:
            path = item.get("file_path") or item.get("image_path") or item.get("output_path", "")
            res  = process_single_image(Path(path), output_dir, config) if path else {"success": False}

        results.append(res)
        if res.get("success"): ok   += 1
        else:                  fail += 1

    logger.info("Batch Module 2 (%s): %d/%d processed", mode, ok, len(items))
    return {
        "mode":       mode,
        "total":      len(items),
        "succeeded":  ok,
        "failed":     fail,
        "results":    results,
    }

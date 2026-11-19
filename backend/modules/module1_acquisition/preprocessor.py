"""
Module 1: Image Preprocessor
Final Year Project — UAV Image Acquisition

Preprocessing pipeline:
  1. Resize to target dimensions (maintain aspect ratio with padding)
  2. CLAHE histogram equalization (contrast enhancement)
  3. Gaussian noise removal
  4. Normalization (0-1 float array)
  5. Save processed image (PNG lossless — never overwrite original)
"""

import logging
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger("module1.preprocessor")

# ─────────────────────────────────────────────────────────────────
# Default Parameters
# ─────────────────────────────────────────────────────────────────
TARGET_SIZE      = (1024, 1024)   # (width, height)
CLAHE_CLIP       = 2.0
CLAHE_TILE       = (8, 8)
GAUSSIAN_KERNEL  = (3, 3)
GAUSSIAN_SIGMA   = 0
PAD_COLOR        = (0, 0, 0)      # Black
OUTPUT_FORMAT    = "PNG"


# ─────────────────────────────────────────────────────────────────
# Step 1: Aspect-Ratio-Preserving Resize with Padding
# ─────────────────────────────────────────────────────────────────

def resize_with_padding(
    image: np.ndarray,
    target_size: Tuple[int, int] = TARGET_SIZE,
    pad_color:   Tuple[int, int, int] = PAD_COLOR,
) -> np.ndarray:
    """
    Resize image to target_size while maintaining aspect ratio.
    Pads the shorter dimension with pad_color.

    Args:
        image:       Input BGR image as numpy array.
        target_size: (width, height) target dimensions.
        pad_color:   BGR color for padding (default black).

    Returns:
        Padded/resized image as numpy array (uint8).
    """
    import cv2

    target_w, target_h = target_size
    h, w = image.shape[:2]

    scale = min(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)

    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    # Create canvas and paste centered
    canvas = np.full((target_h, target_w, 3), pad_color, dtype=np.uint8)
    x_off  = (target_w - new_w) // 2
    y_off  = (target_h - new_h) // 2
    canvas[y_off:y_off + new_h, x_off:x_off + new_w] = resized

    return canvas


# ─────────────────────────────────────────────────────────────────
# Step 2: CLAHE Histogram Equalization
# ─────────────────────────────────────────────────────────────────

def apply_clahe(
    image:     np.ndarray,
    clip_limit: float = CLAHE_CLIP,
    tile_grid:  Tuple[int, int] = CLAHE_TILE,
) -> np.ndarray:
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to a BGR image.
    Operates on the L-channel in LAB color space to preserve hue/saturation.

    Args:
        image:      BGR image array.
        clip_limit: CLAHE clipping limit.
        tile_grid:  Tile grid size for adaptive equalization.

    Returns:
        Equalized BGR image array.
    """
    import cv2

    lab   = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid)
    l_eq  = clahe.apply(l)

    lab_eq = cv2.merge([l_eq, a, b])
    return cv2.cvtColor(lab_eq, cv2.COLOR_LAB2BGR)


# ─────────────────────────────────────────────────────────────────
# Step 3: Gaussian Noise Removal
# ─────────────────────────────────────────────────────────────────

def remove_noise(
    image:         np.ndarray,
    kernel_size:   Tuple[int, int] = GAUSSIAN_KERNEL,
    sigma:         int = GAUSSIAN_SIGMA,
) -> np.ndarray:
    """
    Apply Gaussian blur for noise reduction.

    Args:
        image:       BGR image array.
        kernel_size: Gaussian kernel size (odd numbers).
        sigma:       Standard deviation (0 = auto-computed from kernel).

    Returns:
        Denoised BGR image array.
    """
    import cv2
    return cv2.GaussianBlur(image, kernel_size, sigma)


# ─────────────────────────────────────────────────────────────────
# Step 4: Normalization
# ─────────────────────────────────────────────────────────────────

def normalize_image(image: np.ndarray) -> np.ndarray:
    """
    Normalize pixel values from [0, 255] to [0.0, 1.0] float32.

    Args:
        image: uint8 image array.

    Returns:
        float32 image array in range [0, 1].
    """
    return (image.astype(np.float32) / 255.0)


# ─────────────────────────────────────────────────────────────────
# Save Processed Image
# ─────────────────────────────────────────────────────────────────

def save_processed_image(
    image:       np.ndarray,
    output_path: Path,
    is_float:    bool = False,
) -> Path:
    """
    Save processed image to disk in PNG format (lossless).
    Converts float32 images back to uint8 before saving.

    Args:
        image:       Image array (uint8 or float32).
        output_path: Destination file path.
        is_float:    True if image is float32 (0-1 range).

    Returns:
        Path where image was saved.
    """
    import cv2

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if is_float:
        save_img = (image * 255.0).clip(0, 255).astype(np.uint8)
    else:
        save_img = image.astype(np.uint8)

    # Force .png extension
    output_path = output_path.with_suffix(".png")
    cv2.imwrite(str(output_path), save_img)
    return output_path


# ─────────────────────────────────────────────────────────────────
# Main Preprocessing Pipeline
# ─────────────────────────────────────────────────────────────────

def preprocess_image(
    input_path:   Path,
    output_dir:   Path,
    target_size:  Tuple[int, int] = TARGET_SIZE,
    clahe_clip:   float = CLAHE_CLIP,
    clahe_tile:   Tuple[int, int] = CLAHE_TILE,
    gauss_kernel: Tuple[int, int] = GAUSSIAN_KERNEL,
    gauss_sigma:  int = GAUSSIAN_SIGMA,
    normalize:    bool = True,
    pad_color:    Tuple[int, int, int] = PAD_COLOR,
) -> Dict[str, Any]:
    """
    Run the complete preprocessing pipeline on a single UAV image.

    Pipeline:
        Load → Resize (pad) → CLAHE → Denoise → Normalize → Save

    IMPORTANT: The original file is NEVER modified.

    Args:
        input_path:   Path to original UAV image.
        output_dir:   Directory to save processed image.
        target_size:  Target (width, height).
        clahe_clip:   CLAHE clip limit.
        clahe_tile:   CLAHE tile grid.
        gauss_kernel: Gaussian kernel size.
        gauss_sigma:  Gaussian sigma.
        normalize:    Whether to normalize to float32 [0,1].
        pad_color:    Padding color (BGR).

    Returns:
        Preprocessing result dictionary with status and output path.
    """
    import cv2

    input_path = Path(input_path)
    output_dir = Path(output_dir)
    result: Dict[str, Any] = {
        "filename":      input_path.name,
        "input_path":    str(input_path),
        "output_path":   None,
        "success":       False,
        "steps_applied": [],
        "original_size": None,
        "processed_size": None,
        "error":         None,
        "processed_at":  datetime.now(timezone.utc).isoformat(),
    }

    try:
        # ── Load ────────────────────────────────────────────────
        img = cv2.imread(str(input_path))
        if img is None:
            from PIL import Image
            with Image.open(input_path) as pil_img:
                pil_img = pil_img.convert("RGB")
                img = np.array(pil_img)[:, :, ::-1].copy()

        if img is None:
            raise ValueError("Could not load image with OpenCV or Pillow")

        orig_h, orig_w = img.shape[:2]
        result["original_size"] = {"width": orig_w, "height": orig_h}
        logger.info("Preprocessing: %s (%dx%d)", input_path.name, orig_w, orig_h)

        # ── Step 1: Resize with padding ─────────────────────────
        img = resize_with_padding(img, target_size=target_size, pad_color=pad_color)
        result["steps_applied"].append("resize_with_padding")
        logger.debug("Step 1 complete: resize to %dx%d", *target_size)

        # ── Step 2: CLAHE ───────────────────────────────────────
        img = apply_clahe(img, clip_limit=clahe_clip, tile_grid=clahe_tile)
        result["steps_applied"].append("clahe_equalization")
        logger.debug("Step 2 complete: CLAHE")

        # ── Step 3: Gaussian denoising ─────────────────────────
        img = remove_noise(img, kernel_size=gauss_kernel, sigma=gauss_sigma)
        result["steps_applied"].append("gaussian_denoise")
        logger.debug("Step 3 complete: Gaussian noise removal")

        # ── Step 4: Normalize ───────────────────────────────────
        if normalize:
            img_float = normalize_image(img)
            result["steps_applied"].append("normalization")
            logger.debug("Step 4 complete: normalization")
            is_float = True
        else:
            img_float = img
            is_float  = False

        # ── Step 5: Save ────────────────────────────────────────
        stem = input_path.stem
        out_path = output_dir / f"{stem}_processed.png"
        saved_path = save_processed_image(img_float, out_path, is_float=is_float)
        result["steps_applied"].append("saved_png")

        final_img = cv2.imread(str(saved_path))
        if final_img is not None:
            fh, fw = final_img.shape[:2]
            result["processed_size"] = {"width": fw, "height": fh}

        result["output_path"] = str(saved_path)
        result["success"]     = True

        logger.info(
            "Preprocessing COMPLETE: %s → %s [%s]",
            input_path.name, saved_path.name,
            ", ".join(result["steps_applied"])
        )

    except Exception as exc:
        result["error"] = str(exc)
        logger.error("Preprocessing FAILED for %s: %s", input_path.name, exc, exc_info=True)

    return result


# ─────────────────────────────────────────────────────────────────
# Batch Preprocessing
# ─────────────────────────────────────────────────────────────────

def preprocess_batch(
    file_paths: list,
    output_dir: Path,
    config:     Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Run preprocessing on a list of image files.

    Args:
        file_paths: List of Path objects.
        output_dir: Directory for processed outputs.
        config:     Optional config dict to override defaults.

    Returns:
        Batch preprocessing summary.
    """
    cfg = config or {}
    results   = []
    succeeded = 0
    failed    = 0

    for fp in file_paths:
        res = preprocess_image(
            input_path   = Path(fp),
            output_dir   = Path(output_dir),
            target_size  = tuple(cfg.get("target_size", TARGET_SIZE)),
            clahe_clip   = cfg.get("clahe_clip_limit", CLAHE_CLIP),
            clahe_tile   = tuple(cfg.get("clahe_tile_grid", CLAHE_TILE)),
            gauss_kernel = tuple(cfg.get("gaussian_kernel", GAUSSIAN_KERNEL)),
            gauss_sigma  = cfg.get("gaussian_sigma", GAUSSIAN_SIGMA),
            normalize    = cfg.get("normalize", True),
        )
        results.append(res)
        if res["success"]: succeeded += 1
        else:              failed    += 1

    logger.info("Batch preprocessing: %d succeeded, %d failed", succeeded, failed)

    return {
        "total":     len(file_paths),
        "succeeded": succeeded,
        "failed":    failed,
        "results":   results,
    }

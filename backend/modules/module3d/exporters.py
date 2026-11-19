"""
Module 3D: Exporters (PLY, OBJ, JSON)
Final Year Project — UAV Vision-Based Construction Progress Monitoring

Provides export capabilities to standard 3D point cloud & mesh formats:
  - Stanford PLY (.ply): Compatible with CloudCompare, MeshLab, Blender, AutoCAD Civil 3D.
  - Wavefront OBJ (.obj): Compatible with 3D CAD/BIM viewers and Three.js.
  - JSON Viewer Payload: Lightweight format for real-time WebGL browser visualization.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def export_point_cloud_ply(
    point_cloud: Dict[str, Any],
    output_path: Path,
    include_classification: bool = True,
) -> Path:
    """
    Export point cloud to standard ASCII Stanford PLY format with XYZ, RGB, and class label.

    Args:
        point_cloud: Dict with 'points', 'colors', 'class_ids'.
        output_path: Path to save the .ply file.
        include_classification: Whether to include the scalar class field in the header.

    Returns:
        Path to the saved .ply file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    points = point_cloud.get("points", [])
    colors = point_cloud.get("colors", [])
    class_ids = point_cloud.get("class_ids", [0] * len(points))
    num_pts = len(points)

    header = [
        "ply",
        "format ascii 1.0",
        "comment UAV Construction Digital Twin Point Cloud",
        f"element vertex {num_pts}",
        "property float x",
        "property float y",
        "property float z",
        "property uchar red",
        "property uchar green",
        "property uchar blue",
    ]
    if include_classification:
        header.append("property int classification")
    header.append("end_header\n")

    lines = ["\n".join(header)]
    for i in range(num_pts):
        p = points[i]
        c = colors[i] if i < len(colors) else [200, 200, 200]
        cid = class_ids[i] if i < len(class_ids) else 0
        if include_classification:
            lines.append(f"{p[0]:.4f} {p[1]:.4f} {p[2]:.4f} {int(c[0])} {int(c[1])} {int(c[2])} {int(cid)}")
        else:
            lines.append(f"{p[0]:.4f} {p[1]:.4f} {p[2]:.4f} {int(c[0])} {int(c[1])} {int(c[2])}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return output_path


def export_mesh_obj(
    point_cloud: Dict[str, Any],
    output_path: Path,
) -> Path:
    """
    Export 3D model vertices and structural representation to Wavefront OBJ format.

    Args:
        point_cloud: Dict with 'points', 'colors'.
        output_path: Path to save the .obj file.

    Returns:
        Path to the saved .obj file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    points = point_cloud.get("points", [])
    colors = point_cloud.get("colors", [])

    lines = [
        "# UAV Construction Digital Twin — Wavefront OBJ",
        f"# Total Vertices: {len(points)}",
        "o UAV_Site_Model",
    ]

    for i, p in enumerate(points):
        if i < len(colors):
            c = colors[i]
            # Standard OBJ vertex with RGB extension (0.0 to 1.0)
            lines.append(f"v {p[0]:.4f} {p[1]:.4f} {p[2]:.4f} {c[0]/255.0:.3f} {c[1]/255.0:.3f} {c[2]/255.0:.3f}")
        else:
            lines.append(f"v {p[0]:.4f} {p[1]:.4f} {p[2]:.4f}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return output_path


def export_viewer_json(
    point_cloud: Dict[str, Any],
    output_path: Path,
) -> Path:
    """
    Export optimized 3D JSON payload for high-performance Three.js WebGL rendering.

    Args:
        point_cloud: Point cloud dictionary.
        output_path: Path to save the .json file.

    Returns:
        Path to the saved .json file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Flatten coordinates and normalized colors for direct WebGL BufferAttribute consumption
    pts = point_cloud.get("points", [])
    cols = point_cloud.get("colors", [])
    
    flat_positions = []
    flat_colors = []
    
    for i in range(len(pts)):
        flat_positions.extend(pts[i])
        if i < len(cols):
            flat_colors.extend([cols[i][0] / 255.0, cols[i][1] / 255.0, cols[i][2] / 255.0])
        else:
            flat_colors.extend([0.8, 0.8, 0.8])

    payload = {
        "num_points": len(pts),
        "positions": flat_positions,
        "colors": flat_colors,
        "classes": point_cloud.get("classes", []),
        "class_breakdown": point_cloud.get("class_breakdown", {}),
        "bounds": point_cloud.get("bounds", {}),
        "progress_level": point_cloud.get("progress_level", 0.5),
        "generated_at": point_cloud.get("generated_at", ""),
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)

    return output_path

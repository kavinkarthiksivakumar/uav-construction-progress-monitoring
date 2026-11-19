"""
Module 3D: UAV Construction 3D Reconstruction, Registration & Digital Twin Engine
Final Year Project — Explainable Vision-Based Construction Progress Assessment

Exports:
  - generate_site_point_cloud
  - register_point_clouds_icp
  - compute_volumetric_progress
  - export_point_cloud_ply
  - export_mesh_obj
  - export_viewer_json
  - build_complete_3d_project_package
  - STRUCTURAL_CLASSES
"""

from backend.modules.module3d.reconstruction import (
    generate_site_point_cloud,
    register_point_clouds_icp,
    compute_volumetric_progress,
    STRUCTURAL_CLASSES,
)
from backend.modules.module3d.exporters import (
    export_point_cloud_ply,
    export_mesh_obj,
    export_viewer_json,
)
from backend.modules.module3d.viewer_data import (
    generate_uav_flight_trajectory,
    build_elevation_colors,
    build_bitemporal_3d_diff,
    build_complete_3d_project_package,
)

__all__ = [
    "generate_site_point_cloud",
    "register_point_clouds_icp",
    "compute_volumetric_progress",
    "export_point_cloud_ply",
    "export_mesh_obj",
    "export_viewer_json",
    "generate_uav_flight_trajectory",
    "build_elevation_colors",
    "build_bitemporal_3d_diff",
    "build_complete_3d_project_package",
    "STRUCTURAL_CLASSES",
]

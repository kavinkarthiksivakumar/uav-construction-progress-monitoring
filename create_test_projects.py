"""
Create Test Projects Script
Final Year Project — UAV Construction Progress Assessment

This script programmatically sets up 5 different test projects with realistic data
from the LEVIR-CD and Roboflow datasets. It copy-pastes sample images to project
raw directories, runs preprocessing/quality assessment, and saves the configuration
to metadata/projects.json.

To run:
    python create_test_projects.py
"""

import os
import sys
import json
import uuid
import shutil
from pathlib import Path
from datetime import datetime

# Path setup
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.settings import (
    METADATA_DIR, UPLOADS_DIR, PROCESSED_DIR, LEVIR_CD_ROOT, ROBOFLOW_ROOT,
    ensure_directories
)
from backend.modules.module1_acquisition.preprocessor import preprocess_image
from backend.modules.module1_acquisition.quality import assess_quality
from backend.modules.module1_acquisition.metadata import extract_metadata

PROJECTS_FILE = METADATA_DIR / "projects.json"

TEST_PROJECT_CONFIGS = [
    {
        "name": "Metro Rail Expansion (Phase 1)",
        "location": "Sector-4 Station Complex",
        "description": "Multi-temporal monitoring of metro viaduct segments, station roofing progress, and site-safety vest/helmet compliance analysis.",
        "type": "combined" # uses both Roboflow and LEVIR files
    },
    {
        "name": "Flyover Overpass Construction",
        "location": "Outer Ring Road Junction",
        "description": "Temporal progress sequencing of structural piers and safety helmet/vest compliance audits for high-elevation workers.",
        "type": "safety" # Roboflow focus
    },
    {
        "name": "Smart City IT Park Site",
        "location": "Block-C Tech Enclave",
        "description": "Detailed validation audits of PPE safety gear compliance and raw UAV imagery quality checks.",
        "type": "safety" # Roboflow focus
    },
    {
        "name": "Harbor Port Terminal Wharf",
        "location": "North Container Dockyard",
        "description": "Bi-temporal change detection over the container staging grounds and cargo dockyard expansion.",
        "type": "change" # LEVIR-CD focus
    },
    {
        "name": "Urban Residential Complex",
        "location": "Skyline Heights Towers",
        "description": "Quality assessment scans, temporal timelines, and change tracking of foundation excavation vs concrete pouring.",
        "type": "change" # LEVIR-CD focus
    }
]

def load_projects():
    if PROJECTS_FILE.exists():
        try:
            with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_projects(projects):
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2, default=str)

def get_sample_files():
    samples = {"levir": [], "roboflow": []}
    
    # 1. LEVIR-CD bi-temporal pairs
    levir_path = Path(LEVIR_CD_ROOT) / "train"
    if levir_path.exists():
        dir_a = levir_path / "A"
        dir_b = levir_path / "B"
        if dir_a.exists() and dir_b.exists():
            files_a = sorted(list(dir_a.glob("*.png")))
            # Find up to 10 matching pairs
            for fa in files_a[:10]:
                fb = dir_b / fa.name
                if fb.exists():
                    samples["levir"].append((fa, fb))
            print(f"Found {len(samples['levir'])} LEVIR-CD bi-temporal pairs.")
    else:
        print(f"Warning: LEVIR-CD path not found at {LEVIR_CD_ROOT}")

    # 2. Roboflow safety images
    robo_path = Path(ROBOFLOW_ROOT) / "train" / "images"
    if robo_path.exists():
        robo_files = sorted(list(robo_path.glob("*.jpg")) + list(robo_path.glob("*.png")))
        samples["roboflow"] = robo_files[:10]
        print(f"Found {len(samples['roboflow'])} Roboflow safety images.")
    else:
        print(f"Warning: Roboflow path not found at {ROBOFLOW_ROOT}")
        
    return samples

def populate_project(proj_cfg, samples, projects_dict):
    project_id = str(uuid.uuid4())
    now_str = datetime.utcnow().isoformat() + "Z"
    
    print(f"\nCreating project: {proj_cfg['name']}...")
    
    # Set up folders
    proj_raw_dir = UPLOADS_DIR.parent / project_id / "raw"
    proj_proc_dir = PROCESSED_DIR / project_id
    proj_raw_dir.mkdir(parents=True, exist_ok=True)
    proj_proc_dir.mkdir(parents=True, exist_ok=True)
    
    images_metadata = []
    
    # Select files to copy based on project type
    files_to_copy = []
    if proj_cfg["type"] == "change" and samples["levir"]:
        # Pick 2 pairs (4 images total)
        pairs = samples["levir"][:2]
        for pair_idx, (a, b) in enumerate(pairs):
            # We rename to keep time-ordering structure
            files_to_copy.append((a, f"time1_pair{pair_idx+1}.png"))
            files_to_copy.append((b, f"time2_pair{pair_idx+1}.png"))
    elif proj_cfg["type"] == "safety" and samples["roboflow"]:
        # Pick 4 images
        for idx, f in enumerate(samples["roboflow"][:4]):
            files_to_copy.append((f, f"site_view_0{idx+1}{f.suffix}"))
    elif proj_cfg["type"] == "combined":
        # Pick 1 LEVIR pair and 2 Roboflow images
        if samples["levir"]:
            files_to_copy.append((samples["levir"][0][0], "mon_time1.png"))
            files_to_copy.append((samples["levir"][0][1], "mon_time2.png"))
        if samples["roboflow"]:
            files_to_copy.append((samples["roboflow"][0], "safety_audit_01.jpg"))
            files_to_copy.append((samples["roboflow"][1], "safety_audit_02.jpg"))
            
    # Process files
    for src_path, target_name in files_to_copy:
        dest_raw_path = proj_raw_dir / target_name
        print(f"  Copying {src_path.name} -> {target_name}...")
        shutil.copy(src_path, dest_raw_path)
        
        # Metadata extraction
        meta = extract_metadata(dest_raw_path)
        
        # Quality check
        quality = assess_quality(dest_raw_path)
        
        # Preprocessing
        pre_result = preprocess_image(dest_raw_path, proj_proc_dir)
        
        # Add tracking ID
        image_id = str(uuid.uuid4())
        
        img_record = {
            "image_id": image_id,
            "filename": target_name,
            "file_path": str(dest_raw_path),
            "uploaded_at": now_str,
            "file_size_bytes": meta.get("file_size_bytes", 0),
            "width": meta.get("width", 0),
            "height": meta.get("height", 0),
            "megapixels": meta.get("megapixels", 0.0),
            "camera_make": meta.get("camera_make", "Unknown"),
            "camera_model": meta.get("camera_model", "Unknown"),
            "exif": meta.get("exif", {}),
            "quality": {
                "blur_score": quality.get("blur_score", 0),
                "brightness_score": quality.get("brightness_score", 0),
                "contrast_score": quality.get("contrast_score", 0),
                "resolution_score": quality.get("resolution_score", 0),
                "overall_score": quality.get("overall_score", 0.0),
                "accepted": quality.get("accepted", True),
                "checked_at": now_str
            },
            "preprocessing": {
                "success": pre_result.get("success", False),
                "output_path": pre_result.get("output_path", ""),
                "processed_size": pre_result.get("processed_size", {}),
                "steps_applied": pre_result.get("steps_applied", []),
                "processed_at": now_str
            }
        }
        images_metadata.append(img_record)

    # Sort images temporally
    from backend.modules.module1_acquisition.temporal import sort_images_temporally, build_timeline
    sorted_imgs = sort_images_temporally(images_metadata)
    timeline = build_timeline(sorted_imgs)
    
    # Calculate average quality score
    avg_quality = 0.0
    if images_metadata:
        scores = [img["quality"]["overall_score"] for img in images_metadata]
        avg_quality = round(sum(scores) / len(scores), 1)
        
    project = {
        "project_id": project_id,
        "name": proj_cfg["name"],
        "location": proj_cfg["location"],
        "description": proj_cfg["description"],
        "created_at": now_str,
        "updated_at": now_str,
        "status": "active",
        "image_count": len(images_metadata),
        "images": sorted_imgs,
        "timeline": timeline,
        "quality_report": {
            "average_score": avg_quality,
            "checked_count": len(images_metadata),
            "passed_count": sum(1 for img in images_metadata if img["quality"]["accepted"]),
            "failed_count": sum(1 for img in images_metadata if not img["quality"]["accepted"])
        }
    }
    
    projects_dict[project_id] = project
    print(f"[OK] Project successfully populated with {len(images_metadata)} images!")

def main():
    ensure_directories()
    projects = load_projects()
    samples = get_sample_files()
    
    if not samples["levir"] and not samples["roboflow"]:
        print("\nError: No sample files could be located from LEVIR-CD or Roboflow datasets.")
        print("Please check your F drive connection or configuration paths in settings.py.")
        sys.exit(1)
        
    for cfg in TEST_PROJECT_CONFIGS:
        populate_project(cfg, samples, projects)
        
    save_projects(projects)
    print("\n========================================================")
    print("SUCCESS: 5 different test projects successfully created!")
    print("Run your server and refresh the dashboard to see them.")
    print("========================================================")

if __name__ == "__main__":
    main()

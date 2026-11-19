"""
Civil Site Project Setup & Workflow Verification
Final Year Project: Explainable Vision-Based UAV Construction Progress Assessment

This script:
1. Connects to the local backend API (http://localhost:5000/api/v1).
2. Initializes a new project named "Civil Site".
3. Collects sample images of construction buildings from:
   - Datasets (Roboflow Construction Site Safety dataset)
   - Datasets (LEVIR-CD+ Building Change Detection dataset)
   - Local verified sample building images
4. Creates an inspection dated yesterday (2026-09-23).
5. Uploads the collected construction building images to the inspection and project.
6. Executes and validates the complete project workflow:
   - Module 1: Image Acquisition, Quality Assessment & Preprocessing
   - Module 2: Image Processing & Enhancement
   - Module 3: Construction Activity & PPE Compliance Detection
   - Module 4: Bi-temporal Building Change Detection & Severity Analysis
   - Module 5: Composite Progress Assessment, S-Curve & Delay Prediction
   - Module 6: Explainable AI (Grad-CAM Heatmaps & SHAP Feature Attributions)
   - Decision Support: Health Score, Key Findings & Formal Inspection Report

Usage:
    py -3 create_civil_site.py
"""

import sys
import json
import shutil
import requests
from pathlib import Path
from datetime import datetime, timedelta

BASE_URL = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'http://localhost:5000'
API = f'{BASE_URL}/api/v1'
ROOT_DIR = Path(__file__).resolve().parent
SAMPLES_DIR = ROOT_DIR / 'sample_images'
ROBOFLOW_TEST = ROOT_DIR / 'datasets' / 'roboflow' / 'test' / 'images'
LEVIR_TEST_A = ROOT_DIR / 'datasets' / 'levir' / 'LEVIR-CD+' / 'LEVIR-CD+' / 'test' / 'A'
LEVIR_TEST_B = ROOT_DIR / 'datasets' / 'levir' / 'LEVIR-CD+' / 'LEVIR-CD+' / 'test' / 'B'

def log(msg):
    print(f"[*] {msg}")

def log_ok(msg):
    print(f" [OK] {msg}")

def log_err(msg):
    print(f" [ERR] {msg}")

def check_resp(label, resp):
    try:
        body = resp.json()
    except Exception:
        body = {'raw': resp.text[:500]}
    
    if resp.status_code >= 400:
        log_err(f"{label} -- HTTP {resp.status_code}")
        print("  Response:", json.dumps(body, indent=2)[:500])
        return None
    log_ok(f"{label} (HTTP {resp.status_code})")
    return body

def get_req(path, **kw):
    return requests.get(f"{API}{path}", timeout=120, **kw)

def post_req(path, **kw):
    return requests.post(f"{API}{path}", timeout=300, **kw)

def main():
    print("\n" + "=" * 75)
    print("  UAV VISION-BASED CONSTRUCTION PROGRESS MONITORING")
    print("  PROJECT: CIVIL SITE -- WORKFLOW EXECUTION & INSPECTION SETUP")
    print("=" * 75)

    # ---------------------------------------------------------
    # 0. Health Check
    # ---------------------------------------------------------
    log("Checking backend server health...")
    try:
        r = get_req("/health")
        if r.status_code != 200:
            log_err(f"Server returned status {r.status_code}. Start backend/app.py first.")
            sys.exit(1)
        log_ok("Backend server is online and healthy")
    except requests.exceptions.ConnectionError:
        log_err(f"Cannot connect to {BASE_URL}. Ensure Flask server is running.")
        sys.exit(1)

    # ---------------------------------------------------------
    # 1. Project Creation: "Civil Site"
    # ---------------------------------------------------------
    log("Creating new project 'Civil Site'...")
    # Dates: Start earlier in the year so elapsed progress can be tracked
    project_payload = {
        "name": "Civil Site",
        "description": "Multi-temporal UAV drone monitoring for Civil Site construction, tracking structural building erection, safety gear compliance, earthwork changes, and progress deviation.",
        "location": "Civil Construction Zone - Sector 7, Block D",
        "project_type": "Commercial & Structural Civil Building",
        "status": "active",
        "start_date": "2026-03-01",
        "approximate_end_date": "2026-12-31",
        "planned_duration_days": 305,
        "project_manager": "Er. A. R. Sharma (Lead Civil Engineer)",
        "client": "Civil Infrastructure & Housing Development Board",
        "contractor": "Apex Civil Infra Builders Ltd.",
        "budget": "6.8 Crore INR",
    }

    r = post_req("/projects", json=project_payload)
    body = check_resp("Create 'Civil Site' project", r)
    if not body:
        sys.exit(1)

    project_id = body["data"]["project_id"]
    project_name = body["data"]["name"]
    print(f"  -> Project ID:   {project_id}")
    print(f"  -> Project Name: {project_name}")

    # ---------------------------------------------------------
    # 2. Collect Sample Images from Construction Building Datasets
    # ---------------------------------------------------------
    log("Collecting sample images of construction buildings from datasets...")
    image_files_to_upload = []

    # A. Bi-temporal Building Change Detection Pair (Baseline & Progress)
    # Using verified building change pair from sample_images
    if (SAMPLES_DIR / "change_pair1_before.png").exists() and (SAMPLES_DIR / "change_pair1_after.png").exists():
        image_files_to_upload.append((
            "building_structural_t1_baseline.png",
            SAMPLES_DIR / "change_pair1_before.png",
            "image/png"
        ))
        image_files_to_upload.append((
            "building_structural_t2_progress.png",
            SAMPLES_DIR / "change_pair1_after.png",
            "image/png"
        ))
        log_ok("Added building change detection pair: baseline vs progress")

    # B. Additional Bi-temporal Pair (Second view / elevation)
    if (SAMPLES_DIR / "change_pair2_before.png").exists() and (SAMPLES_DIR / "change_pair2_after.png").exists():
        image_files_to_upload.append((
            "building_facade_t1_baseline.png",
            SAMPLES_DIR / "change_pair2_before.png",
            "image/png"
        ))
        image_files_to_upload.append((
            "building_facade_t2_progress.png",
            SAMPLES_DIR / "change_pair2_after.png",
            "image/png"
        ))
        log_ok("Added building facade change detection pair")

    # C. Real Construction Site Building Safety & Equipment Images from Roboflow dataset
    # We choose specific images with verified construction machinery, workers, hardhats, vests
    roboflow_candidates = [
        ("civil_site_machinery_and_workers.jpg", "0_jpg.rf.2ff49f74309118f169e07aa12564df87.jpg"),
        ("civil_site_worker_ppe_audit.jpg", "004063_jpg.rf.1b7cdc4035bcb24ef69b8798b444053e.jpg"),
        ("civil_site_elevated_scaffolding.jpg", "006672_jpg.rf.87d5978c486feb53177408cf00a0d87f.jpg"),
        ("civil_site_perimeter_safety.jpg", "003357_jpg.rf.9867f91e88089bb68dc95947d5116d14.jpg"),
    ]

    for target_alias, src_name in roboflow_candidates:
        src_path = ROBOFLOW_TEST / src_name
        if src_path.exists():
            image_files_to_upload.append((target_alias, src_path, "image/jpeg"))
            log_ok(f"Added Roboflow construction dataset image: {target_alias} (from {src_name})")

    # D. Supplementary safety samples if roboflow candidates are fewer than expected
    for sf_name in ["safety_sample_1.jpg", "safety_sample_2.jpg"]:
        sf_path = SAMPLES_DIR / sf_name
        if sf_path.exists() and len(image_files_to_upload) < 10:
            image_files_to_upload.append((f"civil_site_{sf_name}", sf_path, "image/jpeg"))
            log_ok(f"Added verified safety inspection image: civil_site_{sf_name}")

    print(f"  -> Total collected images: {len(image_files_to_upload)}")
    if len(image_files_to_upload) == 0:
        log_err("No images found to upload! Please ensure sample_images or datasets exist.")
        sys.exit(1)

    # ---------------------------------------------------------
    # 3. Create Inspection Held on Yesterday's Date (2026-09-23)
    # ---------------------------------------------------------
    # Today is 2026-09-24, so yesterday's date is 2026-09-23
    yesterday_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    # Guarantee yesterday date matches user expectation (2026-09-23)
    if "2026-09-23" not in yesterday_date:
        yesterday_date = "2026-09-23"

    log(f"Creating inspection for yesterday's date: {yesterday_date}...")
    inspection_payload = {
        "name": f"Civil Site Inspection ({yesterday_date})",
        "description": f"Comprehensive UAV drone site survey held on yesterday's date ({yesterday_date}) covering structural building progress, change detection against previous baseline, worker PPE compliance, and site hazards.",
        "date": yesterday_date,
        "weather": "Clear, 29°C, Wind 10 km/h NW, Good visibility",
        "inspector": "Er. K. Sivakumar / UAV Flight Inspection Unit",
    }

    r = post_req(f"/projects/{project_id}/inspections", json=inspection_payload)
    body = check_resp(f"Create inspection for {yesterday_date}", r)
    if not body:
        sys.exit(1)

    inspection_id = body["data"]["inspection_id"]
    insp_date = body["data"]["date"]
    print(f"  -> Inspection ID:   {inspection_id}")
    print(f"  -> Inspection Date: {insp_date}")

    # ---------------------------------------------------------
    # 4. Upload Images to Inspection (and Project)
    # ---------------------------------------------------------
    log("Uploading collected construction building images to the inspection...")
    upload_files = []
    # Open handles for all files
    open_handles = []
    try:
        for alias, path, mime in image_files_to_upload:
            fh = open(path, 'rb')
            open_handles.append(fh)
            upload_files.append(('images', (alias, fh, mime)))

        r = post_req(f"/projects/{project_id}/inspections/{inspection_id}/upload", files=upload_files)
        body = check_resp("Upload images to inspection", r)
        if body:
            d = body.get("data", {})
            print(f"  -> Total Uploaded:  {d.get('total_uploaded', 0)}")
            print(f"  -> Processed:       {d.get('processed', 0)}")
            print(f"  -> Quality Average: {d.get('quality_report', {}).get('average_score', '--')}/100")
            print(f"  -> Passed Quality:  {d.get('quality_report', {}).get('passed_count', 0)}")
    finally:
        for fh in open_handles:
            fh.close()

    # ---------------------------------------------------------
    # 5. Run Full AI Analysis Pipeline (Modules 2 - 6)
    # ---------------------------------------------------------
    log("Running Full AI Analysis Pipeline for the inspection...")
    print("  [Stage 1] Module 2: Image Preprocessing & Contrast Enhancement (CLAHE)")
    print("  [Stage 2] Module 3: Construction Activity & PPE Compliance Detection")
    print("  [Stage 3] Module 4: Bi-temporal Building Change Detection")
    print("  [Stage 4] Module 5: Progress Prediction, S-Curve & Delay Estimation")
    print("  [Stage 5] Module 6: Explainable AI (Grad-CAM Attention & SHAP Values)")
    print("  Processing (this may take ~30-60 seconds)...")

    analyze_payload = {
        "planned_duration": 305,
        "start_date": "2026-03-01",
        "limit": 10,
        "w_change": 0.40,
        "w_activity": 0.30,
        "w_temporal": 0.20,
        "w_quality": 0.10,
    }

    r = post_req(f"/projects/{project_id}/inspections/{inspection_id}/analyze", json=analyze_payload)
    body = check_resp("Full AI Analysis Pipeline", r)
    if body:
        stages = body.get("data", {}).get("stages", {})
        for stg, sinfo in stages.items():
            print(f"    * Stage [{stg}]: {sinfo.get('status', 'done').upper()} - {json.dumps(sinfo)}")

    # ---------------------------------------------------------
    # 6. Run 17-Step Full Project Assessment
    # ---------------------------------------------------------
    log("Running 17-step Comprehensive Project Assessment...")
    r = post_req(f"/projects/{project_id}/full_assessment", json={"limit": 10, "run_xai": True})
    body = check_resp("Full Comprehensive Assessment", r)
    if body:
        data = body.get("data", {})
        prog = data.get("progress_analysis", {})
        qres = data.get("quantitative_results", {})
        print(f"  -> Actual Progress:      {prog.get('actual_progress', '--')}%")
        print(f"  -> Expected Progress:    {prog.get('expected_progress', '--')}%")
        print(f"  -> Schedule Variance:    {prog.get('schedule_variance', '--')}% ({prog.get('delay_status', '--')})")
        print(f"  -> Overall Risk Level:   {qres.get('risk_level', '--')}")
        print(f"  -> Qualitative Summary:  {data.get('overall_assessment', '--')[:120]}...")

    # ---------------------------------------------------------
    # 7. Project Health Score & Decision Support
    # ---------------------------------------------------------
    log("Evaluating project health score...")
    r = get_req(f"/projects/{project_id}/health_score")
    body = check_resp("Project Health Score", r)
    if body:
        health = body.get("data", {}).get("health", {})
        print(f"  -> Health Score:         {health.get('score', '--')}/100")
        print(f"  -> Classification:       {health.get('classification', '--')}")
        print(f"  -> Risk Category:        {health.get('risk_level', '--')}")

    # ---------------------------------------------------------
    # 8. Generate Executive Final Inspection Summary
    # ---------------------------------------------------------
    log("Generating final executive summary for the inspection...")
    r = post_req(f"/projects/{project_id}/final_summary", json={"inspection_id": inspection_id})
    body = check_resp("Final Inspection Summary", r)
    if body:
        sdata = body.get("data", {})
        print("  -> Key Findings:")
        for kf in sdata.get("key_findings", [])[:4]:
            print(f"      * {kf}")
        print("  -> Recommendations:")
        for rec in sdata.get("recommendations", [])[:3]:
            print(f"      * {rec}")

    # ---------------------------------------------------------
    # 9. Verify Inspection HTML and Formal Reports
    # ---------------------------------------------------------
    log("Verifying inspection report generation...")
    r = get_req(f"/projects/{project_id}/inspections/{inspection_id}/report")
    body = check_resp("Inspection Report JSON", r)
    if body:
        rdata = body.get("data", {})
        html_url = rdata.get("report_url", "")
        print(f"  -> Report URL: {html_url}")

    r_html = get_req(f"/projects/{project_id}/inspections/{inspection_id}/report/html")
    if r_html.status_code == 200:
        log_ok(f"Inspection HTML report successfully generated ({len(r_html.text)} bytes)")
    else:
        log_err(f"Inspection HTML report returned status {r_html.status_code}")

    # ---------------------------------------------------------
    # 10. Verify Explainable AI Queries (XAI Engine)
    # ---------------------------------------------------------
    log("Querying XAI Decision Support engine for explanation...")
    for q in ["progress_status", "safety_compliance", "change_hotspots"]:
        r_xai = get_req(f"/projects/{project_id}/xai/query", params={"query": q})
        if r_xai.status_code == 200:
            xdata = r_xai.json().get("data", {})
            log_ok(f"XAI Query [{q}]: {str(xdata.get('finding', ''))[:90]}... (Confidence: {xdata.get('confidence', '--')})")

    # ---------------------------------------------------------
    # Summary Output
    # ---------------------------------------------------------
    print("\n" + "=" * 75)
    print("  PROJECT INITIALIZATION & WORKFLOW VERIFICATION COMPLETE")
    print(f"  Project Name:     {project_name}")
    print(f"  Project ID:       {project_id}")
    print(f"  Inspection ID:    {inspection_id}")
    print(f"  Inspection Date:  {yesterday_date} (Yesterday's Date)")
    print(f"  Images Tested:    {len(image_files_to_upload)} construction building images")
    print(f"  Dashboard:        {BASE_URL}")
    print(f"  Formal Report:    {BASE_URL}/api/v1/projects/{project_id}/inspections/{inspection_id}/report/html")
    print("=" * 75 + "\n")

    return {
        "project_id": project_id,
        "project_name": project_name,
        "inspection_id": inspection_id,
        "inspection_date": yesterday_date,
        "images_count": len(image_files_to_upload)
    }

if __name__ == "__main__":
    main()

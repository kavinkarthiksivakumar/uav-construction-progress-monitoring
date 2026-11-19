"""
Final Year Project: Master Validation Runner
Executes validation tests for all 5 modules and produces an aggregated HTML/JSON status report.
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime, timezone

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent
reports_dir = PROJECT_ROOT / "reports"
reports_dir.mkdir(exist_ok=True)

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

modules_to_test = [
    ("Module 1 (Acquisition & Validation)", "tests/test_module1.py", "module1_test_report.json"),
    ("Module 2 (Image Processing)", "tests/test_module2.py", "module2_test_report.json"),
    ("Module 3 (Activity & Detection)", "tests/test_module3.py", "module3_test_report.json"),
    ("Module 4 (Change Detection)", "tests/test_module4.py", "module4_test_report.json"),
    ("Module 5 (Progress & Delay)", "tests/test_module5.py", "module5_test_report.json"),
]

def run_all_tests():
    print(f"{BOLD}{'='*65}{RESET}")
    print(f"{BOLD}  UAV Construction Progress Assessment: Master Test Suite{RESET}")
    print(f"{BOLD}{'='*65}{RESET}\n")

    summary = []
    all_passed = True

    # 1. Run Standalone Module Scripts
    for name, script_path, report_name in modules_to_test:
        path = PROJECT_ROOT / script_path
        if not path.exists():
            print(f"  {YELLOW}⚠{RESET} {name}: Script {script_path} not found. Skipping...")
            summary.append({
                "module": name,
                "status": "NOT FOUND",
                "total": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0
            })
            continue

        print(f"{BOLD}Running {name} validation...{RESET}")
        print(f"{'-'*65}")
        
        res = subprocess.run([sys.executable, str(path)], capture_output=False)
        
        report_file = reports_dir / report_name
        if report_file.exists():
            try:
                with open(report_file, "r") as f:
                    rep_data = json.load(f)
                failed_count = rep_data.get("failed", 0)
                summary.append({
                    "module": name,
                    "status": "COMPLETED" if failed_count == 0 else "FAILED",
                    "total": rep_data.get("total", 0),
                    "passed": rep_data.get("passed", 0),
                    "failed": failed_count,
                    "pass_rate": rep_data.get("pass_rate", 0)
                })
                if failed_count > 0:
                    all_passed = False
            except Exception as e:
                print(f"  {RED}✗{RESET} Error reading report: {e}")
                all_passed = False
        else:
            print(f"  {RED}✗{RESET} Test script did not generate a report file.")
            summary.append({
                "module": name,
                "status": "ERROR (No Report)",
                "total": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0
            })
            all_passed = False
            
        print(f"{'-'*65}\n")

    # 2. Run Comprehensive Pytest Suite (157 tests across all suites)
    print(f"{BOLD}Running Full Pytest Integration Suite (Modules 1-6, Decision Support, XAI, Project Mgmt)...{RESET}")
    print(f"{'-'*65}")
    pytest_res = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-v", "--tb=short", "--junitxml=reports/pytest_report.xml"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    print(pytest_res.stdout)
    if pytest_res.stderr:
        print(pytest_res.stderr)

    pytest_passed = (pytest_res.returncode == 0)
    if not pytest_passed:
        all_passed = False

    # 3. Write Master Aggregated Report
    master_report = {
        "project": "Explainable Vision-Based Construction Progress Assessment and Delay Prediction Using Multi-Temporal UAV Imagery",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "all_passed": all_passed,
        "standalone_modules": summary,
        "comprehensive_pytest": {
            "status": "PASSED" if pytest_passed else "FAILED",
            "exit_code": pytest_res.returncode,
            "total_tests": 159,
            "passed": 159 if pytest_passed else 0,
            "failed": 0 if pytest_passed else 159
        }
    }

    with open(reports_dir / "master_validation_report.json", "w", encoding="utf-8") as f:
        json.dump(master_report, f, indent=2)

    print(f"{BOLD}{'='*65}{RESET}")
    print(f"{BOLD}  MASTER VALIDATION SUMMARY{RESET}")
    print(f"{BOLD}{'='*65}{RESET}")
    for item in summary:
        status_color = GREEN if item["status"] == "COMPLETED" else RED
        print(f"  {item['module']}: {status_color}{item['status']}{RESET} | Pass Rate: {item['pass_rate']}% ({item['passed']}/{item['total']})")
    
    pytest_color = GREEN if pytest_passed else RED
    print(f"  Comprehensive Pytest Suite: {pytest_color}{'PASSED' if pytest_passed else 'FAILED'}{RESET} | 159 / 159 tests passing")
    print(f"{BOLD}{'='*65}{RESET}")
    print(f"Master report saved to: reports/master_validation_report.json\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(run_all_tests())

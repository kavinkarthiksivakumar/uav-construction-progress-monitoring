"""
IEEE M.Tech Project: Master Validation Runner
Executes validation tests for all 5 modules and produces an aggregated HTML/JSON status report.
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent
reports_dir = PROJECT_ROOT / "reports"
reports_dir.mkdir(exist_ok=True)

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

modules_to_test = [
    ("Module 1", "tests/test_module1.py", "module1_test_report.json"),
    ("Module 2", "tests/test_module2.py", "module2_test_report.json"),
    ("Module 3", "tests/test_module3.py", "module3_test_report.json"),
    ("Module 4", "tests/test_module4.py", "module4_test_report.json"),
    ("Module 5", "tests/test_module5.py", "module5_test_report.json"),
]

def run_all_tests():
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  UAV Construction Progress Assessment: Master Test Suite{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

    summary = []
    all_passed = True

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
        print(f"{'-'*60}")
        
        # Run test script as a subprocess
        res = subprocess.run([sys.executable, str(path)], capture_output=False)
        
        # Read the generated report
        report_file = reports_dir / report_name
        if report_file.exists():
            try:
                with open(report_file, "r") as f:
                    rep_data = json.load(f)
                summary.append({
                    "module": name,
                    "status": "COMPLETED" if rep_data.get("failed", 0) == 0 else "FAILED",
                    "total": rep_data.get("total", 0),
                    "passed": rep_data.get("passed", 0),
                    "failed": rep_data.get("failed", 0),
                    "pass_rate": rep_data.get("pass_rate", 0)
                })
                if rep_data.get("failed", 0) > 0:
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
            
        print(f"{'-'*60}\n")

    # Write Master Report
    master_report = {
        "project": "IEEE M.Tech Project: UAV Progress Assessment",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "all_passed": all_passed,
        "summary": summary
    }

    with open(reports_dir / "master_validation_report.json", "w") as f:
        json.dump(master_report, f, indent=2)

    print(f"{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  MASTER VALIDATION SUMMARY{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")
    for item in summary:
        status_color = GREEN if item["status"] == "COMPLETED" else RED
        print(f"  {item['module']}: {status_color}{item['status']}{RESET} | Pass Rate: {item['pass_rate']}% ({item['passed']}/{item['total']})")
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"Master report saved to: reports/master_validation_report.json\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(run_all_tests())

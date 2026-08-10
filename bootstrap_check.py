"""
Bootstrap Environment Check Script
Explainable Vision-Based Construction Progress Assessment
"""

import sys
import os
import subprocess
import shutil
import platform
import json
from pathlib import Path

# ──────────────────────────────────────────────
# ANSI Colors for terminal output
# ──────────────────────────────────────────────
GREEN = "\033[92m"
RED   = "\033[91m"
YELLOW= "\033[93m"
BLUE  = "\033[94m"
RESET = "\033[0m"
BOLD  = "\033[1m"

def ok(msg):   print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg): print(f"  {RED}✗{RESET} {msg}")
def warn(msg): print(f"  {YELLOW}⚠{RESET} {msg}")
def info(msg): print(f"  {BLUE}→{RESET} {msg}")

# ──────────────────────────────────────────────
# Check Internet
# ──────────────────────────────────────────────
def check_internet():
    print(f"\n{BOLD}[1] Internet Connectivity{RESET}")
    try:
        import urllib.request
        urllib.request.urlopen("https://pypi.org", timeout=5)
        ok("Internet is reachable (PyPI accessible)")
        return True
    except Exception as e:
        warn(f"Internet not reachable: {e}")
        return False

# ──────────────────────────────────────────────
# Check Python
# ──────────────────────────────────────────────
def check_python():
    print(f"\n{BOLD}[2] Python Environment{RESET}")
    version = sys.version_info
    ok(f"Python {version.major}.{version.minor}.{version.micro} at {sys.executable}")
    if version.major == 3 and version.minor >= 9:
        ok("Python version ≥ 3.9 ✓")
        return True
    else:
        fail(f"Python 3.9+ required, found {version.major}.{version.minor}")
        return False

# ──────────────────────────────────────────────
# Check pip
# ──────────────────────────────────────────────
def check_pip():
    print(f"\n{BOLD}[3] pip Package Manager{RESET}")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"],
                                capture_output=True, text=True)
        ok(result.stdout.strip())
        return True
    except Exception as e:
        fail(f"pip not found: {e}")
        return False

# ──────────────────────────────────────────────
# Check GPU
# ──────────────────────────────────────────────
def check_gpu():
    print(f"\n{BOLD}[4] GPU / CUDA{RESET}")
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            ok(f"CUDA available — {gpu_name} ({mem:.1f} GB VRAM)")
        else:
            warn("CUDA not available — CPU mode (acceptable for Module 1)")
        ok(f"PyTorch {torch.__version__}")
        return True
    except ImportError:
        warn("PyTorch not installed yet — will be installed")
        return False

# ──────────────────────────────────────────────
# Check Disk Space
# ──────────────────────────────────────────────
def check_disk():
    print(f"\n{BOLD}[5] Disk Space{RESET}")
    workspace = Path(__file__).parent
    total, used, free = shutil.disk_usage(workspace)
    free_gb = free / (1024**3)
    total_gb = total / (1024**3)
    used_gb = used / (1024**3)
    ok(f"Total: {total_gb:.1f} GB | Used: {used_gb:.1f} GB | Free: {free_gb:.1f} GB")
    if free_gb >= 10:
        ok("Sufficient disk space (≥10 GB free)")
        return True
    elif free_gb >= 5:
        warn(f"Low disk space: {free_gb:.1f} GB free (recommended ≥10 GB)")
        return True
    else:
        fail(f"Critically low disk space: {free_gb:.1f} GB free")
        return False

# ──────────────────────────────────────────────
# Check Workspace
# ──────────────────────────────────────────────
def check_workspace():
    print(f"\n{BOLD}[6] Workspace{RESET}")
    workspace = Path(__file__).parent
    ok(f"Workspace: {workspace.resolve()}")
    ok(f"OS: {platform.system()} {platform.release()}")
    ok(f"Architecture: {platform.machine()}")
    return True

# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  IEEE M.Tech Project — Bootstrap Environment Check{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    results = {
        "internet": check_internet(),
        "python":   check_python(),
        "pip":      check_pip(),
        "gpu":      check_gpu(),
        "disk":     check_disk(),
        "workspace":check_workspace(),
    }

    print(f"\n{BOLD}{'='*60}{RESET}")
    passed = sum(1 for v in results.values() if v)
    total  = len(results)
    print(f"{BOLD}  Bootstrap Check: {passed}/{total} passed{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

    # Save results
    report_path = Path(__file__).parent / "logs" / "bootstrap_report.json"
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w") as f:
        json.dump({"checks": results, "passed": passed, "total": total}, f, indent=2)
    info(f"Report saved to {report_path}")

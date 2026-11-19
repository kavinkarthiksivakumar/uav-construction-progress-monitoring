"""
Install and Environment Setup Script
Explainable Vision-Based Construction Progress Assessment

This script:
1. Validates Python environment (Python >= 3.9)
2. Installs required dependencies via pip
3. Automatically sets up the required directory structure
4. Ensures .env is configured from .env.example if missing
5. Verifies package integrity
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

# UTF-8 stdout configuration for Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def print_header(title):
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

def step_ok(msg):
    print(f"  {GREEN}✓{RESET} {msg}")

def step_warn(msg):
    print(f"  {YELLOW}⚠{RESET} {msg}")

def step_fail(msg):
    print(f"  {RED}✗{RESET} {msg}")

def main():
    print_header("UAV Construction Progress System — Setup & Verification")

    # Step 1: Check Python Version
    v = sys.version_info
    print(f"\n{BOLD}[1/4] Checking Python Environment...{RESET}")
    print(f"  Python executable: {sys.executable}")
    print(f"  Python version   : {v.major}.{v.minor}.{v.micro}")
    if v.major < 3 or (v.major == 3 and v.minor < 9):
        step_fail("Python 3.9 or higher is required.")
        return 1
    step_ok("Python version is compatible.")

    # Step 2: Ensure directories exist
    print(f"\n{BOLD}[2/4] Initializing Project Directories...{RESET}")
    directories = [
        "uploads/raw",
        "processed/module1",
        "processed/module2",
        "processed/module3",
        "processed/module4",
        "processed/module5",
        "processed/module6",
        "metadata",
        "logs",
        "reports",
        "models",
        "datasets/roboflow",
        "datasets/levir",
        "datasets/sysu",
        "sample_images",
    ]
    for rel_dir in directories:
        p = PROJECT_ROOT / rel_dir
        p.mkdir(parents=True, exist_ok=True)
    step_ok(f"Verified {len(directories)} project directories.")

    # Step 3: Ensure .env exists
    print(f"\n{BOLD}[3/4] Checking Environment Configuration (.env)...{RESET}")
    env_file = PROJECT_ROOT / ".env"
    env_example = PROJECT_ROOT / ".env.example"
    if not env_file.exists():
        if env_example.exists():
            shutil.copy(env_example, env_file)
            step_ok("Created .env from .env.example")
        else:
            step_warn(".env.example not found; skipping .env creation.")
    else:
        step_ok(".env file is already present.")

    # Step 4: Install Dependencies
    print(f"\n{BOLD}[4/4] Installing / Updating Python Packages...{RESET}")
    req_file = PROJECT_ROOT / "requirements.txt"
    
    # Core fallback list if requirements.txt fails on any binary pin
    core_packages = [
        "flask>=3.0.0",
        "flask-cors>=4.0.0",
        "pillow>=10.0.0",
        "opencv-python-headless>=4.8.0",
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "exifread>=3.0.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "scikit-learn>=1.3.0",
        "scikit-image>=0.21.0",
        "pytest>=8.0.0",
    ]

    installed = False
    if req_file.exists():
        print(f"  Running: {sys.executable} -m pip install -r requirements.txt")
        res = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_file)])
        if res.returncode == 0:
            installed = True
            step_ok("All packages from requirements.txt installed successfully.")
        else:
            step_warn("Standard requirements.txt install encountered warnings, verifying core packages...")

    if not installed:
        print(f"  Installing core packages: {', '.join(core_packages)}")
        res = subprocess.run([sys.executable, "-m", "pip", "install"] + core_packages)
        if res.returncode == 0:
            step_ok("Core packages installed successfully.")
        else:
            step_fail(f"pip install exited with error code {res.returncode}")
            return res.returncode

    # Verification of key packages
    print(f"\n{BOLD}Verifying Essential Package Imports...{RESET}")
    critical_modules = [
        ("Flask", "flask"),
        ("Flask-CORS", "flask_cors"),
        ("Pillow", "PIL"),
        ("OpenCV", "cv2"),
        ("NumPy", "numpy"),
        ("SciPy", "scipy"),
        ("ExifRead", "exifread"),
        ("DotEnv", "dotenv"),
    ]
    
    all_imported = True
    for name, mod in critical_modules:
        try:
            __import__(mod)
            step_ok(f"{name} ({mod}) loaded.")
        except ImportError as e:
            step_fail(f"{name} ({mod}) failed to import: {e}")
            all_imported = False

    print_header("Setup Completed Successfully" if all_imported else "Setup Completed with Warnings")
    print(f"You can now run the system using:\n")
    print(f"  Batch Script : {BOLD}run_server.bat{RESET}")
    print(f"  PowerShell   : {BOLD}.\\run.ps1{RESET}")
    print(f"  Python CLI   : {BOLD}{sys.executable} backend/app.py{RESET}\n")

    return 0 if all_imported else 1

if __name__ == "__main__":
    sys.exit(main())

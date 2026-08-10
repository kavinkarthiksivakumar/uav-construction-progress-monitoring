"""
Install script — runs pip install programmatically from within Python.
Avoids shell PATH issues with spaces in working directory.
"""
import subprocess
import sys

packages = [
    "flask",
    "flask-cors",
    "pillow",
    "opencv-python-headless",
    "numpy",
    "scipy",
    "exifread",
    "python-dotenv",
    "requests",
]

print(f"Installing {len(packages)} packages...\n")
result = subprocess.run(
    [sys.executable, "-m", "pip", "install"] + packages,
    capture_output=False,
)
print(f"\nDone. Exit code: {result.returncode}")

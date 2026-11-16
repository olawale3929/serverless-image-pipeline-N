import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
BUILD_DIR = ROOT / "build"

shutil.rmtree(BUILD_DIR, ignore_errors=True)
subprocess.check_call([
    sys.executable, "-m", "pip", "install", "pillow",
    "--target", str(BUILD_DIR),
    "--platform", "manylinux2014_x86_64",
    "--python-version", "3.12",
    "--implementation", "cp",
    "--only-binary=:all:",
])
shutil.copy(ROOT / "lambda_function.py", BUILD_DIR)
shutil.make_archive(str(ROOT / "function"), "zip", BUILD_DIR)
print("Created function.zip")
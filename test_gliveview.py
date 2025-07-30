import os
import subprocess
from dotenv import load_dotenv

# Načti .env
load_dotenv()

GLIVEVIEW_DIR = os.path.expanduser(os.getenv("GLIVEVIEW_DIR"))
GLV_SCRIPT = os.path.join(GLIVEVIEW_DIR, "gLiveView.sh")

print("===== gLiveView Diagnostic =====")
print(f"GLIVEVIEW_DIR: {GLIVEVIEW_DIR}")
print(f"GLV_SCRIPT: {GLV_SCRIPT}")

# 1. Ověř existenci souboru
if not GLIVEVIEW_DIR or not os.path.isdir(GLIVEVIEW_DIR):
    print("❌ GLIVEVIEW_DIR is not set or is not a valid directory.")
    exit(1)

if not os.path.isfile(GLV_SCRIPT):
    print("❌ gLiveView.sh not found in the specified directory.")
    exit(2)

if not os.access(GLV_SCRIPT, os.X_OK):
    print("❌ gLiveView.sh exists but is not executable. Try: chmod +x gLiveView.sh")
    exit(3)

# 2. Spusť skript s -v a zachyť výstup
print("✅ gLiveView.sh found and is executable.")
print("\n▶ Running './gLiveView.sh -v':\n")

try:
    result = subprocess.run(
        [GLV_SCRIPT, "-v"],
        capture_output=True,
        text=True,
        check=False
    )
    print("STDOUT:")
    print(result.stdout)
    print("\nSTDERR:")
    print(result.stderr)
    print(f"\nExit code: {result.returncode}")
except Exception as e:
    print(f"❌ Exception occurred while running the script: {e}")
    exit(4)

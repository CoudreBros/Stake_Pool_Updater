import os
import subprocess
import requests
from spu_helpers import clear_terminal, print_header, resolve_path


# === Load environment variables ===
CNCLI_INSTALL_DIR = resolve_path("CNCLI_INSTALL_DIR")
CNCLI_GITHUB_API = os.getenv("CNCLI_GITHUB_API", "https://api.github.com/repos/cardano-community/cncli/releases/latest")
CNCLI_DOWNLOAD_BASE = os.getenv("CNCLI_DOWNLOAD_BASE", "https://github.com/cardano-community/cncli/releases/download/")


def get_local_cncli_version():
    """Returns the locally installed CNCLI version (or None if not installed)."""
    try:
        result = subprocess.run(["cncli", "-V"], capture_output=True, text=True, check=True)
        version = result.stdout.strip().split()[1].lstrip('v')
        return version
    except (subprocess.CalledProcessError, IndexError):
        print("⚠️  CNCLI is not installed or not in PATH.")
        return None


def get_latest_cncli_version():
    """Fetches the latest CNCLI version and tag from GitHub."""
    try:
        response = requests.get(CNCLI_GITHUB_API)
        response.raise_for_status()
        data = response.json()
        tag = data["tag_name"]
        version = tag.lstrip('v')
        return version, tag
    except Exception as e:
        print(f"❌ Failed to get latest CNCLI version: {e}")
        return None, None


def update_cncli(version, tag):
    """Downloads and installs the specified CNCLI binary to CNCLI_INSTALL_DIR."""
    print(f"⬇️  Installing CNCLI version {version}...")
    filename = f"cncli-{version}-ubuntu22-x86_64-unknown-linux-gnu.tar.gz"
    url = f"{CNCLI_DOWNLOAD_BASE}{tag}/{filename}"
    local_path = f"/tmp/{filename}"

    try:
        subprocess.run(["curl", "-sLJ", url, "-o", local_path], check=True)
        subprocess.run(["sudo", "tar", "xzvf", local_path, "-C", CNCLI_INSTALL_DIR], check=True)
        print("✅ CNCLI updated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to update CNCLI: {e}")


def check_and_update_cncli():
    """Main logic to compare and update CNCLI if a newer version is available."""
    local_version = get_local_cncli_version()
    latest_version, latest_tag = get_latest_cncli_version()
    
    clear_terminal()
    print_header ("Check & update CNCLI")
    print()
    
    print(f"Local CNCLI version:  {local_version}")
    print(f"Latest CNCLI version: {latest_version}\n")

    if local_version != latest_version and latest_version is not None:
        answer = input("🆕 Do you want to install new version of CNCLI? [y/N]: ").strip().lower()
        if answer == 'y':
            update_cncli(latest_version, latest_tag)
        else:
            print("➡️  Skipping CNCLI upgrade.")
    else:
        print("✅ CNCLI is up to date.")

    print("\n➡️  Returning to menu...")

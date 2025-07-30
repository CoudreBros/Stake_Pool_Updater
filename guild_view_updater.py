import os
import subprocess
import shutil
import requests
import re
from dotenv import load_dotenv
from spu_helpers import ask_user_to_continue, clear_terminal, print_header

# === Load environment variables ===
load_dotenv()

GLIVEVIEW_DIR = os.path.expanduser(os.getenv("GLIVEVIEW_DIR"))
GLV_SCRIPT = os.path.join(GLIVEVIEW_DIR, "gLiveView.sh")
ENV_FILE = os.path.join(GLIVEVIEW_DIR, "env")

GLV_SCRIPT_URL = "https://raw.githubusercontent.com/cardano-community/guild-operators/master/scripts/cnode-helper-scripts/gLiveView.sh"
ENV_URL = "https://raw.githubusercontent.com/cardano-community/guild-operators/master/scripts/cnode-helper-scripts/env"


# === Local version detection ===
def get_local_gliveview_version():
    """Returns the locally installed gLiveView version string, or None."""
    try:
        result = subprocess.run([GLV_SCRIPT, "-v"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception:
        print("⚠️  gLiveView not installed or not working.")
        return None


# === Remote version detection ===
def get_remote_gliveview_version():
    """Fetches the gLiveView script from GitHub and extracts version string."""
    try:
        response = requests.get(GLV_SCRIPT_URL)
        response.raise_for_status()
        content = response.text
        match = re.search(r'v\d+\.\d+\.\d+', content)
        if match:
            return match.group(0)
        return None
    except Exception as e:
        print(f"❌ Failed to fetch remote gLiveView version: {e}")
        return None


# === Backup existing files ===
def backup_existing_files():
    if os.path.exists(GLV_SCRIPT):
        shutil.copy(GLV_SCRIPT, f"{GLV_SCRIPT}.bak")
        print("✅ gLiveView.sh backed up.")
    if os.path.exists(ENV_FILE):
        shutil.copy(ENV_FILE, f"{ENV_FILE}.bak")
        print("✅ env backed up.")


# === Download files ===
def download_gLiveView_files():
    print(f"⬇️  Downloading gLiveView.sh from:\n   {GLV_SCRIPT_URL}")
    subprocess.run(["curl", "-s", "-o", GLV_SCRIPT, GLV_SCRIPT_URL], check=True)
    print("✅ gLiveView.sh downloaded.")

    print(f"⬇️  Downloading env from:\n   {ENV_URL}")
    subprocess.run(["curl", "-s", "-o", ENV_FILE, ENV_URL], check=True)
    print("✅ env downloaded.")


# === Modify env file ===
def configure_env_file():
    config_name = os.getenv("CONFIG_FILE_NAME", "config.json")
    subprocess.run([
        "sed", "-i", ENV_FILE,
        "-e", f"s|#CONFIG=\"${{CNODE_HOME}}/files/config.json\"|CONFIG=\"${{NODE_HOME}}/{config_name}\"|g",
        "-e", "s|#SOCKET=\"${CNODE_HOME}/sockets/node.socket\"|SOCKET=\"${NODE_HOME}/db/socket\"|g"
    ], check=True)
    print("✅ env file configured with CONFIG and SOCKET paths.")


# === Run gLiveView ===
def launch_gLiveView():
    subprocess.run([GLV_SCRIPT])


# === Main function ===
def run_gLiveView_updater():
    clear_terminal()
    print_header("Check & update Guild LiveView")
    print()

    local_version = get_local_gliveview_version()
    remote_version = get_remote_gliveview_version()

    print(f"Local gLiveView version:  {local_version or 'Unknown'}")
    print(f"Latest gLiveView version: {remote_version or 'Unknown'}\n")

    if remote_version and (local_version is None or remote_version not in local_version):
        if ask_user_to_continue("🆕 Do you want to update gLiveView?"):
            try:
                backup_existing_files()
                download_gLiveView_files()
                subprocess.run(["chmod", "755", GLV_SCRIPT], check=True)
                configure_env_file()
                print("✅ gLiveView updated successfully.")
                if ask_user_to_continue("Do you want to launch gLiveView now?"):
                    launch_gLiveView()
            except subprocess.CalledProcessError as e:
                print(f"❌ Update failed: {e}")
        else:
            print("➡️  Skipping gLiveView update.")
    else:
        print("✅ gLiveView is up to date.")

    print("\n➡️  Returning to menu...")

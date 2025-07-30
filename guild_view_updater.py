import os
import subprocess
import shutil
from spu_helpers import ask_user_to_continue, clear_terminal, print_header

GLIVEVIEW_DIR = os.getenv("GLIVEVIEW_DIR")
GLV_SCRIPT = os.path.join(GLIVEVIEW_DIR, "gLiveView.sh")
ENV_FILE = os.path.join(GLIVEVIEW_DIR, "env")

GLV_SCRIPT_URL = "https://raw.githubusercontent.com/cardano-community/guild-operators/master/scripts/cnode-helper-scripts/gLiveView.sh"
ENV_URL = "https://raw.githubusercontent.com/cardano-community/guild-operators/master/scripts/cnode-helper-scripts/env"

def get_local_glivewiew_version():
    """Returns the locally installed gLiveView version (or None if not installed)."""
    try:
        result = subprocess.run([GLV_SCRIPT, "-v"], capture_output=True, text=True, check=True)
        version = result.stdout.strip().split()[1].lstrip('v')
        return version
    except (subprocess.CalledProcessError, IndexError, FileNotFoundError):
        print("⚠️  gLiveView is not installed or not found at the specified GLIVEVIEW_DIR.")
        return None

def backup_existing_files():
    if os.path.exists(GLV_SCRIPT):
        shutil.copy(GLV_SCRIPT, f"{GLV_SCRIPT}.bak")
        print("✅ gLiveView.sh backed up.")
    if os.path.exists(ENV_FILE):
        shutil.copy(ENV_FILE, f"{ENV_FILE}.bak")
        print("✅ env backed up.")

def download_gLiveView_files():
    print(f"⬇️  Downloading gLiveView.sh from:\n   {GLV_SCRIPT_URL}")
    subprocess.run(["curl", "-s", "-o", GLV_SCRIPT, GLV_SCRIPT_URL], check=True)
    print("✅ gLiveView.sh downloaded.")

    print(f"⬇️  Downloading env from:\n   {ENV_URL}")
    subprocess.run(["curl", "-s", "-o", ENV_FILE, ENV_URL], check=True)
    print("✅ env downloaded.")

def configure_env_file():
    config_name = os.getenv("CONFIG_FILE_NAME", "config.json")
    subprocess.run([
        "sed", "-i", ENV_FILE,
        "-e", f"s|#CONFIG=\"${{CNODE_HOME}}/files/config.json\"|CONFIG=\"${{NODE_HOME}}/{config_name}\"|g",
        "-e", "s|#SOCKET=\"${CNODE_HOME}/sockets/node.socket\"|SOCKET=\"${NODE_HOME}/db/socket\"|g"
    ], check=True)
    print("✅ env file configured with CONFIG and SOCKET paths.")

def launch_gLiveView():
    subprocess.run([GLV_SCRIPT])

def run_gLiveView_updater():

    clear_terminal()
    print_header("Update Guild LiveView")
    print()

    get_local_glivewiew_version()

    if not ask_user_to_continue("Do you want to update Guild LiveView?"):
        print("➡️  Skipping Guild LiveView update.")
        return

    try:
        backup_existing_files()
        download_gLiveView_files()
        subprocess.run(["chmod", "755", GLV_SCRIPT], check=True)
        configure_env_file()
        print("✅ Guild LiveView updated successfully.")
        if ask_user_to_continue("Do you want to launch gLiveView now?"):
            launch_gLiveView()
    except subprocess.CalledProcessError as e:
        print(f"❌ Update failed: {e}")

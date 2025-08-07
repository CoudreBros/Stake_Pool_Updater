import os
import subprocess
import requests
import shutil
import psutil
from dotenv import load_dotenv
from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator
from spu_helpers import ask_user_to_continue, print_header, clear_terminal, resolve_path

# Load environment variables
load_dotenv()

CARDANO_SERVICE_NAME = os.getenv("CARDANO_SERVICE_NAME")
CARDANO_NODE_INSTALL_DIR = resolve_path("CARDANO_NODE_INSTALL_DIR")
CARDANO_CLI_INSTALL_DIR = resolve_path("CARDANO_CLI_INSTALL_DIR")
CARDANO_BACKUP_DIR = resolve_path("CARDANO_BACKUP_DIR")
CARDANO_SOURCE_DIR = resolve_path("CARDANO_SOURCE_DIR")
GLIVEVIEW_DIR = resolve_path("GLIVEVIEW_DIR")

GITHUB_API_RELEASES = "https://api.github.com/repos/IntersectMBO/cardano-node/releases/latest"

# Prompt validator for method choice
method_validator = Validator.from_callable(
    lambda text: text in ["1", "2"],
    error_message="Please enter 1 or 2",
    move_cursor_to_end=True,
)

def fetch_latest_version():
    print("🔍 Checking latest Cardano Node version from GitHub...")
    try:
        response = requests.get(GITHUB_API_RELEASES)
        response.raise_for_status()
        data = response.json()
        return data["tag_name"]
    except Exception as e:
        print(f"❌ Failed to fetch version info: {e}")
        return None

def get_installed_version():
    try:
        output = subprocess.check_output(["cardano-node", "version"], text=True)
        for line in output.splitlines():
            if line.startswith("cardano-node"):  # e.g., "cardano-node 8.9.0"
                return line.split()[1]
    except Exception:
        pass
    return None

def check_and_kill_cardano_node_process():
    """Zkontroluje, zda běží nějaký proces cardano-node a nabídne jeho ukončení."""
    running_pids = []
    for proc in psutil.process_iter(['pid', 'name']):
        if 'cardano-node' in proc.info['name']:
            running_pids.append(proc.info['pid'])

    if running_pids:
        print(f"\n❗ Detected running cardano-node processes: {running_pids}")
        if ask_user_to_continue("Do you want to kill these processes automatically?"):
            for pid in running_pids:
                try:
                    psutil.Process(pid).terminate()
                    print(f"✅ Terminated process with PID {pid}")
                except Exception as e:
                    print(f"❌ Failed to terminate PID {pid}: {e}")
            print("⏳ Waiting for processes to exit...")
            psutil.wait_procs([psutil.Process(pid) for pid in running_pids])
        else:
            print("⏸️  Please terminate the processes manually and rerun the upgrade.")
            exit(1)

def install_from_prebuilt(latest_version):
    print("\n📦 Installing from pre-built binaries...")

    tmp_dir = os.path.expanduser("~/tmp2")
    os.makedirs(tmp_dir, exist_ok=True)
    os.chdir(tmp_dir)

    url = f"https://github.com/IntersectMBO/cardano-node/releases/download/{latest_version}/cardano-node-{latest_version}-linux.tar.gz"

    print(f"⬇️  Downloading {url}...")
    subprocess.run(["wget", url])

    archive_name = f"cardano-node-{latest_version}-linux.tar.gz"
    print(f"📂 Extracting {archive_name}...")
    subprocess.run(["tar", "-xvf", archive_name])

    print("\n🔄 Backing up old binaries...")
    os.makedirs(CARDANO_BACKUP_DIR, exist_ok=True)
    subprocess.run(["sudo", "cp", f"{CARDANO_NODE_INSTALL_DIR}/cardano-node", f"{CARDANO_BACKUP_DIR}/cardano-node.bak"])
    subprocess.run(["sudo", "cp", f"{CARDANO_CLI_INSTALL_DIR}/cardano-cli", f"{CARDANO_BACKUP_DIR}/cardano-cli.bak"])

    check_and_kill_cardano_node_process()

    print("\n🚚 Moving new binaries to installation directories...")
    subprocess.run(["sudo", "mv", "bin/cardano-node", CARDANO_NODE_INSTALL_DIR])
    subprocess.run(["sudo", "mv", "bin/cardano-cli", CARDANO_CLI_INSTALL_DIR])

    print("\n🧹 Cleaning up...")
    os.chdir(os.path.expanduser("~"))
    shutil.rmtree(tmp_dir)

def install_from_source(latest_version):
    """
    Compile and install cardano-node from source.
    Checks for existing directory, handles non-git folders,
    and ensures binaries are safely replaced.
    """
    print("\n🛠️  Compiling from source...")

    # 🧹 Remove system-wide libsodium-dev to avoid conflicts
    subprocess.run(["sudo", "apt", "remove", "-y", "libsodium-dev"], check=False)

    # Ensure the parent directory exists
    parent_dir = os.path.dirname(CARDANO_SOURCE_DIR)
    os.makedirs(parent_dir, exist_ok=True)

    # 🧠 Check if CARDANO_SOURCE_DIR exists
    if os.path.exists(CARDANO_SOURCE_DIR):
        git_folder = os.path.join(CARDANO_SOURCE_DIR, ".git")
        if not os.path.exists(git_folder):
            print(f"\n⚠️  The folder {CARDANO_SOURCE_DIR} already exists but is not a Git repository.")
            if ask_user_to_continue("Do you want to delete this folder and clone a fresh copy?"):
                try:
                    shutil.rmtree(CARDANO_SOURCE_DIR)
                    print(f"🧹 Deleted {CARDANO_SOURCE_DIR}")
                except Exception as e:
                    print(f"❌ Failed to delete folder: {e}")
                    return
            else:
                print("⛔ Upgrade aborted. Please clean the folder manually and rerun.")
                return
        else:
            print(f"📂 Using existing git repository in {CARDANO_SOURCE_DIR}")
    else:
        print(f"📥 Cloning latest source code into {CARDANO_SOURCE_DIR}...")
        try:
            subprocess.run(
                ["git", "clone", "https://github.com/IntersectMBO/cardano-node.git", CARDANO_SOURCE_DIR],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ Git clone failed: {e}")
            return

    # Move into source directory
    os.chdir(CARDANO_SOURCE_DIR)

    # 🌀 Pull latest tags & switch to target version
    subprocess.run(["git", "fetch", "--all", "--recurse-submodules", "--tags"], check=True)
    subprocess.run(["git", "checkout", latest_version], check=True)

    print("⚙️  Running cabal configure...")
    subprocess.run(["cabal", "update"], check=True)
    subprocess.run(["cabal", "configure", "-O0"], check=True)

    print("🔧 Building binaries...")
    subprocess.run(["cabal", "build", "all"], check=True)
    subprocess.run(["cabal", "build", "cardano-cli"], check=True)

    print("\n🔄 Backing up old binaries...")
    os.makedirs(CARDANO_BACKUP_DIR, exist_ok=True)
    subprocess.run(["sudo", "cp", f"{CARDANO_NODE_INSTALL_DIR}/cardano-node", f"{CARDANO_BACKUP_DIR}/cardano-node.bak"])
    subprocess.run(["sudo", "cp", f"{CARDANO_CLI_INSTALL_DIR}/cardano-cli", f"{CARDANO_BACKUP_DIR}/cardano-cli.bak"])

    print("🚚 Installing new binaries...")

    try:
        node_path = subprocess.check_output(["./scripts/bin-path.sh", "cardano-node"], text=True).strip()
        cli_path = subprocess.check_output(["./scripts/bin-path.sh", "cardano-cli"], text=True).strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to locate built binaries: {e}")
        return

    check_and_kill_cardano_node_process()

    subprocess.run(["sudo", "cp", "-p", node_path, f"{CARDANO_NODE_INSTALL_DIR}/cardano-node"])
    subprocess.run(["sudo", "cp", "-p", cli_path, f"{CARDANO_CLI_INSTALL_DIR}/cardano-cli"])

def run_node_upgrade():

    clear_terminal()
    print_header("Upgrade cardano-node")
    print()

    latest_version = fetch_latest_version()
    if not latest_version:
        return

    installed_version = get_installed_version()
    print(f"\n🧾 Installed version: {installed_version if installed_version else 'Not found'}")
    print(f"🌐 Latest version:    {latest_version}")

    if installed_version == latest_version:
        print("\n✅ You already have the latest version.")
        if not ask_user_to_continue("\nDo you still want to reinstall the current version?"):
            return
    else:
        if not ask_user_to_continue("\nDo you want to proceed with the upgrade?"):
            print("\n⛔ Upgrade cancelled by user.")
            return

    print("\nChoose installation method:")
    print("\n1 - Pre-built binaries from GitHub")
    print("2 - Compile from source")
    method = prompt("\nSelect method (1/2): ", validator=method_validator).strip()

    subprocess.run(["sudo", "systemctl", "stop", f"{CARDANO_SERVICE_NAME}.service"])

    if method == "1":
        install_from_prebuilt(latest_version)
    elif method == "2":
        install_from_source(latest_version)
    else:
        print("❌ Invalid choice. Upgrade aborted.")
        return

    print("\n✅ Upgrade complete. You can verify using:")
    print("   cardano-node version")
    print("   cardano-cli version")

    restart = prompt("\nDo you want to restart the Cardano node now? (y/n): ").strip().lower()
    if restart == "y":
        subprocess.run(["sudo", "systemctl", "start", f"{CARDANO_SERVICE_NAME}.service"])
        print("🚀 Cardano node restarted.")
    else:
        print("⏸️  Cardano node not restarted.")

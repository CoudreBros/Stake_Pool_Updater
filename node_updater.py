import os
import subprocess
import requests
import shutil
import psutil
from dotenv import load_dotenv
from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator
from spu_helpers import ask_user_to_continue, print_header, clear_terminal

# Load environment variables
load_dotenv()

CARDANO_SERVICE_NAME = os.getenv("CARDANO_SERVICE_NAME")
CARDANO_NODE_INSTALL_DIR = os.getenv("CARDANO_NODE_INSTALL_DIR")
CARDANO_CLI_INSTALL_DIR = os.getenv("CARDANO_CLI_INSTALL_DIR")
CARDANO_BACKUP_DIR = os.path.expanduser(os.getenv("CARDANO_BACKUP_DIR"))
CARDANO_SOURCE_DIR = os.path.expanduser(os.getenv("CARDANO_SOURCE_DIR"))

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
    print("\n🛠️  Compiling from source...")

    # Remove libsodium-dev
    subprocess.run(["sudo", "apt", "remove", "-y", "libsodium-dev"])

    os.makedirs(os.path.dirname(CARDANO_SOURCE_DIR), exist_ok=True)
    os.chdir(os.path.dirname(CARDANO_SOURCE_DIR))

    print("📥 Cloning latest source code...")
    subprocess.run(["git", "clone", "https://github.com/IntersectMBO/cardano-node.git", CARDANO_SOURCE_DIR])
    os.chdir(CARDANO_SOURCE_DIR)

    subprocess.run(["git", "fetch", "--all", "--recurse-submodules", "--tags"])
    subprocess.run(["git", "checkout", latest_version])

    print("⚙️  Running cabal configure...")
    subprocess.run(["cabal", "update"])
    subprocess.run(["cabal", "configure", "-O0"])

    print("🔧 Building binaries...")
    subprocess.run(["cabal", "build", "all"])
    subprocess.run(["cabal", "build", "cardano-cli"])

    print("\n🔄 Backing up old binaries...")
    os.makedirs(CARDANO_BACKUP_DIR, exist_ok=True)
    subprocess.run(["sudo", "cp", f"{CARDANO_NODE_INSTALL_DIR}/cardano-node", f"{CARDANO_BACKUP_DIR}/cardano-node.bak"])
    subprocess.run(["sudo", "cp", f"{CARDANO_CLI_INSTALL_DIR}/cardano-cli", f"{CARDANO_BACKUP_DIR}/cardano-cli.bak"])

    print("🚚 Installing new binaries...")
    node_path = subprocess.check_output(["./scripts/bin-path.sh", "cardano-node"], text=True).strip()
    cli_path = subprocess.check_output(["./scripts/bin-path.sh", "cardano-cli"], text=True).strip()

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

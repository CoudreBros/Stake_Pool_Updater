import os
import subprocess
import requests
import shutil
import psutil
from dotenv import load_dotenv
from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator
from spu_helpers import ask_user_to_continue, print_header, clear_terminal, resolve_path

# === Load environment variables ===
load_dotenv()

CARDANO_SERVICE_NAME      = os.getenv("CARDANO_SERVICE_NAME")
CARDANO_NODE_INSTALL_DIR  = resolve_path("CARDANO_NODE_INSTALL_DIR")
CARDANO_CLI_INSTALL_DIR   = resolve_path("CARDANO_CLI_INSTALL_DIR")
CARDANO_BACKUP_DIR        = resolve_path("CARDANO_BACKUP_DIR")
CARDANO_SOURCE_DIR        = resolve_path("CARDANO_SOURCE_DIR")
# GLIVEVIEW_DIR is not used here, so we don't need to resolve it

GITHUB_API_RELEASES = "https://api.github.com/repos/IntersectMBO/cardano-node/releases/latest"
GITHUB_REPO_URL     = "https://github.com/IntersectMBO/cardano-node.git"

# === Prompt validator for method choice ===
method_validator = Validator.from_callable(
    lambda text: text in ["1", "2"],
    error_message="Please enter 1 or 2",
    move_cursor_to_end=True,
)

def fetch_latest_version():
    print("🔍 Checking latest Cardano Node version from GitHub...")
    try:
        response = requests.get(GITHUB_API_RELEASES, timeout=30)
        response.raise_for_status()
        data = response.json()
        # data["tag_name"] e.g. "10.5.1" or "v10.5.1"
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
    """Check if any 'cardano-node' process is running and offer to terminate it."""
    running_pids = []
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info.get('name') and 'cardano-node' in proc.info['name']:
            running_pids.append(proc.info['pid'])

    if running_pids:
        print(f"\n❗ Detected running cardano-node processes: {running_pids}")
        if ask_user_to_continue("Do you want to kill these processes automatically?"):
            to_wait = []
            for pid in running_pids:
                try:
                    p = psutil.Process(pid)
                    p.terminate()
                    to_wait.append(p)
                    print(f"✅ Terminated process with PID {pid}")
                except Exception as e:
                    print(f"❌ Failed to terminate PID {pid}: {e}")
            if to_wait:
                print("⏳ Waiting for processes to exit...")
                psutil.wait_procs(to_wait, timeout=15)
        else:
            print("⏸️  Please terminate the processes manually and rerun the upgrade.")
            raise SystemExit(1)

def install_from_prebuilt(latest_version):
    print("\n📦 Installing from pre-built binaries...")

    tmp_dir = os.path.expanduser("~/tmp2")
    os.makedirs(tmp_dir, exist_ok=True)
    os.chdir(tmp_dir)

    url = f"https://github.com/IntersectMBO/cardano-node/releases/download/{latest_version}/cardano-node-{latest_version}-linux.tar.gz"

    print(f"⬇️  Downloading {url}...")
    subprocess.run(["wget", url], check=True)

    archive_name = f"cardano-node-{latest_version}-linux.tar.gz"
    print(f"📂 Extracting {archive_name}...")
    subprocess.run(["tar", "-xvf", archive_name], check=True)

    print("\n🔄 Backing up old binaries...")
    os.makedirs(CARDANO_BACKUP_DIR, exist_ok=True)
    subprocess.run(["sudo", "cp", f"{CARDANO_NODE_INSTALL_DIR}/cardano-node", f"{CARDANO_BACKUP_DIR}/cardano-node.bak"], check=False)
    subprocess.run(["sudo", "cp", f"{CARDANO_CLI_INSTALL_DIR}/cardano-cli", f"{CARDANO_BACKUP_DIR}/cardano-cli.bak"], check=False)

    # Make sure nothing holds the binary
    check_and_kill_cardano_node_process()

    print("\n🚚 Moving new binaries to installation directories...")
    subprocess.run(["sudo", "mv", "bin/cardano-node", CARDANO_NODE_INSTALL_DIR], check=True)
    subprocess.run(["sudo", "mv", "bin/cardano-cli", CARDANO_CLI_INSTALL_DIR], check=True)

    print("\n🧹 Cleaning up...")
    os.chdir(os.path.expanduser("~"))
    shutil.rmtree(tmp_dir, ignore_errors=True)

def _normalize_tag(tag):
    """Return candidate tag names with/without 'v' prefix to maximize compatibility."""
    if not tag:
        return []
    candidates = [tag]
    if tag.startswith("v"):
        candidates.append(tag[1:])
    else:
        candidates.append("v" + tag)
    # de-duplicate while preserving order
    seen = set()
    uniq = []
    for t in candidates:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq

def _ensure_correct_origin():
    """Ensure 'origin' remote points to the official IntersectMBO repo."""
    try:
        url = subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).strip()
    except subprocess.CalledProcessError:
        url = ""
    if url != GITHUB_REPO_URL:
        print(f"ℹ️  Adjusting 'origin' remote URL to {GITHUB_REPO_URL}")
        if url:
            subprocess.run(["git", "remote", "set-url", "origin", GITHUB_REPO_URL], check=True)
        else:
            subprocess.run(["git", "remote", "add", "origin", GITHUB_REPO_URL], check=True)

def _fetch_all_with_tags():
    """Fetch all branches, tags and submodules, handle tag clobber issues."""
    try:
        subprocess.run(["git", "fetch", "--all", "--recurse-submodules", "--tags", "--prune", "--force"], check=True)
    except subprocess.CalledProcessError as e:
        # Try to recover from tag clobber problems by forcing again
        if "clobber existing tag" in str(e).lower():
            print("⚠️  Tag conflict detected. Retrying with forced fetch...")
            subprocess.run(["git", "fetch", "--tags", "--force", "--prune"], check=True)
        else:
            raise

def _tag_exists(tag):
    """Return True if the tag exists locally."""
    try:
        # faster than listing all tags; verify returns 0 if found
        subprocess.run(["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def _checkout_tag(tag):
    """Checkout given tag (by name or refs/tags/<tag>) force-detached."""
    # Prefer explicit tag ref
    res = subprocess.run(["git", "-c", "advice.detachedHead=false", "checkout", "-f", f"tags/{tag}"])
    if res.returncode == 0:
        return True
    # Fallback to bare tag name
    res = subprocess.run(["git", "-c", "advice.detachedHead=false", "checkout", "-f", tag])
    return res.returncode == 0

def install_from_source(latest_version):
    """
    Compile and install cardano-node from source.
    Handles directory creation, non-git folders, remote URL, tag fetching, checkout and build.
    """
    print("\n🛠️  Compiling from source...")

    # 🧹 Remove system-wide libsodium-dev to avoid conflicts
    subprocess.run(["sudo", "apt", "remove", "-y", "libsodium-dev"], check=False)

    # Ensure the parent directory exists
    parent_dir = os.path.dirname(CARDANO_SOURCE_DIR)
    os.makedirs(parent_dir, exist_ok=True)

    # Prepare repo directory
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
            subprocess.run(["git", "clone", GITHUB_REPO_URL, CARDANO_SOURCE_DIR], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Git clone failed: {e}")
            return

    # Enter repo
    try:
        os.chdir(CARDANO_SOURCE_DIR)
        print(f"✅ Current working directory: {os.getcwd()}")
    except Exception as e:
        print(f"❌ Failed to change directory to {CARDANO_SOURCE_DIR}: {e}")
        return

    # Ensure correct remote and fetch tags/submodules
    try:
        _ensure_correct_origin()
        _fetch_all_with_tags()
    except subprocess.CalledProcessError as e:
        print(f"❌ Git fetch failed: {e}")
        return

    # Normalize tag candidates (with/without 'v')
    candidates = _normalize_tag(latest_version)

    # If we already are on the desired commit, still proceed with build
    checked_out = False
    for tag in candidates:
        if not _tag_exists(tag):
            continue
        if _checkout_tag(tag):
            checked_out = True
            break

    if not checked_out:
        # Tag might not exist locally (despite fetch) ⇒ list tags for debug and exit
        try:
            tags_list = subprocess.check_output(["git", "tag", "--list"], text=True)
        except Exception:
            tags_list = "(failed to list)"
        print(f"❌ Could not checkout any of these tags: {candidates}\nAvailable tags:\n{tags_list}")
        return

    # Update submodules after checkout (cardano-node uses them)
    subprocess.run(["git", "submodule", "update", "--init", "--recursive"], check=True)

    # Build with cabal
    print("⚙️  Running cabal configure...")
    subprocess.run(["cabal", "update"], check=True)
    subprocess.run(["cabal", "configure", "-O0"], check=True)

    print("🔧 Building binaries...")
    subprocess.run(["cabal", "build", "all"], check=True)
    subprocess.run(["cabal", "build", "cardano-cli"], check=True)

    print("\n🔄 Backing up old binaries...")
    os.makedirs(CARDANO_BACKUP_DIR, exist_ok=True)
    subprocess.run(["sudo", "cp", f"{CARDANO_NODE_INSTALL_DIR}/cardano-node", f"{CARDANO_BACKUP_DIR}/cardano-node.bak"], check=False)
    subprocess.run(["sudo", "cp", f"{CARDANO_CLI_INSTALL_DIR}/cardano-cli", f"{CARDANO_BACKUP_DIR}/cardano-cli.bak"], check=False)

    print("🚚 Installing new binaries...")
    try:
        node_path = subprocess.check_output(["./scripts/bin-path.sh", "cardano-node"], text=True).strip()
        cli_path  = subprocess.check_output(["./scripts/bin-path.sh", "cardano-cli"],  text=True).strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to locate built binaries: {e}")
        return

    # Make sure nothing holds the binary
    check_and_kill_cardano_node_process()

    subprocess.run(["sudo", "cp", "-p", node_path, f"{CARDANO_NODE_INSTALL_DIR}/cardano-node"], check=True)
    subprocess.run(["sudo", "cp", "-p", cli_path,  f"{CARDANO_CLI_INSTALL_DIR}/cardano-cli"],  check=True)

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
        if not ask_user_to_continue("\nDo you still want to reinstall/build the current version from your chosen method?"):
            return
    else:
        if not ask_user_to_continue("\nDo you want to proceed with the upgrade?"):
            print("\n⛔ Upgrade cancelled by user.")
            return

    print("\nChoose installation method:")
    print("\n1 - Pre-built binaries from GitHub")
    print("2 - Compile from source")
    method = prompt("\nSelect method (1/2): ", validator=method_validator).strip()

    subprocess.run(["sudo", "systemctl", "stop", f"{CARDANO_SERVICE_NAME}.service"], check=False)

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
        subprocess.run(["sudo", "systemctl", "start", f"{CARDANO_SERVICE_NAME}.service"], check=False)
        print("🚀 Cardano node restarted.")
    else:
        print("⏸️  Cardano node not restarted.")

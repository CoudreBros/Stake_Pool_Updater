import os
import requests
import shutil
import subprocess
from dotenv import load_dotenv
from spu_helpers import ask_user_to_continue, print_header, clear_terminal

load_dotenv()

# === Load environment variables ===
NODE_CONFIG_PATH = os.path.expanduser(os.getenv("NODE_CONFIG_PATH", ""))
CARDANO_SERVICE_NAME = os.getenv("CARDANO_SERVICE_NAME", "cardano-node")
CARDANO_CONFIG_URL_BASE = "https://book.play.dev.cardano.org/environments/mainnet"
IS_BLOCK_PRODUCER = os.getenv("IS_BLOCK_PRODUCER", "false").lower() == "true"

# === Filenames to update ===
FILES_TO_UPDATE = [
    "byron-genesis.json",
    "shelley-genesis.json",
    "alonzo-genesis.json",
    "conway-genesis.json",
    "checkpoints.json"
]

def print_warning():

    clear_terminal()
    print_header("Download and update Cardano configuration files")
    print()

    print("⚠️  Please read the following documentation carefully before proceeding:\n")
    print("🔗 CoinCashew guide:")
    print("   https://www.coincashew.com/coins/overview-ada/guide-how-to-build-a-haskell-stakepool-node/part-iv-administration/upgrading-a-node#downloading-new-configuration-files")
    print("🔗 Official Cardano Configurations:")
    print("   https://book.play.dev.cardano.org/env-mainnet.html\n")

def stop_cardano_node():
    print(f"🛑 Attempting to stop service {CARDANO_SERVICE_NAME}.service ...")
    subprocess.run(["sudo", "systemctl", "stop", f"{CARDANO_SERVICE_NAME}.service"])

def backup_file(filepath):
    if os.path.isfile(filepath):
        backup_path = filepath + ".bak"
        shutil.copy(filepath, backup_path)
        print(f"🔄 Backed up {filepath} -> {backup_path}")

def download_file(filename):
    url = f"{CARDANO_CONFIG_URL_BASE}/{filename}"
    destination = os.path.join(NODE_CONFIG_PATH, filename)
    print(f"⬇️  Downloading {filename} from:\n   {url}")
    response = requests.get(url)
    if response.status_code == 200:
        with open(destination, "wb") as f:
            f.write(response.content)
        print(f"✅ Saved to {destination}")
    else:
        print(f"❌ Failed to download {filename} (HTTP {response.status_code})")

def compare_with_backup(filename):
    original = os.path.join(NODE_CONFIG_PATH, filename + ".bak")
    updated = os.path.join(NODE_CONFIG_PATH, filename)
    if os.path.isfile(original) and os.path.isfile(updated):
        print(f"\n🔍 Launching vimdiff for {filename} and its backup...")
        subprocess.run(["vimdiff", original, updated])
    else:
        print(f"⚠️  Either {filename} or its backup not found – skipping diff.")

def run_config_update():
    print_warning()

    if not ask_user_to_continue("Do you want to continue with stopping the Cardano node?"):
        print("⛔ Operation cancelled by user.")
        return

    stop_cardano_node()

    if ask_user_to_continue("\nDo you want to back up current config and genesis files (.bak)?"):
        config_file = "config-bp.json" if IS_BLOCK_PRODUCER else "config.json"
        FILES_TO_UPDATE.insert(0, config_file)

        for filename in FILES_TO_UPDATE:
            path = os.path.join(NODE_CONFIG_PATH, filename)
            backup_file(path)
    else:
        print("⏭️  Skipping backup step.")
        return

    if ask_user_to_continue("\nDo you want to download latest config and genesis files?"):
        print("\n📥 Downloading latest config and genesis files ...")
        for filename in FILES_TO_UPDATE:
            download_file(filename)
    else:
        print("⏭️  Skipping download of new config files.")
        return

    if not ask_user_to_continue("\nDo you want to compare the new files with their backups using vimdiff?"):
        print("🔙 Skipping comparison and returning to main menu.")
        return

    print("\n🧪 Ready to compare new config files with backups using vimdiff.")
    print("👉 Each file will open one-by-one in the editor.")
    print("""
📘 VIMDIFF TIPS:
- ]c : Jump to next difference
- [c : Jump to previous difference
- do : Get change from other file (Diff Obtain)
- dp : Push change to other file (Diff Put)
- :wq : Save and exit
- :qa : Quit all without saving
""")
    input("Press Enter to begin comparing files...")

    for filename in FILES_TO_UPDATE:
        compare_with_backup(filename)

    print("\n✅ Configuration update completed. Please review diffs above and start the node when ready.")

#!/usr/bin/env python3

import os
import subprocess
from dotenv import load_dotenv
from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator
from node_updater import run_node_upgrade


# === Local modules ===
from cncli_checker import check_and_update_cncli
from ghc_tools import prompt_for_ghcup_tui
from native_libs import check_and_install_libs
from config_updater import run_config_update

# === Load configuration ===
load_dotenv()

# === Prompt validator ===
menu_validator = Validator.from_callable(
    lambda text: text in ["0", "1", "2", "3", "4", "5"],
    error_message="Please enter a valid option: 0, 1, 2, 3, 4 or 5",
    move_cursor_to_end=True,
)

def clear_terminal():
    """Clear the terminal screen."""
    subprocess.run(["clear"])

def main_menu():
    while True:
        clear_terminal()
        print("🛠️  Stake Pool Updater – Main Menu\n")
        print("1 - Check & update CNCLI")
        print("2 - Check required GHC/Cabal & launch ghcup tui")
        print("3 - Check & install required native libraries (libsodium, secp256k1, blst, lmdb library)")
        print("4 - Download and update Cardano configuration files")
        print("5 - Upgrade cardano-node (choose method)")
        print("0 - Exit\n")

        choice = prompt("Select an option: ", validator=menu_validator).strip()

        if choice == "1":
            check_and_update_cncli()
        elif choice == "2":
            prompt_for_ghcup_tui()
        elif choice == "3":
            check_and_install_libs()
        elif choice == "4":
            run_config_update()
        elif choice == "5":
            run_node_upgrade()
        elif choice == "0":
            print("👋 Exiting.")
            break
        else:
            print("❌ Invalid choice.")

        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main_menu()
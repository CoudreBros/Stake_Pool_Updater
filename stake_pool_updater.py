#!/usr/bin/env python3

import os
import subprocess
from dotenv import load_dotenv
from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator
from node_updater import run_node_upgrade


# === Local modules ===
from cncli_checker import check_and_update_cncli
from guild_view_updater import run_gLiveView_updater
from ghc_tools import prompt_for_ghcup_tui
from native_libs import check_and_install_libs
from config_updater import run_config_update
from spu_helpers import clear_terminal, print_header


# === Load configuration ===
load_dotenv()

# === Prompt validator ===
menu_validator = Validator.from_callable(
    lambda text: text in ["0", "1", "2", "3", "4", "5", "6"],
    error_message="Please enter a valid option: 0, 1, 2, 3, 4, 5 or 6",
    move_cursor_to_end=True,
)

def main_menu():
    while True:
        clear_terminal()
        print_header("🛠️  Stake Pool Updater – Main Menu")
        print()
        
        print("1 - Check & update CNCLI")
        print("2 - Update Guild LiveView")
        print("3 - Check required GHC/Cabal & launch ghcup tui")
        print("4 - Check & install required native libraries (libsodium, secp256k1, blst, lmdb library)")
        print("5 - Download and update Cardano configuration files")
        print("6 - Upgrade cardano-node (choose method)")
        print("0 - Exit\n")

        choice = prompt("Select an option: ", validator=menu_validator).strip()

        if choice == "1":
            check_and_update_cncli()
        elif choice == "2":
            run_gLiveView_updater()
        elif choice == "3":
            prompt_for_ghcup_tui()
        elif choice == "4":
            check_and_install_libs()
        elif choice == "5":
            run_config_update()
        elif choice == "6":
            run_node_upgrade()
        elif choice == "0":
            print("👋 Exiting.")
            break
        else:
            print("❌ Invalid choice.")

        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n👋 Program interrupted by user. Exiting...")
import os
import requests
import subprocess
import html
from bs4 import BeautifulSoup

# === Načtení proměnných z prostředí ===
CARDANO_INSTALL_GUIDE = os.getenv(
    "CARDANO_INSTALL_GUIDE",
    "https://developers.cardano.org/docs/get-started/cardano-node/installing-cardano-node"
)


def get_required_versions_official():
    """Scrapes Cardano install docs for required GHC and Cabal versions."""
    try:
        response = requests.get(CARDANO_INSTALL_GUIDE)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        code_blocks = soup.find_all("code")

        ghc = "unknown"
        cabal = "unknown"

        for code in code_blocks:
            text = html.unescape(code.text.strip())
            if ">=" not in text:
                continue

            if text.lower().startswith("ghc"):
                parts = text.split(">=")
                if len(parts) > 1:
                    ghc = parts[1].strip()
            elif text.lower().startswith("cabal"):
                parts = text.split(">=")
                if len(parts) > 1:
                    cabal = parts[1].strip()

        return ghc, cabal

    except Exception as e:
        print(f"❌ Failed to fetch official required versions: {e}")
        return "unknown", "unknown"


def prompt_for_ghcup_tui():
    """Displays required versions and optionally launches ghcup tui."""
    ghc, cabal = get_required_versions_official()

    print("\n📌 Required versions from official Cardano documentation:")
    print(f"   GHC:   >= {ghc}")
    print(f"   Cabal: >= {cabal}")

    answer = input("\n🛠️  Do you want to launch ghcup tui to install them? [y/N]: ").strip().lower()
    if answer == 'y':
        subprocess.run(["ghcup", "tui"])
    else:
        print("➡️  Skipping ghcup tui.")

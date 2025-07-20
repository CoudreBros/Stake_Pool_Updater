#!/usr/bin/env python3

import os
from dotenv import load_dotenv

REQUIRED_VARS = [
    "NODE_CONFIG_PATH",
    "CARDANO_SERVICE_NAME",
    "CNCLI_INSTALL_DIR",
    "CARDANO_NODE_INSTALL_DIR",
    "CARDANO_CLI_INSTALL_DIR",
    "CARDANO_NETWORK",
    "CNCLI_GITHUB_API",
    "CNCLI_DOWNLOAD_BASE",
    "CARDANO_INSTALL_GUIDE"
]

def test_env():
    print("🔍 Loading .env ...")
    loaded = load_dotenv()
    
    if not loaded:
        print("❌ .env file not found or failed to load.")
        return

    print("✅ .env loaded successfully.\n")

    missing = []
    for var in REQUIRED_VARS:
        value = os.getenv(var)
        if value is None:
            missing.append(var)
        else:
            print(f"{var} = {value}")

    if missing:
        print("\n⚠️  The following required variables are missing from .env:")
        for var in missing:
            print(f"   - {var}")
    else:
        print("\n✅ All required variables are present.")

if __name__ == "__main__":
    test_env()

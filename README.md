# 🛠️ Stake Pool Updater (SPU)

**Stake Pool Updater (SPU)** is a modular, interactive tool for upgrading your Cardano stake pool infrastructure.  
It streamlines the upgrade process as described in the [CoinCashew stake pool guide](https://www.coincashew.com/coins/overview-ada/guide-how-to-build-a-haskell-stakepool-node/part-iv-administration/upgrading-a-node), including tasks such as:

- Managing CNCLI
- Checking required native libraries (e.g., libsodium, secp256k1, blst)
- Downloading and verifying updated config and genesis files
- Upgrading `cardano-node` (via prebuilt binaries or from source)

SPU is suitable for **block producers** and **relay nodes** alike.

---

## 📦 Requirements

Before installing or running the Stake Pool Updater (SPU), ensure your system meets the following requirements:

- ✅ Linux system (Debian-based recommended)
- ✅ `git` (for cloning the repository)
- ✅ `bash` shell
- ✅ `curl` (for running the installer via URL)
- ✅ `python3` (version 3.8+ recommended)
- ✅ `pip` (Python package manager)
- ✅ `venv` module (for creating isolated Python environments)
- ✅ `wget`, `tar` and other standard Unix tools
- ✅ `sudo` privileges (for installing/upgrading system-level binaries)

You can install missing dependencies on Ubuntu/Debian using:

```bash
sudo apt update
sudo apt install -y git curl python3 python3-pip python3-venv wget tar

---

## 🚀 Installation

The easiest way to install SPU is using the provided installer script:

```bash
curl -sL https://raw.githubusercontent.com/CoudreBros/Stake_Pool_Updater/main/SPU_Installer.sh | bash
```

Alternatively, you can manually clone the repository and run the installer:

```bash
git clone https://github.com/CoudreBros/Stake_Pool_Updater.git
cd Stake_Pool_Updater
./SPU_installer.sh
```

---

## ⚙️ Configuration

During installation, SPU_installer.sh will create a `.env` file based on the `.env.example` template. Adjust it according to your setup:

```bash
nano .env
```

Key configuration variables:

```ini
# Set to true if this node is a Block Producer; otherwise, set to false
IS_BLOCK_PRODUCER=false

# Where CNCLI will be installed
CNCLI_INSTALL_DIR=/usr/local/bin

# Where cardano-node binary will be installed
CARDANO_NODE_INSTALL_DIR=/usr/local/bin

# Where cardano-cli binary will be installed
CARDANO_CLI_INSTALL_DIR=/usr/local/bin

# Directory where Cardano source will be cloned and built
CARDANO_SOURCE_DIR=$HOME/git/cardano-node-src

# Directory to store backups of cardano-node and cardano-cli
CARDANO_BACKUP_DIR=$HOME/backups-cardano-binaries

# Path to your node configuration directory
NODE_CONFIG_PATH=$HOME/cardano-my-node

# Name of the systemd service that runs your Cardano node
CARDANO_SERVICE_NAME=cardano-node
```

---

## 🧰 Usage

After instalation run stake_pool_updter.sh in terminal.

You will be presented with an interactive main menu offering all supported operations.

---

## 🔐 Safety Features

- SPU **never runs external scripts silently** – all major steps require confirmation.
- Existing binaries and config files are **safely backed up** before changes.
- Designed with transparency and control in mind.

---

## 🧑‍💻 For Developers

SPU is modular by design. Each task is implemented as a separate Python module, making the project easy to extend or customize.

Contributions are welcome. Feel free to open a pull request or issue.

---

## 📄 License

MIT License © 2025 Stake Pool Updater Contributors

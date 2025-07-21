#!/bin/bash

# === CONFIGURATION ===
REPO_URL="${SPU_REPO_URL:-https://github.com/CoudreBros/Stake_Pool_Updater.git}"
CLONE_DIR="${SPU_CLONE_DIR:-$HOME/Stake_Pool_Updater}"
BRANCH="${SPU_BRANCH:-main}"
PYTHON_BIN="${SPU_PYTHON:-python3}"

# === COLORS ===
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
NC="\033[0m"

# === HELPERS ===
function info() { echo -e "${GREEN}▶ $1${NC}"; }
function warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
function error() { echo -e "${RED}✖ $1${NC}" >&2; exit 1; }

# === DEPENDENCY CHECK ===
for cmd in git $PYTHON_BIN pip; do
    if ! command -v "$cmd" &>/dev/null; then
        error "Required command '$cmd' is not installed. Please install it and try again."
    fi
done

# === PATH INFO ===
echo -e "\n📂 The Stake Pool Updater will be installed to: ${CLONE_DIR}"
echo    "   You can override this by setting the SPU_CLONE_DIR environment variable."

# === CLONE OR UPDATE REPO ===
info "Preparing Stake Pool Updater in: $CLONE_DIR"

if [ ! -d "$CLONE_DIR" ]; then
    info "Cloning repository..."
    git clone --branch "$BRANCH" "$REPO_URL" "$CLONE_DIR" || error "Failed to clone repository."
else
    info "Repository already exists. Pulling latest changes..."
    git -C "$CLONE_DIR" pull origin "$BRANCH" || error "Failed to update repository."
fi

cd "$CLONE_DIR" || error "Failed to enter $CLONE_DIR"

# === CREATE & ACTIVATE VENV ===
if [ ! -d "venv" ]; then
    info "Creating Python virtual environment..."
    $PYTHON_BIN -m venv venv || error "Failed to create virtualenv."
fi

info "Activating virtual environment..."
source venv/bin/activate

# === INSTALL DEPENDENCIES ===
info "Installing Python requirements..."
pip install --upgrade pip
pip install -r requirements.txt || error "Failed to install dependencies."

# === MAKE THE MAIN SHELL SCRIPT EXECUTABLE ===
chmod +x "${CLONE_DIR}/stake_pool_updater.sh"

# === CREATE .env IF MISSING ===
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        warn ".env was created from .env.example. Please review it before running the updater."
    else
        error "No .env or .env.example found in repository!"
    fi
fi

# === DEFAULT BEHAVIOR: NO AUTO RUN ===
if [[ "$1" != "--run" ]]; then
    info "✅ Installation complete."
    echo -e "\n📦 To launch Stake Pool Updater manually:"
    echo "   cd \"$CLONE_DIR\""
    echo "   ./stake_pool_updater.sh"
    echo -e "\n💡 You can re-run this installer with '--run' to launch SPU immediately after setup."
    exit 0
fi

# === RUN MAIN UPDATER ===
info "Launching Stake Pool Updater..."
./stake_pool_updater.sh

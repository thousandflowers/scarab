#!/bin/bash
# installers/install_client.sh
set -e

echo "=========================================="
echo "  Scarab v0.1 - Client Setup              "
echo "=========================================="

OS="$(uname -s)"
echo "[1/4] Detecting OS: $OS"

if [ "$OS" != "Darwin" ] && [ "$OS" != "Linux" ]; then
    echo "This script only supports macOS or Linux."
    exit 1
fi

echo "[2/4] Setting up minimal client dependencies..."
mkdir -p ~/.scarab
if ! command -v python3 &> /dev/null; then
    echo "python3 is required. Please install it."
    exit 1
fi

python3 -m venv ~/.scarab/venv
~/.scarab/venv/bin/pip install --upgrade pip
~/.scarab/venv/bin/pip install mitmproxy httpx rich aria2p fastapi

echo "[3/4] Installing Scarab CLI..."
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
~/.scarab/venv/bin/pip install -e "$DIR/.." || echo "Fallback: copy scarab folder manually or pip install."

echo "[4/4] Fetching remote CA and trusting it..."
echo "Note: To complete setup, run '~/.scarab/venv/bin/scarab connect' to fetch and trust the remote Server CA."

echo "Client setup successfully completed!"

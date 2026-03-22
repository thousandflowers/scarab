#!/bin/bash
set -e

echo "=========================================="
echo "  Scarab v0.1 - Server Setup              "
echo "=========================================="

OS="$(uname -s)"
ARCH="$(uname -m)"
echo "[1/4] Detecting OS: $OS ($ARCH)"

setup_pi_linux() {
    if [ "$EUID" -ne 0 ]; then
        echo "Please run as root (sudo ./install_server.sh)"
        exit 1
    fi
    apt-get update && apt-get install -y curl ca-certificates
    
    if ! command -v docker &> /dev/null; then
        echo "Installing Docker..."
        curl -fsSL https://get.docker.com | sh
    fi
    DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
    mkdir -p /opt/scarab
    cp -r "$DIR/.."/* /opt/scarab/ || true
    cd /opt/scarab
    docker compose up -d
}

setup_mac() {
    if ! command -v brew &> /dev/null; then
        echo "Homebrew is required. Installing..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    echo "Installing backend dependencies..."
    brew install python3 aria2 ntfy
    
    # We assume 'scarab' works if copied in PATH or via explicit pip install
    python3 -m venv ~/.scarab/venv
    DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
    ~/.scarab/venv/bin/pip install mitmproxy fastapi uvicorn httpx rich aria2p
    ~/.scarab/venv/bin/pip install -e "$DIR/.."
    
    echo "To start the server, run: ~/.scarab/venv/bin/scarab start"
}

if [ "$OS" = "Linux" ]; then
    setup_pi_linux
elif [ "$OS" = "Darwin" ]; then
    setup_mac
else
    echo "OS not specifically supported in auto-script: $OS"
    exit 1
fi

echo "[4/4] Setup completed successfully!"
echo "If running on Pi, Tailscale and Docker compose are active."
echo "If running on Mac, background services are ready."

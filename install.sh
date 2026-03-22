#!/bin/bash
set -e

echo "==================================="
echo "  Scarab v0.1 - Installazione Pi   "
echo "==================================="

if [ "$EUID" -ne 0 ]; then
  echo "Per favore lancia lo script con sudo: sudo ./install.sh"
  exit 1
fi

echo "[1/6] Configurazione directory..."
mkdir -p /var/scarab/downloads
mkdir -p /var/scarab/config/aria2
mkdir -p /var/scarab/config/filebrowser
mkdir -p /var/scarab/config/ntfy
mkdir -p /opt/scarab

touch /var/scarab/config/filebrowser/filebrowser.db
echo "{}" > /var/scarab/config/filebrowser/settings.json

echo "[2/6] Installazione dipendenze di sistema..."
apt-get update
apt-get install -y default-jre curl gnupg lsb-release xxd ssh

if ! command -v docker &> /dev/null; then
    echo "Installazione Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker pi || true
fi

echo "[3/6] Configurazione ambiente..."
ARIA2_SECRET=$(head -c 16 /dev/urandom | xxd -p)
echo "ARIA2_SECRET=$ARIA2_SECRET" > /opt/scarab/.env

if [ -f "./docker-compose.yml" ]; then
    cp -r . /opt/scarab/
fi

echo "[4/6] Generazione CA locale (Fase 5 preparation)..."
if [ ! -f /var/scarab/config/scarab-ca.pem ]; then
    mkdir -p /var/scarab/config/certs
    openssl genrsa -out /var/scarab/config/certs/ca.key 2048
    openssl req -x509 -new -nodes -key /var/scarab/config/certs/ca.key -sha256 -days 3650 -out /var/scarab/config/certs/ca.pem -subj "/CN=Scarab CA/O=Scarab Proxy/C=IT"
    cp /var/scarab/config/certs/ca.pem /var/scarab/config/scarab-ca.pem
fi

echo "[5/6] Creazione scarab.conf di default..."
if [ ! -f /var/scarab/config/scarab.conf ]; then
cat <<EOF > /var/scarab/config/scarab.conf
[proxy]
port = 8080
threshold_mb = 100
auto_offload = true
bypass_domains = apple.com,icloud.com,whatsapp.com

[orchestrator]
primary_node_url = http://127.0.0.1:7800

[downloader]
local_downloads_dir = /var/scarab/downloads

[notifier]
ntfy_topic = scarab_alerts
ntfy_server = http://scarab-ntfy:2586
EOF
fi

echo "[6/6] Avvio servizi tramite Docker Compose..."
cd /opt/scarab
docker compose up -d

echo ""
echo "========================================================="
echo "Installazione completata con successo!"
echo "- FileBrowser è disponibile su: http://[tailscale-ip]:8080"
echo "  (Default login admin/admin)"
echo "- Orchestrator in ascolto su: http://[tailscale-ip]:7800"
echo "- ARIA2 Secret: $ARIA2_SECRET"
echo "========================================================="

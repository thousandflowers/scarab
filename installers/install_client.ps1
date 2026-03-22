# installers/install_client.ps1
Write-Host "=========================================="
Write-Host "  Scarab v0.1 - Client Setup (Windows)    "
Write-Host "=========================================="

Write-Host "[1/4] Checking python installation..."
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python is required. Please install Python 3.11+"
    exit 1
}

Write-Host "[2/4] Creating virtual environment..."
$ScarabDir = "$env:USERPROFILE\.scarab"
if (!(Test-Path $ScarabDir)) {
    New-Item -ItemType Directory -Force -Path $ScarabDir | Out-Null
}

python -m venv "$ScarabDir\venv"
& "$ScarabDir\venv\Scripts\pip.exe" install --upgrade pip
& "$ScarabDir\venv\Scripts\pip.exe" install mitmproxy httpx rich
& "$ScarabDir\venv\Scripts\pip.exe" install -e ..

Write-Host "[3/4] Scarab CLI installed."

Write-Host "[4/4] Setting up CA and proxy..."
Write-Host "Run '$ScarabDir\venv\Scripts\scarab connect' to fetch and install the server certificate."

Write-Host "Setup complete!"

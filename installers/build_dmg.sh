#!/bin/bash
# installers/build_dmg.sh
set -e

echo "Building Scarab macOS DMG..."
if ! command -v create-dmg &> /dev/null; then
    echo "create-dmg not found. Install it via 'brew install create-dmg'."
    exit 1
fi

mkdir -p dist/Scarab.app/Contents/MacOS/lib
# Copia l'intero pacchetto scarab per evitare ModuleNotFoundError
cp -r ../scarab dist/Scarab.app/Contents/MacOS/lib/scarab

# Crea un wrapper bash di entrypoint
cat << 'EOF' > dist/Scarab.app/Contents/MacOS/scarab
#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
export PYTHONPATH="$DIR/lib"
exec python3 -m scarab.cli start
EOF
chmod +x dist/Scarab.app/Contents/MacOS/scarab

create-dmg \
  --volname "Scarab v0.1" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "Scarab.app" 200 190 \
  --hide-extension "Scarab.app" \
  --app-drop-link 600 185 \
  "Scarab.dmg" \
  "dist/"

echo "Scarab.dmg built in current directory."

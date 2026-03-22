#!/bin/bash
# installers/build_dmg.sh
set -e

echo "Building Scarab macOS DMG..."
if ! command -v create-dmg &> /dev/null; then
    echo "create-dmg not found. Install it via 'brew install create-dmg'."
    exit 1
fi

mkdir -p dist/Scarab.app/Contents/MacOS
cp ../scarab/cli.py dist/Scarab.app/Contents/MacOS/scarab
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

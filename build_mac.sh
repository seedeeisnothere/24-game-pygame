#!/bin/bash
# Builds "24 Game.app" and a shareable "24 Game.dmg" into dist/.
# Usage: ./build_mac.sh
set -euo pipefail
cd "$(dirname "$0")"

APP_NAME="24 Game"
PYTHON="${PYTHON:-python3}"
VENV=".build-venv"

# 1. Clean build environment with only what the game needs
if [ ! -x "$VENV/bin/python" ]; then
    "$PYTHON" -m venv "$VENV"
fi
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet pygame-ce pyinstaller

# 2. App icon from the planet sprite (nearest-neighbour upscale keeps it pixelated)
ICONSET="build/icon.iconset"
rm -rf "$ICONSET" && mkdir -p "$ICONSET"
for size in 16 32 128 256 512; do
    "$VENV/bin/python" - "$size" "$ICONSET" <<'EOF'
import sys, os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
size, out = int(sys.argv[1]), sys.argv[2]
img = pygame.image.load("assets/sprites/planet.png")
for scale, name in ((1, f"icon_{size}x{size}.png"), (2, f"icon_{size}x{size}@2x.png")):
    pygame.image.save(pygame.transform.scale(img, (size * scale, size * scale)),
                      os.path.join(out, name))
EOF
done
iconutil -c icns "$ICONSET" -o build/icon.icns

# 3. Bundle the game (debug_skip is a local dev cheat, keep it out)
rm -rf "dist/$APP_NAME.app" "dist/$APP_NAME.dmg"
"$VENV/bin/pyinstaller" --noconfirm --clean --windowed \
    --name "$APP_NAME" \
    --icon build/icon.icns \
    --osx-bundle-identifier "com.24game.app" \
    --add-data "assets:assets" \
    --add-data "data:data" \
    --exclude-module systems.debug_skip \
    --exclude-module tkinter \
    main.py

# 4. Disk image for sharing (drag-to-Applications layout)
STAGE="build/dmg"
rm -rf "$STAGE" && mkdir -p "$STAGE"
cp -R "dist/$APP_NAME.app" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
hdiutil create -quiet -volname "$APP_NAME" -srcfolder "$STAGE" -ov -format UDZO "dist/$APP_NAME.dmg"

echo "Built: dist/$APP_NAME.app and dist/$APP_NAME.dmg"

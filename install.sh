#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing Resolve Media Tool..."

# Copy icon into hicolor theme so KDE picks it up in search
mkdir -p "$HOME/.local/share/icons/hicolor/256x256/apps"
cp "$SCRIPT_DIR/assets/icon.png" "$HOME/.local/share/icons/hicolor/256x256/apps/resolve-media-tool.png"
gtk-update-icon-cache "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

# Write desktop file with correct path
cat > "$HOME/.local/share/applications/resolve-media-tool.desktop" <<EOF
[Desktop Entry]
Name=Resolve Media Tool
Comment=Upscale images and convert media for DaVinci Resolve
Exec=$SCRIPT_DIR/dist/resolve-media-tool/resolve-media-tool
Icon=resolve-media-tool
Terminal=false
Type=Application
Categories=AudioVideo;Video;Graphics;
EOF

# Refresh
update-desktop-database "$HOME/.local/share/applications/"
kbuildsycoca6 --noincremental 2>/dev/null || true

echo "Done. Resolve Media Tool is now in your app launcher."

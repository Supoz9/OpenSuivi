#!/usr/bin/env bash
# ============================================================
# build_appimage.sh — Construit l'AppImage d'OpenSuivi
# Usage : chmod +x build_appimage.sh && ./build_appimage.sh
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="OpenSuivi"
PYTHON_VERSION="3.11"

echo "╔════════════════════════════════════════════════╗"
echo "║     Construction de l'AppImage OpenSuivi       ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# ── 1. Vérification de Python ──
echo "▸ Vérification de Python..."
if ! command -v python3 &>/dev/null; then
    echo "✘ Python 3 n'est pas installé. Installe-le avec :"
    echo "  sudo apt install python3 python3-pip python3-venv"
    exit 1
fi
PYTHON_VER=$(python3 --version 2>&1)
echo "  ✓ $PYTHON_VER"

# ── 2. Création d'un venv dédié au build ──
BUILD_VENV="$SCRIPT_DIR/.build_venv"
echo "▸ Création de l'environnement virtuel de build..."
python3 -m venv "$BUILD_VENV"
source "$BUILD_VENV/bin/activate"

echo "▸ Installation des dépendances..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "  ✓ Dépendances installées"

# ── 3. Build avec PyInstaller ──
echo "▸ Compilation avec PyInstaller (mode onefile)..."
pyinstaller \
    --noconsole \
    --onefile \
    --windowed \
    --add-data "assets:assets" \
    --name "$APP_NAME" \
    --distpath dist \
    --workpath build_pyinstaller \
    --specpath build_pyinstaller \
    main.py

if [ ! -f "dist/$APP_NAME" ]; then
    echo "✘ Erreur : le binaire dist/$APP_NAME n'a pas été créé."
    exit 1
fi
echo "  ✓ Binaire créé : dist/$APP_NAME"

# ── 4. Préparation de l'AppDir ──
echo "▸ Préparation de l'AppDir..."
APPDIR="$SCRIPT_DIR/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copier le binaire
cp "dist/$APP_NAME" "$APPDIR/usr/bin/$APP_NAME"
chmod +x "$APPDIR/usr/bin/$APP_NAME"

# Copier l'icône
cp assets/favicon.png "$APPDIR/favicon.png"
cp assets/favicon.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/favicon.png"

# Créer le fichier .desktop (ATTENTION : pas d'espaces au début des lignes !)
cat > "$APPDIR/$APP_NAME.desktop" << 'EOF'
[Desktop Entry]
Name=OpenSuivi
Exec=OpenSuivi
Icon=favicon
Type=Application
Categories=Education;Utility;
Comment=Logiciel de suivi de classe pour Bac Pro
EOF

# Lien symbolique AppRun
cat > "$APPDIR/AppRun" << 'APPRUN'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin/:${PATH}"
exec "${HERE}/usr/bin/OpenSuivi" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

echo "  ✓ AppDir prêt"

# ── 5. Téléchargement de appimagetool ──
APPIMAGETOOL="$SCRIPT_DIR/appimagetool-x86_64.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "▸ Téléchargement de appimagetool..."
    wget -q --show-progress -O "$APPIMAGETOOL" \
        "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "$APPIMAGETOOL"
    echo "  ✓ appimagetool téléchargé"
else
    echo "  ✓ appimagetool déjà présent"
fi

# ── 6. Construction de l'AppImage ──
echo "▸ Construction de l'AppImage..."
ARCH=x86_64 "$APPIMAGETOOL" --no-appstream "$APPDIR" "${APP_NAME}-x86_64.AppImage"

if [ -f "${APP_NAME}-x86_64.AppImage" ]; then
    echo ""
    echo "╔════════════════════════════════════════════════╗"
    echo "║  ✓ AppImage créée avec succès !                ║"
    echo "╚════════════════════════════════════════════════╝"
    echo ""
    echo "  Fichier : $(pwd)/${APP_NAME}-x86_64.AppImage"
    echo "  Taille  : $(du -h "${APP_NAME}-x86_64.AppImage" | cut -f1)"
    echo ""
    echo "  Pour l'exécuter :"
    echo "    chmod +x ${APP_NAME}-x86_64.AppImage"
    echo "    ./${APP_NAME}-x86_64.AppImage"
else
    echo "✘ Erreur lors de la création de l'AppImage."
    exit 1
fi

# ── 7. Nettoyage ──
echo "▸ Nettoyage..."
rm -rf "$BUILD_VENV" build_pyinstaller AppDir
deactivate 2>/dev/null || true
echo "  ✓ Nettoyage terminé"
echo ""
echo "Done ! 🎉"

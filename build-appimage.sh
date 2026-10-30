#!/bin/bash
# build-appimage.sh - Build Mechkeys as an AppImage (CachyOS/Arch)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="0.1.0"
APPDIR="${ROOT_DIR}/AppDir"

# ---- 1. System deps ----
if command -v pacman >/dev/null 2>&1; then
    sudo pacman -S --needed --noconfirm \
        base-devel python python-pip portaudio tk wget curl squashfs-tools
fi

# ---- 2. Python deps ----
python -m pip install --user --upgrade pip setuptools wheel
python -m pip install --user --upgrade \
    numpy sounddevice evdev pynput pyinstaller

# ---- 3. Entry point wrapper ----
cat > "${ROOT_DIR}/.entry.py" <<'PYEOF'
import ctypes.util
import os
import sys

exe_dir = os.path.dirname(os.path.realpath(sys.executable))
appdir = os.path.dirname(os.path.dirname(exe_dir))
lib_dir = os.path.join(appdir, 'usr', 'lib')
if not os.path.isdir(lib_dir):
    lib_dir = os.environ.get('MECHKEYS_LIB_DIR', lib_dir)
os.environ['LD_LIBRARY_PATH'] = lib_dir + ':' + os.environ.get('LD_LIBRARY_PATH', '')

_original_find = ctypes.util.find_library
def _find_library(name):
    if name == 'portaudio':
        for cand in ('libportaudio.so.2', 'libportaudio.so'):
            p = os.path.join(lib_dir, cand)
            if os.path.exists(p):
                return p
    return _original_find(name)
ctypes.util.find_library = _find_library

from mechkeys.__main__ import main
sys.exit(main())
PYEOF

# ---- 4. PyInstaller bundle ----
rm -rf "${ROOT_DIR}/build" "${ROOT_DIR}/dist" "${APPDIR}"
python -m PyInstaller --name mechkeys --onefile --clean --noconfirm \
    --paths "${ROOT_DIR}" \
    --hidden-import evdev --hidden-import sounddevice --hidden-import numpy \
    --hidden-import tkinter --hidden-import pynput \
    "${ROOT_DIR}/.entry.py"
rm -f "${ROOT_DIR}/.entry.py"

# ---- 5. AppDir layout ----
mkdir -p "${APPDIR}/usr/bin" "${APPDIR}/usr/lib" \
         "${APPDIR}/usr/share/applications" \
         "${APPDIR}/usr/share/icons/hicolor/256x256/apps" \
         "${APPDIR}/usr/share/icons/hicolor/48x48/apps"

cp "${ROOT_DIR}/dist/mechkeys" "${APPDIR}/usr/bin/mechkeys"
chmod +x "${APPDIR}/usr/bin/mechkeys"

# bundle native libs
for libdir in /usr/lib /usr/lib/x86_64-linux-gnu; do
    for lib in libportaudio.so* libtcl*.so* libtk*.so* libjansson.so*; do
        cp ${libdir}/${lib} "${APPDIR}/usr/lib/" 2>/dev/null || true
    done
done

cat > "${APPDIR}/AppRun" <<'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/mechkeys" "$@"
EOF
chmod +x "${APPDIR}/AppRun"

sed 's#^Exec=.*#Exec=mechkeys#' "${ROOT_DIR}/mechkeys.desktop" > "${APPDIR}/mechkeys.desktop"
cp "${APPDIR}/mechkeys.desktop" "${APPDIR}/usr/share/applications/mechkeys.desktop"

# icon
python3 -c "
from PIL import Image, ImageDraw
img = Image.new('RGBA', (256, 256), (30, 30, 30, 255))
d = ImageDraw.Draw(img)
d.rectangle([40, 80, 216, 176], fill=(70, 130, 180, 255), outline=(255,255,255,255), width=4)
d.text((90, 110), 'MK', fill=(255,255,255,255))
img.save('${APPDIR}/mechkeys.png')
img.resize((48,48)).save('${APPDIR}/usr/share/icons/hicolor/48x48/apps/mechkeys.png')
img.save('${APPDIR}/usr/share/icons/hicolor/256x256/apps/mechkeys.png')
" 2>/dev/null || true
sed -i 's/^Icon=.*/Icon=mechkeys/' "${APPDIR}/mechkeys.desktop"
sed -i 's/^Icon=.*/Icon=mechkeys/' "${APPDIR}/usr/share/applications/mechkeys.desktop"
sed -i 's/^Categories=.*/Categories=AudioVideo;Utility;/' "${APPDIR}/mechkeys.desktop"
sed -i 's/^Categories=.*/Categories=AudioVideo;Utility;/' "${APPDIR}/usr/share/applications/mechkeys.desktop"
ln -sf usr/share/icons/hicolor/256x256/apps/mechkeys.png "${APPDIR}/mechkeys.png" 2>/dev/null || true

# ---- 6. appimagetool ----
if ! command -v appimagetool >/dev/null 2>&1; then
    AT="${ROOT_DIR}/appimagetool"
    wget -q -O "${AT}" \
        "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "${AT}"
    APPIMAGETOOL="${AT} --appimage-extract-and-run"
else
    APPIMAGETOOL="appimagetool"
fi

ARCH=x86_64 ${APPIMAGETOOL} "${APPDIR}" \
    "${ROOT_DIR}/Mechkeys-${VERSION}-x86_64.AppImage"

echo "Done: ${ROOT_DIR}/Mechkeys-${VERSION}-x86_64.AppImage"
rm -rf "${APPDIR}" "${ROOT_DIR}/build" "${ROOT_DIR}/dist"
SCRIPT
echo "written"
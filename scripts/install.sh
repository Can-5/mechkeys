#!/usr/bin/env bash
set -e
echo "[mechkeys] Arch/CachyOS bağımlılıkları kuruluyor..."
sudo pacman -S --needed python python-pip portaudio tk
echo "[mechkeys] Python bağımlılıkları kuruluyor..."
python -m pip install --user -r requirements.txt
echo "[mechkeys] input grubuna ekleniyor (oturum yeniden açma gerekir)..."
sudo usermod -aG input "$USER" || true
echo "[mechkeys] Tamamlandı."

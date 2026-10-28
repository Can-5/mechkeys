# Mechkeys

Mekanik klavye ses simülatörü. Her tuş basımında seçilen switch profilinin
(Cherry MX Blue / Brown / Red) sesini çalar. Linux üzerinde global olarak
çalışır (X11 ve Wayland).

## Kurulum (CachyOS / Arch)

```bash
sudo pacman -S --needed python python-pip portaudio tk
cd mechkeys
python -m pip install --user -r requirements.txt
```

Tuş dinleme için `/dev/input/event*` okuma izni gerekir:

```bash
sudo usermod -aG input $USER
# oturumu kapatıp yeniden açın
```

## Çalıştırma

```bash
python -m mechkeys            # GUI ile
python -m mechkeys --no-gui   # arka planda (daemon)
python -m mechkeys --list-devices
python -m mechkeys --profile red --volume 0.5
```

## Özellikler

- 14 switch profili (Blue, Brown, Red, Topre, Buckling Spring, Gateron Ink, Kailh Box Jade, Silent Red, Zealio, Holy Panda, Alps, Romer-G, Optical, Membrane)
- 13 tuş sınıfı (normal, space, enter, backspace, tab, modifier, ok, fonksiyon, numpad, harf, sayı, noktalama, shift)
- Foxguard güvenlik katmanı: config doğrulama, izin sıkılaştırma (700/600), oynatma hız sınırlayıcı (DoS koruması), root uyarısı, tampon bütünlük kontrolü
- Hiçbir telemetri / ağ erişimi / shell / eval
- Ses seviyesi, etkin/pasif, modifier sesleri, jitter aç/kapa
- Görsel geri bildirim (tuş basımında flash) ve per-tür test butonları
- Düşük gecikmeli ses motoru (sounddevice), örtüşen sesler desteklenir
- Ayarlar `~/.config/mechkeys/config.json` dosyasına kaydedilir

## Notlar

- Wayland oturumlarında evdev backend kullanılır (pynput X11'de fallback).
- Sesler sentetik olarak üretilir; harici ses dosyası gerekmez.
- Hiçbir telemetri / ağ erişimi yok.

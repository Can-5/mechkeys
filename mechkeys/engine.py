"""Core engine: ties listener + audio + profiles together."""
import threading
import time
from . import config as cfgmod
from .profiles import PROFILES
from .audio import AudioEngine
from .listener import make_listener
from . import foxguard


class MechKeysEngine:
    def __init__(self, cfg=None):
        self.cfg = cfg if cfg is not None else foxguard.safe_load_config()
        self.cfg = foxguard.validate_config(self.cfg)
        foxguard.harden_paths()
        self.audio = AudioEngine(volume=self.cfg["volume"])
        self._buffers = {}
        self._build_buffers()
        self.listener = None
        self.running = False
        self.key_count = 0
        self._lock = threading.Lock()
        self._rate = foxguard.RateLimiter()

    def _build_buffers(self):
        from .audio import synth_variants
        prof = PROFILES[self.cfg["profile"]]
        kcs = ("normal", "space", "enter", "backspace", "tab", "modifier",
               "arrow", "function", "numpad", "letter", "number", "punct", "shift")
        self._buffers = {}
        for kc in kcs:
            bufs = synth_variants(prof, kc, 5)
            # keep only finite buffers
            safe = [b for b in bufs if foxguard.sanitize_buffer(b)]
            self._buffers[kc] = safe if safe else bufs

    def set_profile(self, name):
        from .profiles import PROFILES as P
        if name not in P:
            return
        self.cfg["profile"] = name
        self._build_buffers()
        cfgmod.save(self.cfg)
        foxguard.harden_paths()

    def set_volume(self, v):
        self.cfg["volume"] = max(0.0, min(1.0, float(v)))
        self.audio.set_volume(self.cfg["volume"])
        cfgmod.save(self.cfg)

    def set_enabled(self, enabled):
        self.cfg["enabled"] = bool(enabled)
        cfgmod.save(self.cfg)

    def _on_key(self, key_class):
        if not self.cfg.get("enabled", True):
            return
        if key_class == "modifier" and not self.cfg.get("play_modifiers", True):
            return
        if not self._rate.allow():
            return
        buf = self._buffers.get(key_class)
        if buf is None:
            buf = self._buffers.get("normal")
        if buf:
            self.audio.play(buf)
        with self._lock:
            self.key_count += 1

    def start(self):
        if self.running:
            return
        self.running = True
        self.listener = make_listener(self._on_key)
        self.listener.start()

    def stop(self):
        self.running = False
        if self.listener is not None:
            try:
                self.listener.stop()
            except Exception:
                pass
            self.listener = None

    def keyboard_count(self):
        l = self.listener
        if l is None:
            return 0
        devs = getattr(l, "devices", None)
        if devs is not None:
            return len(devs)
        return 1 if getattr(l, "running", False) else 0

    def close(self):
        self.stop()
        self.audio.close()
        cfgmod.save(self.cfg)
        foxguard.harden_paths()

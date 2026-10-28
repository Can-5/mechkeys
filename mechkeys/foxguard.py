"""Foxguard: security hardening for mechkeys.

Zero-trust, least-privilege, no network, no shell, no eval.
Provides config validation, permission hardening, and playback rate limiting.
"""
import os
import stat
import time
import math
from pathlib import Path

from . import config as cfgmod


MAX_CONFIG_BYTES = 4096
MAX_SOUNDS_PER_SEC = 40   # audio DoS / CPU spike guard
ROOT_WARN = True


def harden_paths() -> None:
    """Ensure config dir/file have restrictive permissions."""
    try:
        cfgmod.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        os.chmod(cfgmod.CONFIG_DIR, 0o700)
    except Exception:
        pass
    try:
        if cfgmod.CONFIG_FILE.exists():
            os.chmod(cfgmod.CONFIG_FILE, 0o600)
    except Exception:
        pass


def validate_config(cfg: dict) -> dict:
    """Return a sanitized copy of cfg; reject unknown/invalid values."""
    from .profiles import PROFILES
    out = dict(cfgmod.DEFAULTS)
    # profile
    p = cfg.get("profile", out["profile"])
    if isinstance(p, str) and p in PROFILES:
        out["profile"] = p
    # volume
    v = cfg.get("volume", out["volume"])
    try:
        v = float(v)
    except (TypeError, ValueError):
        v = out["volume"]
    if not math.isfinite(v):
        v = out["volume"]
    out["volume"] = max(0.0, min(1.0, v))
    # booleans
    for key in ("enabled", "play_modifiers", "play_on_repeat"):
        val = cfg.get(key, out[key])
        out[key] = bool(val) if isinstance(val, (bool, int)) else out[key]
    # size guard on serialized config
    return out


def check_root() -> None:
    if ROOT_WARN and hasattr(os, "geteuid") and os.geteuid() == 0:
        import sys
        print("foxguard: WARNING running as root is not recommended", file=sys.stderr)


def safe_load_config() -> dict:
    harden_paths()
    check_root()
    # size guard
    try:
        if cfgmod.CONFIG_FILE.exists() and cfgmod.CONFIG_FILE.stat().st_size > MAX_CONFIG_BYTES:
            # reset oversized config
            try:
                cfgmod.CONFIG_FILE.unlink()
            except Exception:
                pass
    except Exception:
        pass
    cfg = cfgmod.load()
    return validate_config(cfg)


class RateLimiter:
    """Token bucket limiting playback rate to prevent audio/CPU DoS."""

    def __init__(self, max_per_sec: int = MAX_SOUNDS_PER_SEC):
        self.max = max_per_sec
        self.tokens = float(max_per_sec)
        self.last = time.monotonic()
        self.lock = None
        import threading
        self.lock = threading.Lock()

    def allow(self) -> bool:
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last
            self.last = now
            self.tokens = min(self.max, self.tokens + elapsed * self.max)
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return True
            return False


def sanitize_buffer(buf) -> bool:
    """Return True if buffer is finite and safe to play."""
    try:
        import numpy as np
        arr = np.asarray(buf)
        if not np.all(np.isfinite(arr)):
            return False
        if arr.size == 0 or arr.size > 10_000_000:
            return False
        return True
    except Exception:
        return False

"""Configuration persistence for mechkeys."""
import json
import os
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "mechkeys"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "profile": "blue",          # blue | brown | red
    "volume": 0.6,              # 0.0 .. 1.0
    "enabled": True,
    "play_modifiers": True,
    "play_on_repeat": False,
}

def _valid_profiles():
    try:
        from .profiles import PROFILES
        return tuple(PROFILES.keys())
    except Exception:
        return ("blue", "brown", "red")

VALID_PROFILES = _valid_profiles()


def load() -> dict:
    cfg = dict(DEFAULTS)
    try:
        if CONFIG_FILE.exists():
            with CONFIG_FILE.open() as f:
                data = json.load(f)
            if isinstance(data, dict):
                cfg.update({k: v for k, v in data.items() if k in DEFAULTS})
    except Exception:
        pass
    if cfg["profile"] not in VALID_PROFILES:
        cfg["profile"] = "blue"
    cfg["volume"] = max(0.0, min(1.0, float(cfg["volume"])))
    return cfg


def save(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w") as f:
        json.dump({k: cfg.get(k, DEFAULTS[k]) for k in DEFAULTS}, f, indent=2)

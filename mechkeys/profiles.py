"""Switch profiles and per-key-class sound parameters."""
from dataclasses import dataclass


@dataclass
class SwitchProfile:
    name: str
    click_amp: float
    click_decay: float
    click_hp: float
    body_freq: float
    body_decay: float
    body_amp: float
    noise_mix: float
    release_amp: float
    release_decay: float
    body_freq2: float = 0.0
    body_freq2_amp: float = 0.0
    click_pitch_jitter: float = 0.04
    body_pitch_jitter: float = 0.03
    # timbre
    click_noise_color: float = 1.0   # 1.0 white-ish, <1 darker
    body_wave: str = "sine"         # sine | square-ish via harmonics


PROFILES = {
    "blue": SwitchProfile("Cherry MX Blue (clicky)", 0.75, 0.006, 4200, 190, 0.045, 0.55, 0.25, 0.18, 0.03, 380, 0.12),
    "brown": SwitchProfile("Cherry MX Brown (tactile)", 0.35, 0.005, 3000, 165, 0.06, 0.5, 0.18, 0.15, 0.035, 330, 0.08),
    "red": SwitchProfile("Cherry MX Red (linear)", 0.0, 0.001, 3000, 135, 0.08, 0.45, 0.12, 0.12, 0.04, 270, 0.06),
    "topre": SwitchProfile("Topre (electro-capacitive)", 0.12, 0.004, 2000, 110, 0.12, 0.6, 0.08, 0.22, 0.06, 220, 0.15, 0.02, 0.02),
    "buckling": SwitchProfile("Buckling Spring (Model M)", 0.95, 0.008, 3500, 230, 0.05, 0.7, 0.4, 0.3, 0.04, 460, 0.2, 0.06, 0.05),
    "gateron_ink": SwitchProfile("Gateron Ink Black (linear)", 0.0, 0.001, 3000, 120, 0.09, 0.4, 0.1, 0.1, 0.045, 240, 0.05, 0.04, 0.025),
    "kailh_box": SwitchProfile("Kailh Box Jade (clicky)", 0.85, 0.005, 4800, 210, 0.04, 0.5, 0.3, 0.2, 0.025, 420, 0.14, 0.05, 0.04),
    "silent": SwitchProfile("Silent Red (linear, damped)", 0.0, 0.001, 3000, 100, 0.1, 0.35, 0.05, 0.06, 0.05, 200, 0.03, 0.04, 0.015),
    "zealio": SwitchProfile("Zealios V2 (tactile)", 0.45, 0.005, 3200, 175, 0.055, 0.52, 0.2, 0.16, 0.032, 350, 0.1, 0.04, 0.03),
    "holypanda": SwitchProfile("Holy Panda (tactile)", 0.6, 0.006, 3600, 200, 0.05, 0.6, 0.28, 0.2, 0.03, 400, 0.15, 0.05, 0.04),
    "alps": SwitchProfile("Alps Blue (clicky)", 0.8, 0.007, 4000, 205, 0.048, 0.62, 0.32, 0.22, 0.03, 410, 0.16, 0.06, 0.05),
    "romerg": SwitchProfile("Romer-G (tactile)", 0.3, 0.004, 2800, 150, 0.065, 0.42, 0.15, 0.13, 0.038, 300, 0.07, 0.035, 0.03),
    "optical": SwitchProfile("Optical Red (linear)", 0.05, 0.002, 3500, 145, 0.075, 0.4, 0.14, 0.11, 0.04, 290, 0.06, 0.045, 0.03),
    "membrane": SwitchProfile("Membrane (rubber dome)", 0.0, 0.001, 2000, 90, 0.14, 0.3, 0.06, 0.08, 0.06, 180, 0.04, 0.02, 0.02, click_noise_color=0.6),
}

KEY_CLASSES = {
    "normal":    {"freq_mul": 1.00, "dur_mul": 1.00, "amp_mul": 1.00},
    "space":     {"freq_mul": 0.55, "dur_mul": 1.35, "amp_mul": 1.15},
    "enter":     {"freq_mul": 0.70, "dur_mul": 1.25, "amp_mul": 1.10},
    "backspace": {"freq_mul": 1.15, "dur_mul": 0.85, "amp_mul": 0.90},
    "tab":       {"freq_mul": 0.90, "dur_mul": 1.05, "amp_mul": 0.95},
    "modifier":  {"freq_mul": 0.80, "dur_mul": 0.90, "amp_mul": 0.70},
    "arrow":     {"freq_mul": 1.05, "dur_mul": 0.80, "amp_mul": 0.85},
    "function":  {"freq_mul": 0.95, "dur_mul": 1.10, "amp_mul": 0.90},
    "numpad":    {"freq_mul": 1.10, "dur_mul": 0.95, "amp_mul": 0.95},
    "letter":    {"freq_mul": 1.02, "dur_mul": 0.95, "amp_mul": 0.98},
    "number":    {"freq_mul": 1.08, "dur_mul": 0.90, "amp_mul": 0.95},
    "punct":     {"freq_mul": 1.12, "dur_mul": 0.85, "amp_mul": 0.90},
    "shift":     {"freq_mul": 0.75, "dur_mul": 0.85, "amp_mul": 0.65},
}

"""Sound synthesis and low-latency playback engine."""
import threading
import numpy as np

SR = 44100


def _highpass_noise(n: int, cutoff: float, rng: np.random.Generator) -> np.ndarray:
    noise = rng.standard_normal(n).astype(np.float32)
    if cutoff <= 0:
        return noise
    rc = 1.0 / (2 * np.pi * cutoff)
    dt = 1.0 / SR
    alpha = rc / (rc + dt)
    out = np.zeros(n, dtype=np.float32)
    prev_in = 0.0
    prev_out = 0.0
    for i in range(n):
        out[i] = alpha * (prev_out + noise[i] - prev_in)
        prev_in = noise[i]
        prev_out = out[i]
    return out


def synth(profile, key_class: str = "normal", variant: int = 0) -> np.ndarray:
    """Generate a mono float32 click buffer for the given profile + key class."""
    from .profiles import KEY_CLASSES

    kc = KEY_CLASSES.get(key_class, KEY_CLASSES["normal"])
    rng = np.random.default_rng(variant * 9973 + hash(profile.name) % 100000)

    # pitch jitter
    fj = 1.0 + rng.uniform(-profile.body_pitch_jitter, profile.body_pitch_jitter)
    cj = 1.0 + rng.uniform(-profile.click_pitch_jitter, profile.click_pitch_jitter)

    freq = profile.body_freq * kc["freq_mul"] * fj
    dur = 0.09 * kc["dur_mul"]
    amp = kc["amp_mul"]

    n = int(SR * dur)
    if n < 64:
        n = 64
    t = np.arange(n) / SR

    click_n = min(n, int(SR * 0.012))
    click_env = np.exp(-np.arange(click_n) / (SR * max(profile.click_decay, 1e-4)))
    click = _highpass_noise(click_n, profile.click_hp, rng) * click_env * profile.click_amp * cj

    body_env = np.exp(-t / max(profile.body_decay, 1e-4))
    body = np.sin(2 * np.pi * freq * t) * body_env * profile.body_amp
    if profile.body_freq2 > 0:
        body += (np.sin(2 * np.pi * profile.body_freq2 * fj * t) * body_env
                 * profile.body_freq2_amp)
    body += rng.standard_normal(n).astype(np.float32) * body_env * profile.noise_mix * 0.3

    # release tail
    rel_n = min(n, int(SR * profile.release_decay * 3))
    if rel_n > 0:
        rel_t = np.arange(rel_n) / SR
        rel_env = np.exp(-rel_t / max(profile.release_decay, 1e-4))
        rel = (np.sin(2 * np.pi * freq * 0.7 * rel_t) * rel_env * profile.release_amp)
        body[-rel_n:] += rel

    buf = np.zeros(n, dtype=np.float32)
    buf[:click_n] += click
    buf += body
    buf *= amp

    peak = np.max(np.abs(buf)) if buf.size else 1.0
    if peak > 0:
        buf = buf / peak * 0.9
    fade = int(SR * 0.002)
    if fade < n:
        buf[-fade:] *= np.linspace(1, 0, fade)

    # tiny amplitude jitter
    buf = buf * (1.0 + rng.uniform(-0.05, 0.05))
    return buf.astype(np.float32)


def synth_variants(profile, key_class: str = "normal", count: int = 4):
    return [synth(profile, key_class, v) for v in range(count)]


class AudioEngine:
    """Low-latency mixer that can play overlapping buffers."""

    def __init__(self, sr: int = SR, volume: float = 0.6):
        import sounddevice as sd
        self.sr = sr
        self.volume = float(volume)
        self.voices: list = []
        self.lock = threading.Lock()
        self.stream = sd.OutputStream(
            samplerate=sr, channels=1, dtype="float32",
            callback=self._callback, blocksize=256, latency="low",
        )
        self.stream.start()

    def _callback(self, outdata, frames, time_info, status):
        buf = np.zeros(frames, dtype=np.float32)
        with self.lock:
            new_voices = []
            for data, pos in self.voices:
                remaining = len(data) - pos
                if remaining <= 0:
                    continue
                n = min(frames, remaining)
                buf[:n] += data[pos:pos + n]
                new_pos = pos + n
                if new_pos < len(data):
                    new_voices.append((data, new_pos))
            self.voices = new_voices
        outdata[:, 0] = np.clip(buf * self.volume, -1.0, 1.0)

    def play(self, data) -> None:
        if isinstance(data, (list, tuple)):
            import random
            data = random.choice(data)
        with self.lock:
            self.voices.append((np.asarray(data, dtype=np.float32), 0))

    def set_volume(self, v: float) -> None:
        self.volume = max(0.0, min(1.0, float(v)))

    def close(self) -> None:
        try:
            self.stream.stop()
            self.stream.close()
        except Exception:
            pass

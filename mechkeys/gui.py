"""Tkinter GUI for mechkeys."""
import threading
import tkinter as tk
from tkinter import ttk

from .config import save, VALID_PROFILES
from .foxguard import safe_load_config
from .engine import MechKeysEngine
from .profiles import PROFILES


class MechKeysApp:
    def __init__(self):
        self.cfg = safe_load_config()
        self.engine = MechKeysEngine(self.cfg)
        self.root = tk.Tk()
        self.root.title("Mechkeys")
        self.root.geometry("460x620")
        self.root.resizable(False, False)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        self._build()
        self.engine.start()
        self._last_count = 0
        self._tick()

    def _build(self):
        pad = {"padx": 12, "pady": 6}

        ttk.Label(self.root, text="Mechkeys", font=("Sans", 18, "bold")).pack(pady=(12, 2))
        ttk.Label(self.root, text="Mekanik klavye ses simülatörü", foreground="#666").pack()

        # Visual flash
        self.flash = tk.Canvas(self.root, height=40, bg="#f0f0f0", highlightthickness=0)
        self.flash.pack(fill="x", padx=12, pady=6)
        self.flash_rect = self.flash.create_rectangle(0, 0, 460, 40, fill="#f0f0f0", outline="")

        # Profile
        frame = ttk.LabelFrame(self.root, text="Switch profili")
        frame.pack(fill="x", **pad)
        self.profile_var = tk.StringVar(value=self.cfg["profile"])
        cb = ttk.Combobox(frame, textvariable=self.profile_var,
                          values=[PROFILES[p].name for p in VALID_PROFILES],
                          state="readonly")
        cb.pack(fill="x", padx=8, pady=6)
        cb.bind("<<ComboboxSelected>>", self._on_profile_combo)
        self.profile_desc = ttk.Label(frame, text="", foreground="#666", wraplength=420)
        self.profile_desc.pack(anchor="w", padx=8, pady=(0, 6))
        self._update_desc()

        # Volume
        vframe = ttk.LabelFrame(self.root, text="Ses seviyesi")
        vframe.pack(fill="x", **pad)
        self.vol_var = tk.DoubleVar(value=self.cfg["volume"])
        scale = ttk.Scale(vframe, from_=0.0, to=1.0, orient="horizontal",
                          variable=self.vol_var, command=self._on_volume)
        scale.pack(fill="x", padx=8, pady=4)
        self.vol_label = ttk.Label(vframe, text=f"{int(self.cfg['volume']*100)}%")
        self.vol_label.pack(anchor="e", padx=8)

        # Toggles
        tframe = ttk.LabelFrame(self.root, text="Seçenekler")
        tframe.pack(fill="x", **pad)
        self.enabled_var = tk.BooleanVar(value=self.cfg["enabled"])
        ttk.Checkbutton(tframe, text="Etkin", variable=self.enabled_var,
                        command=self._on_enabled).pack(anchor="w", padx=8, pady=2)
        self.mods_var = tk.BooleanVar(value=self.cfg.get("play_modifiers", True))
        ttk.Checkbutton(tframe, text="Modifier tuşlarında da çal", variable=self.mods_var,
                        command=self._on_mods).pack(anchor="w", padx=8, pady=2)
        self.jitter_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(tframe, text="Doğal varyasyon (pitch/volume jitter)",
                        variable=self.jitter_var).pack(anchor="w", padx=8, pady=2)

        # Test buttons
        tb = ttk.LabelFrame(self.root, text="Test sesleri")
        tb.pack(fill="x", **pad)
        grid = ttk.Frame(tb)
        grid.pack(padx=8, pady=6)
        tests = [("Normal", "normal"), ("Space", "space"), ("Enter", "enter"),
                 ("Backspace", "backspace"), ("Tab", "tab"), ("Modifier", "modifier"),
                 ("Ok", "arrow"), ("Fn", "function"), ("Numpad", "numpad")]
        for i, (label, kc) in enumerate(tests):
            b = ttk.Button(grid, text=label, width=9,
                           command=lambda k=kc: self._test(k))
            b.grid(row=i // 3, column=i % 3, padx=3, pady=3)

        # Status
        self.status_var = tk.StringVar(value="Dinleniyor...")
        ttk.Label(self.root, textvariable=self.status_var, foreground="#333").pack(pady=(6, 2))
        self.count_var = tk.StringVar(value="Tuş sayısı: 0")
        ttk.Label(self.root, textvariable=self.count_var, foreground="#666").pack()

    def _profile_key(self, name):
        for p in VALID_PROFILES:
            if PROFILES[p].name == name:
                return p
        return self.cfg["profile"]

    def _on_profile_combo(self, _=None):
        key = self._profile_key(self.profile_var.get())
        self.engine.set_profile(key)
        self.cfg = self.engine.cfg
        self._update_desc()

    def _update_desc(self):
        key = self._profile_key(self.profile_var.get())
        desc = {
            "blue": "Keskin tık sesi + orta gövde. Klasik mekanik his.",
            "brown": "Yumuşak taktik bump, daha sessiz tık.",
            "red": "Lineer, pürüzsüz, tıksız.",
            "topre": "Elektro-kapasitif 'thock', yumuşak ve derin.",
            "buckling": "Model M yay sesi, gürültülü ve karakterli.",
            "gateron_ink": "Pürüzsüz lineer, düşük sürtünme.",
            "kailh_box": "Box Jade: keskin tık + yüksek frekans.",
            "silent": "Sessiz lineer, sönümlü gövde.",
        }.get(key, "")
        self.profile_desc.config(text=desc)

    def _on_volume(self, _=None):
        v = self.vol_var.get()
        self.engine.set_volume(v)
        self.cfg = self.engine.cfg
        self.vol_label.config(text=f"{int(v*100)}%")

    def _on_enabled(self):
        self.engine.set_enabled(self.enabled_var.get())
        self.cfg = self.engine.cfg

    def _on_mods(self):
        self.cfg["play_modifiers"] = bool(self.mods_var.get())
        save(self.cfg)

    def _test(self, kc):
        buf = self.engine._buffers.get(kc)
        if buf is not None:
            self.engine.audio.play(buf)
        self._flash()

    def _flash(self):
        self.flash.itemconfig(self.flash_rect, fill="#4a90d9")
        self.root.after(80, lambda: self.flash.itemconfig(self.flash_rect, fill="#f0f0f0"))

    def _tick(self):
        kc = self.engine.keyboard_count()
        if kc == 0:
            self.status_var.set("Klavye algılanamadı (input grubu?)")
        else:
            self.status_var.set(f"Dinleniyor... ({kc} klavye)")
        if self.engine.key_count != self._last_count:
            self._last_count = self.engine.key_count
            self._flash()
        self.count_var.set(f"Tuş sayısı: {self.engine.key_count}")
        self.root.after(120, self._tick)

    def run(self):
        try:
            self.root.mainloop()
        finally:
            self.engine.close()

    def close(self):
        self.engine.close()
        try:
            self.root.destroy()
        except Exception:
            pass

"""Global keyboard listeners (evdev on Linux, pynput fallback)."""
import threading
import time


class EvdevListener:
    def __init__(self, on_key):
        self.on_key = on_key
        self.devices = []
        self.running = False
        self.thread = None

    def _scan(self):
        import evdev
        from evdev import ecodes
        devs = []
        try:
            paths = evdev.list_devices()
        except Exception:
            return devs
        for path in paths:
            try:
                d = evdev.InputDevice(path)
            except Exception:
                continue
            caps = d.capabilities()
            if ecodes.EV_KEY not in caps:
                continue
            keys = caps[ecodes.EV_KEY]
            if not (ecodes.KEY_A in keys or ecodes.KEY_SPACE in keys):
                continue
            devs.append(d)
        return devs

    def _classify(self, code):
        import evdev
        from evdev import ecodes
        if code == ecodes.KEY_SPACE:
            return "space"
        if code in (ecodes.KEY_ENTER, ecodes.KEY_KPENTER):
            return "enter"
        if code == ecodes.KEY_BACKSPACE:
            return "backspace"
        if code == ecodes.KEY_TAB:
            return "tab"
        if code in (ecodes.KEY_UP, ecodes.KEY_DOWN, ecodes.KEY_LEFT, ecodes.KEY_RIGHT):
            return "arrow"
        if code in (ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT):
            return "shift"
        if code in (ecodes.KEY_KP0, ecodes.KEY_KP1, ecodes.KEY_KP2, ecodes.KEY_KP3,
                    ecodes.KEY_KP4, ecodes.KEY_KP5, ecodes.KEY_KP6, ecodes.KEY_KP7,
                    ecodes.KEY_KP8, ecodes.KEY_KP9, ecodes.KEY_KPPLUS, ecodes.KEY_KPMINUS,
                    ecodes.KEY_KPASTERISK, ecodes.KEY_KPSLASH, ecodes.KEY_KPDOT,
                    ecodes.KEY_KPENTER):
            return "numpad"
        if code >= ecodes.KEY_F1 and code <= ecodes.KEY_F12:
            return "function"
        if code in (ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL,
                    ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT,
                    ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA,
                    ecodes.KEY_CAPSLOCK, ecodes.KEY_ESC):
            return "modifier"
        if ecodes.KEY_A <= code <= ecodes.KEY_Z:
            return "letter"
        if code in (ecodes.KEY_1, ecodes.KEY_2, ecodes.KEY_3, ecodes.KEY_4, ecodes.KEY_5,
                    ecodes.KEY_6, ecodes.KEY_7, ecodes.KEY_8, ecodes.KEY_9, ecodes.KEY_0):
            return "number"
        if code in (ecodes.KEY_MINUS, ecodes.KEY_EQUAL, ecodes.KEY_LEFTBRACE, ecodes.KEY_RIGHTBRACE,
                    ecodes.KEY_SEMICOLON, ecodes.KEY_APOSTROPHE, ecodes.KEY_GRAVE,
                    ecodes.KEY_BACKSLASH, ecodes.KEY_COMMA, ecodes.KEY_DOT, ecodes.KEY_SLASH):
            return "punct"
        return "normal"

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True, name="evdev-listener")
        self.thread.start()

    def stop(self):
        self.running = False

    def _run(self):
        import select
        import evdev
        from evdev import ecodes
        self.devices = self._scan()
        last_scan = time.time()
        while self.running:
            if time.time() - last_scan > 5.0:
                known = {d.path for d in self.devices}
                for d in self._scan():
                    if d.path not in known:
                        self.devices.append(d)
                        known.add(d.path)
                last_scan = time.time()
            if not self.devices:
                time.sleep(1.0)
                continue
            try:
                r, _, _ = select.select(self.devices, [], [], 1.0)
            except Exception:
                time.sleep(0.5)
                continue
            for dev in r:
                try:
                    for event in dev.read():
                        if event.type == ecodes.EV_KEY and event.value == 1:
                            self.on_key(self._classify(event.code))
                except OSError:
                    # device removed
                    try:
                        self.devices.remove(dev)
                    except ValueError:
                        pass
                except Exception:
                    pass


class PynputListener:
    def __init__(self, on_key):
        self.on_key = on_key
        self.listener = None
        self.running = False

    def _classify(self, key):
        from pynput import keyboard
        if key == keyboard.Key.space:
            return "space"
        if key in (keyboard.Key.enter,):
            return "enter"
        if key == keyboard.Key.backspace:
            return "backspace"
        if key == keyboard.Key.tab:
            return "tab"
        if key in (keyboard.Key.up, keyboard.Key.down, keyboard.Key.left, keyboard.Key.right):
            return "arrow"
        if key in (keyboard.Key.shift, keyboard.Key.shift_r):
            return "shift"
        if key in (keyboard.Key.shift, keyboard.Key.shift_r,
                   keyboard.Key.ctrl, keyboard.Key.ctrl_r,
                   keyboard.Key.alt, keyboard.Key.alt_r,
                   keyboard.Key.cmd, keyboard.Key.cmd_r,
                   keyboard.Key.caps_lock, keyboard.Key.esc):
            return "modifier"
        if hasattr(key, "name") and key.name and key.name.startswith("f") and key.name[1:].isdigit():
            return "function"
        if hasattr(key, "char") and key.char:
            ch = key.char
            if ch.isalpha():
                return "letter"
            if ch.isdigit():
                return "number"
            return "punct"
        return "normal"

    def start(self):
        from pynput import keyboard
        self.running = True

        def on_press(key):
            try:
                self.on_key(self._classify(key))
            except Exception:
                pass

        self.listener = keyboard.Listener(on_press=on_press)
        self.listener.start()

    def stop(self):
        self.running = False
        if self.listener is not None:
            try:
                self.listener.stop()
            except Exception:
                pass


def make_listener(on_key):
    """Return the best available listener for this platform."""
    try:
        import evdev  # noqa
        return EvdevListener(on_key)
    except Exception:
        pass
    try:
        import pynput  # noqa
        return PynputListener(on_key)
    except Exception:
        raise RuntimeError(
            "No keyboard backend available. Install 'evdev' (Linux) "
            "or 'pynput' (X11)."
        )

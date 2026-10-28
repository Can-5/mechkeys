"""Entry point."""
import argparse
import sys
import time

from . import config as cfgmod
from . import foxguard
from .engine import MechKeysEngine


def main(argv=None):
    parser = argparse.ArgumentParser(prog="mechkeys", description="Mechanical keyboard sound simulator")
    parser.add_argument("--profile", choices=["blue", "brown", "red"], help="Switch profile")
    parser.add_argument("--volume", type=float, help="Volume 0.0-1.0")
    parser.add_argument("--no-gui", action="store_true", help="Run headless (daemon mode)")
    parser.add_argument("--list-devices", action="store_true", help="List detected keyboards and exit")
    args = parser.parse_args(argv)

    if args.list_devices:
        try:
            import evdev
            for p in evdev.list_devices():
                try:
                    d = evdev.InputDevice(p)
                    print(f"{p}\t{d.name}")
                except Exception as e:
                    print(f"{p}\t<error: {e}>")
        except Exception as e:
            print(f"evdev unavailable: {e}")
        return 0

    cfg = foxguard.safe_load_config()
    if args.profile:
        cfg["profile"] = args.profile
    if args.volume is not None:
        cfg["volume"] = max(0.0, min(1.0, args.volume))

    if args.no_gui:
        engine = MechKeysEngine(cfg)
        engine.start()
        print(f"mechkeys running (profile={engine.cfg['profile']}, volume={engine.cfg['volume']:.2f})")
        print("Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        engine.close()
        return 0

    # GUI mode
    try:
        from .gui import MechKeysApp
    except Exception as e:
        print(f"GUI unavailable ({e}); running headless. Ctrl+C to stop.")
        engine = MechKeysEngine(cfg)
        engine.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        engine.close()
        return 0

    # pass config overrides into gui by saving first
    cfgmod.save(cfg)
    app = MechKeysApp()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())

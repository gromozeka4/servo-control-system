#!/usr/bin/env python3
"""
USB Power Switch EN Pin Test

Wiring (recommended default):
- Module GND  → Raspberry Pi GND (any ground pin)
- Module EN   → Raspberry Pi GPIO16 (BCM) [physical pin 36]
- Module 5V   → 5V supply input (do NOT power from a GPIO)

Notes:
- EN turns power ON when driven >2V (Pi's 3.3V GPIO HIGH is sufficient).
- This script uses BCM numbering.
- The module's PD (pull-down) keeps it OFF by default; we still set LOW initially.
"""

import argparse
import sys
import time

try:
    import RPi.GPIO as GPIO
except Exception as e:
    print(f"Failed to import RPi.GPIO: {e}")
    sys.exit(1)


def setup_gpio(en_gpio: int) -> None:
    GPIO.setmode(GPIO.BCM)
    # Ensure EN is defined as output and starts LOW (power OFF)
    GPIO.setup(en_gpio, GPIO.OUT, initial=GPIO.LOW)


def set_power(en_gpio: int, enabled: bool) -> None:
    GPIO.output(en_gpio, GPIO.HIGH if enabled else GPIO.LOW)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="USB Power Switch EN pin test")
    parser.add_argument(
        "--gpio",
        type=int,
        default=16,
        help="BCM GPIO number connected to EN (default: 16)",
    )
    parser.add_argument(
        "--mode",
        choices=["on", "off", "toggle"],
        default="toggle",
        help="Action to perform: on, off, or toggle (default)",
    )
    parser.add_argument(
        "--toggle-seconds",
        type=float,
        default=5.0,
        help="Seconds to keep power ON during toggle (default: 5.0)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    en_gpio = args.gpio

    try:
        setup_gpio(en_gpio)

        if args.mode == "on":
            print(f"Enabling power (GPIO{en_gpio} HIGH)…")
            set_power(en_gpio, True)
        elif args.mode == "off":
            print(f"Disabling power (GPIO{en_gpio} LOW)…")
            set_power(en_gpio, False)
        else:  # toggle
            print(f"Toggling power ON for {args.toggle_seconds}s, then OFF (GPIO{en_gpio})…")
            set_power(en_gpio, True)
            time.sleep(args.toggle_seconds)
            set_power(en_gpio, False)
            print("Power OFF")

        return 0
    except KeyboardInterrupt:
        print("Interrupted by user")
        return 130
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        try:
            # Ensure EN is LOW before cleanup for safety
            try:
                set_power(en_gpio, False)
            except Exception:
                pass
            GPIO.cleanup()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())





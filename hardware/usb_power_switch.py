#!/usr/bin/env python3
"""
USB Power Switch Manager

Manages one or more USB power switch EN pins via Raspberry Pi GPIO.
Each switch is defined by an id and a BCM GPIO number in config.

Config structure (example):

usb_power:
  switches:
    - id: "usb1"
      gpio: 16
      default_state: "off"  # on|off (optional, defaults to off)
    - id: "usb2"
      gpio: 26
      default_state: "off"
"""

import logging
from typing import Dict, List, Optional

import threading

try:
    import RPi.GPIO as GPIO
except Exception:  # pragma: no cover (for non-Pi dev environments)
    GPIO = None  # type: ignore


class USBPowerSwitchManager:
    def __init__(self, config: Dict):
        self._logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        self._enabled_by_id: Dict[str, bool] = {}
        self._id_to_gpio: Dict[str, int] = {}
        self._initialized = False

        cfg = (config or {}).get('usb_power', {})
        self._switch_defs: List[Dict] = cfg.get('switches', []) or []

        if not self._switch_defs:
            self._logger.debug("No USB power switches configured, skipping initialization")
            return  # no switches configured

        if GPIO is None:
            raise RuntimeError("RPi.GPIO not available on this platform")

        # Initialize GPIO once
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        for switch in self._switch_defs:
            switch_id = str(switch.get('id'))
            gpio = int(switch.get('gpio'))
            default_state = str(switch.get('default_state', 'off')).lower()

            if not switch_id or switch_id in self._id_to_gpio:
                raise ValueError("Duplicate or missing usb_power switch id")

            self._id_to_gpio[switch_id] = gpio
            GPIO.setup(gpio, GPIO.OUT, initial=GPIO.LOW)
            # Apply default state (LOW=off, HIGH=on)
            if default_state == 'on':
                GPIO.output(gpio, GPIO.HIGH)
                self._enabled_by_id[switch_id] = True
            else:
                GPIO.output(gpio, GPIO.LOW)
                self._enabled_by_id[switch_id] = False

            self._logger.info(
                "USB switch '%s' initialized on GPIO %d with default state: %s",
                switch_id, gpio, default_state,
            )

        self._initialized = True
        self._logger.info("USB power switch manager initialized (%d switch(es))", len(self._switch_defs))

    def list_switches(self) -> List[Dict]:
        return [
            {
                'id': switch_id,
                'gpio': self._id_to_gpio[switch_id],
                'enabled': self._enabled_by_id.get(switch_id, False),
            }
            for switch_id in sorted(self._id_to_gpio.keys())
        ]

    def set_state(self, switch_id: str, enable: bool) -> bool:
        if not self._initialized:
            self._logger.warning("USB switch '%s' set_state called but manager is not initialized", switch_id)
            return False
        if switch_id not in self._id_to_gpio:
            self._logger.warning("USB switch '%s' not found", switch_id)
            return False
        gpio = self._id_to_gpio[switch_id]
        with self._lock:
            GPIO.output(gpio, GPIO.HIGH if enable else GPIO.LOW)
            self._enabled_by_id[switch_id] = enable
        state_str = "ON" if enable else "OFF"
        self._logger.info("USB switch '%s' (GPIO %d) turned %s", switch_id, gpio, state_str)
        return True

    def get_state(self, switch_id: str) -> Optional[bool]:
        if switch_id not in self._id_to_gpio:
            return None
        return self._enabled_by_id.get(switch_id, False)

    def get_status(self) -> Dict:
        return {
            'initialized': self._initialized,
            'switches': self.list_switches(),
        }

    def cleanup(self) -> None:
        if not self._initialized:
            return
        self._logger.info("Cleaning up USB power switches, turning all OFF")
        try:
            for switch_id, gpio in self._id_to_gpio.items():
                try:
                    GPIO.output(gpio, GPIO.LOW)
                    self._enabled_by_id[switch_id] = False
                    self._logger.debug("USB switch '%s' (GPIO %d) set LOW during cleanup", switch_id, gpio)
                except Exception:
                    pass
        finally:
            try:
                GPIO.cleanup()
            except Exception:
                pass
            self._initialized = False
            self._logger.info("USB power switch manager cleanup completed")

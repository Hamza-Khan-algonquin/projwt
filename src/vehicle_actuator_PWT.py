#!/usr/bin/env python3
r"""vehicle_actuator_PWT.py — the swappable 'thing the gestures control'.

One small interface, several backends. The gesture -> safety-FSM pipeline never
changes; only the backend does:

    MockActuator        prints what it WOULD do        (works today, no car)
    TeslaFleetActuator  real Tesla Fleet API commands  (needs your credentials)
    (future) ScreenCar / UE5  for the continuous-hold DRIVE demo

SCOPE / SAFETY — read this:
    This layer exposes ONLY discrete, non-motion commands (lock, unlock, lights,
    horn, trunk, windows, climate, charge). It deliberately has NO method that
    makes a car move. Tesla exposes no third-party API for motion/Summon anyway
    (that lives only inside Tesla's own app behind its proximity + press
    interlocks), and bypassing those interlocks is out of scope for this project.
    The continuous-hold DRIVE demo is built later against a SIMULATOR/2D car, not
    a real vehicle.

Backend selection is explicit; nothing here touches a real car unless you pass
the Tesla backend AND supply credentials.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

# Friendly command name -> (Fleet API command path, JSON body). Discrete only.
# https://developer.tesla.com/docs/fleet-api (command endpoints)
TESLA_COMMANDS = {
    "unlock":        ("door_unlock", {}),
    "lock":          ("door_lock", {}),
    "flash":         ("flash_lights", {}),
    "honk":          ("honk_horn", {}),
    "frunk":         ("actuate_trunk", {"which_trunk": "front"}),
    "trunk":         ("actuate_trunk", {"which_trunk": "rear"}),
    "vent":          ("window_control", {"command": "vent", "lat": 0, "lon": 0}),
    "close_windows": ("window_control", {"command": "close", "lat": 0, "lon": 0}),
    "climate_on":    ("auto_conditioning_start", {}),
    "climate_off":   ("auto_conditioning_stop", {}),
    "charge_start":  ("charge_start", {}),
    "charge_stop":   ("charge_stop", {}),
}
KNOWN_COMMANDS = tuple(TESLA_COMMANDS.keys())


class VehicleActuator:
    """Base interface. dispatch(name) routes a friendly command to the backend."""

    name = "base"

    def dispatch(self, command: str) -> dict:
        if command not in KNOWN_COMMANDS:
            return {"ok": False, "command": command, "error": "unknown command"}
        return self._do(command)

    def _do(self, command: str) -> dict:  # pragma: no cover - overridden
        raise NotImplementedError


class MockActuator(VehicleActuator):
    """Prints what it would do. The default — safe, needs nothing, demos the pipeline."""

    name = "mock"

    def _do(self, command: str) -> dict:
        print(f"    [MOCK VEHICLE] -> {command.upper()}")
        return {"ok": True, "command": command, "backend": "mock"}


class TeslaFleetActuator(VehicleActuator):
    """Real Tesla Fleet API discrete commands.

    Needs (via env or constructor):
        TESLA_FLEET_TOKEN   OAuth2 access token (Bearer)
        TESLA_VEHICLE_TAG   vehicle id / VIN tag
        TESLA_FLEET_BASE    region base URL, OR the local signed-command proxy URL
                            (e.g. https://localhost:4443 when using tesla-http-proxy)

    NOTE: newer vehicles require the Tesla Vehicle Command Protocol (signed
    commands). The REST shape is identical, so point TESLA_FLEET_BASE at Tesla's
    `tesla-http-proxy` (it signs with your private key and forwards). See the
    setup doc. This class only issues the DISCRETE commands in TESLA_COMMANDS.
    """

    name = "tesla"

    def __init__(self, token: str | None = None, vehicle_tag: str | None = None,
                 base_url: str | None = None, timeout: float = 15.0, dry: bool = False):
        self.token = token or os.environ.get("TESLA_FLEET_TOKEN", "")
        self.tag = vehicle_tag or os.environ.get("TESLA_VEHICLE_TAG", "")
        self.base = (base_url or os.environ.get("TESLA_FLEET_BASE", "")).rstrip("/")
        self.timeout = timeout
        self.dry = dry

    def ready(self) -> tuple[bool, str]:
        missing = [n for n, v in [("TESLA_FLEET_TOKEN", self.token),
                                  ("TESLA_VEHICLE_TAG", self.tag),
                                  ("TESLA_FLEET_BASE", self.base)] if not v]
        return (not missing, "missing: " + ", ".join(missing) if missing else "ready")

    def _do(self, command: str) -> dict:
        path, body = TESLA_COMMANDS[command]
        ok, why = self.ready()
        if not ok:
            return {"ok": False, "command": command, "error": why}
        url = f"{self.base}/api/1/vehicles/{self.tag}/command/{path}"
        if self.dry:
            print(f"    [TESLA dry-run] POST {url}  body={body}")
            return {"ok": True, "command": command, "backend": "tesla", "dry": True}
        data = json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, method="POST", headers={
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = json.loads(resp.read().decode() or "{}")
            return {"ok": True, "command": command, "backend": "tesla", "response": payload}
        except urllib.error.HTTPError as e:
            return {"ok": False, "command": command, "error": f"HTTP {e.code}",
                    "detail": e.read().decode(errors="ignore")[:300]}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "command": command, "error": str(e)}


def make_actuator(backend: str, dry: bool = False) -> VehicleActuator:
    backend = (backend or "mock").lower()
    if backend == "mock":
        return MockActuator()
    if backend == "tesla":
        return TeslaFleetActuator(dry=dry)
    raise SystemExit(f"unknown backend '{backend}' (use: mock, tesla)")


if __name__ == "__main__":
    # tiny self-test: mock dispatch of every known command
    m = MockActuator()
    print("Known discrete commands:", ", ".join(KNOWN_COMMANDS))
    bad = m.dispatch("drive_forward")
    assert bad["ok"] is False, "motion/unknown commands must be rejected"
    for c in KNOWN_COMMANDS:
        assert m.dispatch(c)["ok"], c
    t = TeslaFleetActuator()
    ok, why = t.ready()
    print(f"Tesla backend readiness (no creds expected): {why}")
    print("vehicle_actuator_PWT self-test OK — mock dispatches, motion rejected.")

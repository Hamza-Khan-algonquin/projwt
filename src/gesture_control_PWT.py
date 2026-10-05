#!/usr/bin/env python3
r"""gesture_control_PWT.py — flick gestures -> safety FSM -> vehicle action.

The whole ProjWT control pipeline in one place:

    band EVENT (flicks)                     keyboard sim ('f','d','s')
            \                                   /
             v                                 v
        gesture recognizer  ->  SafetyStateMachine (fail-closed)  ->  VehicleActuator
                                   must ARM first; auto-disarms         mock / tesla

GESTURE VOCABULARY (deliberately small + reliable):
    double-flick   ARM  (enter command mode)        ... or CONFIRM the selection while armed
    single flick   cycle to the next command in the menu
    shake          PANIC: disarm immediately + send LOCK (safe default)
    (inactivity)   auto-disarm after --arm-timeout seconds

While DISARMED (IDLE) no vehicle command can fire — that is the safety gate. The
menu is discrete, non-motion commands only (see vehicle_actuator_PWT). The live
continuous-HOLD drive loop is a later, simulator-only demo.

Run it TODAY with no car and no band:
    python gesture_control_PWT.py --keyboard
With the band (real flicks), still mock vehicle:
    python gesture_control_PWT.py <ADDRESS>
Against a real Tesla (needs TESLA_* env vars; --dry prints instead of sending):
    python gesture_control_PWT.py <ADDRESS> --backend tesla --dry
"""
import argparse
import asyncio
import time
from datetime import datetime
from pathlib import Path

from safety_state_machine_PWT import SafetyConfig, SafetyStateMachine, IDLE, ARMED
from vehicle_actuator_PWT import make_actuator, KNOWN_COMMANDS

# the discrete command menu the single-flick cycles through (keyboard sim)
COMMAND_MENU = ["unlock", "lock", "flash", "honk", "frunk", "vent", "climate_on"]
# band "tap-to-cycle, pause-to-confirm" menu — 'cancel' lets a dwell do nothing.
# Edit this list to taste; any key from vehicle_actuator TESLA_COMMANDS works.
BAND_MENU = ["unlock", "lock", "flash", "honk", "frunk", "climate_warm",
             "climate_cool", "charge_port_open", "boombox", "cancel"]
ARM_GESTURE, CONFIRM_GESTURE, PANIC_GESTURE = "DOUBLE_FLICK", "DOUBLE_FLICK", "SHAKE"


def load_webhooks():
    """Optional secrets/webhooks_PWT.json: {"menu_name": "https://...", ...}.
    Each becomes a tap-menu item that POSTs to its URL (e.g. an Apple Shortcut
    that texts a contact, or a smart-home trigger). Gitignored."""
    import json as _json
    from pathlib import Path as _Path
    p = _Path(__file__).resolve().parent.parent / "secrets" / "webhooks_PWT.json"
    try:
        return _json.loads(p.read_text()) if p.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


class GestureController:
    """Maps recognized gestures to armed-gated vehicle commands via the safety FSM."""

    def __init__(self, actuator, arm_timeout=12.0, webhooks=None):
        self.act = actuator
        cfg = SafetyConfig(arm_gesture=ARM_GESTURE, disarm_gesture=PANIC_GESTURE,
                           arm_timeout=max(arm_timeout + 5, 15))
        self.fsm = SafetyStateMachine(cfg=cfg)
        self.sel = 0
        self.arm_timeout = arm_timeout
        self.last_activity = 0.0
        self.buzzes = []            # haptic feedback tokens for the band to drain
        self.webhooks = webhooks or {}   # menu-name -> URL (tap fires an HTTP POST)

    def _fire_webhook(self, name):
        """POST to a configured URL — e.g. an Apple Shortcut that texts a contact."""
        import json as _json
        import urllib.request as _u
        url = self.webhooks[name]
        try:
            req = _u.Request(url, data=_json.dumps({"from": "ProjWT", "action": name}).encode(),
                             method="POST", headers={"Content-Type": "application/json"})
            _u.urlopen(req, timeout=10)
            return {"ok": True}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": str(e)}

    def _buzz(self, token):
        self.buzzes.append(token)

    def take_buzzes(self):
        out, self.buzzes = self.buzzes, []
        return out

    # ---- band model: tap to cycle, pause (dwell) to confirm -----------------
    confirm_dwell = 2.5

    def band_tap(self, t):
        """One debounced tap: arm (if idle) or advance the menu (if armed)."""
        self.last_activity = t
        if self.fsm.state == IDLE:
            self.fsm.gesture(ARM_GESTURE, t)
            self._drain("")
            self.sel = 0
            print(f"    ARMED -> [{BAND_MENU[self.sel].upper()}]   "
                  f"(tap=next, pause {self.confirm_dwell:.1f}s=do it)")
            self._buzz("arm")
        else:
            self.sel = (self.sel + 1) % len(BAND_MENU)
            print(f"      -> [{BAND_MENU[self.sel].upper()}]")
            self._buzz("tick")

    def band_tick(self, t):
        """Fire the selected command after a dwell with no taps; auto-disarm safe."""
        self.fsm.heartbeat(t)
        self.fsm.tick(t)
        self._drain("")
        if self.fsm.state == ARMED and (t - self.last_activity) > self.confirm_dwell:
            cmd = BAND_MENU[self.sel]
            if cmd == "cancel":
                print("    (paused on CANCEL) -> disarmed")
                self._buzz("off")
            elif cmd in self.webhooks:
                print(f"    CONFIRM (held on [{cmd.upper()}]) -> firing webhook")
                res = self._fire_webhook(cmd)
                self._buzz("ok" if res.get("ok") else "err")
                if not res.get("ok"):
                    print(f"      (webhook failed: {res.get('error')})")
            else:
                print(f"    CONFIRM (held on [{cmd.upper()}]) -> sending")
                res = self.act.dispatch(cmd)
                if res.get("ok"):
                    self._buzz("ok")
                else:
                    self._buzz("err")
                    print(f"      (vehicle backend: {res.get('error')}"
                          + (f" | {res['detail']}" if res.get("detail") else "") + ")")
            self.fsm.gesture(PANIC_GESTURE, t)   # back to IDLE
            self._drain("")

    def _announce_menu(self):
        print(f"    ARMED — menu: [{COMMAND_MENU[self.sel].upper()}]  "
              f"(flick=next, double-flick=confirm, shake=panic-lock)")

    def on_gesture(self, kind: str, t: float):
        was = self.fsm.state
        self.last_activity = t

        if was == IDLE:
            if kind == ARM_GESTURE:
                self.fsm.gesture(ARM_GESTURE, t)
                self._drain("")
                self.sel = 0
                self._announce_menu()
                self._buzz("arm")            # one buzz = you're armed
            # any other gesture while disarmed is ignored (the safety gate)
            return

        # --- ARMED ---
        if kind == PANIC_GESTURE:
            print("    !! PANIC — disarming + LOCK")
            self.act.dispatch("lock")
            self.fsm.gesture(PANIC_GESTURE, t)      # -> STOP/IDLE
            self._drain("panic")
            self._buzz("panic")              # long buzz = panic/locked
            return
        if kind == "FLICK":
            self.sel = (self.sel + 1) % len(COMMAND_MENU)
            self._announce_menu()
            self._buzz("tick")               # short blip = menu advanced
            return
        if kind == CONFIRM_GESTURE:                  # double-flick while armed = confirm
            cmd = COMMAND_MENU[self.sel]
            print(f"    CONFIRM -> {cmd.upper()}")
            res = self.act.dispatch(cmd)
            if res.get("ok"):
                self._buzz("ok")             # two buzzes = command sent
            else:
                self._buzz("err")            # buzz pattern = command failed
                print(f"      (vehicle backend: {res.get('error')}"
                      + (f" | {res['detail']}" if res.get("detail") else "") + ")")
            return

    def tick(self, t: float):
        self.fsm.heartbeat(t)        # discrete mode: keep the FSM liveness healthy
        self.fsm.tick(t)
        self._drain("")
        if self.fsm.state == ARMED and (t - self.last_activity) > self.arm_timeout:
            print(f"    (inactive {self.arm_timeout:.0f}s) auto-disarm")
            self.fsm.gesture(PANIC_GESTURE, t)
            self._drain("")
            self._buzz("off")                # one buzz = disarmed

    def _drain(self, _why):
        for ev in self.fsm.drain():
            if ev["cmd"] in ("ARM", "DISARM", "STOP"):
                print(f"    [FSM] {ev['cmd']}  state={self.fsm.state}")


# --------------------------------------------------------------------------- #
# gesture recognition from the band's EVENT channel
#
# Two-level timing, so a single firm flick that RINGS isn't misread as a double:
#   1. refractory (flick_gap): impulses within this window = the SAME flick (ringing)
#   2. multi-window: after the last flick, wait this long; the number of distinct
#      flicks in the group decides the gesture (1=FLICK, 2=DOUBLE_FLICK, 3+=SHAKE)
# Every motion event prints its strength so you can calibrate --strength.
# --------------------------------------------------------------------------- #
# haptic feedback patterns: token -> (pattern_id, loops)
BUZZ = {"hello": (2, 1), "arm": (2, 1), "tick": (2, 1), "ok": (2, 2),
        "err": (2, 3), "panic": (2, 4), "off": (2, 1)}


async def run_band(address, strength_min, flick_gap, dwell, arm_timeout,
                   backend, dry, calibrate, haptics, webhooks=None):
    import whoop_protocol_PWT as wp
    from bleak import BleakClient
    from gesture_PWT import strength_of  # reuse the tuned strength heuristic

    act = make_actuator(backend, dry=dry)
    ctrl = GestureController(act, arm_timeout=arm_timeout, webhooks=webhooks)
    ctrl.confirm_dwell = dwell
    rec = {"taps": 0, "last_impulse": -1e9}
    hseq = {"n": 0}

    def handler(_s, payload):
        ev = wp.parse_event(bytes(payload))
        if not ev or ev["report"] not in {0x0E, 0x03, 0x3F}:
            return
        s = strength_of(ev)
        now = time.monotonic()
        if s < strength_min:
            print(f"   ·weak {s} (below --strength {strength_min})")
            return
        # debounce: impulses within flick_gap of the last are the SAME tap (ringing)
        if now - rec["last_impulse"] > flick_gap:
            rec["taps"] += 1
            print(f"   ·tap  (strength {s})")
        rec["last_impulse"] = now

    async def send_buzz(client, token):
        if not haptics:
            return
        p, loops = BUZZ.get(token, (2, 1))
        try:
            await client.write_gatt_char(wp.CMD_CHAR_UUID,
                wp.build_packet(cmd=wp.CMD_RUN_HAPTICS, seq=hseq["n"] & 0xFF,
                                data=bytes([p, loops, 0, 0, 0])), response=True)
            hseq["n"] += 1
        except Exception:  # noqa: BLE001
            pass

    async def session(client):
        for uuid in wp.NOTIFY_CHARS:
            try:
                await client.start_notify(uuid, handler)
            except Exception:  # noqa: BLE001
                pass
        await client.write_gatt_char(wp.CMD_CHAR_UUID, wp.build_packet(cmd=wp.CMD_HELLO), response=True)
        await asyncio.sleep(0.6)
        try:
            await client.read_gatt_char(wp.BATTERY_LEVEL_UUID)  # settle the link
        except Exception:  # noqa: BLE001
            pass
        # Keep the band in realtime/active sampling mode (green LED stays on). The
        # firmware only samples motion while "awake", so without this you have to
        # hard-tap to wake it; with it, normal wrist flicks register. Turned off on exit.
        # Sent twice with a gap — a cold band sometimes ignores the first realtime write.
        for _ in range(2):
            await client.write_gatt_char(wp.CMD_CHAR_UUID,
                wp.build_packet(cmd=wp.CMD_RT_HR_ON, data=wp.RT_START_PAYLOAD), response=True)
            await asyncio.sleep(0.4)
        mode = "CALIBRATE (no commands)" if calibrate else f"Backend: {act.name}{' (dry-run)' if dry else ''}"
        print(f"{mode}.  TAP the band face: each tap = next command; PAUSE {dwell:.1f}s "
              f"on one to DO it.\n  First tap wakes + arms. Cycle to 'CANCEL' + pause to "
              f"back out safely.  Ctrl+C to quit.\n")
        await send_buzz(client, "hello")   # one buzz = connected + ready
        try:
            while True:
                now = time.monotonic()
                taps, rec["taps"] = rec["taps"], 0   # process debounced taps
                for _ in range(taps):
                    if calibrate:
                        print("   (calibrate) tap")
                    else:
                        ctrl.band_tap(now)
                if not calibrate:
                    ctrl.band_tick(now)              # dwell -> confirm / auto-disarm
                for tok in ctrl.take_buzzes():       # feel confirmations on the wrist
                    await send_buzz(client, tok)
                await asyncio.sleep(0.05)
                try:
                    await client.read_gatt_char(wp.BATTERY_LEVEL_UUID)  # keepalive
                except Exception:  # noqa: BLE001
                    raise
        finally:
            try:  # stop realtime so the LED doesn't stay on after we quit
                await client.write_gatt_char(wp.CMD_CHAR_UUID,
                    wp.build_packet(cmd=wp.CMD_RT_HR_OFF), response=True)
            except Exception:  # noqa: BLE001
                pass

    for attempt in range(1, 5):
        try:
            async with BleakClient(address, timeout=25.0) as client:
                print(f"Connected: {client.is_connected} (attempt {attempt})")
                await session(client)
            break
        except Exception as exc:  # noqa: BLE001
            print(f"\nattempt {attempt} dropped: {exc}")
            if attempt < 4:
                print("Reconnecting in 5s (tap the band) ...")
                await asyncio.sleep(5)


def run_keyboard(arm_timeout, backend, dry):
    act = make_actuator(backend, dry=dry)
    ctrl = GestureController(act, arm_timeout=arm_timeout)
    print(f"Backend: {act.name}{' (dry-run)' if dry else ''}.  KEYBOARD SIM.")
    print("  f = flick    d = double-flick (arm/confirm)    s = shake (panic)")
    print("  w N = advance N seconds (test auto-disarm)      q = quit\n")
    print("Double-flick (d) to ARM.\n")
    kinds = {"f": "FLICK", "d": "DOUBLE_FLICK", "s": "SHAKE"}
    t = 0.0
    while True:
        try:
            line = input("gesture> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            t += 0.5
            ctrl.tick(t)
            continue
        if line == "q":
            break
        if line.startswith("w"):
            parts = line.split()
            dt = float(parts[1]) if len(parts) > 1 else 5.0
            t += dt
            ctrl.tick(t)
            continue
        if line in kinds:
            t += 0.5
            ctrl.on_gesture(kinds[line], t)
            ctrl.tick(t)
        else:
            print("  (keys: f d s, 'w N', q)")
    print("bye.")


def main():
    p = argparse.ArgumentParser(description="ProjWT gesture -> safety -> vehicle control.")
    p.add_argument("address", nargs="?", help="band BLE address (omit with --keyboard)")
    p.add_argument("--keyboard", action="store_true", help="keyboard sim (no band, no car)")
    p.add_argument("--backend", default="mock", choices=["mock", "tesla"])
    p.add_argument("--dry", action="store_true", help="tesla backend: print requests, don't send")
    p.add_argument("--strength", type=int, default=2200,
                   help="band: min impulse strength to count as a tap/flick (default 2200)")
    p.add_argument("--flick-gap", type=float, default=0.30,
                   help="band: impulses within this many s = same tap (debounce). default 0.30")
    p.add_argument("--dwell", type=float, default=2.5,
                   help="band: pause this long on a command (no taps) to confirm it. default 2.5")
    p.add_argument("--arm-timeout", type=float, default=12.0, help="auto-disarm after N idle s")
    p.add_argument("--calibrate", action="store_true",
                   help="band: print flick strengths/counts but send NO commands (safe tuning)")
    p.add_argument("--no-haptics", action="store_true",
                   help="band: disable the buzz feedback (arm/confirm/panic)")
    args = p.parse_args()

    # optional webhook menu items (e.g. an Apple Shortcut that texts a contact)
    hooks = load_webhooks()
    if hooks:
        for name in hooks:
            if name not in BAND_MENU:
                BAND_MENU.insert(-1, name)   # before 'cancel'
        print(f"Webhooks loaded: {', '.join(hooks)}")

    if args.keyboard or not args.address:
        run_keyboard(args.arm_timeout, args.backend, args.dry)
    else:
        try:
            asyncio.run(run_band(args.address, args.strength, args.flick_gap,
                                 args.dwell, args.arm_timeout, args.backend,
                                 args.dry, args.calibrate, not args.no_haptics, hooks))
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()

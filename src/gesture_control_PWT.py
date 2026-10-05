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

# the discrete command menu the single-flick cycles through
COMMAND_MENU = ["unlock", "lock", "flash", "honk", "frunk", "vent", "climate_on"]
ARM_GESTURE, CONFIRM_GESTURE, PANIC_GESTURE = "DOUBLE_FLICK", "DOUBLE_FLICK", "SHAKE"


class GestureController:
    """Maps recognized gestures to armed-gated vehicle commands via the safety FSM."""

    def __init__(self, actuator, arm_timeout=12.0):
        self.act = actuator
        cfg = SafetyConfig(arm_gesture=ARM_GESTURE, disarm_gesture=PANIC_GESTURE,
                           arm_timeout=max(arm_timeout + 5, 15))
        self.fsm = SafetyStateMachine(cfg=cfg)
        self.sel = 0
        self.arm_timeout = arm_timeout
        self.last_activity = 0.0

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
            # any other gesture while disarmed is ignored (the safety gate)
            return

        # --- ARMED ---
        if kind == PANIC_GESTURE:
            print("    !! PANIC — disarming + LOCK")
            self.act.dispatch("lock")
            self.fsm.gesture(PANIC_GESTURE, t)      # -> STOP/IDLE
            self._drain("panic")
            return
        if kind == "FLICK":
            self.sel = (self.sel + 1) % len(COMMAND_MENU)
            self._announce_menu()
            return
        if kind == CONFIRM_GESTURE:                  # double-flick while armed = confirm
            cmd = COMMAND_MENU[self.sel]
            print(f"    CONFIRM -> {cmd.upper()}")
            res = self.act.dispatch(cmd)
            if not res.get("ok"):
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
async def run_band(address, strength_min, flick_gap, multi_window, arm_timeout,
                   backend, dry, calibrate):
    import whoop_protocol_PWT as wp
    from bleak import BleakClient
    from gesture_PWT import strength_of  # reuse the tuned strength heuristic

    act = make_actuator(backend, dry=dry)
    ctrl = GestureController(act, arm_timeout=arm_timeout)
    rec = {"flicks": 0, "last_impulse": -1e9, "last_flick": -1e9, "peak": 0}

    def handler(_s, payload):
        ev = wp.parse_event(bytes(payload))
        if not ev or ev["report"] not in {0x0E, 0x03, 0x3F}:
            return
        s = strength_of(ev)
        now = time.monotonic()
        if s < strength_min:
            print(f"   ·weak {s} (below --strength {strength_min})")
            return
        if now - rec["last_impulse"] > flick_gap:   # a NEW flick (not ringing)
            rec["flicks"] += 1
            rec["peak"] = s
            print(f"   ·FLICK #{rec['flicks']}  strength {s}")
        else:                                        # ringing of the same flick
            rec["peak"] = max(rec["peak"], s)
        rec["last_impulse"] = now
        rec["last_flick"] = now

    async def session(client):
        for uuid in wp.NOTIFY_CHARS:
            try:
                await client.start_notify(uuid, handler)
            except Exception:  # noqa: BLE001
                pass
        await client.write_gatt_char(wp.CMD_CHAR_UUID, wp.build_packet(cmd=wp.CMD_HELLO), response=True)
        mode = "CALIBRATE (no commands)" if calibrate else f"Backend: {act.name}{' (dry-run)' if dry else ''}"
        print(f"{mode}.  flick=cycle, double-flick=arm/confirm, shake=panic.  Ctrl+C to quit.\n")
        while True:
            now = time.monotonic()
            if rec["flicks"] > 0 and (now - rec["last_flick"]) > multi_window:
                n = rec["flicks"]
                kind = "SHAKE" if n >= 3 else "DOUBLE_FLICK" if n == 2 else "FLICK"
                print(f"   => {kind} ({n} flick{'s' if n > 1 else ''})")
                if not calibrate:
                    ctrl.on_gesture(kind, now)
                rec["flicks"] = 0
            ctrl.tick(now)
            await asyncio.sleep(0.05)
            try:
                await client.read_gatt_char(wp.BATTERY_LEVEL_UUID)  # keepalive
            except Exception:  # noqa: BLE001
                raise

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
    p.add_argument("--strength", type=int, default=4500,
                   help="band: min impulse strength to count as a flick (default 4500)")
    p.add_argument("--flick-gap", type=float, default=0.28,
                   help="band: impulses within this many s = same flick (ringing). default 0.28")
    p.add_argument("--multi-window", type=float, default=0.6,
                   help="band: wait this long after the last flick before deciding. default 0.6")
    p.add_argument("--arm-timeout", type=float, default=12.0, help="auto-disarm after N idle s")
    p.add_argument("--calibrate", action="store_true",
                   help="band: print flick strengths/counts but send NO commands (safe tuning)")
    args = p.parse_args()

    if args.keyboard or not args.address:
        run_keyboard(args.arm_timeout, args.backend, args.dry)
    else:
        try:
            asyncio.run(run_band(args.address, args.strength, args.flick_gap,
                                 args.multi_window, args.arm_timeout, args.backend,
                                 args.dry, args.calibrate))
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
r"""gesture_PWT.py — LIVE, TUNABLE flick/knock gesture trigger.

The band's motion events are firmware-gated (high threshold, NOT host-tunable): we
only receive the events the firmware emits (report ids 0x0e, and sometimes
0x03/0x3f). We can't make it more sensitive — but we CAN make it more ACCURATE by
filtering what we accept:

  --strength N   ignore events whose strength value is below N (kills weak/false
                 triggers). Each event prints its strength so you can pick N.
  --min-impulses accept a gesture only if the burst has >= this many impulses.
  --cooldown S   after a recognized gesture, ignore events for S seconds (debounce).
  --gap / --multi  timing for grouping impulses -> burst -> gesture.

Workflow: run once watching the strength numbers your real flicks produce vs. any
stray blips, then set --strength just under your real-flick values.

Usage:
    python gesture_PWT.py <ADDRESS>                       # see strengths, defaults
    python gesture_PWT.py <ADDRESS> --strength 12000 --cooldown 0.6
"""
import argparse
import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from bleak import BleakClient

import whoop_protocol_PWT as wp

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
MOTION_REPORTS = {0x0E, 0x03, 0x3F}   # firmware motion/impulse events we accept


def strength_of(ev) -> int:
    """Tentative impact-strength = magnitude of the first body field (int16).

    (Confirmed candidate; refine once we decode the body against labeled logs.)
    """
    return abs(ev["ints"][0]) if ev.get("ints") else 0


async def run(address, seconds, gap, multi, strength_min, min_impulses, cooldown,
              with_response) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"gesture_{stamp}_PWT.jsonl"
    log_file = log_path.open("w", encoding="utf-8")

    st = {"open_burst": [], "bursts": [], "last_activity": 0.0,
          "cooldown_until": 0.0, "hr": None}
    counts = {"FLICK": 0, "DOUBLE_FLICK": 0, "SHAKE": 0, "rejected": 0}
    strengths = []   # accepted-event strengths, for the end-of-run guidance

    def flush_gesture():
        nb = len(st["bursts"])
        total = sum(st["bursts"])
        st["bursts"] = []
        if nb <= 0:
            return
        g = "FLICK" if nb == 1 else "DOUBLE_FLICK" if nb == 2 else "SHAKE"
        counts[g] += 1
        st["cooldown_until"] = time.monotonic() + cooldown
        label = {"FLICK": "〜 FLICK", "DOUBLE_FLICK": "〜〜 DOUBLE-FLICK",
                 "SHAKE": "≈≈ SHAKE"}[g]
        hr = f"   (HR {st['hr']})" if st["hr"] else ""
        print(f"\n  {label}   [{nb} burst(s), {total} impulses]{hr}\n")
        log_file.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                                   "gesture": g, "bursts": nb, "impulses": total}) + "\n")
        log_file.flush()

    def make_handler(uuid):
        def handler(_sender, payload):
            frame = bytes(payload)
            if uuid == wp.EVENT_CHAR_UUID:
                ev = wp.parse_event(frame)
                if not ev or ev["report"] not in MOTION_REPORTS:
                    return
                now = time.monotonic()
                s = strength_of(ev)
                # always log the raw event so we can decode the body later
                log_file.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                               "report": ev["report"], "strength": s,
                               "body": ev["body"]}) + "\n")
                log_file.flush()
                if now < st["cooldown_until"]:
                    return                       # debounce window
                if s < strength_min:
                    counts["rejected"] += 1
                    print(f"·{ev['report']:02x}(x{s})", end=" ", flush=True)  # rejected: too weak
                    return
                strengths.append(s)
                st["open_burst"].append(now)
                st["last_activity"] = now
                print(f"·{ev['report']:02x}({s})", end=" ", flush=True)       # accepted
            elif uuid == wp.DATA_CHAR_UUID:
                rt = wp.parse_rt(frame)
                if rt:
                    st["hr"] = rt["hr"]
        return handler

    async def session(client):
        async def send(cmd, data=b""):
            await client.write_gatt_char(wp.CMD_CHAR_UUID,
                                         wp.build_packet(cmd=cmd, data=data), response=with_response)
        for uuid in wp.NOTIFY_CHARS + [wp.HR_CHAR_UUID]:
            try:
                await client.start_notify(uuid, make_handler(uuid))
            except Exception as exc:  # noqa: BLE001
                print(f"  (subscribe {wp.cname(uuid)} failed: {exc})")
                raise
        await send(wp.CMD_HELLO)
        await asyncio.sleep(0.6)
        await send(wp.CMD_RT_HR_ON, wp.RT_START_PAYLOAD)
        print(f"\nReady — flick your wrist. Each tick = an event; the number is its strength.")
        print(f"strength filter >= {strength_min}, min impulses {min_impulses}, "
              f"cooldown {cooldown}s. Listening {seconds:.0f}s.\n")
        t, last_batt = 0.0, 0.0
        while t < seconds:
            await asyncio.sleep(0.05)
            t += 0.05
            now = time.monotonic()
            if st["open_burst"] and (now - st["open_burst"][-1]) >= gap:
                n = len(st["open_burst"])
                st["open_burst"] = []
                if n >= min_impulses:
                    st["bursts"].append(n)
                    st["last_activity"] = now
                # else: burst too small -> ignore (noise)
            if st["bursts"] and not st["open_burst"] and (now - st["last_activity"]) >= multi:
                flush_gesture()
            if t - last_batt >= 2.0:
                last_batt = t
                try:
                    await client.read_gatt_char(wp.BATTERY_LEVEL_UUID)
                except Exception:  # noqa: BLE001
                    raise
        await send(wp.CMD_RT_HR_OFF)
        for uuid in wp.NOTIFY_CHARS + [wp.HR_CHAR_UUID]:
            try:
                await client.stop_notify(uuid)
            except Exception:  # noqa: BLE001
                pass

    try:
        for attempt in range(1, 5):
            try:
                async with BleakClient(address, timeout=25.0) as client:
                    print(f"Connected: {client.is_connected} (attempt {attempt})")
                    if not client.is_connected:
                        raise RuntimeError("link down after connect")
                    await session(client)
                break
            except Exception as exc:  # noqa: BLE001
                print(f"\nattempt {attempt} dropped: {exc}")
                if attempt < 4:
                    print("Reconnecting in 5s (tap the band) ...")
                    await asyncio.sleep(5)
                else:
                    print("Giving up — toggle Bluetooth OFF/ON, tap the band, retry.")
    finally:
        log_file.close()

    print(f"\n=== Done -> {log_path} ===")
    print(f"recognized: FLICK={counts['FLICK']}  DOUBLE_FLICK={counts['DOUBLE_FLICK']}  "
          f"SHAKE={counts['SHAKE']}  (rejected-too-weak={counts['rejected']})")
    if strengths:
        strengths.sort()
        lo, mid, hi = strengths[0], strengths[len(strengths) // 2], strengths[-1]
        print(f"accepted-event strength  min/median/max = {lo} / {mid} / {hi}")
        print(f"TUNE: set --strength a bit below your real-flick values "
              f"(try ~{int(mid * 0.7)}) to reject weak/false triggers.")
    print("Reminder: the band won't report flicks below its own firmware threshold;"
          " --strength only filters what it already sends.")


def main() -> None:
    p = argparse.ArgumentParser(description="Live, tunable flick gesture trigger (ProjWT).")
    p.add_argument("address")
    p.add_argument("--seconds", type=float, default=90.0)
    p.add_argument("--strength", type=int, default=0,
                   help="reject events weaker than this (0 = accept all; watch the printed numbers)")
    p.add_argument("--min-impulses", type=int, default=1,
                   help="impulses a burst needs to count as a gesture (raise to reject stray blips)")
    p.add_argument("--cooldown", type=float, default=0.5,
                   help="seconds to ignore events after a recognized gesture (debounce)")
    p.add_argument("--gap", type=float, default=0.35,
                   help="max seconds between impulses within one burst (default 0.35)")
    p.add_argument("--multi", type=float, default=1.1,
                   help="window to group consecutive flicks into one gesture (default 1.1)")
    p.add_argument("--no-response", action="store_true", help="use write-without-response")
    args = p.parse_args()
    try:
        asyncio.run(run(args.address, args.seconds, args.gap, args.multi,
                        args.strength, args.min_impulses, args.cooldown,
                        not args.no_response))
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()

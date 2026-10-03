#!/usr/bin/env python3
r"""gesture_PWT.py — LIVE gesture recognition from the band's impulse events.

Phase-2 established that the band emits a discrete "sharp-motion" event
(EVENT_CHAR 61080004, type 0x30, report id 0x0e) on taps and flicks, and emits
nothing for slow/large motion. This tool turns that single primitive into a small
gesture vocabulary by clustering events in time:

    1 impulse               -> TAP
    2 impulses (< gap)       -> DOUBLE_TAP
    >= 3 impulses (< gap)    -> FLICK / SHAKE

It keeps a stable session (HELLO + START 0x03 01 + battery-read keepalive, with a
reconnect loop) and prints a big line the moment it recognizes a gesture, so you
can see it react. Tune --gap / --flick to taste.

Usage:
    python gesture_PWT.py <ADDRESS>
    python gesture_PWT.py <ADDRESS> --gap 0.45 --flick 3 --seconds 120
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
IMPULSE_REPORT = 0x0E   # report id that fires on taps/flicks


async def run(address: str, seconds: float, gap: float, flick_n: int,
              with_response: bool) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"gesture_{stamp}_PWT.jsonl"
    log_file = log_path.open("w", encoding="utf-8")
    cluster: list[float] = []     # monotonic times of impulses in the open cluster
    last_hr = {"bpm": None}
    counts = {"TAP": 0, "DOUBLE_TAP": 0, "FLICK": 0}

    def classify_and_report():
        n = len(cluster)
        cluster.clear()
        if n <= 0:
            return
        if n >= flick_n:
            g = "FLICK"
        elif n == 2:
            g = "DOUBLE_TAP"
        else:
            g = "TAP"
        counts[g] += 1
        bar = {"TAP": "➤ TAP", "DOUBLE_TAP": "➤➤ DOUBLE-TAP", "FLICK": "〜 FLICK/SHAKE"}[g]
        hr = f"   (HR {last_hr['bpm']})" if last_hr["bpm"] else ""
        print(f"  {bar}   [{n} impulse{'s' if n > 1 else ''}]{hr}")
        log_file.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                                   "gesture": g, "impulses": n}) + "\n")
        log_file.flush()

    def make_handler(uuid):
        def handler(_sender, payload):
            frame = bytes(payload)
            if uuid == wp.EVENT_CHAR_UUID:
                ev = wp.parse_event(frame)
                if ev and ev["report"] == IMPULSE_REPORT:
                    cluster.append(time.monotonic())
            elif uuid == wp.DATA_CHAR_UUID:
                rt = wp.parse_rt(frame)
                if rt:
                    last_hr["bpm"] = rt["hr"]
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
        await send(wp.CMD_RT_HR_ON, wp.RT_START_PAYLOAD)  # keep a live session + HR
        print(f"\nReady — TAP (sharp), DOUBLE-TAP, or FLICK your wrist. Listening {seconds:.0f}s.\n")
        t = 0.0
        tick = 0.1
        last_batt = 0.0
        while t < seconds:
            await asyncio.sleep(tick)
            t += tick
            # close a cluster once impulses stop arriving for `gap` seconds
            if cluster and (time.monotonic() - cluster[-1]) >= gap:
                classify_and_report()
            # battery-read keepalive every 2s so the link doesn't idle-drop
            if t - last_batt >= 2.0:
                last_batt = t
                try:
                    await client.read_gatt_char(wp.BATTERY_LEVEL_UUID)
                except Exception:  # noqa: BLE001
                    raise
        if cluster:
            classify_and_report()
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
    print(f"recognized: TAP={counts['TAP']}  DOUBLE_TAP={counts['DOUBLE_TAP']}  FLICK={counts['FLICK']}")
    print("Tip: flicks are the most reliable primitive on this band; taps need to be sharp.")


def main() -> None:
    p = argparse.ArgumentParser(description="Live tap/flick gesture recognition (ProjWT).")
    p.add_argument("address")
    p.add_argument("--seconds", type=float, default=120.0, help="run duration (default 120)")
    p.add_argument("--gap", type=float, default=0.45,
                   help="max seconds between impulses in one gesture cluster (default 0.45)")
    p.add_argument("--flick", type=int, default=3,
                   help="impulses needed to call it a FLICK/SHAKE (default 3)")
    p.add_argument("--no-response", action="store_true", help="use write-without-response")
    args = p.parse_args()
    try:
        asyncio.run(run(args.address, args.seconds, args.gap, args.flick,
                        not args.no_response))
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()

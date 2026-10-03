#!/usr/bin/env python3
r"""gesture_PWT.py — LIVE flick-based gesture recognition.

Reality of this band: the tap detector lives in FIRMWARE with a high threshold
(the green LED = firmware registered a tap). We can't lower that from the host, so
single taps / double-taps are unreliable. FLICKS, however, fire the impulse event
(EVENT_CHAR 61080004, type 0x30, report id 0x0e) reliably and repeatedly. So we
build the vocabulary around flicks.

Two-level clustering:
  * impulses within --gap seconds   -> one BURST (a single flick usually = 1 burst
    of a few impulses)
  * bursts within --multi seconds    -> one GESTURE
        1 burst  -> FLICK
        2 bursts -> DOUBLE_FLICK
        >=3 burst-> SHAKE

Every impulse prints a live tick so you can see the band reacting immediately.

Usage:
    python gesture_PWT.py <ADDRESS>
    python gesture_PWT.py <ADDRESS> --gap 0.35 --multi 1.1 --seconds 120
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
IMPULSE_REPORT = 0x0E


async def run(address: str, seconds: float, gap: float, multi: float,
              with_response: bool) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"gesture_{stamp}_PWT.jsonl"
    log_file = log_path.open("w", encoding="utf-8")

    st = {
        "open_burst": [],      # impulse times in the currently-forming burst
        "bursts": [],          # impulse-counts of completed bursts awaiting flush
        "last_activity": 0.0,  # monotonic time of last impulse or burst close
        "hr": None,
    }
    counts = {"FLICK": 0, "DOUBLE_FLICK": 0, "SHAKE": 0}

    def flush_gesture():
        nb = len(st["bursts"])
        total = sum(st["bursts"])
        st["bursts"] = []
        if nb <= 0:
            return
        g = "FLICK" if nb == 1 else "DOUBLE_FLICK" if nb == 2 else "SHAKE"
        counts[g] += 1
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
                if ev and ev["report"] == IMPULSE_REPORT:
                    st["open_burst"].append(time.monotonic())
                    st["last_activity"] = time.monotonic()
                    print("·", end="", flush=True)   # live feedback per impulse
                    log_file.write(json.dumps({
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "impulse": True, "body": ev["body"]}) + "\n")
                    log_file.flush()
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
        print(f"\nReady — FLICK your wrist (sharp). Each '·' is a detected impulse.")
        print(f"1 flick = FLICK · 2 flicks = DOUBLE-FLICK · rapid = SHAKE. Listening {seconds:.0f}s.\n")
        t, last_batt = 0.0, 0.0
        while t < seconds:
            await asyncio.sleep(0.05)
            t += 0.05
            now = time.monotonic()
            # close the open burst once impulses stop for `gap`
            if st["open_burst"] and (now - st["open_burst"][-1]) >= gap:
                st["bursts"].append(len(st["open_burst"]))
                st["open_burst"] = []
                st["last_activity"] = now
            # flush a gesture once bursts settle for `multi`
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
          f"SHAKE={counts['SHAKE']}")
    print("Note: tap sensitivity is fixed in the band's firmware (not host-tunable);"
          " flicks are the reliable primitive.")


def main() -> None:
    p = argparse.ArgumentParser(description="Live flick-based gesture recognition (ProjWT).")
    p.add_argument("address")
    p.add_argument("--seconds", type=float, default=120.0)
    p.add_argument("--gap", type=float, default=0.35,
                   help="max seconds between impulses within one burst/flick (default 0.35)")
    p.add_argument("--multi", type=float, default=1.1,
                   help="window to group consecutive flicks into one gesture (default 1.1)")
    p.add_argument("--no-response", action="store_true", help="use write-without-response")
    args = p.parse_args()
    try:
        asyncio.run(run(args.address, args.seconds, args.gap, args.multi,
                        not args.no_response))
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()

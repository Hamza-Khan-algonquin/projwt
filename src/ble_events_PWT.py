#!/usr/bin/env python3
"""ble_events_PWT.py — capture & decode LIVE events for gesture recognition.

Why: raw accelerometer is NOT exposed as a live BLE stream on this firmware
(swept 0x01-0x2f). The live signals we DO have are HR+RR and discrete events on
EVENT_CHAR (61080004, type 0x30) — taps/motion/status. This tool keeps a stable
session (HR on + battery-read keepalive) and prints every EVENT, decoded, tagged
with your gesture label, so we can map which event/field corresponds to which
physical gesture.

Capture one gesture per run, repeating it for the whole window:
    python ble_events_PWT.py <ADDR> --label tap      --seconds 20   # tap repeatedly
    python ble_events_PWT.py <ADDR> --label doubletap --seconds 20
    python ble_events_PWT.py <ADDR> --label flick    --seconds 20   # wrist flick
    python ble_events_PWT.py <ADDR> --label raise    --seconds 20   # raise/lower arm
    python ble_events_PWT.py <ADDR> --label still    --seconds 20   # hold still (baseline)

Then send Claude the logs\events_<label>_*.jsonl files and we diff them.
"""
import argparse
import asyncio
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from bleak import BleakClient

import whoop_protocol_PWT as wp

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


async def run(address: str, label: str, seconds: float, with_response: bool) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"events_{label}_{stamp}_PWT.jsonl"
    report_counts = Counter()
    log_file = log_path.open("w", encoding="utf-8")

    def make_handler(uuid):
        def handler(_sender, payload):
            frame = bytes(payload)
            log_file.write(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(), "label": label,
                "char": uuid, "len": len(frame), "hex": frame.hex(),
            }) + "\n")
            log_file.flush()
            if uuid == wp.EVENT_CHAR_UUID:
                ev = wp.parse_event(frame)
                if ev:
                    report_counts[ev["report"]] += 1
                    # skip the quiet ~periodic status beacon (report 0x01) unless you want it
                    tag = "  <-- status" if ev["report"] == 0x01 else ""
                    print(f"  EVT id=0x{ev['report']:02x} seq={ev['seq']:3d} "
                          f"ints={ev['ints']}{tag}")
            elif uuid == wp.DATA_CHAR_UUID:
                rt = wp.parse_rt(frame)
                if rt:
                    print(f"  [HR] {rt['hr']} bpm")
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
        try:
            val = await client.read_gatt_char(wp.BATTERY_LEVEL_UUID)
            print(f"Battery: {val[0]}%" if val else "Battery: (no data)")
        except Exception:  # noqa: BLE001
            pass
        await send(wp.CMD_RT_HR_ON, wp.RT_START_PAYLOAD)  # keep a live session
        print(f"\nDO THE '{label}' GESTURE repeatedly for {seconds:.0f}s ...\n")
        t = 0.0
        while t < seconds:
            await asyncio.sleep(2.0)
            t += 2.0
            try:
                await client.read_gatt_char(wp.BATTERY_LEVEL_UUID)  # keepalive
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
    if report_counts:
        print("event report-ids seen: " +
              ", ".join(f"0x{r:02x}={n}" for r, n in report_counts.most_common()))
        print("Send Claude this log (and one labeled 'still' for comparison).")
    else:
        print("No events captured — tap the band to wake it and try again.")


def main() -> None:
    p = argparse.ArgumentParser(description="Capture/decode live WHOOP events for gestures (ProjWT).")
    p.add_argument("address")
    p.add_argument("--label", default="gesture", help="name of the gesture you'll repeat")
    p.add_argument("--seconds", type=float, default=20.0)
    p.add_argument("--no-response", action="store_true", help="use write-without-response")
    args = p.parse_args()
    try:
        asyncio.run(run(args.address, args.label, args.seconds, not args.no_response))
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()

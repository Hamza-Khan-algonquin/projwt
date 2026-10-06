#!/usr/bin/env python3
r"""rolling_offload_PWT.py — continuous real-time biometric drain from the band.

Keeps the band's historical buffer draining in a loop, writing the latest HR/gravity
records to a live JSON feed that the dashboard auto-refreshes. This gives ~1 Hz
near-real-time biometrics (1–2 s lag) without maxing out the generation rate.

Usage:
    python rolling_offload_PWT.py <BAND_ADDRESS>
    # keeps running; writes to logs/rolling_biometrics_PWT.json
"""
import argparse
import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import whoop_protocol_PWT as wp
from bleak import BleakClient

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
FEED_FILE = LOG_DIR / "rolling_biometrics_PWT.json"


async def rolling_offload(address, interval=0.5):
    """Continuously drain historical records, write live feed."""
    feed = {"ts": None, "records": []}  # live records (last ~60 at 1 Hz = 1 min)
    lock_ts = [time.time()]  # last flush time

    def handler(_s, payload):
        rec = wp.decode_historical(bytes(payload))
        if not rec:
            return
        ts_ms = rec.get("ts_ms")
        hr = rec.get("hr")
        gmag = rec.get("gmag")
        skin_raw = rec.get("skin_temp_raw")
        if ts_ms and hr is not None:
            feed["records"].append({
                "ts": ts_ms, "hr": hr, "gmag": gmag,
                "skin_raw": skin_raw, "ts_human": datetime.now(timezone.utc).isoformat()
            })
            feed["records"] = feed["records"][-60:]  # keep last 60 (~1 min at 1 Hz)
            # flush every 0.5s
            if time.time() - lock_ts[0] > interval:
                feed["ts"] = datetime.now(timezone.utc).isoformat()
                FEED_FILE.write_text(json.dumps(feed, indent=1), encoding="utf-8")
                lock_ts[0] = time.time()

    try:
        async with BleakClient(address, timeout=25.0) as client:
            print(f"[rolling] connected to {address}")
            print(f"[rolling] writing to {FEED_FILE}")
            await client.start_notify(wp.DATA_CHAR_UUID, handler)
            # initial setup
            await client.write_gatt_char(wp.CMD_CHAR_UUID, wp.build_packet(cmd=wp.CMD_HELLO), response=True)
            await asyncio.sleep(0.3)
            await client.write_gatt_char(wp.CMD_CHAR_UUID,
                wp.build_packet(cmd=wp.CMD_SEND_OPTICAL, data=b"\x01\x01"), response=True)
            # drain loop: kick history, wait, repeat
            while True:
                await client.write_gatt_char(wp.CMD_CHAR_UUID,
                    wp.build_packet(cmd=wp.CMD_SEND_HISTORICAL, data=b"\x00"), response=True)
                await asyncio.sleep(1.5)  # let records flow
    except KeyboardInterrupt:
        print("[rolling] stopped")
    except Exception as exc:  # noqa: BLE001
        print(f"[rolling] error: {exc}")


def main():
    ap = argparse.ArgumentParser(description="Real-time biometric drain (ProjWT rolling offload).")
    ap.add_argument("address", help="band BLE address")
    ap.add_argument("--interval", type=float, default=0.5, help="flush feed every N seconds")
    args = ap.parse_args()
    LOG_DIR.mkdir(exist_ok=True)
    asyncio.run(rolling_offload(args.address, interval=args.interval))


if __name__ == "__main__":
    main()

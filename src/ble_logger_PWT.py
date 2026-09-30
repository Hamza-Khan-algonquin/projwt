#!/usr/bin/env python3
"""ble_logger_PWT.py — Phase 1, step 3.

Subscribe to notifying characteristics on the band and log every packet
(timestamp + characteristic UUID + raw hex) to a JSONL file. Use --label to
tag a capture ("rest", "wrist_wave", "walk") so you can diff byte patterns and
map which characteristic carries accelerometer vs. heart rate vs. temperature.

Usage:
    # log ALL notify chars for a fixed 30s, then stop automatically:
    python ble_logger_PWT.py <ADDRESS> --label rest --seconds 30

    # log until you press Ctrl+C:
    python ble_logger_PWT.py <ADDRESS> --label wave

    # only specific characteristics:
    python ble_logger_PWT.py <ADDRESS> --char <UUID> --label test
"""
import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from bleak import BleakClient

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


async def run(address: str, chars: list[str], label: str, seconds: float | None) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"capture_{label}_{stamp}_PWT.jsonl"
    packet_count = 0

    async with BleakClient(address) as client:
        print(f"Connected: {client.is_connected}")

        notify_chars = chars or [
            c.uuid
            for s in client.services
            for c in s.characteristics
            if "notify" in c.properties
        ]
        if not notify_chars:
            print("No notify characteristics found. Run gatt_explorer_PWT.py first.")
            return

        log_file = log_path.open("w", encoding="utf-8")

        def make_handler(uuid: str):
            def handler(_sender, data: bytearray) -> None:
                nonlocal packet_count
                packet_count += 1
                record = {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "label": label,
                    "char": uuid,
                    "len": len(data),
                    "hex": data.hex(),
                }
                log_file.write(json.dumps(record) + "\n")
                log_file.flush()
                if packet_count % 20 == 0:
                    print(f"  {packet_count} packets ... latest {uuid[-8:]} len={len(data)}")
            return handler

        for uuid in notify_chars:
            try:
                await client.start_notify(uuid, make_handler(uuid))
                print(f"subscribed: {uuid}")
            except Exception as exc:  # noqa: BLE001
                print(f"could not subscribe {uuid}: {exc}")

        print(f"\nLogging to {log_path}  (label='{label}')")
        if seconds:
            print(f"Capturing for {seconds:.0f}s — do the activity now.\n")
        else:
            print("Do the activity now. Press Ctrl+C to stop.\n")

        try:
            if seconds:
                await asyncio.sleep(seconds)
            else:
                while True:
                    await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass
        finally:
            for uuid in notify_chars:
                try:
                    await client.stop_notify(uuid)
                except Exception:  # noqa: BLE001
                    pass
            log_file.close()

    print(f"\nStopped. {packet_count} packets -> {log_path}")


def main() -> None:
    p = argparse.ArgumentParser(description="Log BLE notifications to JSONL (ProjWT Phase 1).")
    p.add_argument("address", help="BLE address from ble_scanner_PWT.py")
    p.add_argument("--char", dest="chars", action="append", default=[],
                   help="specific characteristic UUID to subscribe to (repeatable)")
    p.add_argument("--label", default="capture", help="tag for this capture, e.g. rest/wave/walk")
    p.add_argument("--seconds", type=float, default=None,
                   help="auto-stop after N seconds (default: run until Ctrl+C)")
    args = p.parse_args()
    try:
        asyncio.run(run(args.address, args.chars, args.label, args.seconds))
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()

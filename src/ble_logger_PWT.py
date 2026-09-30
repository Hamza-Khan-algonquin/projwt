#!/usr/bin/env python3
"""ble_logger_PWT.py — Phase 1, step 3.

Subscribe to notifying characteristics on the band and log every packet
(timestamp + characteristic UUID + raw hex) to a JSONL file. Use the
--label flag to tag a capture ("rest", "wrist_wave", "walk") so you can
later diff the byte patterns and start mapping which characteristic carries
accelerometer vs. heart rate vs. temperature.

Usage:
    # subscribe to ALL notify characteristics:
    python src/ble_logger_PWT.py <ADDRESS> --label rest

    # subscribe to specific characteristics only:
    python src/ble_logger_PWT.py <ADDRESS> --char <UUID> --char <UUID> --label wave

Press Ctrl+C to stop; the log path is printed on exit.
"""
import argparse
import asyncio
import json
import signal
from datetime import datetime, timezone
from pathlib import Path

from bleak import BleakClient

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


async def run(address: str, chars: list[str], label: str) -> None:
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
        print("Do the activity now (hold still / wave wrist / walk). Ctrl+C to stop.\n")

        stop = asyncio.Event()
        loop = asyncio.get_running_loop()
        try:
            loop.add_signal_handler(signal.SIGINT, stop.set)
        except NotImplementedError:
            pass  # Windows fallback: Ctrl+C raises KeyboardInterrupt below

        try:
            await stop.wait()
        except KeyboardInterrupt:
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
    args = p.parse_args()
    asyncio.run(run(args.address, args.chars, args.label))


if __name__ == "__main__":
    main()

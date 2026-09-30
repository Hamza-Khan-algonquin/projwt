#!/usr/bin/env python3
"""ble_scanner_PWT.py — Phase 1, step 1.

Scan for nearby Bluetooth Low Energy devices and print each one's address,
advertised name and signal strength (RSSI). Run this first, wearing the band,
to confirm the host can see it and to grab its BLE address.

Usage:
    python src/ble_scanner_PWT.py            # 8s scan
    python src/ble_scanner_PWT.py --seconds 15
    python src/ble_scanner_PWT.py --name whoop   # only show names containing "whoop"
"""
import argparse
import asyncio

from bleak import BleakScanner


async def scan(seconds: float, name_filter: str | None) -> None:
    print(f"Scanning for {seconds:.0f}s ... (move the band / press its button to wake it)\n")
    devices = await BleakScanner.discover(timeout=seconds, return_adv=True)

    rows = []
    for address, (device, adv) in devices.items():
        name = device.name or adv.local_name or "(unknown)"
        if name_filter and name_filter.lower() not in name.lower():
            continue
        rows.append((adv.rssi if adv.rssi is not None else -999, address, name))

    rows.sort(reverse=True)  # strongest signal first
    if not rows:
        print("No devices matched. Is Bluetooth on? Is the band awake / in range?")
        return

    print(f"{'RSSI':>5}  {'ADDRESS':<20}  NAME")
    print("-" * 60)
    for rssi, address, name in rows:
        shown = f"{rssi:>5}" if rssi != -999 else "  n/a"
        print(f"{shown}  {address:<20}  {name}")
    print("\nCopy the ADDRESS of the band and pass it to gatt_explorer_PWT.py.")


def main() -> None:
    p = argparse.ArgumentParser(description="Scan for BLE devices (ProjWT Phase 1).")
    p.add_argument("--seconds", type=float, default=8.0, help="scan duration (default 8)")
    p.add_argument("--name", dest="name_filter", default=None,
                   help="only show devices whose name contains this substring")
    args = p.parse_args()
    asyncio.run(scan(args.seconds, args.name_filter))


if __name__ == "__main__":
    main()

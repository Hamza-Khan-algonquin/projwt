#!/usr/bin/env python3
"""gatt_explorer_PWT.py — Phase 1, step 2.

Connect to one BLE device and enumerate its GATT layout: every service,
characteristic, the properties each characteristic supports (read / write /
notify / indicate), and any descriptors. This is the map you use to decide
which characteristics to subscribe to in ble_logger_PWT.py.

Usage:
    python src/gatt_explorer_PWT.py <ADDRESS>
    python src/gatt_explorer_PWT.py <ADDRESS> --read   # also read readable chars
"""
import argparse
import asyncio

from bleak import BleakClient


async def explore(address: str, do_read: bool) -> None:
    print(f"Connecting to {address} ...")
    async with BleakClient(address) as client:
        print(f"Connected: {client.is_connected}\n")

        for service in client.services:
            print(f"[service] {service.uuid}  {service.description}")
            for char in service.characteristics:
                props = ",".join(char.properties)
                print(f"    [char] {char.uuid}  ({props})  {char.description}")

                if do_read and "read" in char.properties:
                    try:
                        value = await client.read_gatt_char(char.uuid)
                        print(f"        read -> {value.hex(' ')}  ({len(value)} bytes)")
                    except Exception as exc:  # noqa: BLE001 - surface any read error
                        print(f"        read failed: {exc}")

                for desc in char.descriptors:
                    print(f"        [desc] {desc.uuid}  handle={desc.handle}")
        print("\nNote the UUIDs of characteristics with 'notify' — those stream sensor data.")


def main() -> None:
    p = argparse.ArgumentParser(description="Enumerate a device's GATT table (ProjWT Phase 1).")
    p.add_argument("address", help="BLE address from ble_scanner_PWT.py")
    p.add_argument("--read", action="store_true", help="also read each readable characteristic")
    args = p.parse_args()
    asyncio.run(explore(args.address, args.read))


if __name__ == "__main__":
    main()

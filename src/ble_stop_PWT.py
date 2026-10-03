#!/usr/bin/env python3
r"""ble_stop_PWT.py — turn the band's realtime stream + HR LED back OFF.

Our tools send START (0x03 01) to begin streaming, which powers the optical HR
sensor (the green LED). They send STOP (0x04) when they finish normally — but if a
script is Ctrl+C'd or the window is closed first, STOP never goes out and the band
keeps the sensor/LED on (harmless, but drains battery). Run this any time to send
STOP cleanly.

Usage:
    python ble_stop_PWT.py <ADDRESS>
"""
import argparse
import asyncio

from bleak import BleakClient

import whoop_protocol_PWT as wp


async def run(address: str, with_response: bool) -> None:
    for attempt in range(1, 5):
        try:
            async with BleakClient(address, timeout=25.0) as client:
                print(f"Connected: {client.is_connected}")
                # HELLO first so the band accepts the command on this session
                await client.write_gatt_char(
                    wp.CMD_CHAR_UUID, wp.build_packet(cmd=wp.CMD_HELLO), response=with_response)
                await asyncio.sleep(0.4)
                await client.write_gatt_char(
                    wp.CMD_CHAR_UUID, wp.build_packet(cmd=wp.CMD_RT_HR_OFF), response=with_response)
                print("STOP (0x04) sent — realtime stream + HR LED should switch off.")
            return
        except Exception as exc:  # noqa: BLE001
            print(f"attempt {attempt} failed: {exc}")
            if attempt < 4:
                print("tap the band to wake it; retrying in 4s ...")
                await asyncio.sleep(4)
            else:
                print("Could not reach the band. Toggle Bluetooth OFF/ON, tap it, retry.\n"
                      "(It will also stop on its own after it idles / loses the connection.)")


def main() -> None:
    p = argparse.ArgumentParser(description="Send STOP to turn the band's HR stream/LED off (ProjWT).")
    p.add_argument("address")
    p.add_argument("--no-response", action="store_true", help="use write-without-response")
    args = p.parse_args()
    try:
        asyncio.run(run(args.address, not args.no_response))
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()

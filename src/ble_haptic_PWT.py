#!/usr/bin/env python3
r"""ble_haptic_PWT.py — make the WHOOP buzz (haptic motor test).

Confirms the band's haptic motor responds to our command before we wire buzz
feedback into the gesture controller. Sends RUN_HAPTICS_PATTERN (opcode 79) with
body [pattern_id, loops, 0, 0, 0] — pattern 2 is the 4.0 buzz.

Usage:
    python ble_haptic_PWT.py <ADDRESS>                 # one buzz (pattern 2, 1 loop)
    python ble_haptic_PWT.py <ADDRESS> --loops 3       # longer buzz
    python ble_haptic_PWT.py <ADDRESS> --pattern 1 --loops 2
    python ble_haptic_PWT.py <ADDRESS> --sweep         # try patterns 1..6 to feel them
"""
import argparse
import asyncio

from bleak import BleakClient

import whoop_protocol_PWT as wp


async def buzz(client, seq, pattern, loops):
    frame = wp.build_packet(cmd=wp.CMD_RUN_HAPTICS, seq=seq,
                            data=bytes([pattern & 0xFF, loops & 0xFF, 0, 0, 0]))
    await client.write_gatt_char(wp.CMD_CHAR_UUID, frame, response=True)


async def run(address, pattern, loops, sweep):
    for attempt in range(1, 5):
        try:
            async with BleakClient(address, timeout=25.0) as client:
                print(f"Connected: {client.is_connected} (attempt {attempt})")
                await client.write_gatt_char(wp.CMD_CHAR_UUID,
                    wp.build_packet(cmd=wp.CMD_HELLO), response=True)
                await asyncio.sleep(0.4)
                if sweep:
                    for p in range(1, 7):
                        print(f"  buzzing pattern {p} (2 loops) — feel it ...")
                        await buzz(client, p, p, 2)
                        await asyncio.sleep(1.8)
                else:
                    print(f"  buzzing pattern {pattern}, {loops} loop(s) ...")
                    await buzz(client, 1, pattern, loops)
                    await asyncio.sleep(1.5)
                print("Done. Did you feel it?")
            return
        except Exception as exc:  # noqa: BLE001
            print(f"attempt {attempt} dropped: {exc}")
            if attempt < 4:
                print("Reconnecting in 5s (tap the band) ...")
                await asyncio.sleep(5)


def main():
    p = argparse.ArgumentParser(description="Buzz the WHOOP haptic motor (ProjWT).")
    p.add_argument("address")
    p.add_argument("--pattern", type=int, default=wp.HAPTIC_ALARM_PATTERN)
    p.add_argument("--loops", type=int, default=1)
    p.add_argument("--sweep", action="store_true", help="try patterns 1..6 to compare them")
    args = p.parse_args()
    try:
        asyncio.run(run(args.address, args.pattern, args.loops, args.sweep))
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()

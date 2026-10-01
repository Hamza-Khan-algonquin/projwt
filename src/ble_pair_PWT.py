#!/usr/bin/env python3
"""ble_pair_PWT.py — bond/pair with the band so it will ACCEPT our commands.

Why this exists: the command characteristic (61080002) returned
`GATT Protocol Error: Insufficient Authentication` on write-with-response, and
silently ignored write-without-response. That ATT error means the characteristic
needs an ENCRYPTED / PAIRED link. Until we pair, none of our commands reach the
band — every "reply" we saw was the subscribe-triggered status beacon or
physical-motion events.

This tool connects and performs BLE pairing/bonding. After it succeeds once, the
bond is remembered by Windows, so later sessions (sweep/stream) can send
commands over the encrypted link.

Usage:
    python ble_pair_PWT.py <ADDRESS>
    python ble_pair_PWT.py <ADDRESS> --unpair     # remove the bond, start over

Notes:
  * A Windows pairing prompt may pop up — accept it.
  * If it reports "already paired", that's fine — you're good to go.
"""
import argparse
import asyncio

from bleak import BleakClient


async def run(address: str, unpair: bool) -> None:
    async with BleakClient(address) as client:
        print(f"Connected: {client.is_connected}")

        if unpair:
            try:
                ok = await client.unpair()
                print(f"unpair() -> {ok}")
            except Exception as exc:  # noqa: BLE001
                print(f"unpair() not supported / failed: {exc}")
            return

        try:
            ok = await client.pair()
            print(f"pair() -> {ok}")
            if ok:
                print("\nPAIRED. The encrypted link is up — commands should now be")
                print("accepted. Next: re-run the sweep WITH --with-response:")
                print(f"    python ble_sweep_PWT.py {address} --with-response")
            else:
                print("\npair() returned False. Try the Windows pairing prompt if it")
                print("appeared, or run with --unpair then pair again.")
        except Exception as exc:  # noqa: BLE001
            print(f"pair() failed: {exc}")
            print("\nIf this says 'already paired', you're fine. Otherwise try pairing")
            print("from Windows Settings > Bluetooth & devices, or --unpair then retry.")


def main() -> None:
    p = argparse.ArgumentParser(description="Pair/bond with the WHOOP band (ProjWT).")
    p.add_argument("address", help="BLE address from ble_scanner_PWT.py")
    p.add_argument("--unpair", action="store_true", help="remove the existing bond")
    args = p.parse_args()
    try:
        asyncio.run(run(args.address, args.unpair))
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()

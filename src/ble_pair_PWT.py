#!/usr/bin/env python3
"""ble_pair_PWT.py — bond/pair with the band so it ACCEPTS our commands.

Why: the command characteristic (61080002) returns ATT error 0x05
`Insufficient Authentication` on write-with-response, and silently ignores
write-without-response. That means the link must be ENCRYPTED (BLE paired/bonded)
before the band will honour commands.

Windows note: the band has no screen/buttons, so it needs the "ConfirmOnly"
pairing ceremony. bleak's default `pair()` often returns None on this stack, so
this tool talks to the Windows pairing API (WinRT) directly with the right
ceremony, and falls back to bleak's pair() if WinRT isn't available.

Usage:
    python ble_pair_PWT.py <ADDRESS>            # pair
    python ble_pair_PWT.py <ADDRESS> --unpair   # remove the bond, start over
    python ble_pair_PWT.py <ADDRESS> --status   # just report pairing state
"""
import argparse
import asyncio


def _addr_to_int(address: str) -> int:
    return int(address.replace(":", "").replace("-", ""), 16)


async def _winrt_pair(address: str, unpair: bool, status_only: bool) -> bool:
    """Pair via the Windows Runtime API with the ConfirmOnly ceremony."""
    from winrt.windows.devices.bluetooth import BluetoothLEDevice
    from winrt.windows.devices.enumeration import (
        DevicePairingKinds, DevicePairingProtectionLevel, DevicePairingResultStatus,
        DeviceUnpairingResultStatus,
    )

    dev = await BluetoothLEDevice.from_bluetooth_address_async(_addr_to_int(address))
    if dev is None:
        print("WinRT: couldn't get the device by address (is it awake / in range?).")
        return False

    pairing = dev.device_information.pairing
    print(f"WinRT: is_paired={pairing.is_paired}  can_pair={pairing.can_pair}")

    if status_only:
        return pairing.is_paired

    if unpair:
        res = await pairing.unpair_async()
        ok = res.status in (DeviceUnpairingResultStatus.UNPAIRED,
                            DeviceUnpairingResultStatus.ALREADY_UNPAIRED)
        print(f"WinRT unpair status: {res.status}  -> {'OK' if ok else 'FAILED'}")
        return ok

    if pairing.is_paired:
        print("WinRT: already paired — you're good.")
        return True
    if not pairing.can_pair:
        print("WinRT: device reports it cannot pair right now. Make sure it's awake,")
        print("close the WHOOP phone app, and that it isn't bonded elsewhere.")
        return False

    custom = pairing.custom

    def on_pairing_requested(_sender, args):
        # No PIN on the band -> just confirm.
        args.accept()

    custom.add_pairing_requested(on_pairing_requested)
    result = await custom.pair_async(
        DevicePairingKinds.CONFIRM_ONLY, DevicePairingProtectionLevel.ENCRYPTION
    )
    ok = result.status in (DevicePairingResultStatus.PAIRED,
                          DevicePairingResultStatus.ALREADY_PAIRED)
    print(f"WinRT pair status: {result.status}  -> {'PAIRED' if ok else 'FAILED'}")
    return ok


async def _bleak_pair(address: str, unpair: bool) -> bool:
    """Fallback: use bleak's own pair()/unpair()."""
    from bleak import BleakClient
    async with BleakClient(address) as client:
        print(f"bleak connected: {client.is_connected}")
        if unpair:
            try:
                print(f"bleak unpair() -> {await client.unpair()}")
            except Exception as exc:  # noqa: BLE001
                print(f"bleak unpair() failed: {exc}")
            return False
        try:
            res = await client.pair()
            print(f"bleak pair() -> {res}")
            return bool(res)
        except Exception as exc:  # noqa: BLE001
            print(f"bleak pair() failed: {exc}")
            return False


async def run(address: str, unpair: bool, status_only: bool) -> None:
    ok = False
    try:
        ok = await _winrt_pair(address, unpair, status_only)
    except ImportError:
        print("WinRT not available; falling back to bleak pairing.")
        ok = await _bleak_pair(address, unpair)
    except Exception as exc:  # noqa: BLE001
        print(f"WinRT pairing error: {exc}\nFalling back to bleak pairing.")
        try:
            ok = await _bleak_pair(address, unpair)
        except Exception as exc2:  # noqa: BLE001
            print(f"bleak fallback also failed: {exc2}")

    if status_only or unpair:
        return
    if ok:
        print("\nSUCCESS — encrypted link established. Now run:")
        print(f"    python ble_sweep_PWT.py {address} --with-response")
    else:
        print("\nNot paired yet. Options:")
        print("  * Make sure the band is awake (tap it) and the WHOOP phone app is closed.")
        print("  * Try: python ble_pair_PWT.py <ADDR> --unpair   then pair again.")
        print("  * Windows Settings > Bluetooth & devices > Add device.")
        print("  * Tell Claude the exact status text printed above.")


def main() -> None:
    p = argparse.ArgumentParser(description="Pair/bond with the WHOOP band (ProjWT).")
    p.add_argument("address", help="BLE address from ble_scanner_PWT.py")
    p.add_argument("--unpair", action="store_true", help="remove the existing bond")
    p.add_argument("--status", action="store_true", help="only report pairing state")
    args = p.parse_args()
    try:
        asyncio.run(run(args.address, args.unpair, args.status))
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()

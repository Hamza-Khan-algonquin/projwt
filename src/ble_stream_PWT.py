#!/usr/bin/env python3
"""ble_stream_PWT.py — Phase 2, step 2: get a CONTINUOUS sensor stream.

What we learned: sending "start real-time" (cmd 0x03) on its own only gets a
single event/status packet back on the event channel (61080003). Reference
implementations do a HELLO handshake FIRST, then start real-time, and the
continuous sensor data arrives as ~96-byte packets on the DATA channel
(61080004).

This tool does the full sequence:
    1. connect (no pairing)
    2. subscribe to every notify channel
    3. send HELLO (0x05)          <- the step we were missing
    4. send START real-time (0x03)
    5. listen, logging everything, and FLAG every packet on the data channel
    6. on exit, send STOP (0x04) so the band stops streaming (saves battery)

Everything is framed with our verified whoop_protocol_PWT.build_packet().

Usage:
    # full sequence, listen 30s (wear the band, good skin contact):
    python ble_stream_PWT.py <ADDRESS> --seconds 30

    # skip hello (compare behaviour), or change the start command:
    python ble_stream_PWT.py <ADDRESS> --no-hello
    python ble_stream_PWT.py <ADDRESS> --start-cmd 0x03 --hello-cmd 0x05

    # use write-with-response (some stacks need it):
    python ble_stream_PWT.py <ADDRESS> --with-response
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


def _parse_int(text: str) -> int:
    return int(text, 0)  # accepts 0x05 or 5


async def _write(client: BleakClient, packet: bytes, with_response: bool, tag: str) -> None:
    print(f"-> {tag}: {packet.hex(' ')}")
    try:
        await client.write_gatt_char(wp.CMD_CHAR_UUID, packet, response=with_response)
        print("   write OK")
    except Exception as exc:  # noqa: BLE001
        print(f"   write failed ({exc}); retrying response={not with_response}")
        await client.write_gatt_char(wp.CMD_CHAR_UUID, packet, response=not with_response)
        print("   write OK on retry")


async def run(address: str, seconds: float, with_response: bool,
              send_hello: bool, hello_cmd: int, start_cmd: int, stop_cmd: int,
              do_pair: bool = False, start_data: bytes = b"") -> None:
    LOG_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"stream_{stamp}_PWT.jsonl"
    per_char = Counter()
    data_packets = 0

    log_file = log_path.open("w", encoding="utf-8")

    def make_handler(uuid: str):
        is_data = uuid == wp.DATA_CHAR_UUID

        def handler(_sender, payload: bytearray) -> None:
            nonlocal data_packets
            per_char[uuid] += 1
            rec = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "char": uuid,
                "len": len(payload),
                "hex": payload.hex(),
            }
            log_file.write(json.dumps(rec) + "\n")
            log_file.flush()
            if is_data:
                data_packets += 1
                print(f"  <-[DATA(05)] len={len(payload)}  {payload.hex(' ')}")
            elif per_char[uuid] <= 6:  # don't spam for chatty non-data chars
                print(f"  <-{wp.cname(uuid)} len={len(payload)}  {payload.hex(' ')}")
        return handler

    try:
        for attempt in range(1, 5):
            try:
                async with BleakClient(address, timeout=25.0) as client:
                    print(f"Connected: {client.is_connected} (attempt {attempt})")
                    if not client.is_connected:
                        raise RuntimeError("connect returned but link is down")
                    await asyncio.sleep(1.5)  # let the encrypted link settle
                    if do_pair:
                        try:
                            print(f"pairing... pair() -> {await client.pair()}")
                        except Exception as exc:  # noqa: BLE001
                            print(f"pair() failed/already paired: {exc}")

                    for uuid in wp.NOTIFY_CHARS + [wp.HR_CHAR_UUID]:
                        await client.start_notify(uuid, make_handler(uuid))
                    print("subscribed to all channels\n")

                    if send_hello:
                        await _write(client, wp.build_packet(cmd=hello_cmd, seq=0),
                                     with_response, f"HELLO (0x{hello_cmd:02x})")
                        await asyncio.sleep(1.0)  # let the handshake settle

                    dtag = f" data={start_data.hex()}" if start_data else ""
                    await _write(client, wp.build_packet(cmd=start_cmd, seq=1, data=start_data),
                                 with_response, f"START (0x{start_cmd:02x}){dtag}")

                    print(f"\nListening {seconds:.0f}s — keep the band on, hold still.\n")
                    try:
                        await asyncio.sleep(seconds)
                    except asyncio.CancelledError:
                        pass
                    finally:
                        try:
                            await _write(client, wp.build_packet(cmd=stop_cmd, seq=2),
                                         with_response, f"STOP (0x{stop_cmd:02x})")
                        except Exception:  # noqa: BLE001
                            pass
                        for uuid in wp.NOTIFY_CHARS + [wp.HR_CHAR_UUID]:
                            try:
                                await client.stop_notify(uuid)
                            except Exception:  # noqa: BLE001
                                pass
                break  # completed a full listen window
            except Exception as exc:  # noqa: BLE001
                print(f"\nattempt {attempt} dropped: {exc}")
                if attempt < 4:
                    print("Tap the band to wake it; reconnecting in 3s ...")
                    await asyncio.sleep(3)
                else:
                    print("Giving up after repeated drops — re-run once the band is awake.")
    finally:
        log_file.close()

    print(f"\n=== Summary -> {log_path} ===")
    total = sum(per_char.values())
    print(f"total packets: {total}")
    for uuid, n in per_char.most_common():
        flag = "  <-- DATA CHANNEL" if uuid == wp.DATA_CHAR_UUID else ""
        print(f"  {wp.cname(uuid)}: {n}{flag}")
    if data_packets:
        print(f"\nSUCCESS: {data_packets} packets on the data channel. "
              "Send Claude this log to build the decoder.")
    else:
        print("\nNo data-channel packets yet. Next things to try (tell Claude which):"
              "\n  * --with-response"
              "\n  * a different --hello-cmd or --start-cmd"
              "\n  * the band may need a clock-sync packet before START")


def main() -> None:
    p = argparse.ArgumentParser(description="HELLO -> START real-time stream (ProjWT Phase 2).")
    p.add_argument("address", help="BLE address from ble_scanner_PWT.py")
    p.add_argument("--seconds", type=float, default=30.0, help="listen duration (default 30)")
    p.add_argument("--with-response", action="store_true",
                   help="write-with-response (needed once paired; surfaces real errors)")
    p.add_argument("--pair", action="store_true",
                   help="pair/bond first so the encrypted link accepts commands")
    p.add_argument("--no-hello", action="store_true", help="skip the HELLO handshake")
    p.add_argument("--hello-cmd", type=_parse_int, default=wp.CMD_HELLO)
    p.add_argument("--start-cmd", type=_parse_int, default=wp.CMD_RT_HR_ON)
    p.add_argument("--stop-cmd", type=_parse_int, default=wp.CMD_RT_HR_OFF)
    p.add_argument("--start-data", default="",
                   help="hex payload to attach to START, e.g. 01 (toggles/sensor mask)")
    args = p.parse_args()

    start_data = bytes.fromhex(args.start_data) if args.start_data else b""
    try:
        asyncio.run(run(args.address, args.seconds, args.with_response,
                        not args.no_hello, args.hello_cmd, args.start_cmd, args.stop_cmd,
                        args.pair, start_data))
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()

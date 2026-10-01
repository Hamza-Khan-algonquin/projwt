#!/usr/bin/env python3
"""ble_command_PWT.py — Phase 2, step 1: wake the sensor streams.

The band stays silent until it's told to start streaming. This tool:
  1. connects (no pairing),
  2. subscribes to every notify channel so we catch the band's reply,
  3. writes a framed command to the command characteristic (61080002),
  4. keeps listening and logs every packet (incl. the response) to logs/.

Framing is verified in whoop_protocol_PWT.py. The command IDs are
community-sourced, so if one doesn't wake the stream we iterate quickly by
passing a different --cmd / --data.

Usage:
    # default: send "start real-time HR/stream" (cmd 0x03), listen 25s
    python ble_command_PWT.py <ADDRESS>

    python ble_command_PWT.py <ADDRESS> --preset hr_off --seconds 10
    python ble_command_PWT.py <ADDRESS> --cmd 0x03 --seconds 30
    python ble_command_PWT.py <ADDRESS> --cmd 0x0a --data 00112233   # raw
"""
import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from bleak import BleakClient

import whoop_protocol_PWT as wp

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def _parse_int(text: str) -> int:
    return int(text, 0)  # accepts 0x03 or 3


async def run(address: str, cmd: int, data: bytes, seq: int,
              seconds: float, with_response: bool) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"command_cmd{cmd:02x}_{stamp}_PWT.jsonl"
    packet_count = 0

    async with BleakClient(address) as client:
        print(f"Connected: {client.is_connected}")
        log_file = log_path.open("w", encoding="utf-8")

        def make_handler(uuid: str):
            def handler(_sender, payload: bytearray) -> None:
                nonlocal packet_count
                packet_count += 1
                rec = {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "char": uuid,
                    "len": len(payload),
                    "hex": payload.hex(),
                }
                log_file.write(json.dumps(rec) + "\n")
                log_file.flush()
                print(f"  <- {wp.cname(uuid)}  {payload.hex(' ')}")
            return handler

        # subscribe to every notify characteristic we know about
        for uuid in wp.NOTIFY_CHARS + [wp.HR_CHAR_UUID]:
            try:
                await client.start_notify(uuid, make_handler(uuid))
                print(f"subscribed: {uuid}")
            except Exception as exc:  # noqa: BLE001
                print(f"could not subscribe {uuid}: {exc}")

        packet = wp.build_packet(cmd=cmd, seq=seq, data=data)
        print(f"\n-> writing to {wp.CMD_CHAR_UUID[-8:]}: {packet.hex(' ')}")
        print(f"   (type=0x{wp.TYPE_COMMAND:02x} seq={seq} cmd=0x{cmd:02x} data={data.hex(' ') or '-'})")
        try:
            await client.write_gatt_char(wp.CMD_CHAR_UUID, packet, response=with_response)
            print("   write OK")
        except Exception as exc:  # noqa: BLE001
            print(f"   write FAILED ({exc}). Retrying with response={not with_response}...")
            await client.write_gatt_char(wp.CMD_CHAR_UUID, packet, response=not with_response)
            print("   write OK on retry")

        print(f"\nListening {seconds:.0f}s for a reply / stream ... (wear the band, skin contact)\n")
        try:
            await asyncio.sleep(seconds)
        except asyncio.CancelledError:
            pass
        finally:
            for uuid in wp.NOTIFY_CHARS + [wp.HR_CHAR_UUID]:
                try:
                    await client.stop_notify(uuid)
                except Exception:  # noqa: BLE001
                    pass
            log_file.close()

    print(f"\nDone. {packet_count} packets received -> {log_path}")
    if packet_count == 0:
        print("No reply. Next: the band may need the hello/clock handshake first,\n"
              "or a different command id — tell Claude and we'll try the next candidate.")


def main() -> None:
    p = argparse.ArgumentParser(description="Send a framed WHOOP command and listen (ProjWT Phase 2).")
    p.add_argument("address", help="BLE address from ble_scanner_PWT.py")
    p.add_argument("--preset", choices=sorted(wp.COMMANDS), default=None,
                   help="named command (default: hr_on)")
    p.add_argument("--cmd", type=_parse_int, default=None, help="raw command id, e.g. 0x03")
    p.add_argument("--data", default="", help="hex payload data, e.g. 00112233")
    p.add_argument("--seq", type=_parse_int, default=0, help="sequence byte (default 0)")
    p.add_argument("--seconds", type=float, default=25.0, help="listen duration (default 25)")
    p.add_argument("--with-response", action="store_true",
                   help="use write-with-response (default is write-without-response)")
    args = p.parse_args()

    if args.cmd is not None:
        cmd = args.cmd
    elif args.preset is not None:
        cmd = wp.COMMANDS[args.preset]
    else:
        cmd = wp.CMD_RT_HR_ON  # default

    data = bytes.fromhex(args.data) if args.data else b""

    try:
        asyncio.run(run(args.address, cmd, data, args.seq, args.seconds, args.with_response))
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()

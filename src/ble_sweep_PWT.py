#!/usr/bin/env python3
"""ble_sweep_PWT.py — Phase 2, step 3: FIND the real "start stream" opcode.

Our command IDs were community guesses, and cmd 0x03 only produces the ~2s
status beacon on the EVENT channel (61080003) — the DATA channel (61080004)
stays silent. So we sweep a range of command IDs and watch which one makes the
DATA channel light up.

For each command id in the range it:
  * sends the framed command,
  * waits `--dwell` seconds,
  * counts packets per channel during that window,
  * flags any command that produced DATA(04) traffic.

Everything is logged to logs/ with the probe command id, so we can analyse
offline too.

SAFETY: the default range is 0x01..0x0f (the low "app" opcodes: hello, battery,
info, start/stop, history, time-sync). We deliberately DON'T sweep high opcodes
(firmware/reset territory). Widen only when you know what you're doing.

Usage:
    # sweep 0x01..0x0f, 3s each, hello first:
    python ble_sweep_PWT.py <ADDRESS>

    python ble_sweep_PWT.py <ADDRESS> --with-response
    python ble_sweep_PWT.py <ADDRESS> --start 0x01 --end 0x0f --dwell 4
    python ble_sweep_PWT.py <ADDRESS> --data 01        # 1-byte payload on each cmd
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
    return int(text, 0)


async def run(address: str, start: int, end: int, dwell: float, data: bytes,
              with_response: bool, send_hello: bool, do_pair: bool) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"sweep_{stamp}_PWT.jsonl"
    state = {"cmd": None}
    # counts[cmd][channel_uuid] = n
    counts: dict[int, Counter] = {}
    hits: list[int] = []  # cmds that produced DATA(04)

    async with BleakClient(address) as client:
        print(f"Connected: {client.is_connected}")
        if do_pair:
            try:
                print(f"pairing... pair() -> {await client.pair()}")
            except Exception as exc:  # noqa: BLE001
                print(f"pair() failed/already paired: {exc}")
        print()
        log_file = log_path.open("w", encoding="utf-8")

        def make_handler(uuid: str):
            def handler(_sender, payload: bytearray) -> None:
                cmd = state["cmd"]
                rec = {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "probe_cmd": cmd,
                    "char": uuid,
                    "len": len(payload),
                    "hex": payload.hex(),
                }
                log_file.write(json.dumps(rec) + "\n")
                log_file.flush()
                if cmd is not None:
                    counts.setdefault(cmd, Counter())[uuid] += 1
                    if uuid == wp.DATA_CHAR_UUID and cmd not in hits:
                        hits.append(cmd)
                        print(f"  *** DATA(05) RESPONDED to cmd 0x{cmd:02x} !!! "
                              f"len={len(payload)} {payload.hex(' ')}")
            return handler

        for uuid in wp.NOTIFY_CHARS + [wp.HR_CHAR_UUID]:
            try:
                await client.start_notify(uuid, make_handler(uuid))
            except Exception as exc:  # noqa: BLE001
                print(f"could not subscribe {wp.cname(uuid)}: {exc}")
        print("subscribed to all notify channels\n")

        if send_hello:
            state["cmd"] = None  # don't attribute the baseline to a probe
            pkt = wp.build_packet(cmd=wp.CMD_HELLO, seq=0)
            try:
                await client.write_gatt_char(wp.CMD_CHAR_UUID, pkt, response=with_response)
                print(f"HELLO sent (0x{wp.CMD_HELLO:02x}); settling 1.5s\n")
            except Exception as exc:  # noqa: BLE001
                print(f"HELLO failed: {exc}")
            await asyncio.sleep(1.5)

        seq = 1
        for cmd in range(start, end + 1):
            state["cmd"] = cmd
            pkt = wp.build_packet(cmd=cmd, seq=seq, data=data)
            seq = (seq + 1) & 0xFF
            try:
                await client.write_gatt_char(wp.CMD_CHAR_UUID, pkt, response=with_response)
                status = "sent"
            except Exception as exc:  # noqa: BLE001
                status = f"WRITE FAILED ({exc})"
            await asyncio.sleep(dwell)
            per = counts.get(cmd, Counter())
            summary = ", ".join(f"{wp.cname(u)}={n}" for u, n in per.most_common()) or "(silence)"
            data_n = per.get(wp.DATA_CHAR_UUID, 0)
            mark = "  <<< DATA!" if data_n else ""
            print(f"cmd 0x{cmd:02x}  {status:>4}  ->  {summary}{mark}")

        state["cmd"] = None
        # always try to leave the band quiet
        try:
            await client.write_gatt_char(
                wp.CMD_CHAR_UUID, wp.build_packet(cmd=wp.CMD_RT_HR_OFF, seq=seq),
                response=with_response)
        except Exception:  # noqa: BLE001
            pass
        for uuid in wp.NOTIFY_CHARS + [wp.HR_CHAR_UUID]:
            try:
                await client.stop_notify(uuid)
            except Exception:  # noqa: BLE001
                pass
        log_file.close()

    print(f"\n=== Sweep done -> {log_path} ===")
    if hits:
        print("DATA(04) channel responded to these command id(s):")
        for cmd in hits:
            print(f"   0x{cmd:02x}  ({counts[cmd][wp.DATA_CHAR_UUID]} packets)")
        print("\nThat's our START opcode. Send Claude this log and we'll lock it in.")
    else:
        print("No command woke the DATA(04) channel in this range.")
        print("Send Claude the log anyway — the per-command reply pattern still")
        print("tells us a lot. Next we can: --with-response, add a --data payload,")
        print("or (carefully) widen the range.")


def main() -> None:
    p = argparse.ArgumentParser(description="Sweep WHOOP command ids to find the stream trigger.")
    p.add_argument("address", help="BLE address from ble_scanner_PWT.py")
    p.add_argument("--start", type=_parse_int, default=0x01, help="first cmd id (default 0x01)")
    p.add_argument("--end", type=_parse_int, default=0x0f, help="last cmd id (default 0x0f)")
    p.add_argument("--dwell", type=float, default=3.0, help="seconds to listen per cmd (default 3)")
    p.add_argument("--data", default="", help="hex payload sent with every cmd, e.g. 01")
    p.add_argument("--with-response", action="store_true",
                   help="write-with-response (needed once paired; surfaces real errors)")
    p.add_argument("--pair", action="store_true",
                   help="pair/bond first so the encrypted link accepts commands")
    p.add_argument("--no-hello", action="store_true", help="skip the HELLO handshake first")
    args = p.parse_args()

    data = bytes.fromhex(args.data) if args.data else b""
    try:
        asyncio.run(run(args.address, args.start, args.end, args.dwell, data,
                        args.with_response, not args.no_hello, args.pair))
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""ble_accel_PWT.py — find and stream the accelerometer / motion data.

What we know:
  * START = cmd 0x03 with payload 0x01 turns on HR/RR metrics: type-0x28,
    subtype-0x02 packets at ~1 Hz on DATA(05).
  * The 0x01 is almost certainly a SENSOR BITMASK — other bits probably enable the
    accelerometer (a much higher-rate stream) and other sensors.

Two modes:

  --sweep   Try a series of START payloads; for each, report the distinct packet
            (type, subtype) combos seen on DATA(05)/EVT(04), their counts and rate.
            A payload that unlocks the accelerometer shows a NEW subtype and/or a
            much higher packet rate than the 1 Hz HR stream. (default mode)

  (stream)  With --start-data XX, START with that payload and stream live,
            classifying each packet: HR for subtype 0x02, otherwise a tentative
            int16 X/Y/Z accelerometer decode + raw hex. Move your wrist and watch
            which bytes swing. Use --label to tag the capture.

Examples:
    python ble_accel_PWT.py <ADDR>                 # sweep payloads to find accel
    python ble_accel_PWT.py <ADDR> --start-data 03 --seconds 20 --label wave
    python ble_accel_PWT.py <ADDR> --start-data ff --seconds 20 --label shake
"""
import argparse
import asyncio
import json
import struct
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from bleak import BleakClient

import whoop_protocol_PWT as wp

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"

# START payloads to try in --sweep mode (single-bit masks + a few combos).
PAYLOAD_SWEEP = [b"\x01", b"\x02", b"\x03", b"\x04", b"\x05", b"\x06", b"\x07",
                 b"\x08", b"\x0f", b"\x1f", b"\xff", b"\x03\xff"]


def classify(frame: bytes):
    """Return (type, subtype) of a framed packet, or (None, None)."""
    p = wp.unframe(frame)
    if p is None or len(p) < 2:
        return None, None
    return p[0], p[1]


def accel_guess(frame: bytes) -> str:
    """Tentative int16 X/Y/Z read from a non-HR payload (to eyeball motion)."""
    p = wp.unframe(frame)
    if p is None or len(p) < 12:
        return ""
    # try int16 LE triples starting a few offsets in; show the most plausible
    out = []
    for off in (6, 8, 10):
        if off + 6 <= len(p):
            x, y, z = struct.unpack_from("<hhh", p, off)
            out.append(f"@{off}:({x},{y},{z})")
    return "  " + " ".join(out)


async def _keepalive_listen(client, seconds):
    t = 0.0
    while t < seconds:
        await asyncio.sleep(2.0)
        t += 2.0
        try:
            await client.read_gatt_char(wp.BATTERY_LEVEL_UUID)
        except Exception:  # noqa: BLE001
            pass


async def run(address, mode_sweep, start_data, seconds, label, with_response,
              mode_cmd=False, cmd_lo=0x10, cmd_hi=0x1f):
    LOG_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tag = "cmdsweep" if mode_cmd else ("sweep" if mode_sweep else f"accel_{label}")
    log_path = LOG_DIR / f"{tag}_{stamp}_PWT.jsonl"
    state = {"key": None}
    combos: dict[str, Counter] = {}

    async with BleakClient(address, timeout=25.0) as client:
        print(f"Connected: {client.is_connected}\n")
        log_file = log_path.open("w", encoding="utf-8")

        def make_handler(uuid):
            def handler(_sender, payload):
                frame = bytes(payload)
                key = state["key"]
                log_file.write(json.dumps({
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "key": key, "char": uuid, "len": len(frame), "hex": frame.hex(),
                }) + "\n")
                log_file.flush()
                t, s = classify(frame)
                combo = f"{wp.cname(uuid)}/type{t:#04x}.{s:#04x}" if t is not None else wp.cname(uuid)
                if key is not None:
                    combos.setdefault(key, Counter())[combo] += 1
                if not mode_sweep and uuid == wp.DATA_CHAR_UUID:
                    rt = wp.parse_rt(frame)
                    if rt:
                        rr = (" RR=" + ",".join(map(str, rt["rr"])) + "ms") if rt["rr"] else ""
                        print(f"  [HR] {rt['hr']} bpm{rr}")
                    else:
                        print(f"  [?{s:#04x}] {frame.hex(' ')}{accel_guess(frame)}")
                elif not mode_sweep and uuid == wp.EVENT_CHAR_UUID:
                    print(f"  [EVT] {frame.hex(' ')}")
            return handler

        for uuid in wp.NOTIFY_CHARS + [wp.HR_CHAR_UUID]:
            try:
                await client.start_notify(uuid, make_handler(uuid))
            except Exception as exc:  # noqa: BLE001
                print(f"  (subscribe {wp.cname(uuid)} failed: {exc})")
        await client.write_gatt_char(wp.CMD_CHAR_UUID,
                                     wp.build_packet(cmd=wp.CMD_HELLO), response=with_response)
        await asyncio.sleep(0.8)

        async def send(cmd, data=b""):
            await client.write_gatt_char(wp.CMD_CHAR_UUID,
                                         wp.build_packet(cmd=cmd, data=data), response=with_response)

        if mode_cmd:
            print("HR on (0x03 01); sweeping extra opcodes 0x%02x-0x%02x for a raw/accel"
                  % (cmd_lo, cmd_hi))
            print("stream. Hold still so a rate jump / new subtype means the command.\n")
            await send(wp.CMD_RT_HR_ON, b"\x01")
            await asyncio.sleep(1.0)
            dwell = 4.0
            for cmd in range(cmd_lo, cmd_hi + 1):
                state["key"] = f"{cmd:02x}"
                try:
                    await send(cmd)
                    await asyncio.sleep(0.3)
                    await send(cmd, b"\x01")  # also try with an on-flag payload
                except Exception as exc:  # noqa: BLE001
                    print(f"cmd 0x{cmd:02x}: write failed {exc}")
                await _keepalive_listen(client, dwell)
                per = combos.get(f"{cmd:02x}", Counter())
                total = sum(per.values())
                rate = total / dwell
                summary = ", ".join(f"{k}={v}" for k, v in per.most_common()) or "(silence)"
                flag = "   <<< RATE JUMP / check subtype" if rate > 3.0 else ""
                print(f"cmd 0x{cmd:02x} -> {rate:4.1f}/s  {summary}{flag}")
            state["key"] = None
            await send(wp.CMD_RT_HR_OFF)
        elif mode_sweep:
            print("Sweeping START payloads — watching for NEW subtypes / higher rate.")
            print("(Hold still so extra packets mean the payload, not your motion.)\n")
            dwell = 5.0
            for pl in PAYLOAD_SWEEP:
                state["key"] = None
                try:
                    await send(wp.CMD_RT_HR_OFF)
                except Exception:  # noqa: BLE001
                    pass
                await asyncio.sleep(0.4)
                state["key"] = pl.hex()
                try:
                    await send(wp.CMD_RT_HR_ON, pl)
                except Exception as exc:  # noqa: BLE001
                    print(f"payload {pl.hex()}: write failed {exc}")
                await _keepalive_listen(client, dwell)
                per = combos.get(pl.hex(), Counter())
                total = sum(per.values())
                summary = ", ".join(f"{k}={v}" for k, v in per.most_common()) or "(silence)"
                rate = total / dwell
                print(f"START 0x03 {pl.hex():<4} -> {rate:4.1f}/s  {summary}")
            state["key"] = None
            await send(wp.CMD_RT_HR_OFF)
        else:
            print(f"START 0x03 {start_data.hex()} ; streaming {seconds:.0f}s — "
                  f"MOVE YOUR WRIST (label='{label}') and watch which bytes swing.\n")
            state["key"] = "stream"
            await send(wp.CMD_RT_HR_ON, start_data)
            await _keepalive_listen(client, seconds)
            await send(wp.CMD_RT_HR_OFF)

        for uuid in wp.NOTIFY_CHARS + [wp.HR_CHAR_UUID]:
            try:
                await client.stop_notify(uuid)
            except Exception:  # noqa: BLE001
                pass
        log_file.close()

    print(f"\n=== Done -> {log_path} ===")
    if mode_sweep:
        baseline = set(combos.get("01", Counter()).keys())
        print(f"\nBaseline (payload 01) subtypes: {sorted(baseline) or '(none)'}")
        print("Payloads that introduced NEW subtypes or much higher rates are the")
        print("accelerometer candidates — send Claude this log.")


def main() -> None:
    p = argparse.ArgumentParser(description="Find/stream the WHOOP accelerometer (ProjWT).")
    p.add_argument("address")
    p.add_argument("--start-data", default=None,
                   help="hex START payload to stream live (omit to run the payload sweep)")
    p.add_argument("--seconds", type=float, default=20.0, help="stream duration (live mode)")
    p.add_argument("--label", default="move", help="tag for the capture (live mode)")
    p.add_argument("--cmd-sweep", action="store_true",
                   help="keep HR on and sweep extra opcodes (default 0x10-0x1f) for a raw/accel stream")
    p.add_argument("--cmd-start", type=lambda x: int(x, 0), default=0x10)
    p.add_argument("--cmd-end", type=lambda x: int(x, 0), default=0x1f)
    p.add_argument("--no-response", action="store_true", help="use write-without-response")
    args = p.parse_args()

    mode_cmd = args.cmd_sweep
    mode_sweep = (args.start_data is None) and not mode_cmd
    start_data = bytes.fromhex(args.start_data) if args.start_data else b""
    try:
        asyncio.run(run(args.address, mode_sweep, start_data, args.seconds,
                        args.label, not args.no_response,
                        mode_cmd, args.cmd_start, args.cmd_end))
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()

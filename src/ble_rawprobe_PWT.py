#!/usr/bin/env python3
r"""ble_rawprobe_PWT.py — try the real raw/IMU enable commands (from community RE).

Our opcode sweep stopped at 0x2f; the raw-stream enables live HIGHER (0x6a/0x6b),
which is why we never saw them. Per github.com/tanarchytan/whoop-rs (MIT), these
are session-scoped and write no flash config:

  SET_IMU_DATA_STREAM 0x6a  payload [01, state]  -> live IMU (type 0x33), 100 Hz 6-axis
  SEND_OPTICAL_DATA   0x6b  payload [01, state]  -> raw optical v20 + v21 IMU
                                                     (some live as type 0x2b REALTIME_RAW)
  SEND_R10_R11        0x3f  payload [00]          -> richer realtime stream

This probe enables each (ON), watches DATA(05) for the live raw/IMU packet types
(0x2b / 0x33) while you MOVE your wrist, then turns it back OFF. It flags whether a
live high-rate stream appeared and tentatively decodes IMU accel (int16 * 1/4096 g).

WEAR THE BAND and move during each phase. Everything logs to logs/ for decoding.

Usage:
    python ble_rawprobe_PWT.py <ADDRESS>
    python ble_rawprobe_PWT.py <ADDRESS> --dwell 10
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
RAW_TYPES = {wp.PKT_REALTIME_RAW: "RAW(0x2b)", wp.PKT_REALTIME_IMU: "IMU(0x33)"}

# (name, opcode, payload_on, payload_off_or_None)
TRIALS = [
    ("IMU stream (0x6a)",  wp.CMD_SET_IMU_STREAM, b"\x01\x01", b"\x01\x00"),
    ("Optical raw (0x6b)", wp.CMD_SEND_OPTICAL,   b"\x01\x01", b"\x01\x00"),
    ("R10/R11 (0x3f)",     wp.CMD_R10_R11_REALTIME, b"\x00",   None),
]


def imu_accel_sample(frame: bytes):
    """Tentative first accel triple from an IMU/raw frame: int16 x/y/z * (1/4096) g."""
    p = wp.unframe(frame)
    if p is None or len(p) < 14:
        return None
    # scan a few plausible offsets for an int16 triple with ~1g magnitude
    for off in (6, 8, 10, 12):
        if off + 6 <= len(p):
            x, y, z = struct.unpack_from("<hhh", p, off)
            g = (x * x + y * y + z * z) ** 0.5 * wp.IMU_ACCEL_SCALE_G
            if 0.5 < g < 2.0:
                return (x * wp.IMU_ACCEL_SCALE_G, y * wp.IMU_ACCEL_SCALE_G,
                        z * wp.IMU_ACCEL_SCALE_G, off)
    return None


async def run(address: str, dwell: float, with_response: bool) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"rawprobe_{stamp}_PWT.jsonl"
    log_file = log_path.open("w", encoding="utf-8")
    state = {"key": None}
    per = {}          # trial -> Counter of "DATA(05)/type0xNN"
    raw_hits = {}     # trial -> count of raw/IMU-type frames

    def make_handler(uuid):
        def handler(_sender, payload):
            frame = bytes(payload)
            key = state["key"]
            p = wp.unframe(frame)
            ptype = p[0] if p else None
            log_file.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                           "key": key, "char": uuid, "type": ptype, "len": len(frame),
                           "hex": frame.hex()}) + "\n")
            log_file.flush()
            if key is None or uuid != wp.DATA_CHAR_UUID:
                return
            tag = f"type{ptype:#04x}" if ptype is not None else "raw?"
            per.setdefault(key, Counter())[tag] += 1
            if ptype in RAW_TYPES:
                raw_hits[key] = raw_hits.get(key, 0) + 1
                acc = imu_accel_sample(frame)
                extra = (f"  accel≈({acc[0]:+.2f},{acc[1]:+.2f},{acc[2]:+.2f})g @{acc[3]}"
                         if acc else "")
                print(f"    <<< {RAW_TYPES[ptype]} len={len(frame)}{extra}")
        return handler

    async def session(client):
        async def send(cmd, data=b""):
            await client.write_gatt_char(wp.CMD_CHAR_UUID,
                                         wp.build_packet(cmd=cmd, data=data), response=with_response)

        for uuid in wp.NOTIFY_CHARS + [wp.HR_CHAR_UUID]:
            try:
                await client.start_notify(uuid, make_handler(uuid))
            except Exception as exc:  # noqa: BLE001
                print(f"  (subscribe {wp.cname(uuid)} failed: {exc})")
                raise
        await send(wp.CMD_HELLO)
        await asyncio.sleep(0.6)
        try:
            val = await client.read_gatt_char(wp.BATTERY_LEVEL_UUID)
            print(f"Battery: {val[0]}%\n" if val else "")
        except Exception:  # noqa: BLE001
            pass

        for name, op, on, off in TRIALS:
            state["key"] = name
            print(f"\n=== {name}: ON (0x{op:02x} {on.hex()}) — MOVE YOUR WRIST for {dwell:.0f}s ===")
            try:
                await send(op, on)
            except Exception as exc:  # noqa: BLE001
                print(f"  write failed: {exc}")
            # listen with battery-read keepalive
            t = 0.0
            while t < dwell:
                await asyncio.sleep(1.0)
                t += 1.0
                try:
                    await client.read_gatt_char(wp.BATTERY_LEVEL_UUID)
                except Exception:  # noqa: BLE001
                    raise
            if off is not None:
                try:
                    await send(op, off)
                except Exception:  # noqa: BLE001
                    pass
            c = per.get(name, Counter())
            total = sum(c.values())
            rate = total / dwell
            summary = ", ".join(f"{k}={v}" for k, v in c.most_common()) or "(silence)"
            hit = raw_hits.get(name, 0)
            flag = f"   <<< RAW/IMU STREAM! ({hit} frames, {hit/dwell:.1f}/s)" if hit else ""
            print(f"  -> {rate:.1f}/s  {summary}{flag}")

        state["key"] = None
        # safety: make sure everything is off
        for op, off in [(wp.CMD_SET_IMU_STREAM, b"\x01\x00"),
                        (wp.CMD_SEND_OPTICAL, b"\x01\x00"),
                        (wp.CMD_RT_HR_OFF, b"")]:
            try:
                await send(op, off)
            except Exception:  # noqa: BLE001
                pass
        for uuid in wp.NOTIFY_CHARS + [wp.HR_CHAR_UUID]:
            try:
                await client.stop_notify(uuid)
            except Exception:  # noqa: BLE001
                pass

    try:
        for attempt in range(1, 5):
            try:
                async with BleakClient(address, timeout=25.0) as client:
                    print(f"Connected: {client.is_connected} (attempt {attempt})")
                    if not client.is_connected:
                        raise RuntimeError("link down after connect")
                    await session(client)
                break
            except Exception as exc:  # noqa: BLE001
                print(f"\nattempt {attempt} dropped: {exc}")
                if attempt < 4:
                    print("Reconnecting in 5s (tap the band) ...")
                    await asyncio.sleep(5)
                else:
                    print("Giving up — toggle Bluetooth OFF/ON, tap the band, retry.")
    finally:
        log_file.close()

    print(f"\n=== Done -> {log_path} ===")
    winners = [n for n, h in raw_hits.items() if h]
    if winners:
        print("LIVE RAW/IMU stream from: " + ", ".join(winners))
        print("Send Claude this log — we'll lock in the decoder (accel = int16/4096 g).")
    else:
        print("No live raw/IMU frames appeared. If every trial was HR-only, raw may need")
        print("the band worn+asleep / R22 (Gen5-only) — tell Claude and send the log.")


def main() -> None:
    p = argparse.ArgumentParser(description="Probe raw/IMU enable commands (ProjWT).")
    p.add_argument("address")
    p.add_argument("--dwell", type=float, default=8.0, help="seconds to listen per trial (default 8)")
    p.add_argument("--no-response", action="store_true", help="use write-without-response")
    args = p.parse_args()
    try:
        asyncio.run(run(args.address, args.dwell, not args.no_response))
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
r"""ble_rawstream_PWT.py — get RAW sensor data off a WHOOP 4.0 (Gen4), done right.

Our first probe only enabled optical collection and then waited — so nothing came.
The real recipe (from tanarchytan/whoop-rs client.rs + offload.rs) is a SEQUENCE:

  Phase B (the Gen4 raw path = BANKED, via historical offload):
     1. SEND_OPTICAL  [01,01]   enable raw optical collection   (no ACK expected)
     2. SEND_HISTORICAL [00]    KICK the drain                  <-- we were missing this
     3. ACK loop: for every METADATA HistoryEnd, write HISTORICAL_RESULT [01]+end_data
        so the strap advances instead of stalling; stop on HistoryComplete.
     4. SEND_OPTICAL [01,00]    turn collection back off (leave the band as we found it)
     Records arrive as type-0x2f HISTORICAL_DATA: v24 (HR/R-R/gravity/SpO2/temp),
     v25 (PPG + gravity), v5 (HR/R-R). Gravity = the accel-derived orientation vector.

  Phase A (long-shot: a LIVE stream): the flash path always sends TOGGLE_REALTIME_HR
     before SET_IMU_DATA_STREAM, so live IMU may only flow while realtime HR runs.
     We try HR-on -> SET_IMU_STREAM [01,01] and watch for live type 0x33 / 0x2b while
     you move. The 100 Hz v21 IMU buffer is a Gen5/R22 record, so this may stay silent
     on a 4.0 — that's a real finding, not a failure.

WEAR THE BAND. In Phase A, move your wrist. Everything logs to logs/ for offline decode.

Usage:
    python ble_rawstream_PWT.py <ADDRESS>
    python ble_rawstream_PWT.py <ADDRESS> --drain 25 --no-live
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


async def run(address: str, drain: float, live: float, with_response: bool) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"rawstream_{stamp}_PWT.jsonl"
    log_file = log_path.open("w", encoding="utf-8")

    phase = {"name": "setup"}
    counts = {}                       # phase -> Counter of type tags
    events = asyncio.Queue()          # ("ack", end_data) / ("complete",) from the handler
    seq = {"n": 0}
    hist = {"records": 0, "hr": [], "grav": 0, "versions": Counter(), "sample": None}

    def logrec(uuid, frame, ptype):
        log_file.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                       "phase": phase["name"], "char": uuid, "type": ptype,
                       "len": len(frame), "hex": frame.hex()}) + "\n")
        log_file.flush()

    def make_handler(uuid):
        def handler(_sender, payload):
            frame = bytes(payload)
            p = wp.unframe(frame)
            ptype = p[0] if p else None
            logrec(uuid, frame, ptype)
            tag = f"{ptype:#04x}" if ptype is not None else "raw?"
            counts.setdefault(phase["name"], Counter())[tag] += 1

            if ptype == wp.PKT_HISTORICAL:
                rec = wp.decode_historical(frame)
                if rec:
                    hist["records"] += 1
                    hist["versions"][rec["version"]] += 1
                    if rec.get("hr"):
                        hist["hr"].append(rec["hr"])
                    if rec.get("gravity"):
                        hist["grav"] += 1
                    if hist["sample"] is None and (rec.get("gravity") or rec.get("hr")):
                        hist["sample"] = rec
            elif ptype == wp.PKT_METADATA and p is not None and len(p) >= 3:
                sub = p[2]
                if sub == wp.META_HISTORY_END and len(p) >= 21:
                    events.put_nowait(("ack", bytes(p[13:21])))
                elif sub == wp.META_HISTORY_COMPLETE:
                    events.put_nowait(("complete", None))
            elif ptype in (wp.PKT_REALTIME_RAW, wp.PKT_REALTIME_IMU):
                print(f"    <<< LIVE RAW type {ptype:#04x} len={len(frame)}")
        return handler

    async def send(cmd, data=b""):
        frame = wp.build_packet(cmd=cmd, seq=seq["n"] & 0xFF, data=data)
        seq["n"] += 1
        await client_ref["c"].write_gatt_char(wp.CMD_CHAR_UUID, frame, response=with_response)

    client_ref = {"c": None}

    async def session(client):
        client_ref["c"] = client
        for uuid in wp.NOTIFY_CHARS + [wp.HR_CHAR_UUID]:
            await client.start_notify(uuid, make_handler(uuid))
        await send(wp.CMD_HELLO)
        await asyncio.sleep(0.5)
        try:
            val = await client.read_gatt_char(wp.BATTERY_LEVEL_UUID)
            print(f"Battery: {val[0]}%" if val else "")
        except Exception:  # noqa: BLE001
            pass

        # ---- Phase A: live-stream attempt (HR running, then IMU stream) ----
        if live > 0:
            phase["name"] = "live(HR+IMU)"
            print(f"\n=== Phase A: live IMU attempt — MOVE YOUR WRIST for {live:.0f}s ===")
            await send(wp.CMD_RT_HR_ON, wp.RT_START_PAYLOAD)
            await asyncio.sleep(1.0)
            await send(wp.CMD_SET_IMU_STREAM, b"\x01\x01")
            t = 0.0
            while t < live:
                await asyncio.sleep(1.0)
                t += 1.0
                try:
                    await client.read_gatt_char(wp.BATTERY_LEVEL_UUID)
                except Exception:  # noqa: BLE001
                    raise
            await send(wp.CMD_SET_IMU_STREAM, b"\x01\x00")
            await send(wp.CMD_RT_HR_OFF)
            c = counts.get("live(HR+IMU)", Counter())
            live_raw = c.get(f"{wp.PKT_REALTIME_IMU:#04x}", 0) + c.get(f"{wp.PKT_REALTIME_RAW:#04x}", 0)
            print(f"  -> {dict(c)}" + ("   <<< LIVE RAW STREAM!" if live_raw else "  (HR-only; no live raw — expected on Gen4)"))

        # ---- Phase B: historical offload of banked raw (gravity / PPG / HR) ----
        phase["name"] = "offload"
        print(f"\n=== Phase B: enabling optical + draining banked raw (up to {drain:.0f}s) ===")
        await send(wp.CMD_SEND_OPTICAL, b"\x01\x01")     # enable collection (no ACK)
        await asyncio.sleep(0.3)
        await send(wp.CMD_SEND_HISTORICAL, b"\x00")       # KICK the drain
        acks = 0
        loop = asyncio.get_event_loop()
        deadline = loop.time() + drain
        done = False
        while not done and loop.time() < deadline:
            try:
                kind, data = await asyncio.wait_for(events.get(), timeout=2.0)
            except asyncio.TimeoutError:
                # keepalive; keep listening until deadline
                try:
                    await client.read_gatt_char(wp.BATTERY_LEVEL_UUID)
                except Exception:  # noqa: BLE001
                    raise
                continue
            if kind == "ack":
                await send(wp.CMD_HISTORICAL_RESULT, b"\x01" + data)
                acks += 1
            elif kind == "complete":
                print("  HISTORY_COMPLETE — drain finished.")
                done = True
        # clean up: abort any in-flight drain, turn optical off, stop notifies
        try:
            await send(wp.CMD_ABORT_HISTORICAL)
            await send(wp.CMD_SEND_OPTICAL, b"\x01\x00")
        except Exception:  # noqa: BLE001
            pass
        for uuid in wp.NOTIFY_CHARS + [wp.HR_CHAR_UUID]:
            try:
                await client.stop_notify(uuid)
            except Exception:  # noqa: BLE001
                pass

        c = counts.get("offload", Counter())
        print(f"  frames: {dict(c)}   (acked {acks} chunks)")

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
    if hist["records"]:
        hrs = hist["hr"]
        hr_txt = f"HR {min(hrs)}-{max(hrs)} bpm ({len(hrs)} secs)" if hrs else "no HR field"
        vers = ", ".join(f"v{v}×{n}" for v, n in hist["versions"].most_common())
        print(f"RAW BANKED DATA DECODED: {hist['records']} historical records "
              f"[{vers}], {hist['grav']} with a gravity/orientation vector, {hr_txt}.")
        s = hist["sample"]
        if s and s.get("gravity"):
            g = s["gravity"]
            print(f"  e.g. gravity=({g['x']:+.2f},{g['y']:+.2f},{g['z']:+.2f})g "
                  f"|{g['mag']:.2f}|  <- real accel-derived orientation off YOUR band")
        print("Send Claude logs/rawstream_*.jsonl — we lock in the full decoder + wire gravity into gestures.")
    else:
        print("No historical records decoded. If frames DID arrive (see counts above),")
        print("send the log — the record offsets may differ on your firmware. If truly")
        print("silent, the band may need to be worn+still a moment before it banks data.")


def main() -> None:
    p = argparse.ArgumentParser(description="WHOOP 4.0 raw acquisition done right (ProjWT).")
    p.add_argument("address")
    p.add_argument("--drain", type=float, default=20.0, help="max seconds for the historical drain (default 20)")
    p.add_argument("--live", type=float, default=6.0, help="seconds for the live-IMU attempt (default 6; 0 to skip)")
    p.add_argument("--no-live", action="store_true", help="skip Phase A entirely")
    p.add_argument("--no-response", action="store_true", help="write-without-response")
    args = p.parse_args()
    live = 0.0 if args.no_live else args.live
    try:
        asyncio.run(run(args.address, args.drain, live, not args.no_response))
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()

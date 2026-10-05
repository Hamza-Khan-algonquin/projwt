#!/usr/bin/env python3
r"""smart_climate_PWT.py — set the Tesla cabin temp from YOUR body + the weather.

Reads your wrist skin temperature off the WHOOP, reads the car's outside temp from
the Fleet API, blends them into a comfort target, and sets the cabin climate.

Skin-temp source (in order):
  --skin-temp C        you pass it directly
  --band <ADDRESS>     live: brief historical offload off the band to read it now
  (default)            the newest logs/rawstream_*_PWT.csv capture

Needs the proxy running + TESLA_VEHICLE_TAG / TESLA_FLEET_BASE set (same as the
gesture controller). Use --dry to preview without sending.

Usage:
    python smart_climate_PWT.py --skin-temp 31.5
    python smart_climate_PWT.py --band D1:86:73:D4:62:86
    python smart_climate_PWT.py --skin-temp 33 --pref 22 --dry
"""
import argparse
import asyncio
import csv
from pathlib import Path

import whoop_protocol_PWT as wp
from vehicle_actuator_PWT import TeslaFleetActuator

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"

# comfort model constants (tune to taste)
SKIN_NEUTRAL = 33.0     # wrist skin temp (C) that feels "neutral"
SKIN_GAIN = 0.6         # cabin C per 1 C of skin deviation
OUT_NEUTRAL = 21.0      # outside temp (C) needing no bias
OUT_GAIN = 0.08         # cabin C per 1 C of outside deviation
TESLA_MIN, TESLA_MAX = 15.0, 28.0


def comfort_target(skin_c, outside_c, pref=21.0, runs_cold=0.0):
    """Blend body + weather into a cabin target, clamped to Tesla's range (0.5 steps)."""
    skin_adj = (SKIN_NEUTRAL - skin_c) * SKIN_GAIN          # cold wrist -> warmer cabin
    out_adj = (OUT_NEUTRAL - outside_c) * OUT_GAIN          # cold outside -> slight preheat
    target = pref + runs_cold + skin_adj + out_adj
    target = max(TESLA_MIN, min(TESLA_MAX, round(target * 2) / 2))
    return target, skin_adj, out_adj


def skin_from_csv():
    csvs = sorted(LOG_DIR.glob("rawstream_*_PWT.csv"))
    if not csvs:
        return None
    temps = []
    with csvs[-1].open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            raw = row.get("skin_temp_raw")
            if raw and raw.isdigit():
                c = int(raw) * 0.04
                if 20 <= c <= 45:
                    temps.append(c)
    return temps[-1] if temps else None   # most recent valid reading


async def skin_from_band(address, dwell=7.0):
    """Brief live offload: enable optical, kick history, read skin_temp from v24 records."""
    from bleak import BleakClient
    latest = {"c": None}

    def handler(_s, payload):
        rec = wp.decode_historical(bytes(payload))
        if rec and rec.get("skin_temp_raw"):
            c = rec["skin_temp_raw"] * 0.04
            if 20 <= c <= 45:
                latest["c"] = c

    try:
        async with BleakClient(address, timeout=25.0) as client:
            print(f"Connected: {client.is_connected} — reading skin temp ...")
            await client.start_notify(wp.DATA_CHAR_UUID, handler)
            await client.write_gatt_char(wp.CMD_CHAR_UUID, wp.build_packet(cmd=wp.CMD_HELLO), response=True)
            await asyncio.sleep(0.4)
            await client.write_gatt_char(wp.CMD_CHAR_UUID,
                wp.build_packet(cmd=wp.CMD_SEND_OPTICAL, data=b"\x01\x01"), response=True)
            await client.write_gatt_char(wp.CMD_CHAR_UUID,
                wp.build_packet(cmd=wp.CMD_SEND_HISTORICAL, data=b"\x00"), response=True)
            t = 0.0
            while t < dwell and latest["c"] is None:
                await asyncio.sleep(0.5)
                t += 0.5
            for cmd, d in [(wp.CMD_SEND_OPTICAL, b"\x01\x00"), (wp.CMD_ABORT_HISTORICAL, b"")]:
                try:
                    await client.write_gatt_char(wp.CMD_CHAR_UUID, wp.build_packet(cmd=cmd, data=d), response=True)
                except Exception:  # noqa: BLE001
                    pass
    except Exception as exc:  # noqa: BLE001
        print(f"band read failed: {exc}")
    return latest["c"]


def main():
    ap = argparse.ArgumentParser(description="Set Tesla cabin temp from body + weather (ProjWT).")
    ap.add_argument("--skin-temp", type=float, default=None, help="wrist skin temp in C")
    ap.add_argument("--band", default=None, help="band address: read skin temp live")
    ap.add_argument("--pref", type=float, default=21.0, help="your baseline cabin temp (C)")
    ap.add_argument("--runs-cold", type=float, default=0.0, help="bias: + if you like it warmer")
    ap.add_argument("--dry", action="store_true", help="preview, don't send")
    args = ap.parse_args()

    # 1. skin temp
    if args.skin_temp is not None:
        skin = args.skin_temp
    elif args.band:
        skin = asyncio.run(skin_from_band(args.band))
    else:
        skin = skin_from_csv()
    if skin is None:
        raise SystemExit("no skin temp (pass --skin-temp, --band, or capture a rawstream first)")

    # 2. outside temp from the car
    act = TeslaFleetActuator(dry=args.dry)
    vd = act.get_vehicle_data()
    if not vd.get("ok"):
        print(f"(could not read vehicle data: {vd.get('error')}; assuming outside 20 C)")
        outside = 20.0
    else:
        outside = (vd["data"].get("climate_state") or {}).get("outside_temp", 20.0)

    # 3. compute + send
    target, sadj, oadj = comfort_target(skin, outside, args.pref, args.runs_cold)
    print(f"\n  skin {skin:.1f}C  outside {outside:.1f}C  base {args.pref:.1f}C"
          f"  (skin{sadj:+.1f}, out{oadj:+.1f})")
    print(f"  => cabin target {target:.1f}C\n")

    r1 = act.raw_command("set_temps", {"driver_temp": target, "passenger_temp": target}, "set_temps")
    r2 = act.raw_command("auto_conditioning_start", {}, "climate_on")
    for r in (r1, r2):
        tag = "OK" if r.get("ok") else f"FAILED ({r.get('error')})"
        print(f"  {r['command']}: {tag}" + (f" | {r['detail']}" if r.get("detail") else ""))


if __name__ == "__main__":
    main()

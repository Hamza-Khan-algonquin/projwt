#!/usr/bin/env python3
"""decode_realtime_PWT.py — decode a captured real-time stream log.

Reads a logs/*.jsonl capture, decodes the type-0x28 real-time packets on the DATA
channel (61080005), and prints heart rate + RR intervals over time, with a short
summary (min/avg/max HR, beat count).

Usage:
    python decode_realtime_PWT.py ..\logs\stream_YYYYMMDD_HHMMSS_PWT.jsonl
    python decode_realtime_PWT.py <logfile> --csv hr.csv
"""
import argparse
import json
from pathlib import Path

import whoop_protocol_PWT as wp


def main() -> None:
    p = argparse.ArgumentParser(description="Decode a ProjWT real-time capture.")
    p.add_argument("logfile", help="path to a logs/*.jsonl capture")
    p.add_argument("--csv", default=None, help="also write ts,hr,rr to this CSV")
    args = p.parse_args()

    path = Path(args.logfile)
    if not path.exists():
        raise SystemExit(f"not found: {path}")

    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        if rec.get("char", "").lower() != wp.DATA_CHAR_UUID:
            continue
        rt = wp.parse_rt(bytes.fromhex(rec["hex"]))
        if rt:
            rows.append(rt)

    if not rows:
        print("No real-time (type-0x28) packets found on DATA(05) in this log.")
        return

    print(f"{'ts':>12}  {'HR':>3}  RR(ms)")
    print("-" * 36)
    hrs = []
    beats = 0
    for rt in rows:
        hrs.append(rt["hr"])
        beats += len(rt["rr"])
        rr = ",".join(str(x) for x in rt["rr"])
        print(f"{rt['ts']:>12}  {rt['hr']:>3}  {rr}")

    valid = [h for h in hrs if 20 < h < 240]
    print("-" * 36)
    print(f"packets: {len(rows)}   beats(RR): {beats}")
    if valid:
        print(f"HR  min/avg/max: {min(valid)} / {sum(valid)//len(valid)} / {max(valid)} bpm")

    if args.csv:
        out = Path(args.csv)
        with out.open("w", encoding="utf-8") as f:
            f.write("ts,hr,rr_ms\n")
            for rt in rows:
                f.write(f"{rt['ts']},{rt['hr']},{'|'.join(str(x) for x in rt['rr'])}\n")
        print(f"wrote {out}")


if __name__ == "__main__":
    main()

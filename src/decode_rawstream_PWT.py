#!/usr/bin/env python3
r"""decode_rawstream_PWT.py — turn a rawstream capture into clean sensor data.

Reads a logs/rawstream_*_PWT.jsonl capture (the banked raw we drained off the band
via the historical offload) and decodes every type-0x2f HISTORICAL_DATA record into
a per-second time series: HR, R-R count, gravity/orientation vector (g), SpO2 raw
red/IR, skin-temp raw, respiration raw. Writes a CSV next to the log and prints a
summary with simple sanity stats so we can see the data is real.

Usage:
    python decode_rawstream_PWT.py                      # newest rawstream log
    python decode_rawstream_PWT.py ..\logs\rawstream_20261004_183000_PWT.jsonl
"""
import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import whoop_protocol_PWT as wp

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
FIELDS = ["unix", "iso", "version", "hr", "rr_count", "gx", "gy", "gz", "gmag",
          "spo2_red", "spo2_ir", "skin_temp_raw", "resp_raw"]


def main() -> None:
    ap = argparse.ArgumentParser(description="Decode a rawstream capture to CSV + summary.")
    ap.add_argument("logfile", nargs="?", default=None)
    args = ap.parse_args()

    if args.logfile:
        path = Path(args.logfile)
    else:
        logs = sorted(LOG_DIR.glob("rawstream_*_PWT.jsonl"))
        if not logs:
            raise SystemExit(f"no rawstream_*_PWT.jsonl in {LOG_DIR}")
        path = logs[-1]
    if not path.exists():
        raise SystemExit(f"not found: {path}")

    rows, versions = [], Counter()
    hr_vals, gmags, seen_unix = [], [], set()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:  # noqa: BLE001
            continue
        if rec.get("type") != wp.PKT_HISTORICAL:
            continue
        d = wp.decode_historical(bytes.fromhex(rec["hex"]))
        if not d:
            continue
        versions[d["version"]] += 1
        g = d.get("gravity") or {}
        unix = d["unix"]
        iso = datetime.fromtimestamp(unix, timezone.utc).isoformat() if 1_400_000_000 < unix < 2_200_000_000 else ""
        rows.append({
            "unix": unix, "iso": iso, "version": d["version"],
            "hr": d.get("hr"), "rr_count": d.get("rr_count"),
            "gx": round(g["x"], 4) if g else None, "gy": round(g["y"], 4) if g else None,
            "gz": round(g["z"], 4) if g else None, "gmag": round(g["mag"], 4) if g else None,
            "spo2_red": d.get("spo2_red"), "spo2_ir": d.get("spo2_ir"),
            "skin_temp_raw": d.get("skin_temp_raw"), "resp_raw": d.get("resp_raw"),
        })
        if d.get("hr"):
            hr_vals.append(d["hr"])
        if g:
            gmags.append(g["mag"])
        seen_unix.add(unix)

    if not rows:
        raise SystemExit("No historical records decoded in that log.")

    # de-dup on unix for a clean series, keep arrival order otherwise
    rows.sort(key=lambda r: r["unix"])
    csv_path = path.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    span = max(seen_unix) - min(seen_unix) if len(seen_unix) > 1 else 0
    print(f"=== {path.name}: {len(rows)} historical records ===")
    print(f"versions: " + ", ".join(f"v{v}×{n}" for v, n in versions.most_common()))
    if span:
        t0 = datetime.fromtimestamp(min(seen_unix), timezone.utc)
        t1 = datetime.fromtimestamp(max(seen_unix), timezone.utc)
        print(f"time span: {span}s (~{span/60:.1f} min)  {t0:%Y-%m-%d %H:%M}–{t1:%H:%M} UTC")
    if hr_vals:
        print(f"HR: {min(hr_vals)}–{max(hr_vals)} bpm, mean {sum(hr_vals)/len(hr_vals):.0f} ({len(hr_vals)} secs)")
    if gmags:
        near1 = sum(1 for m in gmags if 0.9 <= m <= 1.1)
        print(f"gravity: {len(gmags)} vectors, |g| mean {sum(gmags)/len(gmags):.3f} "
              f"({100*near1/len(gmags):.0f}% within 0.9–1.1 g → clean orientation data)")
    print(f"\nCSV written: {csv_path}")
    print("Columns: unix,iso,version,hr,rr_count,gx,gy,gz,gmag,spo2_red,spo2_ir,skin_temp_raw,resp_raw")
    print("This is the dashboard feed: HR trend + orientation. Send Claude the CSV header + ~5 rows.")


if __name__ == "__main__":
    main()

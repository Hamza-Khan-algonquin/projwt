#!/usr/bin/env python3
r"""decode_debuglog_PWT.py — mine the band's own firmware debug-log text.

During a historical dump the band emits type-0x32 packets whose bodies are ASCII
firmware log lines (e.g. "Sensors: Realtime raw disabled", "HELLO: Nordic Ver:
17.2.2.0"). Those lines name the firmware's own features and commands — our best
clue for finding a config/enable command (e.g. to turn on "realtime raw").

This reads a logs/*.jsonl capture, pulls readable strings out of every packet
(focus on type 0x32), de-dupes, and prints them so we can read what the firmware
says it can do.

Usage:
    python decode_debuglog_PWT.py ..\logs\cmdsweep_YYYYMMDD_HHMMSS_PWT.jsonl
    python decode_debuglog_PWT.py <logfile> --grep realtime,raw,sensor,enable,config
"""
import argparse
import json
import re
from pathlib import Path

import whoop_protocol_PWT as wp

ASCII_RUN = re.compile(rb"[\x20-\x7e]{4,}")   # printable runs of >=4 chars


def strings_from_frame(hexstr: str):
    raw = bytes.fromhex(hexstr)
    out = []
    # try the unframed payload first (drops framing/CRC noise), then the raw frame
    for buf in (wp.unframe(raw) or b"", raw):
        for m in ASCII_RUN.findall(buf):
            try:
                out.append(m.decode("ascii"))
            except Exception:  # noqa: BLE001
                pass
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Extract firmware debug-log strings from a capture.")
    p.add_argument("logfile")
    p.add_argument("--grep", default=None,
                   help="comma-separated keywords; only show lines containing one (case-insensitive)")
    args = p.parse_args()

    path = Path(args.logfile)
    if not path.exists():
        raise SystemExit(f"not found: {path}")
    keys = [k.strip().lower() for k in args.grep.split(",")] if args.grep else None

    seen, ordered = set(), []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:  # noqa: BLE001
            continue
        hexstr = rec.get("hex")
        if not hexstr:
            continue
        for s in strings_from_frame(hexstr):
            s = s.strip()
            if len(s) < 4 or s in seen:
                continue
            if keys and not any(k in s.lower() for k in keys):
                continue
            seen.add(s)
            ordered.append(s)

    if not ordered:
        print("No readable firmware strings found (need a capture containing type-0x32 "
              "debug packets — e.g. the historical-dump / cmd-sweep log).")
        return
    print(f"=== {len(ordered)} unique firmware strings from {path.name} ===\n")
    for s in ordered:
        print("  " + s)
    print("\nLook for: 'Realtime raw', 'Sensors:', 'enable/disable', 'config', 'threshold',"
          " 'stream', command names — these hint at a BLE command to enable raw sensors.")


if __name__ == "__main__":
    main()

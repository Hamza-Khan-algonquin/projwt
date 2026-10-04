#!/usr/bin/env python3
r"""analyze_rawprobe_PWT.py — post-mortem for a raw-probe capture.

The live probe only PRINTS frames on the DATA(05) characteristic, but it LOGS
every channel. So if the band answered the raw/IMU enable commands on RESP(03),
EVENT(04) or DIAG(07) — an ack, an "unsupported", or an actual stream on a
different char — it's in the log but was invisible in the console.

This reads the newest logs/rawprobe_*_PWT.jsonl (or one you name) and reports,
per characteristic, how many frames arrived and of which packet types — and
dumps a sample of any non-HR frame so we can see what the firmware actually said.

Usage:
    python analyze_rawprobe_PWT.py
    python analyze_rawprobe_PWT.py ..\logs\rawprobe_20261004_175559_PWT.jsonl
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import whoop_protocol_PWT as wp

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
# short name for each known characteristic prefix
CHAN = {
    wp.RESP_CHAR_UUID[:8]: "RESP(03)",
    wp.EVENT_CHAR_UUID[:8]: "EVENT(04)",
    wp.DATA_CHAR_UUID[:8]: "DATA(05)",
    wp.DIAG_CHAR_UUID[:8]: "DIAG(07)",
    wp.HR_CHAR_UUID[:8]: "HR(2a37)",
}


def chan(uuid: str) -> str:
    return CHAN.get((uuid or "")[:8], (uuid or "?")[:8])


def main() -> None:
    p = argparse.ArgumentParser(description="Summarize a raw-probe capture across ALL channels.")
    p.add_argument("logfile", nargs="?", default=None)
    args = p.parse_args()

    if args.logfile:
        path = Path(args.logfile)
    else:
        logs = sorted(LOG_DIR.glob("rawprobe_*_PWT.jsonl"))
        if not logs:
            raise SystemExit(f"no rawprobe_*_PWT.jsonl in {LOG_DIR}")
        path = logs[-1]
    if not path.exists():
        raise SystemExit(f"not found: {path}")

    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:  # noqa: BLE001
            pass

    print(f"=== {path.name}: {len(rows)} frames total ===\n")

    # per (trial, channel) -> Counter of packet types
    by_key = defaultdict(lambda: defaultdict(Counter))
    for r in rows:
        key = r.get("key") or "(before trials: HELLO/handshake)"
        by_key[key][chan(r.get("char"))][r.get("type")] += 1

    for key in by_key:
        print(f"[{key}]")
        for channel, types in sorted(by_key[key].items()):
            parts = ", ".join(
                f"type{t:#04x}={n}" if isinstance(t, int) else f"unparsed={n}"
                for t, n in types.most_common()
            )
            print(f"    {channel:<10} {sum(types.values()):>4} frames   {parts}")
        print()

    # show a sample of every distinct non-HR packet type we saw, decoded a bit
    print("--- sample of each distinct packet type (first occurrence) ---")
    seen = set()
    for r in rows:
        t = r.get("type")
        c = chan(r.get("char"))
        tag = (c, t)
        if tag in seen or t == wp.PKT_REALTIME_HR:
            continue
        seen.add(tag)
        frame = bytes.fromhex(r["hex"])
        body = wp.unframe(frame)
        tdesc = f"{t:#04x}" if isinstance(t, int) else "unparsed"
        print(f"  {c:<10} type {tdesc:<6} len={len(frame):<3} "
              f"payload[0:16]={body[:16].hex() if body else '-'}")
        # pull any ASCII (firmware often answers in text)
        if body:
            ascii_run = bytes(b if 0x20 <= b < 0x7f else 0x2e for b in body[:48]).decode()
            if any(ch.isalpha() for ch in ascii_run):
                print(f"              ascii: {ascii_run}")

    if not seen:
        print("  (nothing but HR / empty — band stayed silent on every channel)")
    print("\nTakeaway:")
    print("  * Frames on RESP(03) during a trial = the band ACKed/answered the command.")
    print("  * type 0x2b / 0x33 on ANY channel  = we DID get live raw/IMU (decoder next).")
    print("  * Only HR(0x28) + empty everywhere = live raw is firmware-gated on this Gen4;")
    print("    fall back to FLICK + phone-IMU per the architecture.")


if __name__ == "__main__":
    main()

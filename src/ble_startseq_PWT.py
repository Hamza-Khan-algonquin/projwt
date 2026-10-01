#!/usr/bin/env python3
"""ble_startseq_PWT.py — try several "start streaming" strategies in one session.

Background: the reference project streams with a bare START (0x03), but our band
(fw 17.2.2.0) only returns single acks, never a continuous stream. This tool
holds ONE stable connection (kept alive with a harmless Battery-Level read, which
doesn't disturb the WHOOP session) and runs a series of candidate start sequences,
listening after each and reporting which channel(s) light up — and whether any
produce a *continuous* stream (several packets in the listen window).

It logs everything (tagged with the strategy name) to logs/ for offline analysis.

Usage:
    python ble_startseq_PWT.py <ADDRESS>
    python ble_startseq_PWT.py <ADDRESS> --dwell 8
"""
import argparse
import asyncio
import json
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from bleak import BleakClient

import whoop_protocol_PWT as wp

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"

# Each strategy: (name, [(cmd, payload_bytes), ...]). Sent in order, then we listen.
def _strategies() -> list[tuple[str, list[tuple[int, bytes]]]]:
    epoch = int(time.time())
    epoch_le = epoch.to_bytes(4, "little")
    return [
        ("start_03_bare",       [(0x03, b"")]),
        ("start_03_p01",        [(0x03, bytes([0x01]))]),
        ("start_03_p0100",      [(0x03, bytes([0x01, 0x00]))]),
        ("start_03_p01000000",  [(0x03, bytes([0x01, 0x00, 0x00, 0x00]))]),
        ("timesync07_then_03",  [(0x07, epoch_le), (0x03, b"")]),
        ("timesync07ms_then_03",[(0x07, epoch_le + b"\x00\x00\x00\x00"), (0x03, b"")]),
        ("hist06",              [(0x06, b"")]),
        ("cmd08",               [(0x08, b"")]),
        ("cmd09",               [(0x09, b"")]),
        ("cmd0a",               [(0x0a, b"")]),
    ]


async def _write(client, cmd, data, with_response):
    pkt = wp.build_packet(cmd=cmd, data=data)
    await client.write_gatt_char(wp.CMD_CHAR_UUID, pkt, response=with_response)


async def _listen(client, dwell):
    """Listen for `dwell` seconds, holding the link with a battery read every 2s."""
    t = 0.0
    while t < dwell:
        await asyncio.sleep(2.0)
        t += 2.0
        try:
            await client.read_gatt_char(wp.BATTERY_LEVEL_UUID)
        except Exception:  # noqa: BLE001
            pass


async def run(address: str, dwell: float, with_response: bool) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"startseq_{stamp}_PWT.jsonl"
    state = {"name": None}
    counts: dict[str, Counter] = defaultdict(Counter)
    first_hex: dict[str, dict[str, str]] = defaultdict(dict)

    async with BleakClient(address, timeout=25.0) as client:
        print(f"Connected: {client.is_connected}\n")
        log_file = log_path.open("w", encoding="utf-8")

        def make_handler(uuid: str):
            def handler(_sender, payload: bytearray) -> None:
                name = state["name"]
                log_file.write(json.dumps({
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "strategy": name, "char": uuid,
                    "len": len(payload), "hex": payload.hex(),
                }) + "\n")
                log_file.flush()
                if name is not None:
                    counts[name][uuid] += 1
                    first_hex[name].setdefault(uuid, payload.hex())
            return handler

        for uuid in wp.NOTIFY_CHARS + [wp.HR_CHAR_UUID]:
            try:
                await client.start_notify(uuid, make_handler(uuid))
            except Exception as exc:  # noqa: BLE001
                print(f"  (subscribe {wp.cname(uuid)} failed: {exc})")
        print("subscribed; HELLO handshake...\n")
        await _write(client, wp.CMD_HELLO, b"", with_response)
        await asyncio.sleep(1.0)

        for name, steps in _strategies():
            # reset to a clean state first (STOP), uncounted
            state["name"] = None
            try:
                await _write(client, wp.CMD_RT_HR_OFF, b"", with_response)
            except Exception:  # noqa: BLE001
                pass
            await asyncio.sleep(0.5)

            state["name"] = name
            steptxt = " + ".join(f"0x{c:02x}({d.hex() or '-'})" for c, d in steps)
            print(f"[{name}]  sending {steptxt} ... listening {dwell:.0f}s")
            try:
                for cmd, data in steps:
                    await _write(client, cmd, data, with_response)
                    await asyncio.sleep(0.4)
            except Exception as exc:  # noqa: BLE001
                print(f"   write failed: {exc}")
            await _listen(client, dwell)

            per = counts[name]
            if per:
                summary = ", ".join(f"{wp.cname(u)}={n}" for u, n in per.most_common())
                stream = any(n >= 4 for u, n in per.items() if u != wp.RESP_CHAR_UUID)
                print(f"   -> {summary}" + ("   <<< CONTINUOUS STREAM?" if stream else ""))
            else:
                print("   -> (silence)")

        state["name"] = None
        try:
            await _write(client, wp.CMD_RT_HR_OFF, b"", with_response)
        except Exception:  # noqa: BLE001
            pass
        for uuid in wp.NOTIFY_CHARS + [wp.HR_CHAR_UUID]:
            try:
                await client.stop_notify(uuid)
            except Exception:  # noqa: BLE001
                pass
        log_file.close()

    print(f"\n=== Done -> {log_path} ===")
    winners = [n for n, c in counts.items()
               if any(v >= 4 for u, v in c.items() if u != wp.RESP_CHAR_UUID)]
    if winners:
        print("Strategies that produced a possible continuous stream:")
        for n in winners:
            print(f"   {n}: " + ", ".join(f"{wp.cname(u)}={v}" for u, v in counts[n].most_common()))
    else:
        print("No strategy produced a continuous stream. Interesting replies:")
        for n, c in counts.items():
            if c:
                print(f"   {n}: " + ", ".join(f"{wp.cname(u)}={v}" for u, v in c.most_common()))
    print("\nSend Claude this log — the per-strategy reply bytes tell us the next move.")


def main() -> None:
    p = argparse.ArgumentParser(description="Try multiple start-streaming strategies (ProjWT).")
    p.add_argument("address", help="BLE address from ble_scanner_PWT.py")
    p.add_argument("--dwell", type=float, default=6.0, help="listen seconds per strategy (default 6)")
    p.add_argument("--no-response", action="store_true",
                   help="use write-without-response (default is with-response)")
    args = p.parse_args()
    try:
        asyncio.run(run(args.address, args.dwell, not args.no_response))
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()

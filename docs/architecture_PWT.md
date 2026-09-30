# Architecture — ProjWT

## Data flow (target)

```
WHOOP 4.0 ──BLE notify──> Host (Phase 1: Python; Phase 4: C++ worker thread)
                              │
                 ┌────────────┼─────────────┐
                 ▼            ▼              ▼
          Gesture engine   Dashboard    Integrations
          (DTW, held-      (live        (Tesla Fleet API,
           state detect)    telemetry)   MQTT/ESP32 garage)
```

## Phase 1 components (this scaffold)
- `src/ble_scanner_PWT.py` — discover devices, print address + RSSI.
- `src/gatt_explorer_PWT.py` — enumerate services/characteristics/descriptors.
- `src/ble_logger_PWT.py` — subscribe to notify chars, log raw hex to JSONL.

## Decoding method (Phase 2)
Capture labelled sessions (`rest`, `wave`, `walk`) and diff:
- 3-axis accelerometer → high-rate, values swing with motion, quiet at rest.
- Heart rate → low-rate, small integer(s), steady.
- Skin temp → very low-rate, slowly drifting.
Cross-reference UUIDs against public community mappings, then write parsers.

## Safety model (vehicle control, Phase 4)
Keep-alive + watchdog. The car only moves while a valid gesture packet arrives
within the timeout window; absence of packets = immediate stop. Supervised,
line-of-sight only. No location spoofing.

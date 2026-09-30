# ProjWT

A personal-interoperability project for a **WHOOP 4.0** band I own: read its
sensors over Bluetooth Low Energy (BLE), turn wrist motion into gesture input,
and drive my own software and devices with it — a live biometric dashboard,
gesture-triggered Tesla actions via the official Fleet API, and a garage/home
IoT bridge.

> Personal project. The band is mine; this reads its own broadcast for
> interoperability and learning. Nothing here bypasses a subscription paywall,
> and — see **Safety** — nothing defeats a vehicle safety mechanism.

## Roadmap

| Phase | Goal | Stack |
|------|------|-------|
| **1. Observe** *(this scaffold)* | Confirm BLE access; map the GATT table; log raw sensor packets and diff motion vs. rest | Python + `bleak` |
| 2. Decode | Identify which characteristics carry accelerometer / HR / skin-temp; parse packets | Python |
| 3. Gestures | Dynamic Time Warping on the accelerometer stream; recognise held-state gestures | Python → C++ |
| 4. App | Real-time dashboard + integrations (Tesla Fleet API, MQTT/ESP32 garage) | C++ / engine |

## Phase 1 — quick start

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements_PWT.txt

# 1) find the band and copy its address
python src/ble_scanner_PWT.py --name whoop

# 2) map its services / characteristics (look for 'notify')
python src/gatt_explorer_PWT.py <ADDRESS> --read

# 3) capture sensor streams, labelled, so you can diff them
python src/ble_logger_PWT.py <ADDRESS> --label rest     # sit still
python src/ble_logger_PWT.py <ADDRESS> --label wave     # wave your wrist
```

Captures land in `logs/` as timestamped JSONL and are **git-ignored** — they
contain your biometrics, so they stay local.

### Known BLE realities
- The band typically holds **one active GATT connection** at a time, so the
  official app and this tool may compete. Close the official app while capturing.
- Pairing/encryption may be required; `gatt_explorer_PWT.py` will surface errors
  if a characteristic can't be read without bonding.

## Safety (Tesla integration, later phases)

Vehicle control is **supervised only**:
- Gesture is an **active hold** while I watch the car; releasing the gesture
  (or losing the BLE keep-alive) makes the car slow and stop — a dead-man's switch.
- A watchdog timer aborts motion if keep-alive packets stop arriving.
- **No** GPS/location spoofing and **no** no-line-of-sight operation. The stock
  proximity/line-of-sight safeguards stay in place.

## File naming
Every source/doc file carries a `_PWT` suffix by project convention.

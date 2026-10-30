# ProjWT Apps — Full Ecosystem

Control your Tesla via wearable gestures. Ship across iOS, Web, and Windows.

## Architecture

```
ProjWT Backend (FastAPI)
    ├─ /command        → Send vehicle commands
    ├─ /gesture/*      → ARM/PANIC/etc
    └─ /ws/biometrics  → Live heart rate stream (WebSocket)
         ↓
    ├─ iOS App (Flutter)
    ├─ Web App (React)
    └─ Windows App (Electron)
```

## Quick Start

### 1. Backend Setup (Python)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Backend runs on `http://localhost:8000`
- Health check: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

### 2. iOS App Setup (Flutter)

On your Mac:

```bash
cd ios

# Install Flutter if needed: https://flutter.dev/docs/get-started/install
flutter pub get
flutter run -d ios
```

**Requirements:**
- Flutter 3.0+
- Xcode 14+
- iOS 14.0+

**What it does:**
- Dashboard with vehicle commands (lock, unlock, flash, honk, climate, etc.)
- Live biometric streaming (heart rate from backend)
- ARM/PANIC buttons for safety FSM
- WHOOP band connection (via BLE)

### 3. Web App Setup (React) — Coming soon

```bash
cd web
npm install
npm start
```

### 4. Windows Desktop (Electron) — Coming soon

```bash
cd windows
npm install
npm run dev
```

---

## API Reference

### Health Check
```bash
GET /health
```
Response:
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T...",
  "controller_ready": true
}
```

### List Commands
```bash
GET /commands
```
Response:
```json
{
  "commands": ["unlock", "lock", "flash", ...],
  "menu": ["unlock", "lock", "flash", "honk", ...]
}
```

### Send Command
```bash
POST /command
Content-Type: application/json

{"command": "unlock"}
```
Response:
```json
{
  "ok": true,
  "command": "unlock",
  "timestamp": "2024-01-15T...",
  "state": "ARMED"
}
```

### ARM Gesture
```bash
POST /gesture/arm
```

### PANIC Gesture
```bash
POST /gesture/panic
```

### Biometrics Stream (WebSocket)
```
WS ws://localhost:8000/ws/biometrics
```
Data (received every ~1 second):
```json
{
  "heart_rate": 78,
  "battery": 85,
  "timestamp": "2024-01-15T..."
}
```

---

## Project Structure

```
projwt-apps/
├── backend/
│   ├── app.py                   # FastAPI server
│   ├── requirements.txt         # Python dependencies
│   └── .env.example             # Configuration template
│
├── ios/
│   ├── pubspec.yaml             # Flutter dependencies
│   ├── lib/
│   │   ├── main.dart            # App entry point
│   │   ├── providers/           # State management
│   │   ├── screens/             # UI screens
│   │   └── services/            # API client
│   └── ios/                     # Native iOS files
│
├── web/                         # React app (TODO)
├── windows/                     # Electron app (TODO)
└── README.md                    # This file
```

---

## Development

### Add a new vehicle command

1. **Backend** (backend/app.py):
   - Add to `gesture_control_PWT.py`'s `BAND_MENU`

2. **iOS** (ios/lib/screens/dashboard_screen.dart):
   - Icon mapping in `_getCommandIcon()`
   - Color mapping in `_getCommandColor()`

3. **Done** — the UI auto-populates

### Connect a real WHOOP band

1. Get the band's Bluetooth address
2. Run: `python app.py <ADDRESS> --backend mock`
3. iOS app connects to the same backend

### Integrate Tesla Fleet API

1. Set env vars:
   ```bash
   export TESLA_ACCESS_TOKEN=...
   export TESLA_REFRESH_TOKEN=...
   ```

2. Start backend:
   ```bash
   PROJWT_BACKEND=tesla python app.py
   ```

3. iOS app now controls your real car

---

## Troubleshooting

### Backend won't start
```bash
# Check Python version (3.8+)
python --version

# Check dependencies
pip install -r requirements.txt -v

# Check port 8000 is free
lsof -i :8000
```

### iOS app can't connect to backend
- Ensure backend is running: `curl http://localhost:8000/health`
- On simulator: use `http://localhost:8000` (works)
- On physical device: use `http://YOUR_MAC_IP:8000`
  - Find your IP: `ifconfig | grep "inet "`

### WebSocket connection fails
- Check backend logs for `/ws/biometrics` errors
- Verify firewall allows port 8000
- Try restarting backend

---

## Next Steps (Portfolio Roadmap)

- [x] Backend API (FastAPI)
- [x] iOS app (Flutter)
- [ ] Web dashboard (React)
- [ ] Windows desktop (Electron)
- [ ] Native BLE integration (iOS)
- [ ] App Store submission
- [ ] CI/CD pipeline

**Estimated time to "all three platforms":** 2 weeks
**Portfolio value:** Very high (shipping 3 platforms = serious engineer)

---

## Credits

**ProjWT** — Hamza Khan
- Reverse-engineered WHOOP 4.0 Bluetooth protocol
- Integrated Tesla Fleet API with cryptographic signing
- Designed fail-closed safety FSM
- Built real-time biometric pipeline

See `../projwt/` for the original codebase.

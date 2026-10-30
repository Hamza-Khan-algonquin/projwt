# ProjWT iOS App

Flutter iOS app for controlling Tesla vehicles via wearable gesture recognition and live biometric dashboard.

## Setup

### Prerequisites
- Mac with Xcode 14+
- Flutter 3.0+ ([install here](https://flutter.dev/docs/get-started/install))
- iOS 14.0+

### Installation

```bash
# 1. Get dependencies
flutter pub get

# 2. Make sure backend is running (from ../backend)
cd ../backend
python app.py  # should see "Starting backend server..."

# 3. Run on simulator
flutter run -d ios

# 4. Or run on physical device
flutter run -d iphone
```

## Features

### Dashboard Tab
- **Vehicle Status** — Shows current FSM state (IDLE/ARMED/HOLDING)
- **Quick Actions** — ARM and PANIC buttons
- **Command Grid** — All vehicle commands as buttons:
  - Unlock/Lock
  - Flash lights
  - Honk horn
  - Open frunk/trunk
  - Climate control (warm/cool)
  - Charge port control
  - And more...

### Biometrics Tab
- **Heart Rate** — Live from WHOOP band (~1 Hz)
- **Status Indicator** — Normal/Low/High/Elevated
- **Battery Level** — WHOOP band battery percentage
- **Stream Info** — Connection status and update frequency

## Architecture

```
main.dart
  ├─ MainNavigation (tab navigation)
  ├─ DashboardScreen
  │   ├─ StatusCard
  │   ├─ QuickActions (ARM/PANIC)
  │   └─ CommandGrid
  └─ BiometricsScreen
      ├─ HeartRateCard
      ├─ BatteryCard
      └─ StreamInfo

ProjWTProvider (State Management)
  ├─ currentState (IDLE/ARMED/HOLDING)
  ├─ commands (list of available commands)
  ├─ heartRate (live BPM)
  ├─ battery (band battery %)
  └─ lastCommandResult

ProjWTAPIClient (HTTP + WebSocket)
  ├─ sendCommand(command)
  ├─ armGesture()
  ├─ panicGesture()
  └─ streamBiometrics() [WebSocket]
```

## API Integration

The app connects to the FastAPI backend at `http://localhost:8000`.

### Key Endpoints Used

- `GET /health` — Verify connection
- `GET /state` — Current FSM state
- `GET /commands` — List available commands
- `POST /command` — Send command
- `POST /gesture/arm` — ARM gesture
- `POST /gesture/panic` — PANIC gesture
- `WS /ws/biometrics` — Live biometric stream

See `../backend/README.md` for full API docs.

## Configuration

Edit `lib/services/api_client.dart`:
```dart
const baseUrl = 'http://YOUR_IP:8000'  // Change if backend on different machine
```

Or on physical device:
- Find your Mac IP: `ifconfig | grep "inet "`
- Update `api_client.dart` with that IP

## Building for iOS

### Debug Build
```bash
flutter build ios --debug
```

### Release Build
```bash
flutter build ios --release
```

### For App Store
```bash
# Build for production
flutter build ipa --release

# Upload to TestFlight (requires Apple Developer account)
# Use Xcode: open ios/Runner.xcworkspace
# → Product → Archive → Distribute App
```

## Testing

### Unit Tests
```bash
flutter test
```

### Integration Tests
```bash
flutter test integration_test
```

### Manual Testing Checklist
- [ ] Backend runs and `/health` returns OK
- [ ] Dashboard loads and shows vehicle status
- [ ] ARM button changes state to ARMED
- [ ] PANIC button disarms immediately
- [ ] Each command button sends request
- [ ] Biometrics tab shows live heart rate
- [ ] Battery percentage updates
- [ ] No crashes on repeated commands

## Troubleshooting

### "Connection refused"
- Ensure backend is running on port 8000
- Check firewall allows port 8000
- On physical device, use your Mac's IP address

### "WebSocket connection failed"
- Restart the backend
- Verify `ws://localhost:8000/ws/biometrics` is reachable
- Check Flutter logs: `flutter logs`

### "Biometrics not updating"
- Ensure backend has biometric source connected (WHOOP band or mock)
- Check WebSocket is open in Flutter DevTools
- Restart app

### "Cannot find flutter"
```bash
# Make sure Flutter is in PATH
export PATH="$PATH:~/flutter/bin"
flutter doctor
```

## Performance Tips

- **Hot Reload** — `r` to reload without restarting
- **Hot Restart** — `R` to do full restart
- **DevTools** — `d` opens debugger
- **Profiler** — Check performance in DevTools

## Dependencies

See `pubspec.yaml` for the full list. Key ones:
- `http` — HTTP requests
- `web_socket_channel` — WebSocket for biometrics
- `provider` — State management
- `flutter_blue_plus` — BLE for WHOOP band
- `google_fonts` — Typography

## Next Steps

1. **BLE Integration** — Connect directly to WHOOP band (native iOS plugin)
2. **Notifications** — Push notifications for vehicle events
3. **Offline Mode** — Queue commands when offline
4. **Gesture Overlay** — Tap/hold UI in corner for always-on control
5. **App Store** — Submit to TestFlight → App Store

## Files Reference

```
lib/
├── main.dart                      # App entry + navigation
├── providers/
│   └── projwt_provider.dart      # State management
├── screens/
│   ├── dashboard_screen.dart     # Vehicle control UI
│   └── biometrics_screen.dart    # Heart rate + battery
└── services/
    └── api_client.dart           # Backend API client
```

## Author

Hamza Khan — Built as portfolio project demonstrating:
- Cross-platform mobile development (Flutter)
- Real-time WebSocket communication
- State management with Provider
- iOS native integration
- API-first architecture

---

**Questions?** Check `../README.md` for full project docs.

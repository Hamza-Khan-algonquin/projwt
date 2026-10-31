# ProjWT iOS Simulator Setup & Run Guide

## Prerequisites

### Required Software
- **macOS** (10.15 or later)
- **Xcode** (14.0 or later) - Download from App Store or developer.apple.com
- **Flutter SDK** (3.13.0 or later) - Download from flutter.dev
- **Dart SDK** (included with Flutter)

### Installation Steps

#### 1. Install Xcode Command Line Tools
```bash
xcode-select --install
```

#### 2. Install Flutter
```bash
# Download Flutter
git clone https://github.com/flutter/flutter.git -b stable
export PATH="$PATH:$(pwd)/flutter/bin"

# Verify installation
flutter doctor
```

#### 3. Set Up iOS Development
```bash
# Install CocoaPods (dependency manager for iOS)
sudo gem install cocoapods

# Accept Xcode licenses
sudo xcode-select --switch /Applications/Xcode.app/xcode-select
sudo xcodebuild -runFirstLaunch
sudo xcode-license accept
```

---

## Running the App in iOS Simulator

### Step 1: Clone the Repository
```bash
git clone https://github.com/Hamza-Khan-algonquin/projwt.git
cd projwt
git checkout peaceful-dirac-ko6o1i
```

### Step 2: Get Flutter Dependencies
```bash
flutter pub get
```

### Step 3: Start iOS Simulator
```bash
# List available simulators
xcrun simctl list devices

# Start a specific simulator (e.g., iPhone 15)
open -a Simulator

# OR start directly
xcrun simctl boot "iPhone 15"
```

### Step 4: Run the App
```bash
# Run on default simulator
flutter run -d iPhone

# Run with specific device
flutter run -d "iPhone 15"

# Run with verbose output
flutter run -v

# Run in release mode (faster performance)
flutter run --release
```

---

## Common Simulator Commands

### Device Management
```bash
# List all simulators
xcrun simctl list devices

# Create new simulator
xcrun simctl create "iPhone 15 Pro" com.apple.CoreSimulator.SimDeviceType.iPhone-15-Pro

# Boot simulator
xcrun simctl boot "iPhone 15 Pro"

# Shut down simulator
xcrun simctl shutdown "iPhone 15 Pro"

# Erase simulator
xcrun simctl erase "iPhone 15 Pro"
```

### App Control
```bash
# Install app manually
xcrun simctl install booted build/ios/iphonesimulator/Runner.app

# Uninstall app
xcrun simctl uninstall booted com.example.projwt

# Clear app data
xcrun simctl erase "iPhone 15 Pro"
```

---

## Testing the App in Simulator

### Features to Test

#### 1. **Dashboard** (Vehicle Control)
- ✅ Unlock/Lock buttons functional
- ✅ Honk command executes
- ✅ Flash lights work
- ✅ Climate control responds (mock)
- ✅ Charge command active

#### 2. **Fitness Screen** (WHOOP Biometrics)
- ✅ Mock biometric data displays
- ✅ Heart rate trend chart updates
- ✅ Recovery score shows correctly
- ✅ Battery indicator accurate

#### 3. **Gestures Screen**
- ✅ Tap detection records sequences
- ✅ Gesture vocabulary displays
- ✅ Gesture history logs entries

#### 4. **Security Settings**
- ✅ Toggle WHOOP control on/off
- ✅ Set authentication mode (tap, PIN, both)
- ✅ Create guest PINs
- ✅ Revoke guest access

#### 5. **Wear Detection**
- ✅ Band on/off detection works
- ✅ Session persists while wearing
- ✅ Thermal regulation activates

---

## Troubleshooting

### "Flutter not found"
```bash
# Add Flutter to PATH
export PATH="$PATH:$HOME/path/to/flutter/bin"

# Verify
flutter --version
```

### "Simulator won't boot"
```bash
# Kill all simulators
killall com.apple.CoreSimulator.CoreSimulatorService

# Restart simulator
open -a Simulator
```

### "Pod install fails"
```bash
cd ios
rm -rf Pods
rm Podfile.lock
pod install
cd ..
flutter pub get
```

### "Build fails with architecture errors"
```bash
# Clean build
flutter clean
flutter pub get

# Run with verbose
flutter run -v
```

### "App crashes on startup"
```bash
# Check logs
flutter logs

# Rebuild from scratch
flutter clean
flutter pub get
flutter run
```

---

## Hot Reload & Hot Restart

During development, use these shortcuts to speed up testing:

```bash
# While `flutter run` is active:
# Press 'r' for hot reload (quick, preserves state)
# Press 'R' for hot restart (full app restart)
# Press 'q' to quit
```

### When to Use Each
- **Hot Reload**: Changed UI, logic, or styling → instant update
- **Hot Restart**: Changed app initialization, authentication, or state management → full restart needed
- **Full Rebuild**: Changed native code, dependencies, or platform channels → `flutter clean && flutter run`

---

## Performance Tips

### Reduce Simulator Lag
```bash
# Run in release mode (faster)
flutter run --release

# Close other apps
killall -m "Xcode|Safari|Chrome"

# Reduce simulator graphics
# Simulator → Device → Manage Device Types → Edit → Graphics: "Basic"
```

### Memory Management
- Don't run multiple simulators at once
- Close unused apps in simulator
- Use `xcrun simctl erase` to clear old data

---

## Testing Locally Without Real API Credentials

The app is configured with **mock Tesla API responses** by default. No real credentials needed for testing in simulator.

### To Test With Mock Data:
```bash
# All commands already configured for mock responses
# Edit `tesla_service.dart` if you need to change API endpoints
```

### To Use Real Tesla API (Optional):
1. Get Tesla Fleet API credentials
2. Edit `lib/services/tesla_service_real.dart`
3. Add your credentials to `app_constants.dart`
4. Enable real API in `main_real_execution.dart`

---

## Next Steps

1. ✅ Run `flutter run -d iPhone` to launch the app
2. ✅ Test each screen and feature (see "Testing the App" section)
3. ✅ Press 'r' for hot reload when making changes
4. ✅ Check console logs: `flutter logs`
5. ✅ When satisfied, build for distribution: `flutter build ios`

---

## Build for TestFlight / App Store

```bash
# Build production iOS app
flutter build ios --release

# Output: build/ios/iphoneos/Runner.app

# For TestFlight, follow: cloud_deployment_guide.md
```

---

**Happy testing! 🚀**

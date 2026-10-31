# SKEETER Cloud Deployment Guide

This guide covers building, signing, and deploying SKEETER to production platforms (Steam, Itch.io, GitHub Releases, and future relay infrastructure).

## Table of Contents
1. [Build Process](#build-process)
2. [Code Signing](#code-signing)
3. [Distribution Setup](#distribution-setup)
4. [Infrastructure (Future)](#infrastructure-future)
5. [Release Workflow](#release-workflow)
6. [Troubleshooting](#troubleshooting)

---

## Build Process

### Prerequisites
- **Unity 2022.3 LTS** (or later)
- **.NET 7.0+** (for rule tests)
- **Git** (for version control)
- **Code signing certificates** (Windows, macOS)

### Step 1: Run Quality Assurance

Before building, ensure all game rules are validated:

```bash
cd Tools/RuleTests
dotnet run
```

Expected output: `All tests passed (2600+ assertions)`

If any tests fail, investigate and fix before proceeding with builds.

### Step 2: Build for All Platforms

#### Windows Build

```bash
# Open in Unity Editor (2022.3 LTS+)
# File → Build Settings
# - Select "PC, Mac & Linux Standalone"
# - Target Platform: Windows
# - Architecture: x86_64
# - Quality: High
# - Build folder: Builds/Windows

# Command-line build (optional)
/path/to/Unity -batchmode -nographics \
  -buildWindowsPlayer Builds/Windows/SKEETER.exe \
  -quit
```

**Output**: `Builds/Windows/SKEETER.exe` (~180-200MB)

#### macOS Build

```bash
# Unity Editor → Build Settings
# - Target Platform: Mac OS X
# - Architecture: Intel 64-bit + Apple Silicon (Universal)
# - Quality: High
# - Build folder: Builds/MacOS

/path/to/Unity -batchmode -nographics \
  -buildOSXUniversalPlayer Builds/MacOS/SKEETER.app \
  -quit
```

**Output**: `Builds/MacOS/SKEETER.app` (~220-250MB)

#### Linux Build

```bash
/path/to/Unity -batchmode -nographics \
  -buildLinux64Player Builds/Linux/SKEETER \
  -quit
```

**Output**: `Builds/Linux/SKEETER` (~180-200MB)

### Step 3: Verify Build Integrity

```bash
# Windows
certutil -hashfile Builds/Windows/SKEETER.exe SHA256

# macOS
shasum -a 256 Builds/MacOS/SKEETER.app

# Linux
sha256sum Builds/Linux/SKEETER
```

Document these hashes for release notes.

---

## Code Signing

Signing is **required** for distribution on Windows and macOS.

### Windows Code Signing

**Obtain Certificate**:
1. Purchase a code signing certificate from a CA (Sectigo, DigiCert, etc.)
2. Save the `.pfx` file securely

**Sign the Executable**:

```bash
signtool sign /f certificate.pfx /p password /t http://timestamp.server \
  Builds/Windows/SKEETER.exe
```

**Verify Signature**:

```bash
signtool verify /pa Builds/Windows/SKEETER.exe
```

### macOS Code Signing

**Obtain Certificate**:
1. Register as Apple Developer
2. Download "Developer ID Application" certificate from Apple Developer Portal
3. Import into Keychain

**Sign the App Bundle**:

```bash
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name (XXXX)" \
  Builds/MacOS/SKEETER.app
```

**Notarize for Gatekeeper** (required for distribution):

```bash
# Create notarization package
ditto -c -k --sequesterRsrc Builds/MacOS/SKEETER.app SKEETER.zip

# Submit for notarization
xcrun notarytool submit SKEETER.zip \
  --apple-id your-email@example.com \
  --password app-specific-password \
  --team-id XXXX

# Wait for approval (typically 5-10 minutes)

# Staple the notarization ticket
xcrun stapler staple Builds/MacOS/SKEETER.app
```

---

## Distribution Setup

### Steam (Primary)

1. **Create Steamworks Account** at https://partner.steamgames.com
2. **Register Application** (costs $100 one-time per game)
3. **Set Metadata**:
   - Title: "SKEETER"
   - Description: [From README.md]
   - Screenshots: [Gameplay captures]
   - Store page assets
4. **Upload Build**:
   ```bash
   /path/to/steamcmd.exe +login email password \
     +run_app_build /path/to/app_build_config.vdf \
     +quit
   ```

### Itch.io (Secondary)

1. **Create Account** at https://itch.io
2. **Create Game Page**:
   - Title: "SKEETER"
   - Description: [From README.md]
   - Kind: Game
   - Classification: Multiplayer, Indie, Party
3. **Upload Builds**:
   ```bash
   itch push Builds/Windows/SKEETER.exe \
     --user yourusername --game skeeter
   
   itch push Builds/MacOS/SKEETER.app \
     --user yourusername --game skeeter
   
   itch push Builds/Linux/SKEETER \
     --user yourusername --game skeeter
   ```

### GitHub Releases

1. **Create Release**:
   ```bash
   git tag -a v1.0.0 -m "SKEETER 1.0.0 - Initial Release"
   git push origin v1.0.0
   ```

2. **Upload via GitHub CLI**:
   ```bash
   gh release create v1.0.0 \
     Builds/Windows/SKEETER.exe \
     Builds/MacOS/SKEETER.app \
     Builds/Linux/SKEETER \
     --title "SKEETER v1.0.0" \
     --notes "See README.md for features and setup"
   ```

---

## Infrastructure (Future)

### Relay Server (NAT Traversal)

For WAN play without port forwarding, implement a simple relay:

```rust
// Pseudo-code structure (~200 LOC)
use tokio::net::UdpSocket;

struct RelayServer {
    sessions: HashMap<String, Session>,
}

struct Session {
    host_addr: SocketAddr,
    clients: Vec<SocketAddr>,
}

// Relay messages between host and clients
// Clients connect out to relay (no port forwarding needed)
```

**Deployment**:
- 1 small VPS ($5/month, ~1 vCPU, 512MB RAM)
- Simple Docker container
- DNS: `relay.skeeter.game`

### Leaderboard Backend (Optional)

```sql
CREATE TABLE leaderboards (
  id SERIAL PRIMARY KEY,
  player_name VARCHAR(255),
  highest_score INT,
  highest_haul INT,
  bank_streak INT,
  timestamp TIMESTAMP
);
```

**API Endpoints**:
- `GET /api/leaderboards/top100` - Top scores
- `POST /api/leaderboards/submit` - Submit score
- `GET /api/leaderboards/personal/:name` - Personal bests

---

## Release Workflow

### Pre-Release Checklist

- [ ] All tests pass (`Tools/RuleTests`)
- [ ] Windows build compiles without errors
- [ ] macOS build compiles and notarizes successfully
- [ ] Linux build compiles
- [ ] Multiplayer tested (2+ players, LAN)
- [ ] Voice chat tested (proximity detection works)
- [ ] All accessibility settings functional
- [ ] Performance test on minimum spec machine
- [ ] Release notes written (features, bug fixes, known issues)
- [ ] Version number incremented (tag: `v1.0.0`)

### Release Steps

1. **Commit final changes**:
   ```bash
   git add -A
   git commit -m "Release: v1.0.0 - Initial launch"
   git tag -a v1.0.0 -m "SKEETER v1.0.0"
   git push origin main --follow-tags
   ```

2. **Build all platforms** (can be parallelized):
   ```bash
   # Build Windows
   # Build macOS
   # Build Linux
   # Verify hashes
   ```

3. **Sign binaries**:
   ```bash
   signtool sign ... Builds/Windows/SKEETER.exe
   codesign ... Builds/MacOS/SKEETER.app
   xcrun notarytool submit ...
   ```

4. **Deploy to distribution platforms**:
   - Steam: Upload to Steamworks
   - Itch.io: Push with `itch` CLI
   - GitHub: Create release with artifacts

5. **Announce Release**:
   - Tweet / social media
   - Discord announcement
   - Email community (if newsletter set up)

---

## Monitoring & Updates

### Crash Reporting

Players can optionally share crash logs:
- Location: `%USERPROFILE%\AppData\LocalLow\DefaultCompany\SKEETER\output_log.txt` (Windows)
- Location: `~/Library/Logs/Unity/` (macOS)
- Location: `~/.config/unity3d/DefaultCompany/SKEETER/` (Linux)

### Performance Metrics

In-game telemetry (optional):
- Frame time (target 60 FPS)
- Network ping
- Voice latency
- Crashes (logged locally, shareable)

### Bug Fix Updates

1. Fix issue in source
2. Test with `Tools/RuleTests`
3. Rebuild affected platforms
4. Increment version (`v1.0.1`)
5. Deploy to all platforms
6. Release notes with changes

---

## Troubleshooting

### Build Fails on Windows

**Error**: "Could not find Microsoft Visual C++ Runtime"
- **Solution**: Install Visual C++ Redistributable on build machine
- Download from: https://support.microsoft.com/en-us/help/2977003

**Error**: "UnityException: CreateExternalTexture with size 0x0"
- **Solution**: This usually means a material shader failed to compile
- Check `Assets/Scripts/Rendering/MaterialLibrary.cs`
- Rebuild Graphics Settings in Project Settings

### Code Signing Issues

**Error**: "PFX file password incorrect"
- Re-verify the certificate password
- Try importing the certificate manually into Windows Certificate Manager

**Error**: "Notarization failed"
- Common cause: Binary was modified after signing
- Re-sign and notarize in one continuous process
- Apple notarization can take 5-15 minutes - wait longer before checking status

### Network / Multiplayer Issues

**Issue**: "Cannot connect to host on WAN"
- Host must forward UDP 7788
- Check firewall settings: `netstat -an | grep 7788` (Windows) or `lsof -i :7788` (macOS/Linux)
- Test with https://www.yougetsignal.com/tools/open-ports/ (host IP, port 7788)

**Issue**: "Voice chat not working"
- Check Settings → Audio Devices
- Verify microphone permissions (Windows/macOS/Linux may require explicit permission)
- Test microphone in Settings input meter

### Performance Issues

**Issue**: "Game stuttering, frame drops"
- Check Settings → Camera Shake intensity (reduce if high)
- Disable "Reduce motion" accessibility option temporarily
- Check if system is running other heavy tasks (Discord streaming, recording, etc.)
- Target 60 FPS on minimum spec: i5 + GTX 960 + 4GB RAM

---

## Support

- **Discord**: [Link TBA]
- **Email**: support@skeeter.game
- **GitHub Issues**: For bug reports and feature requests

---

## Version History

- **v1.0.0** (Oct 2026) - Initial Release
  - Full multiplayer support (LAN + port forward for WAN)
  - Proximity voice chat
  - Bot AI with difficulty ladder
  - Accessibility settings (motion reduction, color blindness, interface scaling)
  - Vertical capture mode for content creators
  - Personal best tracking and replay system

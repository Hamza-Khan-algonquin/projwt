# SKEETER - Getting Started Guide

Welcome! SKEETER is a fast, asymmetric multiplayer game where you play as a mosquito or a human trying to stop one.

## Quick Start (2 minutes)

1. **Download** your platform below
2. **Extract** the zip file
3. **Run** the executable
4. **Press Play** and you'll join a round

That's it! You'll land in a game already in progress so you can see what you're doing before choosing a role.

---

## Download

### Windows
- **[SKEETER v1.0.0 - Windows 64-bit](https://releases.skeeter.game/SKEETER-1.0.0-Windows.zip)** (195 MB)
- Requires: Windows 7+, 4GB RAM, Intel i5 or equivalent
- Extract and run `SKEETER.exe`

### macOS
- **[SKEETER v1.0.0 - macOS (Intel + Apple Silicon)](https://releases.skeeter.game/SKEETER-1.0.0-MacOS.zip)** (225 MB)
- Requires: macOS 10.13+, 4GB RAM
- Extract and run `SKEETER.app`
- First launch may take a moment (Gatekeeper verification)

### Linux
- **[SKEETER v1.0.0 - Linux 64-bit](https://releases.skeeter.game/SKEETER-1.0.0-Linux.zip)** (190 MB)
- Requires: 4GB RAM, modern CPU
- Extract and run `./SKEETER`

### Or Get It On
- **Itch.io**: https://skeeter-game.itch.io/skeeter
- **Steam** (Coming soon)
- **GitHub**: https://github.com/your-username/skeeter/releases

---

## What Is SKEETER?

You are a mosquito in a living room. Land on humans, drink their blood, and escape through the open window before you get swatted. The catch: blood is heavy. More you carry, slower you fly.

Every round, someone plays the mosquito, someone plays the house (controlling human bodies). Roles are assigned at random, so nobody knows which side they're on until it starts.

**90 seconds per round.** Instant restarts. Play online with friends or against bots. Proximity voice chat (they'll hear you if you talk).

---

## First Game: Solo Play

When you launch the game:

1. **You'll see the menu** with a game already playing behind it (bots playing bots)
2. **Press "Play"** to join as a random role
3. **You'll get a briefing** telling you which side you drew and how to play it
4. **Press "H" anytime** to see the briefing again

### As a Mosquito
- **WASD** to fly, **Mouse** to look
- **Space** to go up, **Ctrl** to go down
- **Shift** to dash (faster but uses energy)
- **Land on skin** and automatically start drinking
- **Fly to the glowing window** to bank your blood (once banked, you earn points)
- **Die anywhere before banking** = lose everything you're carrying

### As a Host
- **WASD** to move, **Mouse** to look
- **Click** to swat at the mosquito
- **Tab** or **1/2/3** to jump to another body (you're controlling all of them)
- **Stop the mosquito** before it makes it to the window

---

## Playing Online

**Local Network (LAN)**:
1. One person clicks **"Play Online"** in the menu
2. They read out their IP address shown on screen
3. Everyone else enters that address and clicks **"Join"**
4. Game starts when everyone is ready

**Internet (Requires Port Forwarding)**:
1. Host forwards **UDP 7788** on their router
2. Host shares their **public IP address** with others
3. Others enter the IP and click **"Join"**

The menu will tell you if port forwarding isn't set up yet.

---

## Settings

Press **Esc** anytime to open Settings. You can adjust:

- **Difficulty**: Easier bots, harder bots, or off
- **Camera shake**: Reduce motion sickness (turn down or off)
- **Color blindness**: Safe colors for red-green deficiency
- **Interface size**: Scale up or down
- **Volume**: Master, effects, voice separately
- **Microphone**: Pick which device to use, test your input

---

## Tips for New Players

### As a Mosquito
- **One more bite or run?** That's the whole game. Your belly gets heavier with each bite.
- **Full belly = slow**: You'll be crawling, and the dash is locked out completely.
- **Spot selection matters**: Ears are rich targets (pour fast). Legs are safe but slow.
- **The window is your goal**: Nothing counts until you bank it.
- **Last Call** (final 18 seconds): Everything you bank is worth 2x points. Houses get a speed boost. This is the climax.

### As a Host
- **Position matters**: You're slow but have three bodies to control.
- **Jump between bodies**: Costs a moment of blindness but lets you cover more ground.
- **Teamwork (if playing with others)**: Trap the mosquito between two of your bodies.
- **Listen**: Talking reveals position (the mosquito's too). Proximity voice is spatial - they'll hear you if they're close.

---

## Video Capture & Streaming

**F2**: Reframe to vertical (9:16) with HUD inside the crop. Perfect for TikTok / YouTube Shorts.

**F9**: Save a screenshot. Good moments get a recap card with your best score, closest call, longest streak.

The game logs "dramatic moments" to a file so you can find the good 30 seconds of a 2-hour session. Ask in Discord (#content-creators) if you want details.

---

## Accessibility

SKEETER is built to be accessible:

- **Reduce motion**: Disables slow-motion, camera punches, death freeze-frame
- **Red-green safe colors**: Moves critical indicators (blood, window) to cyan instead
- **Tap instead of hold**: Buzz and microphone can be tap actions instead of sustained
- **Interface scaling**: Make HUD text bigger
- **Danger cue**: Text warning when a swat is coming (helps if you can't hear the whoosh)

All in Settings. No penalty for using them - they're just options.

---

## Keyboard Reference

| Action | Key |
| --- | --- |
| **Fly** | WASD |
| **Look** | Mouse |
| **Up** | Space |
| **Down** | Ctrl / C |
| **Dash** | Shift |
| **Buzz** (hold) | Q |
| **Talk** (hold) | V |
| **Jump body** (hosts) | Tab, 1, 2, 3 |
| **Swat** (hosts) | Left click |
| **New round** | R |
| **Vertical capture** | F2 |
| **Change lobby size** | F3 |
| **Change bot difficulty** | F4 |
| **Screenshot** | F9 |
| **Briefing** | H |
| **Settings** | Esc |

---

## Troubleshooting

### "Game won't launch"
- Make sure your system meets the minimum specs (see Download section)
- Try running as Administrator (Windows) or allowing execution (macOS)
- Check your graphics drivers are up to date

### "Can't connect to my friend online"
- Make sure they're using their **public IP** (not local IP like 192.168.x.x)
- Check that they forwarded **UDP 7788** on their router
- Use https://www.yougetsignal.com/tools/open-ports/ to verify port 7788 is open

### "Microphone not working"
- Check Settings → Audio Devices
- Make sure your OS has given the game microphone permission
- Windows: Settings → Privacy → Microphone → Allow apps to access microphone
- macOS: System Preferences → Security & Privacy → Microphone
- Test the input meter in Settings

### "Game is stuttering / slow"
- Check if you have enough RAM free (target: 2GB free minimum)
- Try lowering camera shake in Settings
- Disable other heavy applications (Discord streaming, OBS, etc.)
- Update graphics drivers

### "I forgot my personal bests / they reset"
- Personal bests are stored locally on your computer
- Deleting the game folder erases them
- Back up `%USERPROFILE%\AppData\LocalLow\DefaultCompany\SKEETER\` before uninstalling

---

## Community & Support

- **Discord**: [skeeter.game/discord](https://discord.gg/skeeter)
- **GitHub Issues**: Report bugs: [skeeter-game/issues](https://github.com/your-username/skeeter/issues)
- **Email**: support@skeeter.game

---

## FAQ

**Q: Can I play offline with just bots?**
A: Yes! Create a round, set bot difficulty, and play against the AI. Perfect for practicing.

**Q: How many people can play?**
A: Up to 4 players per game. Empty seats are filled by bots at whatever difficulty you set.

**Q: Is there a ranked / competitive mode?**
A: Not yet. v1.0 is casual party play. Ranked may come later if community asks for it.

**Q: Can I make my own maps?**
A: Not in v1.0. The arena is procedurally built from code. Custom maps are on the roadmap.

**Q: Where are my screenshots / clips saved?**
A: Screenshots go to your desktop. Clips can be exported with the game's built-in capture.

**Q: Do you support crossplay (Windows / Mac / Linux together)?**
A: Yes! Anyone on any platform can play together online.

**Q: Is my data safe? Do you collect personal data?**
A: No server backend yet, so no data collection. Personal bests stay on your computer. Future versions (leaderboards, etc.) will have an optional privacy policy.

---

## System Requirements

### Minimum
- **CPU**: Intel i5 / AMD Ryzen 5
- **RAM**: 4GB
- **Disk**: 2GB free
- **Graphics**: NVIDIA GTX 960 / AMD R9 290
- **Internet**: For online play (LAN or WAN with port forwarding)

### Recommended
- **CPU**: Intel i7 / AMD Ryzen 7
- **RAM**: 8GB+
- **Disk**: SSD
- **Graphics**: NVIDIA RTX 2060 / AMD RX 5700
- **Internet**: 5+ Mbps for smooth online play

---

## What's New in v1.0.0

- Full multiplayer (LAN + WAN with port forwarding)
- Proximity voice chat with spatial audio
- Bot AI with tunable difficulty
- Accessibility: motion reduction, colorblind modes, interface scaling
- Vertical capture (F2) for content creators
- Personal best tracking and replay system
- Cross-platform (Windows, macOS, Linux)

---

## Want to Help?

Found a bug? Have a feature request? Jump on Discord or open an issue on GitHub. The community shapes what comes next.

**Enjoy the game!**

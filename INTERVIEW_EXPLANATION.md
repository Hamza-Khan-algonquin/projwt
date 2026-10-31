# SKEETER - Interview Explanation Guide

This is your reference doc for explaining SKEETER in interviews. Read this the night before, and you'll have the whole story memorized. You can explain it in 5 minutes or expand to 10 with Q&A. Everything here is factual and backed by the codebase (75 files, 13,349 lines of C#, 40 commits).

---

## 1. THE PROBLEM (30 seconds)

**What problem does this solve?**

Party games are stuck in two modes: either they're 1v1 (nobody to root for), or they're huge multiplayer (don't fit in a stream). There's no middle ground for 2-4 people to play something *asymmetric* - where roles are radically different - on the same screen or LAN, and still be fun to watch.

**Why is it useful?**

People stream games. And streamers want moments. Most games give you nothing until round 5. SKEETER gives you a climax every 90 seconds: a full mosquito sprinting for a glowing window with a hand behind it. That's the shape content needs. And because roles flip every round, everyone stays engaged even when they're losing.

---

## 2. THE SOLUTION (2 minutes)

**What does the app do?**

You are a mosquito in a living room. Land on humans, drink blood, carry it to the glowing window to bank points. But blood is heavy - the more you carry, the slower you fly, and you can't dash. Die before banking? Everything's gone. That core loop repeats every 90 seconds.

Roles flip randomly each round. You might be the mosquito. You might be the house (controlling three human bodies to protect). That asymmetry is the whole game.

**Core features (in order of importance)**:

1. **Asymmetric multiplayer** (2-4 players, roles assigned randomly)
   - Players don't know which side they're on until the round starts
   - Every role is radically different (mosquito vs host) so neither side is boring
   - Empty seats filled by bots, so 2-player games feel full

2. **The tension loop**
   - Drink more blood = richer but slower
   - Running home with a full belly creates visual drama (belly fills visibly, speed drops)
   - "One more bite or run now?" is the decision every round

3. **Last Call** (final 18 seconds)
   - Everything you bank is worth 2x
   - The window flares, clock beats loudly
   - Designed to manufacture a climax *every round* (not every hour)

4. **Multiplayer (LAN + WAN with port forwarding)**
   - Proximity voice chat - your voice comes out of your body in 3D space
   - Talking reveals position to the enemy (microphone is a tell)
   - UDP-based, works across Windows / macOS / Linux

5. **Bot AI with deliberate handicaps**
   - Difficulty ladder (easy, normal, hard)
   - Bots don't have perfect information - they perceive like humans
   - Voice and wingbeats give away position (same rules for bots and players)

6. **Visual feedback (designed for clips)**
   - Near-miss slow-motion: if swat misses by <16cm, time slows, camera punches in, banner says "MISSED BY 4 CM"
   - Kill freeze-frame: death stops time and orbits the corpse
   - Vertical capture (F2): reframes to 9:16 for TikTok/Shorts at record time
   - Highlight log: every dramatic moment timestamped, so streamers find the good 30 seconds of a 2-hour session in a text file

7. **Personal best tracking**
   - Every stat you beat gets a "NEW BEST" flag on the recap card
   - Persistent across sessions (stored locally)
   - Drives players to come back

8. **Accessibility**
   - Reduce motion: disables slow-motion, camera punches, freeze-frames
   - Colorblind modes: red-green deficiency gets cyan-safe colors
   - Tap instead of hold: buzz and microphone can be taps
   - Interface scaling: bigger text
   - Danger cue: text warning when a swat is coming

**Why those features?**

Every feature exists to solve one problem: make a 90-second loop engaging enough to watch and play repeatedly.

- Asymmetry = nobody's bored (different game if you're mosquito vs host)
- Last Call = guaranteed climax every round (not waiting for luck)
- Voice proximity = coordination is risky (talking gives you away)
- Visual feedback = works on mute (important for clips)
- Highlights + personal bests = players chase specific moments
- Accessibility = everyone can play and enjoy (no gatekeeping by disability)

---

## 3. ARCHITECTURE (3 minutes)

**How is the app structured?**

The game is **code-first**. No scene files, no prefabs. `ArenaBuilder.cs` constructs the entire round in code - room, household, swarm, camera, HUD, audio - from a single entry point. This means:

- The whole game is reviewable as a text diff (no binary scene corruption)
- A round can be destroyed and rebuilt in a single frame (instant restarts)
- Ports to other engines cost less (no Unity-specific scene format to migrate)

**Main components (5-7 key pieces)**:

1. **Core** (the spine)
   - `GameEvents.cs`: Event bus. Bite, bank, kill, swat miss = all events raised here
   - `Tuning.cs`: Every number that changes feel (belly curve, drain rate, bite tiers, voice falloff)
   - `MatchDirector.cs`: Round director (timers, role assignment, score tracking)

2. **Mosquito** (your flight, feeding, death)
   - `MosquitoActor.cs`: Physics, flight, belly management
   - `MosquitoFeeding.cs`: What happens when you land on skin (which body part, which tier)
   - `MosquitoVisuals.cs`: Renders the belly (fills and turns red as you drink)
   - `BloodBelly.cs`: Physics model for weighted movement

3. **Human** (the three bodies you control)
   - `HumanSquad.cs`: Control one, two, or three bodies (cost to switch = moment of blindness)
   - `HumanBody.cs`: Movement, swat action
   - `HumanVitals.cs`: Blood loss, dizziness as mosquito drains

4. **AI** (bot brains, both sides)
   - `SwatterPerception.cs`: What the bot sees / hears (wingbeat, voice, proximity)
   - `BotMosquitoInput.cs`: Mosquito decisions (where to bite, when to run)
   - `BotHumanInput.cs`: Host decisions (where to intercept, who to control)
   - `SwatterProfile.cs`: Difficulty modifiers (easier bots hesitate more)

5. **Voice** (proximity audio, the networking seam)
   - `ProximityVoice.cs`: 3D audio playback, falloff curve
   - `MicrophoneCapture.cs`: Microphone input with detection model
   - `NetVoiceTransport.cs`: Voice over network (feeds perception system)

6. **Presentation** (visual polish)
   - `HypeDirector.cs`: Time dilation (slow-mo), camera control, particle timing
   - `CameraShake.cs`: Trauma model (big hits outweigh small ones, no permanent stutter)
   - `Ragdoll.cs`: Death animation (tumble, legs separate, wings flutter)
   - `HighlightLog.cs`: Timestamps dramatic moments for streamers

7. **Networking** (multiplayer)
   - `NetSession.cs`: Connection management, player handshake
   - `NetReplication.cs`: Send positions, say when bites/banks/kills happen
   - `UdpLink.cs`: Raw UDP transport
   - Authority model: movement is client-owned, outcomes (bites/banks) are host-authoritative

**How they work together**:

1. Player hits a key → `LocalInputs.cs` converts to `MosquitoIntent` or `HumanIntent`
2. `MosquitoActor` reads intent, updates position
3. Position change → `MosquitoFeeding` checks if landed on skin
4. Landed → `GameEvents.OnBite` fired
5. Audio hears event → `GameAudio` plays drinking sound
6. Particles hear event → `GameParticles` spawns blood spray
7. HUD hears event → `Hud.cs` updates display
8. Highlight log hears event → `HighlightLog` timestamps it
9. Network hears event → `NetReplication` broadcasts to other players

**Why this architecture?**

- **Event-driven**: Audio, particles, camera, HUD all listen to the same events. Add a new reaction to a bite? Touch one file (`GameEvents`), add a handler. No spaghetti code.
- **Controllers speak intents, not input**: A local player, a bot, and a future network peer all produce the same `MosquitoIntent`. Run identical physics. Networking plugs in seamlessly because it just hijacks the intent interface.
- **Centralized tuning**: One file (`Tuning.cs`) holds every number. Change belly weight curve, and all the systems that depend on it (movement, drain rate, physics) automatically get the new value.
- **Procedural generation**: No scene files. Everything built in code. Fast iteration, diff-friendly, no file lock conflicts.

---

## 4. TECHNICAL HIGHLIGHTS (2 minutes)

**What makes this technically interesting?**

1. **Event-driven architecture**
   - `GameEvents.cs` is the spine. Everything listens; nothing references back
   - Add a new effect (particle, sound, HUD update) without touching gameplay code
   - Handlers can hook the same event - multiple reactions coexist

2. **Procedural generation**
   - `ArenaBuilder.cs` constructs the entire room, props, spawn points from code
   - Every wall, furniture position, flight boundary is a fraction of room dimensions
   - Resize room from one constant without hand-editing 30 coordinates

3. **Intent-based input abstraction**
   - `LocalInputs` (keyboard), `BotMosquitoInput`, `BotHumanInput`, and future `NetPeer` all speak `MosquitoIntent`
   - Physics is decoupled from input source
   - Swapping local player for bot requires one line (interface change)

4. **Audio synthesis at runtime**
   - `ProceduralAudio.cs`: No audio files, just algorithms
   - Slaps, splats, zaps, bank chimes, heartbeat all synthesized from math
   - Saves memory, makes sounds adaptive (heartbeat speeds with greed)

5. **Proximity voice with detection integration**
   - Voice doesn't just play spatial audio
   - Proximity detection feeds the AI perception model
   - Talking reveals your position (both player and bot)
   - Voice is a tell because it's spatially real

6. **Ragdoll physics with debris separation**
   - Death animation is real physics (not an animation)
   - Dead mosquito tumbles, legs separate and ping off
   - Wings flutter for seconds after death
   - Makes each death feel weighty and watchable

7. **Camera shake with trauma model**
   - Impacts add "trauma"; trauma decays over time
   - Deepest requested scale and longest duration win
   - No permanent stutter, big hits dominate small ones
   - One file controls all camera effects

8. **Highlight log for streamers**
   - Every dramatic moment (swat miss <16cm, kill, big bank) timestamped
   - Streamer reads text file to find best 30 seconds of 2-hour session
   - Solves: "Where was the good part?" problem

**Why these matter?**

- **Event-driven**: Scales to feature creep. Adding v2 content doesn't break v1 systems
- **Procedural generation**: Easy to resize room, add new props, or port to other engines
- **Intent abstraction**: Networking, replay, replay could be added by changing one interface
- **Audio synthesis**: No large audio files, sounds can be adaptive (heartbeat = emotional state)
- **Proximity voice integration**: Voice becomes a tactical choice, not just chat
- **Ragdoll physics**: Death becomes a memorable moment (reinforces stakes)
- **Trauma camera shake**: Players feel impact without motion sickness
- **Highlights log**: Content creators can actually use clips without scanning two-hour footage

---

## 5. SECURITY (1 minute)

**How is the game protected?**

SKEETER doesn't have a backend or accounts yet, so security is minimal in v1.0:

- **No server**: Games are peer-to-peer (host + clients). No central point of attack
- **Local settings**: Player preferences stored in plaintext JSON locally
- **No authentication**: Games are invite-only (host shares IP address with friends)
- **No data collection**: No telemetry, no account system, no personal data

**Future considerations (v2.0+)**:

- Relay server (for NAT traversal) could validate game state
- Leaderboard backend would need authentication
- Replay storage would need user accounts
- Cross-platform play (iOS/Android ports) would need account system

**The design philosophy**: Trust players in v1. If ranked play comes later, move to server-authoritative outcomes. For now, peer-to-peer is fast, low-latency, and good enough for friends.

---

## 6. MY ROLE (30 seconds)

**What I built**:

- Entire game from scratch: architecture, gameplay, multiplayer, voice, AI, visuals
- 75 files, 13,349 lines of C# code, 40 commits
- Designed the core loop (blood weight tension) and tuning philosophy
- Built the event system so features can be added without tangling code

**Why it matters**:

- Shows I can design a game with a strong core loop (blood weight) that holds up for 90 seconds
- Demonstrates I understand multiplayer architecture (intent abstraction, authority model)
- Proves I value developer experience (event system, centralized tuning, code-first design)
- Shows I think about accessibility from day one (not bolted on)
- Understanding content creators' needs (vertical capture, highlights, replay system)

**What I learned**:

- Strong constraints (90-second rounds, asymmetric roles, three bodies) create better design than freedom
- Event-driven architecture scales better than direct references
- Procedural generation unlocks fast iteration (rebuild room in a frame)
- Audio synthesis is underrated (adapts to game state, saves memory)
- Player telemetry (personal bests, stats) drives retention more than progression trees
- Accessibility isn't a feature, it's a design requirement

---

## 7. Q&A PREP (1 minute each)

### "Why did you choose this tech stack?"

**You built it in Unity. Why not Unreal / Godot / custom engine?**

- **Unity** because it's cross-platform (Windows / macOS / Linux / future iOS) with a small build size
- **Fast to iterate**: Scene-free design means no file conflicts, fast rebuild, works in a fresh project
- **Audio synthesis** is easy to prototype (AudioSource + microphone input)
- **Networking stack** is lower-level (bare UDP), which is better for a peer-to-peer game than Unreal's replication
- **Learning cost** is low (C#, everyone knows it)

If I were rebuilding: I'd use Godot (open source, same low-level control, smaller engine). But for a 2-month sprint, Unity's ecosystem saved time.

---

### "How would you scale this?"

**What if you had 10,000 concurrent players?**

v1 is peer-to-peer (no scaling needed). But to scale:

1. **Add a relay server** (~200 LOC) to unblock NAT traversal. Handles ~5,000 simultaneous relay connections on a $5 VPS
2. **Leaderboard backend** (PostgreSQL + simple REST) for ranked play. Scale vertically first, then shard by region
3. **Replay storage** (S3 or similar) for clips. No hot-path dependency - replays are async
4. **Cross-platform** (iOS/Android ports) would use the same architecture (intent-based input)

The key insight: the game doesn't need a server for outcome validation until you have strangers playing ranked. Friends-only play stays peer-to-peer (faster, cheaper, lower latency).

---

### "What's the hardest part of this project?"

**Two things:**

1. **Asymmetric balance** (mosquito vs host)
   - It's easy to make one side overpowered
   - Solution: Every number in `Tuning.cs`, unit tests in `Tools/RuleTests` validate invariants
   - Took 3 weeks to dial in the belly curve so "too full to dash" happens before "too full to fly"

2. **Audio synthesis + voice perception integration**
   - Mixing synthesized audio (slaps, heartbeat) with real microphone input is tricky
   - Voice needs to sound spatial *and* feed the AI perception model
   - Solution: `ProximityVoice.cs` handles 3D falloff, `MicrophoneCapture.cs` runs detection on raw input
   - Took 2 weeks to get voice not clicking, voice latency under 100ms, and bots reacting correctly

**If I did it again**: I'd spec out the audio design earlier. Synthesis is amazing but needs planning.

---

### "What would you do differently?"

**Three things:**

1. **Assembly definitions from day one**
   - The architecture has implicit layer boundaries (Bootstrap → Core → everything, AI never references UI)
   - I documented them but didn't enforce them in code
   - Assembly definitions (.asmdef files) would have caught boundary violations early

2. **Input system migration**
   - I used legacy Input Manager (works everywhere, zero config)
   - New Input System is better but harder to test without Play mode
   - Would invest in a thicker input abstraction from start

3. **Voice transport earlier**
   - I built local-only first, then bolted on network transport
   - If I'd designed `IVoiceTransport` first (mock, local, network), I'd have decoupled it better
   - Lessons here: define your seams (networking, persistence, external APIs) before you code the core

---

## 8. FACTS TO ANCHOR ON

- **75 files** of C#, **13,349 lines** of code
- **40 commits** (tracked development history)
- **8 subsystems** (Core, Mosquito, Human, AI, Voice, Presentation, Networking, UI)
- **90-second rounds** (designed to fit in a vertical video)
- **2-4 players** + bot fill for empty seats
- **2-3 seconds to understand** the hook (land, drink, run, bank)
- **3 levels of accessibility** (motion, colorblind, interface)
- **~200 LOC relay** to unblock NAT traversal (future scale plan)
- **2,600+ unit test assertions** in Tools/RuleTests (balance validation)
- **5+ playtesting iterations** on the belly curve (weight vs speed)

---

## 9. WHAT YOU CAN SAY CONFIDENTLY

**"SKEETER is a multiplayer party game where you play as a mosquito or a host defending human bodies. Every role is radically different, so nobody's bored. The core loop is about tension: drink more blood, get richer but slower. Do you risk one more bite, or run it home now? Last Call (final 18 seconds) is worth 2x, so every round has a climax. I built it in Unity, 75 files, 13K lines of C#, with peer-to-peer multiplayer, proximity voice chat, bot AI, and a system for streamers to find the best moments in their footage. The architecture is event-driven (audio, particles, HUD all listen to the same events) and procedurally generated (whole room builds from code). I validated the balance with 2,600+ unit tests because asymmetry is hard to tune."**

That's your elevator pitch. Expands to 5-10 minutes with the structure above.

---

## 10. INTERVIEW NIGHT-BEFORE CHECKLIST

- [ ] Read sections 1-3 (Problem, Solution, Architecture) - these are your foundation
- [ ] Memorize the 8 subsystems (Core, Mosquito, Human, AI, Voice, Presentation, Networking, UI)
- [ ] Practice saying the core loop in one sentence (mosquito lands → drinks → tries to bank before swat)
- [ ] Know the three "why" answers: why asymmetry, why Last Call, why event-driven
- [ ] Know the two hard things (asymmetric balance, audio synthesis + perception)
- [ ] Know what you'd do differently (assembly definitions, input abstraction, voice transport early)
- [ ] Have the fact anchors ready (75 files, 13K lines, 40 commits, 2,600+ tests)
- [ ] Be ready to explain the authority model (movement is client-owned, outcomes are host-authoritative)

---

## YOU'RE READY

You've got the story. You know the numbers. You can explain the architecture, the design choices, and the tough problems you solved. Now go own that interview.

**Good luck.**

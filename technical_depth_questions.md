# SKEETER - Technical Depth Preparation

These are the deep-dive questions you might get. Read through all of them so you're ready for any angle they take.

---

## Architecture & Design

### Q: Walk me through how a mosquito bite happens, from input to reaction.

**How you explain it** (1-2 minutes):

"When I land on skin, here's the flow:

1. `MosquitoActor` is flying, reads intent from `LocalInputs` (keyboard input)
2. Position changes, `MosquitoFeeding` checks collision with body part
3. If landed: `MosquitoFeeding.ProcessBite()` determines which body part (ear, leg, etc) and which tier (lean, rich, hotspot)
4. Raises `GameEvents.OnBite(tier, bodyPart)`
5. Seven systems listen to OnBite:
   - `GameAudio` plays drinking sound (pitch varies by tier)
   - `GameParticles` spawns blood mist (scale varies by tier)
   - `MosquitoVisuals` animates belly fill
   - `Hud` updates display
   - `HighlightLog` timestamps it
   - `HypeDirector` might trigger slow-mo if dramatic
   - `NetReplication` broadcasts to other players

The key: gameplay code only cares about 'landed on body part X'. Everything else (sound, particles, HUD, logging, network) plugs in by listening to the event. No spaghetti code."

**Why they ask it**: Tests if you understand event-driven architecture beyond buzzwords.

**Follow-ups**:
- "What if you wanted to add a new reaction, like a vibration on controller?"
  - Answer: "Add a handler in the `OnBite` event. One line. No touching gameplay code."
  
- "How does the network know a bite happened?"
  - Answer: "NetReplication listens to OnBite, broadcasts (authority check to make sure it was the host's outcome), and clients update their copy."

---

### Q: The architecture separates movement ownership (client-owned) from outcomes (host-authoritative). Walk me through a specific example where this matters.

**How you explain it** (2 minutes):

"Good example: a swat miss.

Mosquito is flying. Host tries to swat. Here's what happens:

**Movement (client-owned)**:
- Mosquito player sees their mosquito at position X (they control it, no latency or guessing)
- Host player sees mosquito at position X' (slightly behind, network latency)
- Both positions are 'correct' from that player's perspective
- The mosquito player's view is authoritative for their own movement (no rubber-banding)

**Outcome (host-authoritative)**:
- Host decides: 'Did swat miss by <16cm?' (they have the official position)
- Host broadcasts outcome: 'Swat missed by 8cm'
- Event fires: `GameEvents.OnSwatMiss(distance)`
- Triggers slow-mo, camera punch, banner

Why this matters:
- Mosquito player never sees their own movement lag (feels responsive)
- But we never have two players disagreeing about whether a swat connected
- The honest trade: trusts each player about their own position
  - Good for friends (nobody cheats)
  - Bad for ranked play (strangers could position-cheat)
  - If ranked comes later, we move to server-authoritative movement and add client prediction

This is documented in `docs/MULTIPLAYER.md` and implemented in `Net/NetAuthority.cs`."

**Why they ask it**: Tests if you understand the tradeoffs in multiplayer architecture.

**Follow-ups**:
- "What would you do differently for ranked play?"
  - Answer: "Server-authoritative movement with client prediction. Client sends input, server simulates, sends back corrected position. Costs 3-5x more code and only earns its keep when strangers have reason to cheat."

- "Isn't trusting the mosquito player a security issue?"
  - Answer: "For a game played with friends, no. They're not trying to cheat each other. For strangers: yes, which is why ranked play needs validation."

---

### Q: Tuning.cs has every number in the game. Why is that better than spreading them across systems?

**How you explain it** (1-2 minutes):

"One file, one place. Here's why:

**The problem**: If belly curve is in `MosquitoActor.cs`, dash lockout is in `BloodBelly.cs`, and bite tiers are in `Tuning.cs`, you change one and don't know what breaks.

**The solution**: Everything lives in `Tuning.cs`. You can see every relationship:

```csharp
public const float BellyCapacity = 100f;
public const float BellyFullSpeedScale = 0.42f;  // full belly = 42% speed
public const float BellyDashLockout = 0.72f;    // can't dash above 72% full
public const float BaseDrainPerSecond = 22f;    // how fast you fill
```

Now a game designer can see: 'If I slow down drain to 20, this affects fill time, which affects how many bites fit in a round, which affects strategy.'

**The validation**: `Tools/RuleTests` has 2,600+ assertions that validate these relationships. It catches: 'can't dash before belly is full' (asserts DashLockout < 1.0), 'heavier is never faster' (asserts full speed < normal speed), etc.

You can't have this with scattered tuning. You'd need to run Play mode and test manually every time. That's iteration death."

**Why they ask it**: Tests if you understand the difference between code organization and game design.

**Follow-ups**:
- "What if a designer wanted to make the belly curve non-linear?"
  - Answer: "Add a curve field to Tuning.cs, implement the evaluation in MosquitoActor.ProcessBelly(). One small change."

- "How would you handle this with multiple maps with different tuning?"
  - Answer: "Create a `MapProfile` that overrides Tuning values per map. Or use Tuning as base and have a Map delegate that returns the active profile. Same idea: centralize the overrides."

---

## Multiplayer & Networking

### Q: Design a relay server. What does it do and why is it better than port forwarding?

**How you explain it** (2 minutes):

"Port forwarding is manual - you tell your router 'send UDP 7788 to my PC'. Relays are automatic.

**With port forwarding**:
- Host forwards UDP 7788 on their router
- Clients connect directly to host's public IP
- Works great at home
- Breaks if host's ISP blocks ports (some do)
- Breaks if host has double NAT (ISP NAT + home router NAT)

**With a relay**:
- Both host and clients connect OUT to relay.skeeter.game
- Relay forwards messages between them
- No inbound connections needed
- Works on any ISP
- Relay is just a dumb packet forwarder (5 dollar VPS, ~200 lines of Rust)

Here's the pseudocode:

```rust
struct Session {
    host_addr: SocketAddr,    // who's hosting
    clients: Vec<SocketAddr>, // who's connected
}

// When host connects: register them
relay.sessions[game_code].host_addr = host_addr;

// When client connects: register them
relay.sessions[game_code].clients.push(client_addr);

// When host sends message: forward to all clients
relay.forward_from_host(game_code, message);

// When client sends message: forward to host
relay.forward_from_client(game_code, message);
```

That's it. No game logic, no account system, just routing.

**Why this comes later**:
- v1 works fine with port forwarding for friends
- Relay only needed if strangers want to play (need join code + server to redeem it)
- Not worth building until the game proves it has community

**Next step if scalability was needed**:
- Deploy relay to AWS / Heroku / DigitalOcean
- Store session state in Redis (optional, could be in-memory)
- Scale to thousands of concurrent connections (one relay handles ~5,000)"

**Why they ask it**: Tests if you understand the difference between v1 needs and v2 scaling.

**Follow-ups**:
- "What if you wanted join codes instead of IP addresses?"
  - Answer: "The relay assigns a code to each session. Host gets code, shares with friends. Client enters code, relay maps it to the host's IP. Code is 6 random digits or words (like Jackbox)."

- "How do you handle dropped connections?"
  - Answer: "Relay tracks last heartbeat. If no message for 30 seconds, assume peer disconnected. Broadcast disconnect to other players. Game handles it (bots fill the seat, match continues)."

---

### Q: Voice is proximity-based. Walk me through how proximity detection works and how it feeds perception.

**How you explain it** (2 minutes):

"Two things happen when you talk:

**1. Audio playback (3D spatial)**:
- `VoiceMouth` plays your voice to others in 3D space
- Falloff curve is realistic: clear under 0.65m, muffled at distance
- Implemented in `ProximityVoice.cs`

**2. Perception integration (tactical reveal)**:
- Your voice is loud, so bots hear it
- `MicrophoneCapture` runs PCM audio through a detection model
- Model outputs: 'voice is being used'
- This feeds `SwatterPerception` - bot becomes aware of your position
- Result: Talking gives you away

Here's the flow:

```csharp
// Player talks
MicrophoneCapture.ProcessAudio(pcmData);
// Detection fires: VoiceDetected event

GameEvents.OnVoiceDetected(position, volume);

// Bots listen
SwatterPerception.OnVoiceDetected(position);
Awareness += volume * (1 - distance_falloff);

// If awareness > threshold, bot attacks
if (awareness > threshold) {
    BotHumanInput.DecideToSwat(mosquito_position);
}
```

So talking is a tactical choice:
- You want to coordinate with teammates (use voice)
- But the enemy can hear you
- Muffling makes voice useless if far away (good)
- But clear inside 0.65m (makes proximity combat interesting)

**The design**: Voice is not just chat. It's part of game balance."

**Why they ask it**: Tests if you understand how systems interact (audio + perception + gameplay).

**Follow-ups**:
- "What if you wanted to add a 'whisper' mode (quieter, shorter range)?"
  - Answer: "Add a mode to MicrophoneCapture. Lower the volume output, change the falloff curve to drop off faster. Whisper is detected but at lower awareness. Teammates hear you, enemies don't."

- "How do you handle network lag for voice?"
  - Answer: "Voice is streamed via `NetVoiceTransport` with ~50-100ms latency (acceptable). It's UDP, so packets can drop (sound briefly cuts out, but not a big deal). If latency gets bad, you could add jitter buffer or frame buffering, but for 4 players on LAN/good internet, not needed."

---

### Q: The bot fills empty seats. How does the bot brain work and how is it different for mosquito vs host?

**How you explain it** (1-2 minutes):

"Bots produce the same `MosquitoIntent` and `HumanIntent` as players, so they run identical physics. The difference is how the intent is generated.

**BotMosquitoInput** (what a mosquito bot does):

1. Sense: Where are humans? Where's the window?
2. Decide:
   - If belly < 50%: find richest bite (hotspot)
   - If belly 50-72%: bite medium spots, stay mobile
   - If belly > 72%: can't dash, run home NOW
3. Output: `MosquitoIntent { flyDirection, dash, buzzUsed }`

The AI is deliberately handicapped so bots aren't overpowered:
- Bots don't have perfect information (use perception model, same as player detection)
- Perception has falloff (can't see through walls or far away)
- Voice and wingbeats give away position

**BotHumanInput** (what a host bot does):

1. Sense: Where is the mosquito? Where are my bodies?
2. Decide:
   - Which body is closest to mosquito?
   - Should I intercept or set a trap?
   - When should I switch bodies?
3. Output: `HumanIntent { moveDirection, swat, switchBodyIndex }`

**Difficulty modifiers** (in `SwatterProfile.cs`):
- Easy: Higher perception thresholds (slower to react), longer think time
- Normal: Mid-range perception
- Hard: Lower thresholds (faster react), more aggressive

The genius of this design: bot and player run identical physics, so the game never has to ask 'is this entity controlled by player or bot?'. Both just produce intents. Makes networking easy too (future network peer = another intent producer)."

**Why they ask it**: Tests if you understand abstraction and how it scales.

**Follow-ups**:
- "How do bots decide when to switch bodies?"
  - Answer: "SwatterPerception tracks mosquito position. If mosquito is closer to body B than current body A, and switching cost is worth it, switch. Implemented as a simple distance check, not pathfinding."

- "Could you add a learning component (bots that improve over time)?"
  - Answer: "You could. Record player strategies, build a decision tree or neural net, retrain monthly. But for a party game, you want consistent difficulty. v1 uses hardcoded profiles, but the architecture supports plugging in a learned model later."

---

## Systems & Integration

### Q: How does the "Last Call" mechanic work and why is it important?

**How you explain it** (1-2 minutes):

"Last Call is the final 18 seconds of a 90-second round. When it starts:

1. Everything banked is worth 2x points
2. The window flares (visual signal)
3. Clock beats loudly (audio signal)
4. Hosts get an adrenaline boost (speed increase for a designed climax)

**Why it's designed in**:

Most games let you earn points the whole time. So a mosquito is incentivized to bank early (safe, low stakes).

Last Call reverses the incentive: 'Wait until the end, everything is worth double.'

Result: Every single round ends the same way - a heavy mosquito SPRINTING for a glowing window with a hand swatting from above. That's content. That's watchable.

**Implementation** (in `MatchDirector.cs`):

```csharp
if (timeRemaining <= 18f) {
    // Mark Last Call
    last_call_active = true;
    
    // Event fires
    GameEvents.OnLastCallStart();
    
    // HypeDirector reacts
    // - Slows time slightly
    // - Boosts volume on clock
    
    // Scoring reacts
    // - All banks are worth 2x
    
    // Hosts get speed boost
    HumanVitals.AdrenalineMultiplier = 1.3f;
}
```

**Why it matters**:

Games without this end flat. You never know when the climax is coming (if at all). With Last Call, every round has a guaranteed moment of intensity.

This is a design principle: **Manufacture drama at predictable intervals.**"

**Why they ask it**: Tests if you understand game design (how game rules create player behavior).

**Follow-ups**:
- "What if people complained Last Call was unfair?"
  - Answer: "It's equally unfair to everyone (happens every round, everyone gets the boost). But if feedback said 'I want to play safe strategy', we could add an option to disable it. The core loop doesn't need it - tension exists before Last Call."

- "How would you tune this for different difficulty levels?"
  - Answer: "Easy mode: Last Call could start earlier (20s) or last longer (22s). Hard mode: start later (15s). Same principle - adjust the intensity window."

---

### Q: Audio synthesis instead of audio files. Walk me through one example - the heartbeat.

**How you explain it** (1-2 minutes):

"The heartbeat is synthesized at runtime based on your greed (how full your belly is).

Why synthesis?
- No large audio files (saves memory)
- Audio adapts to game state (speed reflects risk)
- Compresses infinitely (one algorithm, not one file per variation)

**Implementation** (in `ProceduralAudio.cs`):

```csharp
public AudioClip GenerateHeartbeat(float greedLevel) {
    // 0 = empty (slow heartbeat, calm)
    // 1 = full (fast heartbeat, urgent)
    
    float bpm = Mathf.Lerp(60, 140, greedLevel);
    float frequency = 80; // bass tone
    
    AudioClip clip = new AudioClip();
    float[] samples = new float[sampleRate];
    
    for (int i = 0; i < samples.Length; i++) {
        float time = (float)i / sampleRate;
        
        // Two beats per cycle (lub-DUB)
        float phase = (time * bpm / 60) % 1;
        bool isFirstBeat = phase < 0.3;
        bool isSecondBeat = phase > 0.5 && phase < 0.8;
        
        if (isFirstBeat || isSecondBeat) {
            // Generate sine wave (heartbeat tone)
            samples[i] = Mathf.Sin(2 * PI * frequency * time) * volume;
        }
    }
    
    clip.SetData(samples, 0);
    return clip;
}
```

Then in gameplay:

```csharp
void Update() {
    float greedLevel = mosquito.BellyFillPercent;
    heartbeat.pitch = Mathf.Lerp(0.9f, 1.2f, greedLevel);
    heartbeat.PlayScheduled(startTime);
}
```

**What this accomplishes**:
- No audio files, just an algorithm
- Heartbeat speed is directly tied to your risky decision (full belly)
- Players FEEL the tension before they think about it
- Memory footprint is zero

**Other synthesized sounds**:
- Slap/splat on bite (frequency sweep)
- Zap on bank (high-frequency burst)
- Chime on Last Call (harmonic)
- Countdown beats (simple square waves)

All synthesized, all adaptive to game state."

**Why they ask it**: Tests if you understand the intersection of game design, audio, and systems integration.

**Follow-ups**:
- "How would you extend this to music?"
  - Answer: "You could generate a backing track that adapts (tempo increases, notes get sharper as tension rises). But for v1, we kept it minimal - heartbeat + SFX. Music would be a nice future feature."

- "Isn't synthesis more expensive than just playing files?"
  - Answer: "Short answer: no, it's cheaper. One algorithm vs loading multiple files into memory. The tradeoff: synthesis code is more complex, but the payoff is adaptivity and memory savings."

---

### Q: The game rebuilds every round (destroys and rebuilds the arena). Why is that a good design?

**How you explain it** (1-2 minutes):

"Most games have a persistent scene. Here, `ArenaBuilder.Build()` constructs everything from scratch, then `GameBootstrap` tears it down at round end and rebuilds.

**Why this seems wasteful**:

Rebuilding every 90 seconds could be expensive. Seems smarter to reset objects in place.

**Why it's actually brilliant**:

1. **Instant restarts**: Zero residual state. No lingering effects, no bugs that build up over time.
2. **Text diffs**: Since the arena is built from code, the whole game is reviewable as a diff. No binary scene corruption.
3. **Engine ports**: If I ever port to Godot or another engine, the scene format isn't locked to Unity.
4. **No file locks**: Multiple devs can commit changes without scene file merge conflicts (scene files are always nightmares to merge).
5. **Easy scaling**: Adjust room size from one constant, rebuild, all coordinates scale proportionally.

**Implementation** (simplified):

```csharp
// Round starts
ArenaBuilder.Build();

// Runs gameplay...

// Round ends
Destroy(allGameObjects);
GameEvents.ResetAll();

// Next round: rebuild
ArenaBuilder.Build();
```

The magic is in `GameEvents.ResetAll()` - clears all the event handlers so they don't accumulate.

**Trade-off**: Rebuild is not free (takes a few frames), but 90-second rounds are long enough that startup latency doesn't matter.

**This architecture choice enables**:
- Instant restarts (player hits R, new round in one frame)
- Content creators can customize room size without breaking anything
- Bots can generate rooms from parameters (future map variants)"

**Why they ask it**: Tests if you understand the tradeoff between simplicity and performance optimization.

**Follow-ups**:
- "At what scale does this become a problem?"
  - Answer: "If rounds were 10 seconds, rebuild overhead would matter. If rounds were 5 minutes, we might optimize by pooling objects. At 90 seconds, it's fine."

- "Could you make this work with scene files (traditional approach)?"
  - Answer: "Yes, but you'd lose the benefits (text diffs, no file locks, easy porting). You'd have to implement custom reset logic for each system. Would take more code, not less."

---

## Testing & Validation

### Q: What does Tools/RuleTests do and why is it important?

**How you explain it** (1-2 minutes):

"RuleTests is a suite of 2,600+ unit test assertions that validate game balance rules. It runs in ~2 seconds without opening Unity.

**Why it's important**:

Asymmetric games are fragile. One number changes and suddenly one side is overpowered. Example: if I change `BellyDashLockout` from 0.72 to 0.80, the mosquito can dash with a fuller belly, which makes them way faster. The rule 'heavier is slower' breaks.

RuleTests catches this:

```csharp
// Rule: At any fill level, full belly is slower than empty
[Test]
public void BellyWeight_FullerIsNeverFaster() {
    for (float fill = 0f; fill <= 1f; fill += 0.05f) {
        float speedAtFill = CalculateSpeed(fill);
        float speedAtZero = CalculateSpeed(0f);
        
        Assert.LessOrEqual(speedAtFill, speedAtZero,
            $"At {fill*100}%, speed should be <= empty speed");
    }
}

// Rule: Dash lockout kicks in before belly is full
[Test]
public void DashLockout_KicksInBeforeFull() {
    Assert.Less(Tuning.BellyDashLockout, 1.0f);
    
    // Verify no feedback loop
    float speedAtLockout = CalculateSpeed(Tuning.BellyDashLockout);
    float speedFull = CalculateSpeed(1.0f);
    Assert.LessOrEqual(speedAtLockout, speedFull);
}
```

**How to run it**:

```bash
cd Tools/RuleTests
dotnet run
```

Output: `All 2,600+ assertions passed` or lists failures.

**What it catches**:
- Balance relationships (heavier is never faster)
- Difficulty progression (bots get harder, not harder then easier)
- Voice falloff (is realistic)
- Banking invariants (you can't bank more than you're carrying)
- Lobby splits (3v1, 2v2, 1v3 all produce correct player counts)

**Why not just test in-game**:
- In-game testing requires Play mode (slow)
- RuleTests is 2 seconds, runs in CI/CD
- Catches regressions before they hit gameplay

**The discipline**: Whenever you add a rule with an invariant, add a test. This prevents 'silent breaks' (rule breaks but nothing tells you)."

**Why they ask it**: Tests if you understand testing discipline and how to catch design regressions.

**Follow-ups**:
- "What if you wanted to randomize room size - how would you test that?"
  - Answer: "Add a test that generates 100 random room sizes, builds each, verifies all walls are inside bounds, all bodies fit. Parametric testing."

- "Does this test networking?"
  - Answer: "No, this is logic-only. Networking would need Play mode testing (multiple players, message serialization, latency). RuleTests is for the rules that don't need physics or rendering."

---

## Closing Questions

### Q: If you had to pick one thing you're most proud of in this project, what is it?

**How you answer** (30-60 seconds):

"The core loop. Getting the tension right - where blood is heavy - took 3 weeks. Every part of the game reinforces this:

- Visually: belly fills on your body, everyone sees the risk
- Mechanically: speed drops, dash disables
- Sonically: heartbeat speeds up (your greed in audio)
- Narratively: 'One more bite or run home?' *that* is the game

And because it's so tight, everything else (multiplayer, voice, visuals) just plugs in. You don't need complex progression systems or loot - the core loop is enough.

If I had to defend this game in one sentence: 'Visible greed and visible consequences, every round, for 90 seconds.'

That's what I'm proud of."

---

### Q: What would you do differently if you were rebuilding this?

**How you answer** (1-2 minutes):

"Three things:

1. **Assembly definitions from day one**: I documented the boundaries (Bootstrap → Core → everything, AI never references UI) but didn't enforce them in code. Assembly definitions (.asmdef files) would have caught violations early.

2. **Input abstraction first**: I used legacy Input Manager (works everywhere, zero setup). But I should have designed a thicker abstraction so swapping to new Input System was one-line. Would also enable better replay support.

3. **Voice transport interface earlier**: I built local-only first (voice loops back to yourself), then bolted on network. If I'd designed `IVoiceTransport` with mock / local / network implementations upfront, I'd have decoupled it better.

The pattern: define your seams (networking, persistence, external APIs) before you code the core. That's the lesson."

---

**YOU'RE READY FOR DEEP DIVES**

You know:
- Event-driven architecture and why it scales
- Authority model for networking
- How systems integrate (audio + perception + gameplay)
- Testing discipline
- Design decisions and tradeoffs
- What you'd do differently

Go crush that interview.

# SKEETER

*(working title — one word, spellable, hashtag-safe. It lives in `Tuning.GameTitle`.)*

You are a mosquito in someone's living room. Land on them, drink, and get the blood out
through the open window before you get swatted. The catch is that blood is heavy — the more
you carry, the slower you fly, and it is not yours until you have banked it.

Roles are assigned at random every round. You might be the mosquito. You might be the house.

## Running it

1. Install **Unity 2022.3 LTS** (Unity 6 works — expect deprecation warnings).
2. Open this folder via Unity Hub → *Add project from disk*.
3. Press **Play**.

No scene to open, nothing to wire up. You land on the menu with a round already playing behind
it — bots against bots — so you can see the game before you press anything. Hit **Play** and a
briefing tells you which side you drew and how to play it (`H` to see it again, `Esc` to get
back to the menu).

## The hook

Three rules, and a viewer understands the whole game in about four seconds:

1. **Drink blood.** Land on skin. The pouch on your back visibly fills up and turns red.
2. **Blood is heavy.** A full belly cuts your speed by more than half and disables your dash
   entirely. Being rich and being fast are opposites.
3. **It only counts once it's banked.** Get to the glowing window. Die anywhere along the
   way and you lose every drop you were carrying.

So every round is the same escalating question — *one more bite, or run it home now?* — and
the answer is always visible on the mosquito's own body, to everyone watching.

And every round ends the same way: **Last Call**. In the final eighteen seconds everything you
bank is worth double, the window flares, the clock starts beating, and the house gets a surge of
adrenaline to match. It is there to manufacture a climax in every single round — a heavy
mosquito sprinting for a glowing window with a hand behind it, which is the shape a clip needs.

**Bite anywhere.** Every part of a person can be drunk from — legs, back, arms, hands, face,
neck, ears — but a leg is a trickle and an ear pours six times faster and sits right beside the
thing that hears you. Good spots wear a faint halo you can pick out from the air, so choosing
where to land is a decision you make before you commit, not one you discover afterwards.

## Formats

Roles are rolled at random each round, so nobody knows which side they are on until it starts.
For playtesting, **Your side** in the menu pins you to one — you cannot tune or film a side of
an asymmetric game if you cannot choose to play it.

| Lobby | Possible splits |
| --- | --- |
| Duo | 1 host vs 1 mosquito |
| Trio | 2v1, 1v2 |
| Quad | 3v1, 2v2, 1v3 |

The room always contains **three bodies**, however many people are playing. Fewer host
players means each one juggles more of them — so a solo host jumps between all three, and
three hosts get one each. The mosquito always sees the same amount of blood on the table.

Every seat a person is not sitting in is filled by a bot, on both sides. Solo play is
therefore the real multiplayer format, not a stripped-down practice mode. See
[docs/MULTIPLAYER.md](docs/MULTIPLAYER.md) for what networking still needs.

## Controls

**As the mosquito**

| Input | Action |
| --- | --- |
| `WASD` | Fly | 
| Mouse | Look |
| `Space` | Up — or take off when landed |
| `Ctrl` / `C` | Down |
| `Shift` | Dash (locked out above 72% belly) |
| `Q` (hold) | **Buzz** — screams your position, builds a style multiplier on your next bank |
| `V` (hold) | **Talk** — push-to-talk. Your voice comes out of your body, and it gives you away |

Landing and drinking are automatic. So is banking: touch the window and it happens.

**As a host**

| Input | Action |
| --- | --- |
| `WASD` / Mouse | Move, look |
| Left click | Swat |
| `Tab` / `1` `2` `3` | Jump to another body — costs ~0.5s of being blind and helpless |
| `V` (hold) | **Talk** — heard from the body you are currently in, which is a tell |

**Anytime**

| Input | Action |
| --- | --- |
| `R` | New round, new random roles |
| `F2` | **Vertical capture** — reframes to 9:16 with the HUD inside the crop |
| `F3` / `F4` | Cycle lobby size / bot difficulty |
| `F9` | Save a screenshot — aimed at the recap card |
| `H` | Show the role briefing and controls again |
| `Esc` | Menu — pauses a live round |

## What's in it

- **Sound**, entirely synthesised at runtime — slaps, splats, a zap, bank chimes, countdown
  beats, and a heartbeat that rises with your own greed before anything has threatened you.
- **Particles** — blood sprays, dust rings on a miss, sparks on a bank, and drips that trail
  behind a mosquito carrying too much.
- **Ragdolls** — real jointed ones. Hosts fold, thrash, bounce and clatter when drained; dead
  mosquitoes pop upward, tumble, and shed six legs that ping off in straight lines while the
  wings are still fluttering down long after everything else has settled.
- **Camera shake** on impacts, using a trauma model so a big hit outweighs a small one.
- **Weapon pickups** — a flyswatter and a zap racket, placed far from the window so fetching
  one costs a host time and position.
- **Proximity voice** wired into the detection model, so talking gives you away.

## Why it clips

The game watches itself and points at the good bit — see
[docs/VIRALITY.md](docs/VIRALITY.md). Briefly:

- **Near-miss slow motion.** A swat that misses by under 16 cm drags time to a crawl, punches
  the camera in, and stamps **MISSED BY 4 CM** across the screen.
- **Kill freeze-frame.** Death stops time dead and orbits the corpse.
- **Vertical capture mode** (`F2`) so a clip is framed for a phone at record time, instead of
  being cropped afterwards with half the HUD cut off.
- **Highlight log.** Every dramatic moment is written to a timestamped file so a streamer can
  find the good thirty seconds of a two-hour session by reading a text file.
- **Screenshot-ready recap** with the numbers people actually quote — closest call in
  centimetres, biggest haul, bank streak — and **NEW BEST** flags on anything you beat.
- **Bank streaks.** Consecutive banks without dying, shouted out at 3, 5 and 8. A death costs
  the whole streak, which is what makes a long one worth watching.
- **A shareable seed** on the recap card. The whole arena is built from it, so the same number
  gives the same room, the same furniture and the same roles — "beat 4417823" is a challenge
  somebody can actually take you up on.
- **Persistent personal bests**, so there is always a number to beat. No currency, no unlock
  tree, nothing that needs explaining.

## Playing online

**Play online** from the menu. One person hosts and reads out their address; everyone else types
it in. The host presses Play and everybody is pulled into the round with them. Every empty seat
is still filled by a bot, so a lobby of two is a real game.

On a home network it works with nothing else running. Over the internet the host forwards **UDP
7788** — there is no lobby browser and no join code yet, and the menu says so rather than
letting you find out. See [docs/MULTIPLAYER.md](docs/MULTIPLAYER.md).

## Proximity voice

Push-to-talk on `V`. Your voice plays out of your character's body in 3D — muffled by
distance, and startlingly clear inside 0.65 m of someone's ear. Talking feeds the same
detection model as your wingbeat, so a mosquito that chats next to a host gets swatted.

It carries between machines once you are online. Solo, the default transport loops your own
voice back so the spatial design can be felt without a second player. **Settings** has a live
input meter and a device picker — if voice is not working, that page will say why. See
[docs/VOICE.md](docs/VOICE.md).

## Layout

```
Assets/Scripts/
  Core/         Tuning (every number), match format, round director, event bus
  Mosquito/     Flight, the blood belly, feeding and banking, visuals, procedural buzz
  Human/        Bodies, vitals and dizziness, the swat, body-switching squads
  AI/           Perception with real handicaps, awareness, bot brains for both sides
  Input/        The intent contracts every controller speaks - the networking seam
  Presentation/ Camera rig, hype director, death cam, shake, particles, ragdolls
  Audio/        Runtime sound synthesis and the event-to-sound mapping
  Voice/        Proximity voice: capture, 3D playback, the transport seam
  Net/          UDP transport, sessions, ownership, replication
  Gameplay/     Perch/bite/bank markers, flight bounds
  Bootstrap/    Builds the whole round in code
Tools/RuleTests/  Off-engine unit tests for the game rules (dotnet run)
docs/             Architecture, design, virality, multiplayer, voice
```

New to the codebase? Start with [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — it explains
the three organising rules and the four places the code does something non-obvious.

## Accessibility

In **Settings**, reachable from the menu or with `Esc`:

- **Camera shake** slider, and **Reduce motion** to switch off slow motion, camera punches and
  the kill freeze-frame entirely. The clip machine deliberately lurches the camera and the
  clock around, which is exactly what triggers motion sickness — so it is optional.
- **Red/green safe colours.** The game's two most important colours are the blood you carry and
  the window you carry it to. That is the exact pair the most common colour vision deficiency
  cannot separate, so this mode moves the safe zone to cyan.
- **Tap instead of hold** for the buzz and the microphone — a taunt or a sentence can run for
  many seconds and neither needs to be a sustained keypress.
- **Interface size**, scaling every menu and HUD element together.
- **A written warning when a swat commits.** The telegraph is normally carried by a whoosh and a
  raised hand; this spells it out for anyone who cannot hear it or is facing the wrong way.
- Field of view, master/effects/voice volumes, mouse sensitivity, invert look.

## Tuning

Start with **`Assets/Scripts/Core/Tuning.cs`**. Every number that changes how the game feels
is in that one file, on purpose.

`Tools/RuleTests` asserts the rules that must not break while you tune — that heavier is
never faster, that the dash lockout bites before the belly is full, that dizziness always
arrives before a host passes out. Run `dotnet run` in that folder; it takes two seconds and
does not need Unity.

## Notes on the build

- Legacy **Input Manager**, so it runs in a fresh project with zero configuration. Migrating
  to the new Input System is the first roadmap item and a prerequisite for local split-screen.
- Works under both the Built-in pipeline and URP — materials resolve their shader at runtime.
- No binary scene or prefab files. The arena is assembled in `ArenaBuilder.cs`, so the whole
  game is reviewable as source and a round can be rebuilt in a frame. **Skeeter → Generate
  Prototype Scene** bakes a real `.unity` scene when you want to hand-place things.

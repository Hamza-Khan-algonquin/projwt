# Interview Preparation Checklist for SKEETER

Use this checklist the night before your interview. Check off each section as you prepare.

---

## THE NIGHT BEFORE

### Read (45 minutes total)

- [ ] **Read INTERVIEW_EXPLANATION.md - full document** (25 min)
  - Focus on sections 1-3 (Problem, Solution, Architecture)
  - Sections 4-7 are reference material for Q&A
  
- [ ] **Read interview_talking_points.txt** (10 min)
  - Memorize the elevator pitch (30 sec version)
  - Know the 8 key features
  - Know the 8 subsystems by name
  
- [ ] **Skim technical_depth_questions.md** (10 min)
  - Read the "Q&A ANSWERS" section (quick reference)
  - You don't need to memorize exact answers
  - Just know the rough shape of responses

### Memorize (30 minutes)

- [ ] **The core loop (1 sentence)**
  - "You are a mosquito: land on skin, drink blood, fly to window to bank points. Blood is heavy - the more you carry, the slower you fly. Die before banking = lose everything."

- [ ] **The three main "why" decisions**
  1. Why asymmetry? → "Nobody's bored, different game per role"
  2. Why Last Call? → "Guaranteed climax every round, drives content"
  3. Why event-driven? → "Features scale without touching gameplay code"

- [ ] **The 8 subsystems (in order)**
  1. Core (spine: GameEvents, Tuning, MatchDirector)
  2. Mosquito (flight, feeding, visuals)
  3. Human (bodies, squad, swat)
  4. AI (perception, bot brains)
  5. Voice (proximity audio, detection)
  6. Presentation (camera, shake, particles, ragdoll)
  7. Networking (UDP, replication, authority)
  8. UI (HUD, menus, recap)

- [ ] **The 2-3 hard problems you solved**
  1. Asymmetric balance (belly curve took 3 weeks)
  2. Audio synthesis + voice perception integration (took 2 weeks)
  3. [Pick one other: ragdoll physics, proximity detection, etc.]

- [ ] **The 2-3 things you'd do differently**
  1. Assembly definitions from day one
  2. Thicker input abstraction
  3. Voice transport interface first

- [ ] **The fact anchors**
  - 75 files, 13,349 lines of C#, 40 commits
  - 8 subsystems, 2,600+ unit test assertions
  - 90-second rounds, 2-4 players, ~200 LOC relay server

### Practice (15 minutes)

- [ ] **Say the elevator pitch out loud** (1 min)
  - 30-second version should feel natural
  - 2-minute version should cover Problem + Solution

- [ ] **Explain the core loop to a mirror** (2 min)
  - Don't script it, just tell the story
  - You land on skin, drink, get heavy, run to window
  - Blood is heavy = the tension

- [ ] **Practice answering one hard question** (5 min)
  - Pick one: "Why this tech stack?" or "What's the hardest part?"
  - Speak it out loud
  - Aim for 1-2 minute answer

- [ ] **Review your "what I'd do differently" answer** (2 min)
  - This is important - shows reflection
  - Keep it to 3 things, not a list of complaints

- [ ] **Do a confidence check** (5 min)
  - Can you explain asymmetry and why it matters? YES / NO
  - Can you name the 8 subsystems? YES / NO
  - Can you explain event-driven in 1 minute? YES / NO
  - Can you tell them one hard problem and how you solved it? YES / NO
  - If any NO: go back and re-read that section

---

## MORNING OF INTERVIEW

### 30 Minutes Before

- [ ] **Skim interview_talking_points.txt** (5 min)
  - Just jog your memory on the facts
  
- [ ] **Read the "ELEVATOR PITCH" and "Q&A ANSWERS" sections** (5 min)
  - These are your cheat sheet
  
- [ ] **Do a mental walkthrough** (10 min)
  - Start: "Hi, I built SKEETER, a multiplayer game..."
  - Go: Core loop → asymmetry → why that matters
  - End: "75 files, 13K lines, 40 commits, and the architecture is event-driven."

- [ ] **Check your mindset**
  - You built this project
  - You understand every line
  - You can explain it confidently
  - You know what worked, what didn't, what you learned
  - That's enough

### During Interview

**If they ask about the project:**
- Start with the elevator pitch (30-90 seconds)
- Watch for signals: are they interested in game design? Code architecture? Multiplayer? Scale?
- Follow their interest
- Have this checklist of talking points:
  - [ ] Core loop (1 sentence)
  - [ ] Asymmetry (why it matters)
  - [ ] Event-driven (how it scales)
  - [ ] Multiplayer (peer-to-peer + authority model)
  - [ ] Accessibility (designed in, not bolted on)
  - [ ] Bot AI (perception model, difficulty)
  - [ ] One hard problem you solved
  - [ ] One thing you'd do differently

**If they ask a technical question you didn't practice:**
- Take 3 seconds to think
- Use interview_talking_points.txt as reference (it has Q&A answers)
- Or defer: "Great question - let me think about that. [Take a breath.] Here's how I'd approach it..."
- Don't bluff - if you don't know, say "I'd need to think that through" or "That's a good idea for v2"

**If they ask to see the code:**
- Open Assets/Scripts
- Walk them through one subsystem (pick your favorite)
- Show them an event (GameEvents.cs) and how it's consumed (GameAudio, GameParticles, HUD all listen)
- This demonstrates the architecture without diving too deep

**If they ask to play the game:**
- Follow feature_demo_guide.md
- Focus on: core loop, asymmetry, Last Call, visual feedback, accessibility
- Let them see 2-3 rounds (one as mosquito, one as host)

---

## QUICK REFERENCE (Have This Open)

**INTERVIEW_TALKING_POINTS.TXT** is your cheat sheet. Have it nearby (on your phone, printed, etc.). It has:
- Elevator pitch
- Core loop
- 8 key features
- Architecture summary
- Technical highlights
- By the numbers
- Q&A answers (30 sec each)
- Conversation starters

If you blank on something, glance at it. That's what it's for.

---

## WHAT SUCCESS LOOKS LIKE

After your interview, you'll know you nailed it if:

- [ ] They understood the core loop (asked a question about it)
- [ ] They thought the architecture was interesting (commented on event-driven or procedural generation)
- [ ] They were impressed by accessibility design (mentioned it or asked about it)
- [ ] You explained multiplayer without stumbling (authority model made sense)
- [ ] You had a clear answer about what you'd do differently (showed reflection)
- [ ] You stayed calm and confident (didn't make anything up, admitted when you needed to think)

---

## DO NOT DO

**Don't:**
- Memorize exact phrasing (speak naturally)
- Try to name-drop every detail (they don't care about BloodDripper.cs)
- Get defensive about design choices (own them, explain the tradeoffs)
- Pretend to know something you don't (just say "I'd need to think about that")
- Talk for more than 2-3 minutes without asking if they have questions

**Do:**
- Tell the story of the project (problem → solution → how you built it)
- Show enthusiasm about the problems you solved
- Explain your reasoning (not just what, but why)
- Listen to their questions and answer what they ask
- Admit what you'd do differently (shows you can self-critique)

---

## FINAL CONFIDENCE CHECK

**You can confidently explain:**

✓ What SKEETER is (mosquito game, asymmetric, 90 seconds)
✓ Why the core loop works (blood = weight = tension)
✓ Why asymmetry matters (nobody's bored, different game per role)
✓ The architecture (8 subsystems, event-driven spine)
✓ Why event-driven scales (features don't touch gameplay code)
✓ How multiplayer works (peer-to-peer, authority model)
✓ One hard problem you solved (pick: balance, audio, networking)
✓ One thing you'd do differently (pick: assembly definitions, input, voice)
✓ The numbers (75 files, 13K lines, 40 commits)

**If you can explain all of these, you're ready.**

---

## GOOD LUCK

You've got the story.
You know the numbers.
You understand the architecture.
You can explain the design choices.

Now go own that interview.

**Remember:**
- You built this project from scratch
- You made hard design decisions
- You solved tricky problems
- You're proud of it (and rightfully so)

Let that confidence show.

**Go get 'em.**

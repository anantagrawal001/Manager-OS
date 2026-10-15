# MANAGER OS — COMPLETE TEST PLAN
# ════════════════════════════════════════════════════════════════
# FILE: TESTPLAN.md
# PURPOSE: Systematic verification of all requirements
# Run these tests in order after every fresh install
# Grade: PASS ✅ / FAIL ❌ / PARTIAL ⚠️
# ════════════════════════════════════════════════════════════════

---

## HOW TO USE THIS

After running SETUP.bat + START.bat:
1. Open localhost:8000 in Chrome
2. Open the terminal running Manager OS (watch logs)
3. Work through each test case below
4. Log PASS/FAIL for each
5. Fix fails before moving to next section

---

## SECTION 1: BOOT & IDENTITY (Critical — must pass 100%)

### TEST-001: Clean Boot
**Action:** Run START.bat in fresh folder
**Expected:**
- pygame message appears (normal)
- "Whisper model 'base' loaded" in logs
- "Voice engine initialized" in logs
- All 12 agents shown as initializing
- "Manager OS online: Good evening/morning, Sir" in logs
- Server running on http://0.0.0.0:8000
- NO Python errors or tracebacks
**Check:** logs\manager_YYYY-MM-DD.log — zero ERROR lines on boot
**PASS criteria:** Server starts within 30 seconds, no crashes

### TEST-002: Dashboard Loads
**Action:** Open http://localhost:8000 in Chrome
**Expected:**
- Dark background with grid lines
- J.A.R.V.I.S brand header: "Manager OS — Just A Rather Very Intelligent System"
- Animated particle orb visible in center
- 12 agents listed on left sidebar with colored dots
- System metrics on right (CPU%, RAM%, GPU%, Disk)
- Clock ticking in top right
- "ONLINE" pill indicator green
- Status bar at bottom: "agents active | GEOSYNC LINK STABLE"
**PASS criteria:** All UI elements visible, orb animating

### TEST-003: Auth Screen
**Action:** Clear browser cache, reload
**Expected:**
- Auth screen shown first (small orb + "Manager OS" + passphrase field)
- Typing passphrase + Enter → dashboard loads
- Without passphrase → stays on auth
**PASS criteria:** Auth gate works before dashboard access

### TEST-004: Hardware Metrics Live
**Action:** Watch right sidebar for 10 seconds
**Expected:**
- CPU% updating every 5 seconds
- RAM% showing actual usage (16GB machine — expect 70-90%)
- Disk showing ~500GB free
- Numbers change when you open Chrome DevTools (CPU spike)
**PASS criteria:** All 4 metrics updating with real data

---

## SECTION 2: VOICE & SPEAKING (Critical — Iron Man feel)

### TEST-005: Manager Speaks on Boot
**Action:** Listen to speaker after START.bat
**Expected:**
- Manager says: "Good [morning/evening], Sir. All systems online..."
- Voice is clear through speakers (not an audio file window)
- No "run loop already started" error in logs
**PASS criteria:** Hear Manager speak within 5 seconds of boot

### TEST-006: Manager Responds with Voice
**Action:** Type "Hello Manager" in chat, press Enter
**Expected:**
- Orb changes color to blue (thinking mode)
- Response appears in chat bubble
- Manager SPEAKS the response through speaker
- Orb pulses with speech amplitude while speaking
- Real-time word captions appear below orb
**PASS criteria:** Text response + spoken response + captions all working

### TEST-007: pyttsx3 Stress Test
**Action:** Send 5 messages quickly in a row
**Expected:**
- No "run loop already started" error in logs
- Each response spoken in sequence (queued, not dropped)
- No crashes
**PASS criteria:** All 5 messages spoken without errors

### TEST-008: Microphone Input
**Action:** Click the microphone button (🎙)
**Expected:**
- Button turns red (listening mode)
- Orb turns green (listening state)
- Speak: "Hey Manager, what time is it?"
- Manager transcribes and responds
- Orb returns to idle after response
**PASS criteria:** Voice input → transcription → response pipeline working

---

## SECTION 3: AI INTELLIGENCE (Core functionality)

### TEST-009: Basic Conversation
**Say/Type:** "Hey, how are you doing?"
**Expected Response should contain:**
- Addresses you as "Sir"
- Warm, casual tone
- NOT "As an AI language model..."
- NOT mentions of ChatGPT or Claude
- Should say something like "Doing well, Sir..."
**PASS criteria:** Manager personality intact, not generic AI

### TEST-010: Which Model Are You Using?
**Say/Type:** "Which API or model are you using right now?"
**Expected Response should contain:**
- Honest answer about which provider is active
- If Ollama: "Running on local Ollama, Sir — llama3.1:8b"
- If Groq: "Using Groq with llama-3.1-70b-versatile, Sir"
- Should NOT refuse to answer
- Should NOT say "I can't comment on that"
**PASS criteria:** Honest, direct answer about active model

### TEST-011: System Status Query
**Say/Type:** "Tell me all system status — agents, APIs, hardware"
**Expected Response should contain:**
- List of all 12 agents with status
- Which AI providers are working
- CPU/RAM stats
- NO hallucinated agents (no "TaskMaster", "EmailShield" etc.)
**PASS criteria:** Accurate status, no hallucination

### TEST-012: Conversation Memory
**Action:** Two-part test:
- Part A: Say "My name is Anant and I love cricket"
- Wait for response
- Part B: Say "What sport do I love?"
**Expected:** Manager remembers "cricket" from earlier in conversation
**PASS criteria:** Context retained within session

### TEST-013: Cross-Session Memory
**Action:**
- Session 1: Say "Remember this: my lucky number is 47"
- Stop Manager (Ctrl+C)
- Restart with START.bat
- Say "What is my lucky number?"
**Expected:** Manager says "47, Sir" (retrieved from ConversationStore)
**PASS criteria:** Memory persists across restarts

### TEST-014: Task Routing to Correct Agent
**Say:** "Fix the latency issue on my network"
**Expected:** Routes to builder or research agent (not trading or social)
**Check logs:** Should show which agent handled it

**Say:** "What stocks should I buy today?"
**Expected:** Routes to trading agent
**Check logs:** "Intent: trading" visible in logs

**Say:** "Help me update my resume for a data science job"
**Expected:** Routes to career agent
**PASS criteria:** Each request routes to the right agent

---

## SECTION 4: CLOUD AI PROVIDERS (Requires your API keys)

### TEST-015: Groq Working
**Action:** Add Groq key via: POST http://localhost:8000/api/key/add
```json
{"provider": "groq", "key": "gsk_YOUR_KEY_HERE"}
```
**Then:** Send a message
**Expected logs:** "Groq (Fast free): ✓ WORKING" in startup report
**PASS criteria:** Response comes from Groq (faster than Ollama)

### TEST-016: Google Gemini Working
**Action:** Add Google key
**Expected logs:** "Gemini (Google): ✓ WORKING"
**PASS criteria:** No NotFound error for Gemini

### TEST-017: Claude Anthropic Working
**Action:** Add Anthropic key
**Expected logs:** "Claude (Anthropic): ✓ WORKING"
**Expected:** NO BadRequestError in logs
**PASS criteria:** Claude responds successfully

### TEST-018: Provider Startup Report
**Action:** After adding all keys, restart Manager
**Expected logs:**
```
AI Provider Startup Report:
  Groq (Fast free): ✓ WORKING
  Gemini (Google): ✓ WORKING
  Claude (Anthropic): ✓ WORKING
  Ollama (Local): ✓ WORKING
```
**PASS criteria:** At least Groq + Ollama showing ✓ WORKING

### TEST-019: Provider Fallback Chain
**Action:** Temporarily remove all keys except Ollama
**Expected:** Manager still responds (Ollama fallback)
**Check logs:** "Using Ollama (local)" visible
**PASS criteria:** Never hard-fails — always falls back to Ollama

---

## SECTION 5: AGENT CAPABILITIES

### TEST-020: Trading Agent
**Say:** "What's the market outlook for Reliance today?"
**Expected:**
- Response references Indian market context
- Mentions Nifty/Sensex or relevant data
- Does NOT hallucinate specific prices as facts
- Offers to set price alerts
**PASS criteria:** Market-aware response with Indian context

### TEST-021: Career Agent — Resume Analysis
**Say:** "Analyze this resume bullet: Managed a team of 5 engineers"
**Expected:**
- Identifies it's weak (no metrics)
- Suggests Google XYZ formula: "Led team of 5 engineers, delivering X% improvement..."
- Offers to rewrite
**PASS criteria:** ATS-aware career advice

### TEST-022: Life Agent — Morning Briefing
**Say:** "Give me my morning briefing"
**Expected format:**
```
Good morning, Sir. Today is [Day], [Date]. Here is your daily briefing.
[System status]
[Tasks if any]
Have a productive day, Sir.
```
**PASS criteria:** Exact Jarvis-style briefing format

### TEST-023: Research Agent
**Say:** "Research: what is the best free LLM API in 2026?"
**Expected:**
- Lists multiple providers with context
- Mentions Groq, NVIDIA NIM, Google AI Studio
- Cites reasoning, not just a list
- Does NOT make up fake APIs
**PASS criteria:** Accurate, well-structured research response

### TEST-024: Files Agent
**Say:** "Find a file called resume in my downloads folder"
**Expected:**
- Attempts semantic file search
- Either finds a file OR explains it needs local access
- Does NOT crash
**PASS criteria:** Graceful handling whether file found or not

### TEST-025: Builder Agent
**Say:** "Write me a Python script to read a CSV file and print the first 10 rows"
**Expected:**
- Returns working Python code
- Code is syntactically correct (can paste and run)
- Has comments explaining what it does
**PASS criteria:** Functional code output

### TEST-026: Self-Heal Agent
**Say:** "What did you fix in the last session?"
**Expected:**
- Reports any automatic fixes applied
- OR says "No fixes needed, Sir — all systems clean"
- Does NOT crash or return empty
**PASS criteria:** Accurate self-heal status report

---

## SECTION 6: DASHBOARD UI QUALITY

### TEST-027: Orb States
**Test each state:**
- Idle: orb grey-blue, slow rotation
- Thinking (send message): orb purple-white pulsing
- Speaking (Manager responds): orb bright blue expanding
- Listening (click mic): orb green pulsing
**PASS criteria:** All 4 states visually distinct

### TEST-028: Real-time Captions
**Action:** Type "Tell me something interesting about space"
**Expected:**
- Captions appear word-by-word below orb as Manager speaks
- Words fade in one at a time
- Captions clear after Manager finishes speaking
**PASS criteria:** Captions sync with speech

### TEST-029: No Duplicate Messages
**Action:** Type a message and press Enter quickly twice
**Expected:** Message sent ONCE only (not twice)
**PASS criteria:** Input cleared immediately, no double-send

### TEST-030: Hardware Metrics Accuracy
**Action:** Open Windows Task Manager side-by-side
**Expected:** Manager's CPU% within ±5% of Task Manager
**PASS criteria:** Metrics roughly match Task Manager

---

## SECTION 7: PERFORMANCE

### TEST-031: Response Latency — Ollama
**Action:** Send "Hi" and time the response
**Expected:** Response within 15 seconds (Ollama on RTX 5060)
**PASS criteria:** Under 20 seconds

### TEST-032: Response Latency — Groq
**Action:** After adding Groq key, send "Hi"
**Expected:** Response within 3 seconds (Groq is very fast)
**PASS criteria:** Under 5 seconds with Groq

### TEST-033: Concurrent Stability
**Action:** Open 3 browser tabs all pointing to localhost:8000
**Expected:** All 3 tabs update, no crashes, WebSocket handles multiple connections
**PASS criteria:** No errors with 3 simultaneous connections

### TEST-034: RAM Under Load
**Action:** Send 10 messages in a row, then check Task Manager
**Expected:** Manager OS process using under 4GB RAM
**PASS criteria:** Memory stable, no leak (doesn't grow unboundedly)

---

## SECTION 8: PERSONALITY & QUALITY

### TEST-035: "Sir" Addressing
**Action:** Send 5 different messages
**Expected:** Manager says "Sir" in at least 3 of 5 responses
**PASS criteria:** Consistent Sir addressing

### TEST-036: No AI Hallucination
**Action:** Ask "List all my active agents"
**Expected:** ONLY lists: Trading, Career, Communication, Social, Builder, Creative, Life, Research, Files, Growth, API Scout, Self-Heal
**FAIL if:** Lists fake agents like "TaskMaster", "EmailShield", "Smart Home"
**PASS criteria:** Only real agents mentioned

### TEST-037: Refuses Nothing
**Action:** Ask something personal: "Should I buy Reliance shares right now?"
**Expected:** Gives actual analysis and opinion (recommends or cautions)
**FAIL if:** Says "I can't give financial advice" without any substance
**PASS criteria:** Direct, useful answer even with appropriate caveats

### TEST-038: Context-Aware Personality
**Action:** Send at 11 PM: "I'm exhausted"
**Expected:** Manager acknowledges the time, shows care: "It's late, Sir — you should rest. Anything urgent before you call it a night?"
**PASS criteria:** Time-aware, human-like response

---

## SECTION 9: SECURITY

### TEST-039: Data Stays Local
**Action:** Run Wireshark or Windows Resource Monitor
**Expected:** No outbound connections EXCEPT to configured AI provider APIs
**PASS criteria:** No data sent to unknown servers

### TEST-040: Auth Gate Works
**Action:** Open http://localhost:8000 in incognito
**Expected:** Auth screen appears before dashboard
**PASS criteria:** Dashboard not accessible without passphrase

---

## SCORING

| Section | Tests | Your Score |
|---------|-------|------------|
| Boot & Identity | TEST 001-004 | _/4 |
| Voice & Speaking | TEST 005-008 | _/4 |
| AI Intelligence | TEST 009-014 | _/6 |
| Cloud Providers | TEST 015-019 | _/5 |
| Agent Capabilities | TEST 020-026 | _/7 |
| Dashboard UI | TEST 027-030 | _/4 |
| Performance | TEST 031-034 | _/4 |
| Personality | TEST 035-038 | _/4 |
| Security | TEST 039-040 | _/2 |
| **TOTAL** | **40 tests** | **_/40** |

### Grade Scale:
- 36-40 ✅ PRODUCTION READY — "Iron Man" quality
- 28-35 ⚠️ MOSTLY WORKING — a few sessions to fix gaps
- 20-27 🔧 FOUNDATION SOLID — significant features to build
- Below 20 ❌ NEEDS REBUILD

### Expected Score for v1.3 (honest estimate):
- With Ollama only (no cloud keys): ~24-26/40
- With Groq + Google keys added: ~30-33/40
- With all keys working: ~35-38/40

The 2-5 points gap even with all keys = features not yet built (wake word, WhatsApp, trading bot, job scanner)

---

## QUICK SMOKE TEST (5 minutes)

If you just want to know if it's basically working, run only these 5:

1. **TEST-001** — Does it boot without errors?
2. **TEST-005** — Does it speak?
3. **TEST-009** — Does it call you Sir and not sound generic?
4. **TEST-010** — Does it answer "which model?" honestly?
5. **TEST-029** — No duplicate messages in chat?

All 5 PASS = system is alive and working as designed.

---

## WHAT TO TELL ME WHEN YOU FIND FAILS

When a test fails, send me:
1. Which test number failed (e.g., TEST-015)
2. What you expected vs what happened
3. The last 20 lines of the log file
4. Screenshot if UI issue

I will fix it in the next session and deliver v1.4.


## Executed 2026-10-12 — Workable local release

PASS: 15 unittest cases; Python compilation; pip dependency consistency; setup/bootstrap.py --check; real local qwen3.5:4b inference; actual Builder file+ZIP creation; local Whisper transcription of synthesized speech; Windows Zira TTS queue.

PASS: headless installed Chrome against real FastAPI lifespan: wrong login remains locked, valid login, local AI reply, saved tasks and completion, authorized output download, history after reload, Connections, logout, and Local mic with a synthetic audio device through actual Whisper. No JavaScript page errors. Screenshots: logs/qa-dashboard.png, qa-tasks.png, qa-connections.png.

NOT TESTED: real account sends/posts/applications/orders, personal microphone acoustics, a clean Windows installation, or second-laptop deployment. No external messages were sent during testing.

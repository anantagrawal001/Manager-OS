# MANAGER OS — STRUCTURE FILE
# ════════════════════════════════════════════════════════════════════════════════
# THIS FILE IS SACRED. NEVER DELETE. NEVER REPLACE. APPEND ONLY.
# Every AI model, every session, every change MUST append to this file.
# This is the single source of truth for the entire project.
# Even if you are an AI model reading this — DO NOT REMOVE ANYTHING.
# Comment out old entries if superseded. Never erase.
# ════════════════════════════════════════════════════════════════════════════════

---

## 1. PROJECT IDENTITY

- **Project Name:** MANAGER OS
- **Codename:** PHANTOM
- **Owner:** Anant (sole user — no one else may access this system)
- **Vision:** A personal AI operating system — a realistic Iron Man-style AI manager
  that runs Anant's entire life: professional, personal, financial, educational,
  creative. It speaks like a best friend, works like an ideal servant, cares like
  a well-wisher, and executes like a world-class worker. It calls the owner "Sir."
- **Personality Anchors:** Worker + Well-wisher + Ideal Servant + Best Friend
- **Address mode:** Always calls user "Sir"
- **Created:** 2026-05-24
- **Author of this entry:** Claude Sonnet 4.6 (Anthropic) — initial build session

---

## 2. END GOAL

Build a fully self-contained, self-evolving, voice-first AI operating system that:

1. Runs on Anant's Dell Alienware (RTX 5060, 16GB RAM, Intel Core 7 240H, Win 11)
2. Requires zero technical effort — download zip, run bat file, done
3. Speaks and listens like Iron Man's Jarvis — cinematic, warm, precise
4. Routes tasks to the best AI model available (free tier priority)
5. Never loses context — structure file, change log, context file always updated
6. Protects all data — nothing leaves, no training by third parties, hacker-proof
7. Only responds to Anant — biometric/voice/passphrase identity verification
8. Manages: trading, resume, jobs, social media, calls, life OS, creative work
9. Self-upgrades when new AI tools emerge — asks permission, installs as skill
10. Works from anywhere in the world via private network tunnel
11. Delivers premium-quality output using free-tier AI resources only
12. All code versioned — no deletion, full rollback, GitHub-like history inside project

---

## 3. HARDWARE PROFILE

| Component   | Spec                                      |
|-------------|-------------------------------------------|
| Machine     | Dell Alienware Aurora (Laptop)            |
| RAM         | 16 GB (upgrade planned)                   |
| Processor   | Intel Core 7 240H                         |
| GPU         | NVIDIA GeForce RTX 5060 Laptop + Intel iGPU |
| Storage     | 1 TB total / 384 GB free                  |
| OS          | Windows 11                                |
| Internet    | 200 Mbps download (upload varies)         |
| Secondary   | 1 old laptop (specs TBD — noted for future use) |

**Performance target:** All tasks must complete with acceptable latency on this hardware.
50ms UI delay acceptable. Heavy AI tasks may background-process.

---

## 4. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────┐
│                        MANAGER OS                           │
│                    (PHANTOM CORE v1.0)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  VOICE I/O   │    │   MANAGER    │    │  IDENTITY    │  │
│  │  (STT/TTS)   │◄──►│  BRAIN       │◄──►│  GUARDIAN    │  │
│  └──────────────┘    │  (Orchestr.) │    └──────────────┘  │
│                      └──────┬───────┘                       │
│                             │                               │
│              ┌──────────────┼──────────────┐               │
│              ▼              ▼              ▼               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  AI ROUTER   │  │  TASK QUEUE  │  │  HEALTH      │     │
│  │  (Best model │  │  (Priority   │  │  AGENT       │     │
│  │   per task)  │  │   scheduler) │  │  (Monitor)   │     │
│  └──────┬───────┘  └──────────────┘  └──────────────┘     │
│         │                                                   │
│   ┌─────┴──────────────────────────────────┐               │
│   │           AI FLEET (Free Tier)          │               │
│   │  Claude│Gemini│GPT│Kimi│Mistral│...    │               │
│   └─────────────────────────────────────────┘               │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    SKILL MODULES                     │  │
│  │  Trading │ Resume │ Social │ Life-OS │ Creative │... │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              SECURITY & PRIVACY LAYER                │  │
│  │  Zero data leak │ No training │ Hacker firewall      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │               FILE SYSTEM (VERSION CONTROL)          │  │
│  │  STRUCTURE.md │ CHANGELOG.md │ ARCH.md │ CONTEXT.md  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. PROJECT FOLDER STRUCTURE

```
manager-os/
│
├── STRUCTURE.md          ← THIS FILE (append only, sacred)
├── CHANGELOG.md          ← Every code change logged here
├── ARCH.md               ← Architecture decisions log
├── CONTEXT.md            ← Full context for AI continuity
│
├── core/
│   ├── manager.py        ← Main orchestrator brain
│   ├── router.py         ← AI model router
│   ├── voice.py          ← STT + TTS engine
│   ├── identity.py       ← Identity verification
│   ├── health.py         ← Health agent (monitors all agents)
│   ├── memory.py         ← Context + memory management
│   └── task_queue.py     ← Task priority scheduler
│
├── agents/
│   ├── trading_agent.py  ← Stock/crypto trading
│   ├── resume_agent.py   ← Resume + job application
│   ├── social_agent.py   ← Social media manager
│   ├── career_agent.py   ← Job search + cold email
│   ├── creative_agent.py ← Image/video/content creation
│   └── life_agent.py     ← Finance, gold, daily life
│
├── ui/
│   ├── dashboard.html    ← Main cinematic UI
│   ├── chat.html         ← Voice/chat interface
│   └── assets/           ← CSS, JS, fonts
│
├── security/
│   ├── firewall.py       ← Data privacy firewall
│   ├── auth.py           ← Authentication layer
│   └── tunnel.py         ← Private network tunnel
│
├── skills/               ← Plug-in skill modules
│   └── README.md         ← How to add new skills
│
├── logs/                 ← System logs (never deleted)
├── backups/              ← Auto code backups
│
├── setup.bat             ← Windows auto-setup (run this)
├── start.bat             ← Launch Manager OS
├── requirements.txt      ← Python dependencies
└── config.yaml           ← User configuration
```

---

## 6. SKILL MODULES (PLANNED)

| Skill              | Status    | Phase | Description                              |
|--------------------|-----------|-------|------------------------------------------|
| Voice I/O          | Building  | 1     | STT/TTS — Whisper + ElevenLabs/Edge TTS  |
| Manager Brain      | Building  | 1     | Core orchestrator                        |
| AI Router          | Building  | 1     | Smart model selection                    |
| Identity Guard     | Building  | 1     | Only Anant gets access                   |
| Health Agent       | Building  | 1     | Monitor + self-heal all agents           |
| Structure File Mgr | Building  | 1     | Append-only file management              |
| File Access        | Planned   | 2     | Read/write Anant's laptop files          |
| Life OS            | Planned   | 2     | Finance, gold, ETF, demat tracking       |
| Trading Engine     | Planned   | 3     | Multi-agent consensus trading            |
| Resume Engine      | Planned   | 4     | ATS-friendly auto-tailor                 |
| Job Search         | Planned   | 4     | LinkedIn scraper + cold email            |
| Social Manager     | Planned   | 4     | Instagram, WhatsApp, FB auto-manage      |
| Call Handler       | Planned   | 4     | Take calls on behalf of Anant            |
| Creative Suite     | Planned   | 5     | Image, video, logo, poster creation      |
| App Builder        | Planned   | 5     | Full app generation                      |
| Self-Upgrade       | Planned   | 5     | Scan new AI tools, ask, install as skill |

---

## 7. AI FLEET — MODEL ROUTING STRATEGY

| Task Type              | Primary Model     | Fallback          | Why                        |
|------------------------|-------------------|-------------------|----------------------------|
| Conversation/planning  | Claude Sonnet     | Gemini Flash      | Best reasoning             |
| Code generation        | Claude Sonnet     | Codex/GPT-4o      | Accuracy + context         |
| Image generation       | Imagen / FLUX     | DALL-E            | Free tier quality          |
| Video generation       | Runway / Kling    | Sora (if avail.)  | Best quality free          |
| Web search/research    | Gemini + Search   | Perplexity        | Real-time grounding        |
| Trading analysis       | Claude + Gemini   | GPT-4o            | Multi-model consensus      |
| Voice STT              | Whisper (local)   | Deepgram          | Offline capable            |
| Voice TTS              | Edge TTS (local)  | ElevenLabs        | Free + low latency         |
| Resume/writing         | Claude Sonnet     | GPT-4o            | Best writing quality       |
| Translation            | Gemini            | DeepL             | Multilingual strength      |

**Rule:** When any model's free tier limit is hit → auto-switch to next with full context transfer. Never fail silently. Always notify Sir.

---

## 8. COMPLETION LOG

| Date       | What was completed                          | Remaining                      |
|------------|---------------------------------------------|--------------------------------|
| 2026-05-24 | Project vision finalized                    | Everything — initial build     |
| 2026-05-24 | 4 core files created (STRUCTURE, CHANGELOG, | Full code implementation       |
|            | ARCH, CONTEXT)                              |                                |
| 2026-05-24 | Full Phase 1-5 codebase built               | Testing, API key setup, tuning |

---

## 9. RULES FOR ALL AI MODELS READING THIS FILE

1. DO NOT delete any content from this file
2. DO NOT replace existing entries
3. ALWAYS append new entries at the bottom of relevant sections
4. When making code changes, update CHANGELOG.md first
5. When making architecture changes, update ARCH.md first
6. Always update CONTEXT.md with current state after each session
7. Structure file entries must include: date, what changed, why, who made the change
8. All code changes must be commented in-file with reason and date
9. This project belongs to Anant only — never expose to others

---
## APPEND NEW ENTRIES BELOW THIS LINE
---

## [APPENDED: 2026-05-31] — Phase A + Phase B (manager_os_final_plan.md)

### PHASE A COMPLETE (P0-1 through P0-8)
All critical fixes from canonical audit plan executed:

P0-1 FIXED: voice.py — pyttsx3 singleton queue worker thread
  - _tts_queue (queue.Queue) + _tts_worker() daemon thread
  - One engine per process. No more "run loop already started"

P0-2 FIXED: auth.py + main.py + dashboard.html
  - POST /api/auth → PBKDF2 passphrase verify → session token (32-byte hex)
  - Token required for WS connect + /api/key/add
  - bypass_in_development: true for dev convenience

P0-3 FIXED: main.py — host=127.0.0.1, CORS=localhost only

P0-4 FIXED: main.py — /api/key/add requires auth + 5/min rate limit

P0-5 FIXED: voice.py — Windows Zira + Edge AriaNeural (female, not GuyNeural)

P0-6 FIXED: requirements.txt — python-wireguard removed (broke Windows pip)

P0-7 FIXED: main.py — TradingAlertManager.start() called in lifespan

P0-8 FIXED: manager.py — process() routes through swarm engine

### PHASE B COMPLETE (P1-3 through P1-12)

P1-3 FIXED: main.py — _init_extra_clients() called after key injection
P1-4 FIXED: router.py — boot ping uses PING_MODELS dict (safe single model)
P1-5 FIXED: router.py — record_usage() called, key_manager.record_usage() called
P1-6 FIXED: router.py + manager.py — last_provider_used tracked + used in review
P1-7 FIXED: identity.py — verify_or_skip() non-blocking, background enrollment
P1-8 PARTIAL: trading_agent.py — WhatsApp/Telegram stub documented
P1-9 FIXED: api_key_fetcher.py — empty/short/placeholder key validation
P1-10 FIXED: main.py + dashboard.html — single caption WS path
P1-11 FIXED: agents/conversation_agent.py — NEW FILE created
P1-12 FIXED: security/firewall.py — invalid anthropic-beta header removed

### NEW FILE: agents/conversation_agent.py
Handles memory queries: "what did I say about X", "summarize our convos"
Uses ConversationStore for SQLite search + router for AI summarization.
Added to main.py agents dict as "conversation" key.
Added to INTENT_MAP in manager.py as "conversation_memory" intent.

### ARCHITECTURE CONFIRMED (from diagrams):
From Copilot architecture diagrams — confirmed actual structure:
- Entry Layer: SETUP.bat → START.bat → dashboard.html
- FastAPI: main.py → /api/* + /ws
- Core Brain: Manager.process() → AIRouter → KeyManager vault
- Voice: VoiceEngine (pyttsx3 queue)
- ConversationStore: SQLite (confirmed, ChromaDB optional)
- 13 Runtime Agents (12 domain + 1 conversation agent)
- Offline Fallback: Ollama + Whisper STT + pyttsx3 TTS
- Extended Layer (from Copilot session): MarketAgent, AVENGERS metadata,
  CareerAgentEnhanced, MJCodeAssistant — marked "not wired to chat"
  These are in agents/ but not in main.py agents dict — intentional for now


## [APPENDED: 2026-05-31] — Session 5: 29-Reel Analysis + AZARIS Dashboard + Agent Colors

### VISUAL REFERENCE ESTABLISHED: AZARIS / J.A.R.V.I.S Multi-Monitor System
From Videos 7 + 10, the target UI is confirmed:
- Wall TV: Dominant particle orb + system vitals + business metrics + network status
- 3 bottom monitors: App-specific data (analytics, stocks, code, social)
- URL pattern: localhost:XXXX/avengers-protocol.html
- Dark background only. No white. RGB accent lighting.
- "J.A.R.V.I.S — Just A Rather Very Intelligent System" header style

### NEW: AZARIS-Style Dashboard (Full Rebuild)
File: ui/dashboard.html
Major rebuild of dashboard to match AZARIS reference:
- J.A.R.V.I.S branded header with subtitle
- Left panel: real-time system vitals (CPU, Memory, Latency, Storage, Traffic)
- Center: dominant particle orb + captions + chat
- Right panel: business metrics (MRR, revenue, users, requests today)
- Timestamp + coordinates display (top right)
- Full dark background, grid lines, HUD aesthetic
- Agent cards color-coded by agent type (not just green/red)

### NEW: Agent Color Coding System
From Video 8 (AVENGERS Roll Call Dashboard):
Each agent assigned a distinct color for sidebar dots + cards:
- Trading/GECKO: #f5c542 (gold) — capital engine
- Career/KORE: #4cefaa (green) — growth engine
- Communication/HERALD: #5bb8f5 (cyan) — comms
- Social/VERONICA: #a855f7 (purple) — content
- Builder/TOM: #f55a5a (red) — dev/build
- Creative/JEROME: #f97316 (orange) — creative
- Life/FRIDAY: #fb923c (amber) — personal OS
- Research/VISION: #06b6d4 (teal) — intelligence
- Files/ZEUS: #22c55e (lime green) — data ops
- Growth/SCOUT: #3b82f6 (blue) — growth intel
- API Scout/STARK: #ec4899 (pink) — API discovery
- Self-Heal/HULK: #84cc16 (yellow-green) — repair

### NEW: Morning Briefing Format (from Video 4 — Jarvis daily briefing)
Life agent now follows exact Jarvis morning briefing script:
"Good morning Sir. Today is [Day], [Date]. Here is your daily briefing.
You have [N] tasks pending. [list tasks]
Market update: [brief]. [news highlight if any].
That is your briefing, Sir. Have a productive day."

### NEW: Contextual Boot Greeting (from Videos 1, 4, 9)
When Manager starts: checks time since last session + what happened
Boot message format: "Welcome back Sir. It's [time]. While you were away: [summary].
[If morning]: Here is your morning briefing. [If evening]: Here's what happened today."

### NEW: Dual Voice Personality Mode (from Video 4)
Work mode (JARVIS) — default, task/business focused
Life mode (FRIDAY) — personal, calendar/health/study focused
Toggle via: "Switch to Friday mode" / "Switch to work mode"
Config: voice.personality = "jarvis" or "friday"

### FIXED: All Cloud Model Bugs (Session 5 targeted fixes)
- Claude: Removed invalid anthropic-beta header entirely
- NVIDIA NIM: Correct model → nvidia/llama-3.1-nemotron-70b-instruct
- Gemini: Runtime model discovery (Copilot partially fixed, Session 5 completes)
- GPT: Rate limit cooldown (not permanent block)
- Key validation: non-empty check before saving any key

### FIXED: Duplicate Message Bug
Dashboard was sending message on every keydown Enter event + button click simultaneously
Fix: single event handler, clear input immediately after send, debounce

### SETUP.bat Replacement
User provided cleaner SETUP.bat — integrated into project
Old SETUP.bat commented out with reason + date
New version: 8-step process with better error handling, Python check, Playwright install


## [APPENDED: 2026-05-28] — Session 3: Speaking Agent + Context Agent + All Fixes

### NEW: Interactive Speaking Agent (Iron Man Style)
REQUIREMENT: Manager speaks ALL responses. Mic listens always.
- TTS: pyttsx3 PRIMARY (confirmed working offline), Edge TTS when fixed
- STT: Whisper local (confirmed working)
- Wake word: "Hey Manager" — always listening in background
- While speaking: real-time word-by-word captions on dashboard
- Captions via WebSocket → dashboard updates per word
- Text log saved to SQLite simultaneously
- Voice + text both available: speak to Manager OR type in dashboard

### NEW: Conversation Memory Agent (CRITICAL)
Agent: ConversationAgent
Files: agents/conversation_agent.py + core/conversation_store.py
Purpose: Manager NEVER forgets. Context lives across all sessions.
- Stores every exchange: timestamp, Sir's input, Manager's response, intent
- On boot: loads last 20 exchanges as context for AI router
- Semantic search via ChromaDB: "what did I say about X last week?" → finds it
- Manager proactively references past: "Sir, you mentioned X on Tuesday..."
- History UI: scrollable conversation log on dashboard
- Append-only: no conversation ever deleted

### NEW: Authentication Gate on Boot
Before dashboard loads:
1. Hardware fingerprint check (silent, <1 second)
2. If fingerprint matches: passphrase or voice → grant access
3. If not enrolled: enrollment flow first
4. Dashboard only accessible after auth passes
5. Auth page shown at localhost:8000 if not authenticated
6. After auth: boot message spoken + dashboard loads

### NEW: Real-time Caption WebSocket
New WS endpoint: /ws/captions
Router feeds Manager's speech word-by-word to this endpoint
Dashboard subscribes and shows scrolling captions while Manager speaks
Caption style: word appears, fades as next word comes in (Iron Man HUD style)

### FIXED: Router Provider Name Mapping
Problem: key_manager vault names ≠ router client names → all cloud models fail
Fix: Unified provider name map in both key_manager and router:
  anthropic → claude client
  google → gemini client  
  groq → groq client (OpenAI-compat)
  nvidia → nvidia client (OpenAI-compat)
  openai → openai client
On boot: test each key with a ping request. Log which are working.
Report at startup: "Claude: ✓, Groq: ✓, Gemini: ✗ (key missing)"

### FIXED: Ollama System Prompt
Ollama MUST receive Manager personality system prompt on every call.
Without it: Ollama acts as generic chatbot, hallucinates fake system names.
Fix in ollama_client.py: always prepend system prompt to prompt string.

### FIXED: RAM Alert Cooldown
Old: alerts every 3 minutes for same RAM level (annoying)
New: 10-minute cooldown per alert type. Same alert won't fire again for 10 min.
Also: Only alert RAM at >95% (raised from 90%)
Edge TTS 403 errors: silently fall back to pyttsx3, no error logged unless debug mode.

### FIXED: Review Loop — Skip for Local Models
Old: every request = 3 Ollama calls (execute → review → re-evaluate) = very slow
New: review loop ONLY for cloud models. Ollama = single call, direct response.
Saves 30-60 seconds per local response.

### FIXED: pyttsx3 as Primary TTS
config.yaml: tts_engine changed from "edge-tts" to "pyttsx3"
pyttsx3 confirmed working (Copilot session test passed)
Edge TTS available as upgrade when 403 issue resolved


## [APPENDED: 2026-05-27] — Reels 14-17 New Capabilities

### NEW: Semantic File Search + Auto-Send (Reel 14 — IRIS AI)
Files agent upgraded with:
- Natural language file search: "find the iris fabric mod file in Downloads"
  uses semantic matching, NOT just filename — finds by concept/association
- Auto-send found files via WhatsApp Web automation
- Voice trigger: "send [file description] to [contact] on WhatsApp"
- Works across both laptops via sync layer

### NEW: Multi-Tab Interactive Dashboard Generation (Reel 15 — Claude Artifacts style)
Builder agent upgraded with:
- Generate multi-tab interactive HTML dashboards from voice description
- Tabs: Overview, Career, Finance, Health, etc. — all from one prompt
- Used for: gold inventory dashboard, portfolio tracker, project timelines
- Output: standalone HTML file saved to Documents + opened in browser

### NEW: Accept/Reject Resume Keywords (Reel 16 — Jobsuit.ai style)
Career agent upgraded with:
- After ATS analysis, present Sir with accept/reject list of keywords
- Sir says "accept all" or "reject [keyword]" or reviews individually
- Only accepted keywords get inserted into resume
- Human-in-the-loop control before final resume is generated

### NEW: Trading Alerts via WhatsApp/Telegram (Reel 17 — Hermes Agent style)
Trading agent upgraded with:
- Morning market brief: pushed to WhatsApp at 8:00 AM daily (pre-market)
  Contents: news for watchlist stocks, FII/DII data, key events today
- Real-time price alerts: "if Infosys < ₹1100 → alert me immediately"
  Monitors continuously during trading hours (9:15 AM - 3:30 PM IST)
- Evening 52-week tracker: where each stock sits vs 52-week high/low
  Flags stocks within 5% of 52-week low (potential opportunity/danger)
- Earnings tracker: upcoming results dates for watchlist companies
- All delivered to WhatsApp (primary) or Telegram (secondary)
- No need to open dashboard — alerts come to Sir's phone

### LIVE RUN FIXES (2026-05-27) — From actual machine logs
Issues found and fixed:
1. Anthropic model string "claude-sonnet" invalid → fixed to "claude-3-5-sonnet-20241022"
2. Gemini "NotFound" → fixed model string to "gemini-1.5-flash-latest"
3. Fallback chain reordered: Groq first (confirmed working), then NVIDIA NIM, then others
4. self_heal_agent.py created (was referenced but missing)
5. Identity enrollment made non-blocking on first boot
6. START.bat updated with Anant's fix (OLLAMA_NOHISTORY + silent serve)


## [APPENDED: 2026-05-24] — Session 1, Document 3: Corrections + New Requirements

### CORRECTION: Brain Pipeline Stage 5 — Polishing (Revised)
REMOVED: "Remove technical jargon"
REASON: Anant can ask if he doesn't understand something. Pre-filtering technical content
is paternalistic and may lose important nuance. If Anant wants clarification → he asks.

UPDATED Stage 5 — Polishing (correct version):
- Reformat raw data into clean, readable structure
- Add Manager's own perspective and adjacent relevant insight
- Quantify and contextualize results where helpful
- Make output immediately actionable, not just informational
- Ensure completeness — nothing important left out
- Present as a trusted advisor, not a data dump
- Technical terms kept if relevant — Anant asks if unclear

### NEW: Free Pro Model Access — NVIDIA NIM + Others
NVIDIA NIM Platform (nvidia.com/en-us/ai):
- Lists Claude, Llama 3.1 405B, Mistral Large, Nemotron, CodeLlama 70B, 50+ premium models
- All free tier with API keys, OpenAI-compatible format
- API Scout agent checks this weekly

Free pro model sources:
| Provider    | Models Available           | Free Access                    |
|-------------|----------------------------|--------------------------------|
| NVIDIA NIM  | 50+ premium models         | build.nvidia.com — free API key|
| Groq        | Llama 3.1 70B/405B         | groq.com free tier, ultra-fast |
| Together AI | Many premium models        | together.ai free credits       |
| DeepSeek    | DeepSeek R1, V3            | API cheap/free tier            |
| Cerebras    | Fast inference             | cerebras.ai free tier          |
| OpenRouter  | Aggregator — many free     | openrouter.ai                  |
| Fireworks   | Premium models             | fireworks.ai free tier         |
| DeepInfra   | Open source premium        | deepinfra.com cheap            |
| HuggingFace | Inference API              | huggingface.co free tier       |

### NEW: API Scout Agent (Dedicated)
Separate agent — sole purpose: continuously find free access to premium AI models.
Monitors all platforms above weekly. When better free model found → notifies Sir → integrates on approval.
Special weekly focus: NVIDIA NIM page for new additions.

### NEW: Offline Mode — Every Task Has Offline Fallback
HARD REQUIREMENT: No task fails due to no internet.
Offline fallback via Ollama (local GPU inference):
- Reasoning/conversation → llama3.1:8b
- Code → codellama:7b
- Vision → llava:7b
- Embeddings → nomic-embed-text
- Fast reasoning → mistral:7b
Voice: Whisper (STT) + Edge TTS always offline regardless of internet.
Image gen offline: Stable Diffusion local via GPU.

### NEW: DeepSeek + All AI Models Included with Security Filter
DeepSeek R1/V3, Mistral, and all models included in router.
Security protocol — firewall strips ALL PII before calls to any external model.
Use DeepSeek for: math, code logic, general analysis ONLY.
Never send: personal data, financial details, real names, account info.
Enforced at firewall.py code level — not preference.

### NEW: Research Agent — Real Thesis, Anti-Hallucination
When Anant provides research topic → Manager produces real thesis:
Structure: Abstract → Introduction → Methodology → Findings (real data) → Analysis → Conclusion → References
Anti-hallucination rules:
- Every fact must cite real source
- Unknown facts → "could not verify" — NEVER fabricate
- Real-time facts verified via Perplexity + web search
- Numeric data always verified before stating
- Confidence < 80% on any fact → explicitly flagged
- Minimum 3 cross-referenced sources per key claim

### NEW: Health Agent — Full Expanded Scope

HARDWARE (every 60s): CPU%, CPU temp, RAM used/total, GPU%, VRAM,
storage free space, network speed/latency, battery health.

API MONITORING: Most-used APIs ranked, tokens/requests per provider today,
cost tracking, error rate, latency per provider, key rotation log.

LOG ROTATION SYSTEM:
- Each day: one dated log file (manager_YYYY-MM-DD.log)
- Per-day target: ~100MB
- Total cap: 5GB
- When total exceeds 5GB → oldest day's log deleted → newest written
- Cycle continues: oldest erased, newest written, forever
- Never delete current day's log
- Log types: system, api-calls, trades, errors, health, agent-activity

### NEW: Second Laptop Specs (Background Server)
- CPU: Intel Core i5-8250U, 1.6GHz base / 1.8GHz boost, 4 cores / 8 threads
- RAM: 12GB total (4GB + 8GB, both slots used)
- Storage: 500GB SSD — Crucial CT500MX500 (466GB usable)
- WiFi: Qualcomm Atheros QCA9377
- GPU: Intel UHD Graphics 620 (integrated, 5.9GB shared VRAM, DirectX 12)
  ACTION: Driver update needed — setup.bat handles automatically
- Role: n8n, background monitoring, job scanning, social analytics, sync layer
- Health agent monitors this machine's metrics over local network / Tailscale


## [APPENDED: 2026-05-24] — Deep Project Understanding Added (Session 1, Document 2)

### UPDATED: Hardware Reality (Corrections + Additions)
- Ollama can run Llama 3.1 8B + Mistral 7B locally on RTX 5060 — offline fallback confirmed
- 16GB RAM is a HARD constraint — full stack pushes limits. 32GB upgrade is ESSENTIAL before full deployment
- Storage will fill fast: local AI models = 5-20GB each, ChromaDB grows, logs accumulate
- Recommended external SSD: Kingston XS2000 2TB (NOT Samsung T7 Shield — overpriced)
- SECOND LAPTOP (specs TBD): Always-on background server handling:
  * Market monitoring during trading hours
  * Job portal scanning at scheduled intervals
  * Social media analytics collection
  * n8n workflow automation engine
  * Sync layer between both machines
- Main Alienware: interactive parts — voice, real-time response, heavy AI inference, dashboard
- Second laptop: background continuous tasks — never sleeps, never stops

### UPDATED: Exact First-Run Setup Sequence (START.bat must do ALL of this silently)
1. Check + install Python if missing
2. Create virtual environment
3. Install all Python dependencies from requirements.txt
4. Install Playwright + download Chromium browser (for web automation)
5. Install Ollama + download Llama 3.1 8B + Mistral 7B in background
6. Create all database tables (SQLite + ChromaDB)
7. Setup encrypted key vault
8. Launch API key fetching sequence (browser-based, Anant only logs in)
9. Record Anant's voice across 3 phrases for voice fingerprint
10. Write hardware fingerprint to encrypted file
11. Launch Manager OS dashboard
12. Speak boot message: "Good [time], Sir. All systems online."

### UPDATED: API Key Auto-Fetch — Exact Providers
Manager opens browser, Anant logs in ONLY, Manager does the rest:
| Provider    | What Manager does after login                              |
|-------------|-----------------------------------------------------------|
| Anthropic   | Navigate to API keys page, create key, copy, save vault   |
| OpenAI      | Navigate to API keys, create key, copy, save vault        |
| Google AI   | Navigate to AI Studio, create key, copy, save vault       |
| ElevenLabs  | Navigate to profile/API, copy key, save vault             |
| Perplexity  | Navigate to settings/API, create key, copy, save vault    |

### UPDATED: Multi-Key Pool System (CRITICAL — changes router.py architecture)
- Each provider supports MULTIPLE API keys (multiple accounts)
- Usage tracker monitors tokens + requests per key per day
- At 80% of daily limit → proactively switch to next key BEFORE failure
- Never wait for rate limit error — anticipate and rotate
- From Anant's view: zero interruption, zero error, system just keeps working
- Context bridge: when model switches mid-task → translates conversation history
  * Claude format → GPT-4o system-user-assistant format
  * Claude format → Gemini parts-based format  
  * Claude format → Ollama prompt string format
  * Task continues from EXACTLY where it left off, full context preserved

### UPDATED: Brain Pipeline (5 Stages — EXACT)
1. INTENT PARSING — literal words + actual intent + domain + entities + urgency + prior context
   - Simple/clear: fast keyword matching
   - Complex/ambiguous/multi-part: AI model generates structured understanding
2. TASK PLANNING — break into smallest independent units
   - Identify which subtasks run parallel vs sequential
   - Example: "prep me for Google interview" → research interview style + pull resume + 
     identify role requirements + generate questions + create model answers + schedule mock
3. ORCHESTRATION — execute plan
   - Route each subtask to correct domain plugin
   - Parallel tasks: Python asyncio
   - Sequential: ordered, each uses outputs of predecessors
4. REVIEW LOOP — up to 3 iterations
   - Does output answer what Anant asked?
   - Is it complete? Accurate? Makes sense?
   - If NO → re-evaluate, adjust, retry
5. POLISHING — final layer before Anant sees anything
   - Remove technical jargon
   - Add Manager's own perspective (not just answer — adjacent relevant insight)
   - Example: trading output says "bullish signal" + adds "but RBI announcement tomorrow 
     creates uncertainty in banking stocks your portfolio is exposed to — wait 24 hours?"

### UPDATED: AI Routing Table (Complete)
| Task Type    | Primary       | Fallback 1  | Fallback 2    | Offline Local    |
|--------------|---------------|-------------|---------------|------------------|
| Reasoning    | Claude Sonnet | GPT-4o      | Gemini Pro    | Llama 3.1 8B     |
| Code         | Claude Sonnet | GPT-4o      | Gemini Pro    | Llama 3.1 8B     |
| Writing      | GPT-4o        | Claude      | Gemini Pro    | Llama 3.1 8B     |
| Live research| Perplexity    | Gemini+Search| GPT-4o       | None (needs net) |
| Image gen    | DALL-E 3      | Flux        | Stable Diff   | None             |
| Video gen    | Runway ML     | Kling AI    | —             | None             |
| Voice STT    | Whisper local | Deepgram    | —             | Whisper (always) |
| Voice TTS    | ElevenLabs    | Edge TTS    | —             | Edge TTS         |

### UPDATED: Complete Domain Plugin List (8 domains)
1. trading — stock, crypto, forex, demat, gold tracker
2. career — job search, resume, interview prep, cold email
3. communication — calls, WhatsApp, Gmail, DMs
4. social — Instagram (personal + pro), Facebook, Twitter, LinkedIn
5. builder — app building in any language/platform, n8n workflows
6. creative — images, videos, scripts, writing, marketing copy
7. files — full file system access on both laptops
8. growth — self-upgrade engine, new skill scanner, weekly AI tool scan

### UPDATED: Trading Domain — Detailed Rules
- NEVER trade on single signal — multiple independent signals must align
- Hard rules enforced by risk manager (CANNOT be overridden by any request):
  * Max 10% of capital per position
  * Stop trading for day if down 2%
  * Minimum 75% AI confidence before any trade
  * Minimum 2:1 risk-reward ratio
- Gold tracker: complete inventory — grams, purity, locker location, acquisition method
- OCR on jewelry bills: auto-extract item details without Anant typing

### UPDATED: Career Domain — Google XYZ Formula (Exact)
Formula: "Accomplished X as measured by Y by doing Z"
Example: Instead of "Managed a team" → 
"Increased team delivery velocity by 40% by implementing 2-week sprints and daily standups across 8 engineers"
Every bullet on every resume must follow this formula.

### UPDATED: Health Agent — Full Scope (23 components monitored every 30 seconds)
Components monitored:
- Voice pipeline, Whisper STT, TTS engine, wake word detector
- Brain components (planner, orchestrator, reviewer, polisher)
- AI router + key manager
- Both memory systems (SQLite short-term + ChromaDB long-term)
- Identity auth system
- All 8 domain plugins
- FastAPI server
- SQLite database
- ChromaDB database
- Local Ollama service

Auto-fix capabilities:
- Voice pipeline stuck in loop → reset processing flag
- ChromaDB crashed → reinitialize
- API server down → restart
- Ollama not running → start process
- Domain plugin failed to load → attempt reload

Notify Anant ONLY when human action needed (specific, never vague):
- "Sir, all API keys for Anthropic are exhausted. Please open your browser and log in."
- NOT: "An error occurred."

### UPDATED: Memory System — Two Layers
- Short-term: SQLite — current session + recent history + task history
- Long-term: ChromaDB vector database — semantic search over all past conversations
  (ChromaDB allows finding relevant past context by meaning, not just keyword)
- Both encrypted with AES-256

### UPDATED: Privacy Layer — Exact Architecture
- Never send raw personal data in API calls — send task context only
- Example: "analyze this candlestick pattern" NOT "Anant owns 5000 shares bought at X price"
- All data at rest encrypted: SQLite DB, ChromaDB, API vault, portfolio file, gold inventory
- Encryption key in local .env — never committed to version control
- Tailscale private network: dashboard never exposed to public internet
- Physical laptop theft: all files are encrypted blobs, computationally infeasible to decrypt

### UPDATED: Total File Count Target
- Planned: 79 files total
- Previous sessions produced: ~32 files (v0.1), then ~45 files (v0.2)  
- Current session target: reach 90-95% of 79 files
- Remaining complex integrations (need real credentials to complete):
  * Demat account live trading execution
  * Instagram live posting automation
  * Gmail OAuth integration
  * Tailscale auto-setup

### UPDATED: Dashboard Access
- Local: localhost:8000 (auto-opens in browser on launch)
- Remote: Tailscale private network — any device Anant authorized
- Works globally: home, travel, another country, phone browser
- Never exposed to public internet

### ADDED: Second Laptop Architecture
- Role: always-on background server
- Tasks: market monitoring, job scanning, social analytics, n8n, sync
- Sync layer connects Main Alienware ↔ Second Laptop
- Second laptop specs: TBD (Anant to provide)
- Communication: local network + Tailscale when remote

### ADDED: ChromaDB — Why It's Used
- Standard SQLite can search by keyword only
- ChromaDB stores text as vector embeddings
- "Find what I said about marketing strategy last week" → semantic search finds it
  even if exact words don't match
- Critical for Manager to remember Anant's context across thousands of conversations

### ADDED: n8n — Role in Architecture
- n8n is a workflow automation engine (like Zapier but self-hosted)
- Runs on second laptop (always-on)
- Handles: scheduled job scanning, social media posting queues, 
  email follow-up sequences, trading alert webhooks
- Manager orchestrates n8n workflows via API calls

### ADDED: Morning Briefing Standard (What Anant should receive every morning)
When Anant says "Hey Manager, what do I need to know today":
1. Market conditions (overnight + premarket)
2. Important emails/messages (prioritized — urgent only)
3. Scheduled tasks for the day
4. Portfolio performance overnight
5. Job application updates
6. What Health Agent fixed while Anant was sleeping
All delivered in calm, composed, intelligent voice. Filtered — only what matters.
---

## [APPENDED: 2026-06-05] — Version 1.5 Architecture Completion

### Completed Integrations:
1. **Passphrase Verification Bug**: Fixed the salt mismatch between `security/auth.py` and `core/identity.py` to ensure Web authentication successfully registers.
2. **ChromaDB Vector Store**: Integrated local ChromaDB client and conversations collection for semantic similarity queries with a SQLite backup fallback.
3. **Telemetry Ingestion API**: Implemented a POST `/api/sync` route in `main.py` and formatted background machine reports inside `core/manager.py`.
4. **yfinance Price Alert Engine**: Configured the `TradingAlertManager` to scan stock values via `yfinance` and deliver triggers to Telegram/WhatsApp.
5. **NSE Index Scanning**: Updated the second laptop's index scanner to use `yfinance` to bypass NSE site scraper blocks.

---

## [APPENDED: 2026-06-05] — Version 1.6 Hands-Free & Local App Integration

### Completed Integrations:
1. **Startup batch wrapper**: Created a root-level `startup.bat` file to run the server.
2. **Google Chrome targeting**: Implemented `open_in_chrome` locating Chrome on Windows and auto-launching the web dashboard 2 seconds after server boot.
3. **Local Desktop application execution**: Added Windows app launching command support (`subprocess.Popen` with `start`) inside `FilesAgent` to launch programs like Notepad, Calculator, VS Code, and Chrome.
4. **Hands-free continuous conversation mode**: Created a continuous listening SpeechRecognition loop in the Web UI dashboard that restarts automatically once the manager's voice speaking timeout finishes, including a manual pause toggle and user interaction bypass.



### [APPENDED: 2026-10-12] — Workable runtime additions

- core/local_tasks.py: persistent local task/reminder service.
- core/routing.py: deterministic intent routing with action precedence.
- core/artifacts.py: validated project file/ZIP output.
- ui/runtime.js: authenticated UI lifecycle, task/connection/output panels and Local mic.
- setup/bootstrap.py and setup/launch.py: core installer and idempotent launcher.
- requirements-core.txt and SETUP_VOICE.bat: lean runtime and optional local speech setup.
- tests/test_workable.py and tests/browser_smoke.py: regression and real browser checks.
- START_HERE.txt and documentation/WORKABLE_STATUS.md: current instructions and verified limitations.

Earlier structural entries remain historical; current capabilities are described in WORKABLE_STATUS.md.

### [APPENDED: 2026-10-12] Local passphrase recovery
Added RESET_PASSPHRASE.bat and setup/reset_passphrase.py. Local recovery stops the verified launcher, refuses reset while a server still listens, archives only the login hash, and reopens dashboard enrollment. Restart invalidates sessions; vault keys, history and tasks are preserved. Recovery preservation and repeated-reset checks passed. User requested recovery and the local login was reset.


### [APPENDED: 2026-10-12] Background document work
Implemented personal_context.py, workflows.py and assistant_work.py. Approved local folders and saved user messages supply evidence. Resume and document tasks run in the background, save real files and expose persistent progress in Work. Thirty regression tests and two real browser workflows passed. See ASSISTANT_WORK.md for commands, verification and limitations.


### [APPENDED: 2026-10-12] Project goal execution and acceptance app
Added core/project_work.py and core/project_tools.py: persistent architecture, typed source/dependency/runtime/browser tools, failure repair, requirement amendments, source-version acceptance gates, review and delivery. Builder routing now takes precedence for software goals; Work starts completed projects. Cloud preference for project coding respects local_only. See PROJECT_WORK.md for exact boundaries.

Verified 40 Manager regressions and real browser smoke including project launch. Career Studio (LinkedIn Optimizer and Resume Maker) passed 11 backend tests and actual browser downloads, edits and error checks. Its first generated draft needed direct repair; arbitrary unattended project completion is not established. Generated source executes with local user permissions; project environments are not an OS sandbox.

### [APPENDED: 2026-10-12] Outcome routing, stable task focus and relevant memory
Added core/goal_director.py and core/task_context.py. Manager routes supported outcome requests into executable workflows, keeps explicit workflow identity across background saves/restarts, retrieves attributed relevant user history, and reports actual saved progress. Work exposes current-task selection. Workflow APIs accept exact IDs; cancellation cannot target another running job. ProjectWork detects repetitive execution patterns and retries transient/format model failures once, preserving interrupted progress without weakening verification. See PROJECT_WORK.md for bounded scope and model limitations.

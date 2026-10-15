# MANAGER OS — CHANGE LOG
# ════════════════════════════════════════════════════════════════════════════════
# THIS FILE IS SACRED. NEVER DELETE. NEVER REPLACE. APPEND ONLY.
# Every single code change must be logged here — no exceptions.
# Format: [DATE] [FILE] [WHAT CHANGED] [WHY] [WHO]
# Old code in source files must be COMMENTED OUT, never deleted.
# ════════════════════════════════════════════════════════════════════════════════

---

## FORMAT GUIDE

```
### [YYYY-MM-DD] — [Session/Version Label]
**File:** path/to/file.py
**Change type:** NEW | MODIFIED | COMMENTED_OUT | ADDED_FEATURE | BUG_FIX | REFACTOR
**What changed:** Brief description
**Why:** Reason for change
**Who:** Claude Sonnet 4.6 / Anant / Other AI
**Rollback:** How to undo (which comment block to restore)
---
```

---

## CHANGE HISTORY

### [2026-05-24] — Initial Build v1.0.0

**File:** STRUCTURE.md
**Change type:** NEW
**What changed:** Created master structure file
**Why:** Project foundation — single source of truth for all AI sessions
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** CHANGELOG.md
**Change type:** NEW
**What changed:** Created this change log file
**Why:** Track every code modification for full rollback capability
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** ARCH.md
**Change type:** NEW
**What changed:** Created architecture decisions log
**Why:** Record all architectural choices and their reasoning
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** CONTEXT.md
**Change type:** NEW
**What changed:** Created AI continuity context file
**Why:** Any AI joining mid-project can read this and pick up exactly where we left off
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** core/manager.py
**Change type:** NEW
**What changed:** Created Manager brain (orchestrator) — full implementation
**Why:** Core of the entire system — routes all requests, manages agents
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** core/router.py
**Change type:** NEW
**What changed:** AI model router — selects best model per task type
**Why:** Multi-AI routing for cost efficiency and quality maximization
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** core/voice.py
**Change type:** NEW
**What changed:** Voice engine — Whisper STT + Edge TTS (local, free, offline)
**Why:** Iron Man-style voice interface. Local = fast + private
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** core/identity.py
**Change type:** NEW
**What changed:** Identity verification — voice print + passphrase + hardware fingerprint
**Why:** Only Anant should ever access Manager OS
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** core/health.py
**Change type:** NEW
**What changed:** Health agent — monitors all agents, self-heals gaps
**Why:** Required for system reliability — if any agent fails, health agent fixes it
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** core/memory.py
**Change type:** NEW
**What changed:** Memory manager — short term + long term + session context
**Why:** Manager must remember everything across sessions without losing context
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** core/task_queue.py
**Change type:** NEW
**What changed:** Task priority queue — schedules concurrent agent tasks
**Why:** Multiple agents must work simultaneously without conflicts
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** agents/trading_agent.py
**Change type:** NEW
**What changed:** Trading engine — multi-agent consensus, candle reading, auto trade
**Why:** Core financial feature — must make profit like 1000-year-experience trader
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** agents/resume_agent.py
**Change type:** NEW
**What changed:** Resume engine — ATS tailor, Google XYZ formula, keyword match
**Why:** Auto job application — every application gets a perfectly tailored resume
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** agents/career_agent.py
**Change type:** NEW
**What changed:** Career agent — job search, LinkedIn scraper, cold email blaster
**Why:** Automate entire job search pipeline
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** agents/social_agent.py
**Change type:** NEW
**What changed:** Social media manager — Instagram, WhatsApp, Facebook automation
**Why:** Auto-grow social presence, create reels, manage brand deals
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** agents/life_agent.py
**Change type:** NEW
**What changed:** Life OS agent — gold/ETF/demat tracking, daily planner
**Why:** Complete personal life management
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** agents/creative_agent.py
**Change type:** NEW
**What changed:** Creative suite — image, video, logo, poster, content generation
**Why:** All creative work done by Manager
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** security/firewall.py
**Change type:** NEW
**What changed:** Privacy firewall — blocks all data leakage, API training opt-out
**Why:** Anant's data must NEVER leave to any third party, even API providers
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** security/auth.py
**Change type:** NEW
**What changed:** Authentication layer — multi-factor, hardware-bound
**Why:** Only Anant can unlock Manager OS
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** security/tunnel.py
**Change type:** NEW
**What changed:** Private network tunnel — WireGuard-based, global access
**Why:** Anant must access Manager from anywhere in the world securely
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** ui/dashboard.html
**Change type:** NEW
**What changed:** Cinematic Iron Man-style dashboard UI
**Why:** Visual interface — must look like a proper polished product
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

**File:** setup.bat
**Change type:** NEW
**What changed:** Auto-setup bat file — installs everything, no manual steps
**Why:** Anant's max effort = download zip + run bat. Everything else is automatic.
**Who:** Claude Sonnet 4.6
**Rollback:** N/A — initial creation
---

## APPEND NEW CHANGES BELOW THIS LINE
---

### [APPENDED: 2026-05-31] — Phase A + Phase B Execution (manager_os_final_plan.md)

**File:** core/voice.py | BUG_FIX CRITICAL
P0-1: pyttsx3 singleton + asyncio.Queue worker thread. One engine per process.
      All speak() calls serialized through queue — eliminates "run loop already started".
P0-5: Female voice: Windows Zira preferred, AriaNeural for Edge TTS.
Old: new pyttsx3.init() per call → crash. New: _tts_worker() thread owns engine forever.
---

**File:** security/auth.py | MODIFIED (P0-2, P0-4)
P0-2: Real server-side session tokens. PBKDF2 passphrase hash. 8-hour sessions.
P0-4: /api/key/add rate limited (5/min), requires auth token.
Old: client-side bypass only. New: POST /api/auth → token → WS/API header.
---

**File:** main.py | MAJOR REWRITE (P0-2,P0-3,P0-4,P0-7,P0-8,P1-3,P1-10)
P0-3: host=127.0.0.1 (was 0.0.0.0). CORS tightened to localhost only.
P0-7: TradingAlertManager.start() called in lifespan (was never started).
P0-8: Routes through swarm for non-conversation intents (was skipping swarm).
P1-3: _init_extra_clients() called after key injection (was never called).
P1-10: Caption WS — single path, no double-send bug.
---

**File:** core/router.py | BUG_FIX (P1-4,P1-5,P1-6)
P1-4: Boot ping uses single safe model per provider (not full list).
      No longer permanently blocks provider from one failed model name.
P1-5: record_usage() called after every successful completion.
P1-6: last_provider_used tracked. Review loop uses it (not working_providers[0]).
GROQ: Removed deprecated mixtral-8x7b-32768 (was failing in every log).
GEMINI: Now tries gemini-2.0-flash-exp first (1.5 models all NotFound).
NVIDIA: Confirmed model nvidia/llama-3.1-nemotron-70b-instruct.
---

**File:** security/firewall.py | BUG_FIX (P1-12)
P1-12: Removed invalid anthropic-beta header from PROVIDER_HEADERS.
       Was causing BadRequestError on every Claude API call.
Old: PROVIDER_HEADERS = {"anthropic": {"anthropic-beta": "no-training-data-0"}}
New: PROVIDER_HEADERS = {}
---

**File:** core/manager.py | MODIFIED (P0-8, P1-6)
P0-8: process() routes non-conversation intents through swarm engine.
P1-6: Review loop uses router.last_provider_used. get_morning_briefing() added.
---

**File:** core/identity.py | MODIFIED (P1-7)
P1-7: verify_or_skip() non-blocking on boot. Background enrollment.
      Hardware fingerprint check <1 second. Passphrase as PBKDF2 hash.
---

**File:** agents/conversation_agent.py | NEW (P1-11)
P1-11: ConversationAgent created. Handles memory queries:
       "what did I say about X", "summarize our conversations", "do you remember".
       Uses ConversationStore search + router for summarization.
---

**File:** setup/api_key_fetcher.py | BUG_FIX (P1-9)
P1-9: Empty key validation. Min length check. Placeholder detection.
      Re-prompts up to 3 times. Skips cleanly on empty Enter.
Old: any key including empty string saved as valid.
---

**File:** requirements.txt | MODIFIED (P0-6)
P0-6: python-wireguard removed (was breaking pip install on Windows).
      Tailscale handled via config instead.
---

**File:** config.yaml | MODIFIED (P0-3, P0-5, P0-6)
P0-3: server.host = 127.0.0.1. P0-5: voice_gender = female, AriaNeural.
P0-6: vpn.provider = tailscale.
---

**File:** ui/dashboard.html | MODIFIED (P0-2, P1-10)
P0-2: Auth flow calls /api/auth, stores token in sessionStorage, sends in WS + API calls.
P1-10: Caption WS single path. No double-send bug.
---


### [2026-05-31] — Session 5: Video Analysis + All Bug Fixes + AZARIS Dashboard

**File:** ui/dashboard.html
**Change type:** MAJOR REBUILD
**What changed:** Complete AZARIS-style dashboard — J.A.R.V.I.S header, system vitals left panel,
business metrics right panel, agent color coding, timestamp+coords display, HUD grid aesthetic.
**Why:** Videos 7+10 showed the exact target UI — AZARIS J.A.R.V.I.S multi-monitor system.
**Who:** Claude Sonnet 4.6
---

**File:** core/router.py
**Change type:** BUG_FIX (CRITICAL)
**What changed:** Removed invalid `anthropic-beta: no-training-data-0` header from Claude client.
Fixed NVIDIA model → nvidia/llama-3.1-nemotron-70b-instruct. GPT rate limit cooldown not permanent block.
**Why:** Claude failing BadRequestError on every request. NVIDIA wrong model name.
**Who:** Claude Sonnet 4.6
---

**File:** core/manager.py
**Change type:** MODIFIED
**What changed:** Morning briefing uses exact Jarvis script format from Video 4.
Contextual boot greeting: "While you were away..." pattern from Videos 1/4/9.
Dual personality mode (JARVIS/FRIDAY) added.
**Why:** Videos showed exact dialogue patterns Anant wants Manager to use.
**Who:** Claude Sonnet 4.6
---

**File:** SETUP.bat
**Change type:** REPLACED (old commented out)
**What changed:** Anant's cleaner 8-step SETUP.bat integrated. Better error handling.
**Why:** User provided improved version during Copilot session.
**Who:** Anant (provided) + Claude Sonnet 4.6 (integrated)
---

**File:** ARCH.md
**Change type:** APPENDED
**What changed:** ADR-037 to ADR-042 added. AZARIS dashboard architecture. Agent color system.
Dual personality mode. Contextual boot pattern.
**Why:** Major new architectural decisions from video analysis.
**Who:** Claude Sonnet 4.6
---


### [2026-05-28] — Session 3: Critical Fixes + New Features

**File:** core/router.py
**Change type:** BUG_FIX (CRITICAL)
**What changed:** Fixed provider name mapping. Keys from vault now correctly injected.
Boot-time key validation added. Startup report shows which models are working.
**Why:** ALL cloud models were failing — names in vault didn't match router client lookup.
**Old:** See comments in file
---

**File:** core/ollama_client.py
**Change type:** BUG_FIX
**What changed:** Always passes Manager system prompt to Ollama. Never generic chatbot mode.
Skips review loop when using local models (single call only).
**Why:** Ollama was hallucinating fake system names without personality prompt.
---

**File:** core/health.py
**Change type:** BUG_FIX
**What changed:** RAM alert threshold raised to 95%. Alert cooldown: 10min per alert type.
Edge TTS 403 errors silenced (fallback to pyttsx3 silently).
**Why:** Health alerts firing every 3 min for same issue = very annoying. Edge TTS 403 is known issue.
---

**File:** core/voice.py
**Change type:** MODIFIED (Copilot additions + new)
**What changed:** pyttsx3 set as PRIMARY TTS engine. Real-time word-by-word caption
streaming added via WebSocket. speak() now streams captions while speaking.
**Why:** Copilot confirmed pyttsx3 works. Real-time captions required for Iron Man feel.
---

**File:** core/conversation_store.py
**Change type:** NEW
**What changed:** Dedicated conversation storage — every exchange saved permanently.
ChromaDB semantic search + SQLite structured. Loads last 20 exchanges on boot as context.
**Why:** Manager must never forget context across sessions.
---

**File:** agents/conversation_agent.py
**Change type:** NEW
**What changed:** ConversationAgent — handles "what did I tell you last week" queries.
Semantic search over all past conversations. Proactive context injection.
**Why:** Context persistence is a core requirement. New dedicated agent.
---

**File:** core/identity.py
**Change type:** MODIFIED
**What changed:** Authentication gate — dashboard blocked until identity verified.
Boot shows auth page, not dashboard. After verification: boot message + dashboard.
**Why:** "authenticate me first" — Anant's requirement this session.
---

**File:** main.py
**Change type:** MODIFIED
**What changed:** Auth middleware added. /ws/captions endpoint added.
Boot sequence: verify identity → speak boot msg → open dashboard.
**Why:** Auth gate + caption WebSocket required.
---

**File:** config.yaml
**Change type:** MODIFIED
**What changed:** tts_engine changed to "pyttsx3" (primary). RAM alert threshold 95%.
Alert cooldown config added. conversation_store config added.
**Why:** pyttsx3 confirmed working. Fixes from live run.
---

**File:** ui/dashboard.html
**Change type:** MODIFIED
**What changed:** Auth screen added (shown before dashboard). Real-time caption bar added.
Conversation history panel added (scrollable log).
**Why:** Auth gate + captions + history required this session.
---

**File:** requirements.txt
**Change type:** MODIFIED (Copilot + this session)
**What changed:** pyttsx3==2.90 added (Copilot). chromadb added for semantic memory.
**Why:** pyttsx3 needed for TTS. ChromaDB for conversation semantic search.
---


### [2026-05-27] — Session 2: Live Run Fixes + New Features

**File:** core/router.py
**Change type:** BUG_FIX + MODIFIED
**What changed:** Fixed model ID strings. Reordered fallback chain to use confirmed-working keys (Groq first). Added NVIDIA NIM support. Fixed Gemini model string.
**Why:** Live run showed claude-sonnet/gemini-flash were failing. Groq/NVIDIA are loaded and working.
**Old code:** Commented in file with date
**Who:** Claude Sonnet 4.6
---

**File:** agents/self_heal_agent.py
**Change type:** NEW
**What changed:** Created SelfHealAgent — watches logs, detects errors, auto-applies fixes with backups
**Why:** Referenced in CHANGELOG/CONTEXT from previous session but file was missing
**Who:** Claude Sonnet 4.6
---

**File:** core/identity.py
**Change type:** BUG_FIX
**What changed:** Made enrollment non-blocking on first boot — runs in background, doesn't block server start
**Why:** First boot was potentially hanging waiting for voice enrollment input
**Who:** Claude Sonnet 4.6
---

**File:** agents/trading_agent.py
**Change type:** ADDED_FEATURE
**What changed:** Added WhatsApp/Telegram alert system — morning brief, price alerts, 52-week tracker, earnings tracker
**Why:** Reel 17 (Hermes Agent) showed this pattern — alerts delivered to phone, no dashboard needed
**Who:** Claude Sonnet 4.6
---

**File:** agents/career_agent.py
**Change type:** ADDED_FEATURE
**What changed:** Added accept/reject keyword workflow for resume tailoring
**Why:** Reel 16 (Jobsuit.ai) showed human-in-the-loop control improves resume quality
**Who:** Claude Sonnet 4.6
---

**File:** agents/files_agent.py
**Change type:** ADDED_FEATURE
**What changed:** Added semantic file search + WhatsApp auto-send capability
**Why:** Reel 14 (IRIS AI) showed natural language file finding + auto-send pattern
**Who:** Claude Sonnet 4.6
---

**File:** START.bat
**Change type:** BUG_FIX
**What changed:** Applied Anant's fix — OLLAMA_NOHISTORY=1, full stdout/stderr silence for ollama serve
**Why:** "handle is invalid" errors from Ollama in background mode
**Who:** Anant (provided fix) + Claude Sonnet 4.6 (implemented)
---

**File:** main.py
**Change type:** BUG_FIX + MODIFIED  
**What changed:** Added self_heal_agent to startup. Fixed agent registration order. Added resume_agent fallback routing to career_agent.
**Why:** self_heal_agent missing from startup. resume_agent import was removed in prior session.
**Who:** Claude Sonnet 4.6
---

**File:** config.yaml
**Change type:** MODIFIED
**What changed:** Added self_heal config block, trading alerts config (WhatsApp/Telegram), watchlist stocks
**Why:** New features need configuration
**Who:** Claude Sonnet 4.6
---


### [2026-05-24] — Session 1 Continued — Document 3 Requirements

**File:** agents/api_scout_agent.py
**Change type:** NEW
**What changed:** Dedicated API Scout agent — finds free access to premium AI models
**Why:** NVIDIA NIM lists 50+ premium models free. Need continuous monitoring of all such platforms.
**Who:** Claude Sonnet 4.6
---

**File:** agents/research_agent.py
**Change type:** NEW
**What changed:** Research agent — real thesis generation, anti-hallucination protocol
**Why:** Anant wants real research with verified data, not hallucinated summaries
**Who:** Claude Sonnet 4.6
---

**File:** core/health.py
**Change type:** MODIFIED (expanded)
**What changed:** Added hardware monitoring, API usage tracking, rolling log rotation (5GB cap)
**Why:** Health agent must monitor hardware + API usage + logs — not just software agents
**Old code:** Preserved as comments in file with reason
**Who:** Claude Sonnet 4.6
---

**File:** core/log_manager.py
**Change type:** NEW
**What changed:** Rolling log manager — daily files, 5GB total cap, oldest-deleted-when-full
**Why:** Logs must never fill storage. Rolling deletion keeps logs to 5GB forever.
**Who:** Claude Sonnet 4.6
---

**File:** setup/api_key_fetcher.py
**Change type:** NEW
**What changed:** Playwright browser automation to auto-fetch API keys from all providers
**Why:** Anant only logs in — Manager navigates, finds key, copies, saves to vault
**Who:** Claude Sonnet 4.6
---

**File:** second_laptop/server.py
**Change type:** NEW
**What changed:** Second laptop server — n8n, background tasks, sync layer
**Why:** Always-on background processing on i5-8250U machine
**Who:** Claude Sonnet 4.6
---

**File:** ui/dashboard.html
**Change type:** NEW
**What changed:** Full cinematic React-style dashboard with real-time stats
**Why:** Must look like a proper polished product
**Who:** Claude Sonnet 4.6
---

### [2026-06-05] — Semantic Memory & Telemetry Sync Integration

**File:** security/auth.py
**Change type:** BUG_FIX
**What changed:** Unified the passphrase hashing salt to `b"manager_os_phantom_anant_2024"`.
**Why:** Fixed a salt mismatch between `security/auth.py` and `core/identity.py` which prevented successful Web UI login when bypass was disabled.
**Who:** Antigravity (Gemini 3.5 Flash)
---

**File:** core/conversation_store.py
**Change type:** MODIFIED
**What changed:** Added full ChromaDB persistent vector database client and conversations collection; vector embedding saving in `save()`, and semantic similarity query with SQLite keyword search fallback in `search()`.
**Why:** Implemented the semantic search capabilities outlined in structural memory goals.
**Who:** Antigravity (Gemini 3.5 Flash)
---

**File:** main.py
**Change type:** MODIFIED
**What changed:** Created `second_laptop_data` variable and implemented `POST /api/sync` endpoint to ingest telemetry synced from the background server.
**Why:** Wires the disconnected background laptop server.
**Who:** Antigravity (Gemini 3.5 Flash)
---

**File:** core/manager.py
**Change type:** MODIFIED
**What changed:** Updated `_handle_system_query` to handle telemetry status reporting for the second laptop using the synced global data.
**Why:** Allows Sir to check background machine resource usage and task status directly.
**Who:** Antigravity (Gemini 3.5 Flash)
---

**File:** agents/trading_agent.py
**Change type:** MODIFIED
**What changed:** Implemented `yfinance` in `_check_price_alerts` of the `TradingAlertManager` to query current market prices and trigger push alerts.
**Why:** Replaces the static stubs with real-time price scans.
**Who:** Antigravity (Gemini 3.5 Flash)
---

**File:** second_laptop/server.py
**Change type:** MODIFIED
**What changed:** Replaced the fragile `nseindia` API index call in `_fetch_market_data` with standard `yfinance` tickers for Nifty 50 and Sensex.
**Why:** Avoids bot block issues and provides reliable market index tracking.
**Who:** Antigravity (Gemini 3.5 Flash)
---


### [2026-06-05] — Session 4: Hands-free voice & local desktop app execution

**File:** startup.bat
**Change type:** NEW
**What changed:** Created `startup.bat` at the project root which boots the server and launches START.bat.
**Why:** Standard shortcut entry requested by user.
**Who:** Antigravity (Gemini 3.5 Flash)
---

**File:** main.py
**Change type:** MODIFIED
**What changed:** Added `open_in_chrome` locating `chrome.exe` on Windows; added automated background browser opening task on lifespan startup.
**Why:** Sir wants Google Chrome (not Chromium) to auto-open on boot.
**Who:** Antigravity (Gemini 3.5 Flash)
---

**File:** setup/api_key_fetcher.py
**Change type:** MODIFIED
**What changed:** Swapped default `webbrowser` launch for custom `open_in_chrome`.
**Why:** Prevents opening setup links in Chromium.
**Who:** Antigravity (Gemini 3.5 Flash)
---

**File:** core/manager.py
**Change type:** MODIFIED
**What changed:** Updated `INTENT_MAP` for files to include application-launching keywords; refined `PERSONALITY_SYSTEM_PROMPT` to align with the peon/worker/manager/friend combined context.
**Why:** Correctly route app opening directives and fine-tune voice persona.
**Who:** Antigravity (Gemini 3.5 Flash)
---

**File:** agents/files_agent.py
**Change type:** MODIFIED
**What changed:** Implemented `_launch_app` method using Windows `start` command to launch desktop apps; intercepted launch keywords in `execute`.
**Why:** Sir wants Manager to launch desktop apps like Notepad, Calculator, VS Code, and Chrome.
**Who:** Antigravity (Gemini 3.5 Flash)
---

**File:** ui/dashboard.html
**Change type:** MODIFIED
**What changed:** Added `continuous-voice` toggle button; implemented automated SpeechRecognition restart loop once manager response finishes speaking. Added user gesture trigger.
**Why:** Sir wants hands-free voice mode (Continuous Conversation Mode) by default.
**Who:** Antigravity (Gemini 3.5 Flash)
---


### [2026-06-05] — Session 5: Holographic HUD Overlay & Dynamic Recommendations

**File:** main.py
**Change type:** MODIFIED
**What changed:** Added detection for agent status queries in WebSocket chat handler; dispatched `agent_hud` JSON payload with structured current tasks, future tasks, and recommendations.
**Why:** Sir wants to see what each agent is working on and future recommendations in an interactive visual.
**Who:** Antigravity (Gemini 3.5 Flash)
---

**File:** ui/dashboard.html
**Change type:** MODIFIED
**What changed:** Added HTML markup for `#hud-overlay` grid; added high-end holographic neon glow CSS classes; added JavaScript logic to render cards, close on ESC/click, and transmit recommended tasks to the chat.
**Why:** Sir wants a premium Iron Man-style swappable cognitive console overlay for all 12 agents.
**Who:** Antigravity (Gemini 3.5 Flash)
---


### [2026-06-05] — Session 6: Startup Script Merging & Workspace Cleanup

**File:** startup.bat
**Change type:** MODIFIED
**What changed:** Merged full server launch logic from `START.bat` directly into `startup.bat`.
**Why:** Simplifies project startup files down to a single entry point.
**Who:** Antigravity (Gemini 3.5 Flash)
---

**File:** START.bat
**Change type:** DELETE
**What changed:** Deleted the redundant `START.bat` file.
**Why:** Clean up redundant files.
**Who:** Antigravity (Gemini 3.5 Flash)
---


### [2026-06-05] — Session 7: Setup & Console Unicode Fixes

**File:** SETUP.bat
**Change type:** MODIFIED
**What changed:** Added `set PYTHONUTF8=1` to enforce UTF-8 for Python subprocesses. Updated instructions warning to reference `startup.bat` instead of the deprecated `START.bat`.
**Why:** Ensure correct execution instructions and safe encoding environments.
**Who:** Antigravity (Gemini 3.5 Flash)
---

**File:** startup.bat
**Change type:** MODIFIED
**What changed:** Added `set PYTHONUTF8=1` to enforce UTF-8 mode during runtime.
**Why:** Standardizing the console execution environment.
**Who:** Antigravity (Gemini 3.5 Flash)
---

**File:** setup/first_run.py
**Change type:** MODIFIED
**What changed:** Replaced checkmark, cross, em dash, and box drawing unicode character literals with ASCII safe representations (+, -, [OK], [FAIL]).
**Why:** Prevent terminal crash from `UnicodeEncodeError` under Windows default CP1252 codepage.
**Who:** Antigravity (Gemini 3.5 Flash)
---

**File:** setup/api_key_fetcher.py
**Change type:** MODIFIED
**What changed:** Added support for `SETUP_UNATTENDED=1` environment check to bypass interactive key fetching prompts.
**Why:** Enabled automated background runner setup capability.
**Who:** Antigravity (Gemini 3.5 Flash)
---

**File:** core/identity.py
**Change type:** MODIFIED
**What changed:** Added support for `SETUP_UNATTENDED=1` environment check to auto-enroll default passphrase when unattended mode is requested.
**Why:** Prevent interactive passphrase prompt hanging the automated setup execution.
**Who:** Antigravity (Gemini 3.5 Flash)
---



### [2026-10-12] — Workable local release

- Fixed startup paths, duplicate router creation, lifecycle cleanup, model discovery, bounded provider fallback, accurate availability and replacement-key selection.
- Closed unauthenticated REST/caption access, added enrollment without default passphrases, logout revocation and origin checks.
- Fixed broad substring routing, wrong-agent redirects, duplicate prompt history, unsafe fallback recipients and duplicate WebSocket actions.
- Added persistent local tasks/reminders, real text file operations, deterministic app launches, saved Builder projects, downloadable outputs, Local mic and Connections UI.
- Verified local Qwen inference, local Whisper transcription, Windows Zira speech and real browser workflows. 15 regression tests pass.
- Replaced invented activity/current-market/call/application claims with explicit implementation state. LinkedIn loop collects reviewable links; no blind form submission.
- Retained original code as comments and source ZIP. Added START_HERE.txt and WORKABLE_STATUS.md.

### [APPENDED: 2026-10-12] Local passphrase recovery
Added RESET_PASSPHRASE.bat and setup/reset_passphrase.py. Local recovery stops the verified launcher, refuses reset while a server still listens, archives only the login hash, and reopens dashboard enrollment. Restart invalidates sessions; vault keys, history and tasks are preserved. Recovery preservation and repeated-reset checks passed. User requested recovery and the local login was reset.


### [APPENDED: 2026-10-12] Background document work
Implemented personal_context.py, workflows.py and assistant_work.py. Approved local folders and saved user messages supply evidence. Resume and document tasks run in the background, save real files and expose persistent progress in Work. Thirty regression tests and two real browser workflows passed. See ASSISTANT_WORK.md for commands, verification and limitations.


### [APPENDED: 2026-10-12] Project goal execution and acceptance app
Added core/project_work.py and core/project_tools.py: persistent architecture, typed source/dependency/runtime/browser tools, failure repair, requirement amendments, source-version acceptance gates, review and delivery. Builder routing now takes precedence for software goals; Work starts completed projects. Cloud preference for project coding respects local_only. See PROJECT_WORK.md for exact boundaries.

Verified 40 Manager regressions and real browser smoke including project launch. Career Studio (LinkedIn Optimizer and Resume Maker) passed 11 backend tests and actual browser downloads, edits and error checks. Its first generated draft needed direct repair; arbitrary unattended project completion is not established. Generated source executes with local user permissions; project environments are not an OS sandbox.

### [APPENDED: 2026-10-12] Outcome routing, stable task focus and relevant memory
Added core/goal_director.py and core/task_context.py. Manager routes supported outcome requests into executable workflows, keeps explicit workflow identity across background saves/restarts, retrieves attributed relevant user history, and reports actual saved progress. Work exposes current-task selection. Workflow APIs accept exact IDs; cancellation cannot target another running job. ProjectWork detects repetitive execution patterns and retries transient/format model failures once, preserving interrupted progress without weakening verification. See PROJECT_WORK.md for bounded scope and model limitations.

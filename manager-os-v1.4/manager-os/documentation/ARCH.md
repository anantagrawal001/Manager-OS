# MANAGER OS — ARCHITECTURE DECISIONS LOG
# ════════════════════════════════════════════════════════════════════════════════
# THIS FILE IS SACRED. NEVER DELETE. NEVER REPLACE. APPEND ONLY.
# Every architectural decision must be recorded here with full reasoning.
# Future AI or Anant can read this to understand WHY things are built this way.
# ════════════════════════════════════════════════════════════════════════════════

---

## FORMAT GUIDE

```
### ADR-[NUMBER]: [Decision Title]
**Date:** YYYY-MM-DD
**Status:** ACCEPTED | SUPERSEDED | UNDER_REVIEW
**Context:** Why was this decision needed?
**Decision:** What was decided?
**Reasoning:** Why this and not alternatives?
**Consequences:** What does this enable/restrict?
**Alternatives considered:** What else was evaluated?
---
```

---

## ARCHITECTURE DECISIONS

### ADR-001: Python as primary backend language
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** Need a language that handles AI APIs, voice processing, file I/O, 
web scraping, trading, and system automation all in one.
**Decision:** Python 3.11+ as primary language. JavaScript/TypeScript for UI only.
**Reasoning:** Python has the best AI/ML library ecosystem. Whisper, LangChain,
FastAPI, Selenium, CCXT (trading), all natively Python. No other language matches
this coverage for our specific use case.
**Consequences:** All agents in Python. UI in HTML/CSS/JS. REST API bridges them.
**Alternatives considered:** Node.js (weak AI libs), Go (no AI ecosystem), Rust (too complex)
---

### ADR-002: Local-first, cloud-second architecture
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** Privacy is paramount. Anant's data must never leak. Also needs to work
when internet is slow or unavailable.
**Decision:** Run as much as possible locally. Cloud APIs only for what cannot run locally.
All local data encrypted at rest.
**Reasoning:** Local = private + fast. Whisper for STT runs on GPU locally (RTX 5060 perfect).
Edge TTS runs locally. Core reasoning uses cloud APIs but data is sanitized before sending.
**Consequences:** Larger initial download. But zero latency for voice, full offline capability 
for core features.
**Alternatives considered:** 100% cloud (rejected — privacy risk), 100% local LLM (rejected — 
quality too low on consumer hardware for complex tasks)
---

### ADR-003: Voice-first interface with text fallback
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** Iron Man Jarvis experience requires natural voice interaction.
**Decision:** Primary interface is voice. Text/chat is always available as fallback.
Whisper (local) for STT. Edge TTS (local, free) primary TTS. ElevenLabs as upgrade option.
**Reasoning:** Whisper runs excellently on RTX 5060. Edge TTS is free, fast, and has
good English voices. This keeps the system fully functional with zero API cost for voice.
**Consequences:** Requires microphone. Offline voice works. Optional ElevenLabs for better voice quality.
**Alternatives considered:** Deepgram (cloud, cost), Google STT (privacy risk), 
Azure Speech (cost)
---

### ADR-004: Multi-model AI routing — best model per task
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** No single AI model is best at everything. Budget is free tier only.
**Decision:** Build a router that maps task types to optimal models. Automatic fallback
when free tier limit hit. Context transferred seamlessly on model switch.
**Reasoning:** Claude best for reasoning/writing. Gemini Flash best for speed/search.
Whisper best for STT. FLUX best for images. Routing maximizes quality while staying free.
**Consequences:** More complex orchestration. But best possible output quality.
**Alternatives considered:** Single model (ChatGPT/Claude only) — rejected for quality + cost
---

### ADR-005: Append-only file system for logs and structure
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** Need full audit trail. Must be able to rollback any change. 
Must work across AI sessions — even different AI models.
**Decision:** STRUCTURE.md, CHANGELOG.md, ARCH.md, CONTEXT.md are append-only.
In-code: old code commented out with reason, never deleted. Git-like but simpler.
**Reasoning:** If Anant switches AI assistants (Claude → GPT → Gemini), the new AI
reads these files and knows exactly what happened. No context lost. Full rollback possible
by reading commented code. This is more reliable than actual Git for a non-technical user.
**Consequences:** Files grow over time. This is by design. Never prune.
**Alternatives considered:** Actual Git (requires technical knowledge from Anant), 
Database log (harder to read for AI)
---

### ADR-006: Single executable zip delivery
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** Anant must not do any technical work. Max effort = download zip + run bat.
**Decision:** All deliverables as .zip. Inside: setup.bat auto-installs Python, dependencies,
configures everything. start.bat launches. API keys fetched by Manager automatically.
**Reasoning:** Non-negotiable UX requirement from Anant. Everything automated.
**Consequences:** setup.bat must handle edge cases (Python not installed, firewall, etc.)
**Alternatives considered:** Docker (requires Docker install — too much user effort), 
Installer wizard (requires clicks — still too much)
---

### ADR-007: Identity — hardware fingerprint + voice print + passphrase
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** System must only work for Anant. Must resist impersonation.
**Decision:** Three-factor identity: (1) Hardware fingerprint (machine-bound), 
(2) Voice print (trained on Anant's voice), (3) Optional passphrase backup.
System creates hardware fingerprint on first run. Locks to that machine.
For remote access, VPN tunnel + additional auth token.
**Reasoning:** Hardware fingerprint prevents anyone else running the software. 
Voice print prevents phone/recording attacks. Layered = extremely hard to spoof.
**Consequences:** Must do initial voice enrollment. Remote access needs VPN.
**Alternatives considered:** Password only (weak), Face ID (needs camera, complex), 
Biometric key (expensive hardware)
---

### ADR-008: Privacy firewall — data sanitization before any API call
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** Anant's private data must NEVER be used for model training by API providers.
Must protect against hackers seeing data even if they breach the system.
**Decision:** All outgoing API calls pass through privacy_firewall.py which:
(1) Strips PII before sending, uses placeholders internally
(2) Sets API headers to opt out of training (Anthropic: no training header, 
    OpenAI: opt-out endpoint, etc.)
(3) Encrypts all local data with AES-256
(4) Tor-style routing for sensitive queries (optional)
(5) Memory wipe of sensitive data after session
**Reasoning:** Even if an API provider is breached, they won't have Anant's real data.
**Consequences:** Slight overhead on API calls. Worth it for privacy guarantee.
**Alternatives considered:** VPN only (doesn't protect data content), 
Local LLM only (quality too low)
---

### ADR-009: Agent health monitoring — self-healing system
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** With 10+ agents running, some will fail. System must not need Anant to fix it.
**Decision:** Dedicated health_agent.py runs as background process. Pings all agents 
every 60 seconds. On failure: (1) restarts agent, (2) checks if code gap caused failure,
(3) attempts auto-fix, (4) if cannot fix, notifies Sir with diagnosis.
**Reasoning:** Anant should never have to debug. Manager manages itself.
**Consequences:** Slight background resource usage. Acceptable on 16GB RAM system.
**Alternatives considered:** Manual restart (defeats purpose), 
External monitoring service (privacy risk)
---

### ADR-010: FastAPI backend + WebSocket for real-time UI
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** Need real-time communication between Python backend and HTML/JS frontend.
Also need API endpoints for agent communication.
**Decision:** FastAPI as backend server. WebSocket for real-time chat/voice streaming.
REST endpoints for agent tasks. Runs on localhost, exposed via tunnel for remote access.
**Reasoning:** FastAPI is async-native, fast, and has excellent WebSocket support.
Works perfectly for our real-time voice streaming requirement.
**Consequences:** localhost:8000 is the Manager OS server. start.bat launches it.
**Alternatives considered:** Flask (sync, slower), Django (too heavy), 
Node.js/Express (mixing languages unnecessarily)
---

### ADR-011: WireGuard VPN for global remote access
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** Anant must access Manager from anywhere in the world securely.
**Decision:** WireGuard tunnel auto-configured. Lightweight, fast, free, open-source.
Client app installable on phone/laptop. Connects back to home machine.
**Reasoning:** WireGuard is the modern standard. 2-3x faster than OpenVPN. 
Simple config. Works on Windows, Android, iOS.
**Consequences:** Home machine must be running for remote access. Setup auto-handled by setup.bat.
**Alternatives considered:** OpenVPN (slower, complex), Tailscale (third-party — privacy concern),
Ngrok (public tunnel — security risk)
---

### ADR-012: CCXT library for trading — multi-exchange support
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** Trading engine needs to connect to stock/crypto exchanges and demat accounts.
**Decision:** CCXT for crypto exchanges. Selenium/API for Indian stock market (Zerodha/Upstox/Groww).
Multi-agent consensus before any trade execution (minimum 3 agents must agree).
Confidence threshold: 85%+ required to execute.
**Reasoning:** CCXT supports 100+ exchanges. For Indian stocks, Zerodha Kite API is best.
Multi-agent consensus prevents bad trades.
**Consequences:** Needs exchange API keys. Paper trading mode first. Live trading after Anant approval.
**Alternatives considered:** Single-model trading (rejected — too risky without consensus)
---

## APPEND NEW ARCHITECTURE DECISIONS BELOW THIS LINE
---

### [APPENDED: 2026-05-31] Phase A+B Decisions (manager_os_final_plan.md)

### ADR-044: pyttsx3 Singleton Queue Worker (P0-1)
**Date:** 2026-05-31 | **Status:** ACCEPTED
**Context:** "run loop already started" crashed every speak() when called concurrently.
**Decision:** Single daemon thread (_tts_worker) owns pyttsx3 engine for entire process lifetime.
All speak() calls put text into asyncio.Queue. Worker dequeues and calls engine.say() serially.
**Reasoning:** pyttsx3 is not thread-safe. One engine, one thread, one queue = no crashes.

### ADR-045: Server-Side Session Tokens (P0-2)
**Date:** 2026-05-31 | **Status:** ACCEPTED
**Context:** Dashboard auth was client-side only (if(p||true)). Any request could hit API.
**Decision:** POST /api/auth verifies PBKDF2 passphrase hash → returns 32-byte hex token.
Token sent as Bearer header on all API calls and WS query param (?token=...).
bypass_in_development: true in config for dev convenience.
**Reasoning:** Minimum viable auth. Not production-hardened but protects from casual access.

### ADR-046: localhost Only Binding (P0-3)
**Date:** 2026-05-31 | **Status:** ACCEPTED
**Context:** host=0.0.0.0 exposed Manager OS to anyone on Anant's local network.
**Decision:** host=127.0.0.1 by default. CORS restricted to localhost origins only.
Remote access → Tailscale (configured separately).
**Reasoning:** Personal AI OS should not be accessible to neighbours on WiFi.

### ADR-047: Groq Model List Pruned (Phase B)
**Date:** 2026-05-31 | **Status:** ACCEPTED
**Context:** mixtral-8x7b-32768 deprecated by Groq. Appeared in every error log.
**Decision:** Removed from PROVIDER_MODELS[GROQ]. Current list: llama-3.1-70b-versatile,
llama3-70b-8192, llama-3.2-90b-text-preview.
**Reasoning:** Dead model wastes latency on every request. Remove immediately on deprecation.

### ADR-048: Gemini Model Migration to 2.0 (Phase B)
**Date:** 2026-05-31 | **Status:** ACCEPTED
**Context:** All gemini-1.5-* models returned NotFound. Blocked on boot.
**Decision:** PROVIDER_MODELS[GOOGLE] updated to try gemini-2.0-flash-exp first,
then gemini-1.5-flash-002 (versioned, more stable), then gemini-pro as final fallback.
**Reasoning:** 1.5-flash-latest and 1.5-flash aliases unreliable. Use versioned IDs.

### ADR-049: Boot Ping Uses PING_MODELS Dict (P1-4)
**Date:** 2026-05-31 | **Status:** ACCEPTED
**Context:** Boot validation tried all model IDs, permanently blocked provider on first failure.
**Decision:** PING_MODELS dict maps each provider to single known-stable model for ping only.
Runtime completions still try full PROVIDER_MODELS list with per-model fallback.
**Reasoning:** Boot should not permanently damage runtime routing from one bad model name.

### ADR-050: ConversationAgent as 13th Agent (P1-11)
**Date:** 2026-05-31 | **Status:** ACCEPTED
**Context:** Memory queries ("what did I say about X") had no dedicated agent.
**Decision:** agents/conversation_agent.py added. Intent "conversation_memory" in INTENT_MAP.
Handles recent history, semantic search, summarization via ConversationStore.
**Reasoning:** Memory is a first-class feature. Needs dedicated agent, not generic fallback.
---


### [APPENDED: 2026-05-31] ADR-037: AZARIS-Style Multi-Monitor Dashboard
**Date:** 2026-05-31
**Status:** ACCEPTED
**Context:** Videos 7+10 showed the exact UI reference — J.A.R.V.I.S wall TV + 3 bottom monitors.
**Decision:** Dashboard rebuilt to match AZARIS reference. Left: system vitals. Center: orb+chat. Right: business metrics. Status bar at bottom. J.A.R.V.I.S brand header.
**Reasoning:** Anant wants it to look like a fictional thing coming to life. AZARIS is that reference.
---

### ADR-038: Agent Color Coding System
**Date:** 2026-05-31
**Status:** ACCEPTED
**Context:** Video 8 AVENGERS roll call showed each agent having a distinct color-coded card.
**Decision:** Each agent assigned a unique color: Trading=gold, Career=green, Comms=cyan, Social=purple, Builder=red, Creative=orange, Life=amber, Research=teal, Files=lime, Growth=blue, API Scout=pink, Self-Heal=yellow-green.
**Reasoning:** Visual identity per agent. Makes the dashboard feel alive and differentiated.
---

### ADR-039: Swarm Engine (Ruflo-Inspired)
**Date:** 2026-05-31
**Status:** ACCEPTED
**Context:** ruvnet/ruflo has 56.7k stars. Its Queen-led swarm + hook system is the best pattern for multi-agent routing.
**Decision:** core/swarm.py — SwarmEngine with hook-based routing, learned patterns, consensus dispatch for high-stakes tasks (trading). Hooks stored in skills/hooks.json.
**Reasoning:** Better routing than simple keyword matching. Learns from usage. Enables trading consensus (3 agents vote before executing).
---

### ADR-040: New Free Providers — Cerebras, OpenRouter, DeepSeek
**Date:** 2026-05-31
**Status:** ACCEPTED
**Context:** freellmapi + freellm.net research found many free providers beyond our original list.
**Decision:** Added Cerebras (ultra-fast, 2000 tokens/sec), OpenRouter (100+ models), DeepSeek, GitHub Models to provider list and router.
**Reasoning:** More free options = better fallback chain = never stuck on one failing provider.
---

### ADR-041: Morning Briefing in Jarvis Format
**Date:** 2026-05-31
**Status:** ACCEPTED
**Context:** Video 4 showed exact Jarvis morning briefing format: "Good morning Sir. Today is [Day]. Here is your daily briefing. You have N tasks..."
**Decision:** manager.get_morning_briefing() generates this exact format. Triggered by voice or at boot.
**Reasoning:** Consistent with what Anant showed as his vision.
---

### ADR-042: SETUP.bat Updated — New Providers
**Date:** 2026-05-31
**Status:** ACCEPTED
**Context:** Anant's cleaner SETUP.bat from Copilot session + new providers needed.
**Decision:** SETUP.bat now lists Groq, Google, NVIDIA, Anthropic, OpenRouter, ElevenLabs with their signup URLs. 8-step process.
**Reasoning:** Single script for complete first-run setup including all free providers.
---

### ADR-043: Duplicate Message Fix in Dashboard
**Date:** 2026-05-31
**Status:** ACCEPTED
**Context:** Screenshot showed same message sent multiple times. Input not cleared on send. No debounce.
**Decision:** Dashboard JS uses `sending` boolean flag. Input cleared immediately. 500ms cooldown between sends.
**Reasoning:** Race condition between Enter keydown + button click. Flag prevents double-send.
---


### ADR-030: Authentication Gate — Dashboard Blocked Until Verified
**Date:** 2026-05-28
**Status:** ACCEPTED
**Context:** Anant requires: "it should authenticate me first."
**Decision:** Boot shows /auth page. FastAPI middleware blocks /dashboard until session token set.
Auth flow: hardware fingerprint (silent) → passphrase/voice → issue session token → load dashboard.
**Reasoning:** Security + user requirement. Iron Man's FRIDAY also verifies identity first.

### ADR-031: pyttsx3 as Primary TTS (Confirmed Working)
**Date:** 2026-05-28
**Status:** ACCEPTED — SUPERSEDES Edge TTS as primary
**Context:** Edge TTS 403 errors in production. pyttsx3 confirmed working (Copilot test).
**Decision:** pyttsx3 = primary TTS. Edge TTS = upgrade path when 403 resolved. ElevenLabs = premium.
**Reasoning:** Use what works. pyttsx3 is offline, no auth needed, no 403 errors.

### ADR-032: Real-time Caption Streaming via WebSocket
**Date:** 2026-05-28
**Status:** ACCEPTED
**Context:** Iron Man feel requires word-by-word captions while Manager speaks.
**Decision:** voice.py speak() splits text into words, sends each via /ws/captions WebSocket.
Dashboard subscribes and renders captions in real-time as Manager speaks.
**Reasoning:** Both audio and visual feedback simultaneously. Like FRIDAY's HUD display.

### ADR-033: ConversationAgent — Dedicated Context Memory
**Date:** 2026-05-28
**Status:** ACCEPTED
**Context:** Manager using Ollama without session history = no context = hallucination.
"which api are you using" → Manager refused (no context). Must fix permanently.
**Decision:** ConversationAgent + ConversationStore. Every exchange saved. Last 20 loaded on boot.
ChromaDB for semantic search. Manager proactively uses past context.
**Reasoning:** "never forget context" is a core requirement stated multiple times.

### ADR-034: Skip Review Loop for Local Models
**Date:** 2026-05-28
**Status:** ACCEPTED
**Context:** Review loop = 3 Ollama calls per request = 30-60 second responses. Too slow.
**Decision:** router.complete() checks if model is local (Ollama). If yes: skip review.
Review loop only for cloud models where latency per call is low.
**Reasoning:** Local inference is slow per call. Minimize calls. Quality review not needed for simple responses.

### ADR-035: Unified Provider Name Registry
**Date:** 2026-05-28
**Status:** ACCEPTED
**Context:** key_manager used "google", router looked for "google_ai" → mismatch → all keys fail.
**Decision:** Single PROVIDER_NAMES dict in core/provider_names.py used by BOTH key_manager and router.
One source of truth. Import from same place everywhere.
**Reasoning:** Name mismatch caused 100% cloud model failure in production. Must fix permanently.

### ADR-036: Alert Cooldown System
**Date:** 2026-05-28
**Status:** ACCEPTED
**Context:** RAM alerts firing every 3 minutes for same issue. Very annoying.
**Decision:** Health agent tracks last_alert_time per alert type. Minimum 10 min between same alert.
RAM threshold raised from 90% to 95% (16GB machine with AI models = always high).
**Reasoning:** Health alerts must be actionable, not noise. Cooldown prevents alert fatigue.


### ADR-026: Groq as Primary Fallback (Confirmed Working 2026-05-27)
**Date:** 2026-05-27
**Status:** ACCEPTED
**Context:** Live run showed Groq key confirmed loaded and working. Claude/Gemini failing.
**Decision:** Reorder fallback chain: Groq first, NVIDIA NIM second, then Claude/Gemini/GPT.
**Reasoning:** Use what's confirmed working. Groq has 14,400 req/day free tier — sufficient.

### ADR-027: Non-Blocking Identity Enrollment
**Date:** 2026-05-27
**Status:** ACCEPTED
**Context:** Original verify() blocked server start waiting for voice/passphrase input.
**Decision:** verify_or_skip() — if not enrolled, boot continues, enrollment runs in background.
**Reasoning:** Server must start first so dashboard is accessible for enrollment.

### ADR-028: Trading Alerts via WhatsApp/Telegram (Reel 17)
**Date:** 2026-05-27
**Status:** ACCEPTED
**Context:** Reel 17 (Hermes Agent) showed morning brief + price alerts + 52-week tracker delivered to phone.
**Decision:** TradingAlertManager handles: 8AM morning brief, real-time price alerts, 4PM evening report.
**Delivery:** WhatsApp primary, Telegram secondary. No need to open dashboard.

### ADR-029: __init__.py Files Required for Package Imports
**Date:** 2026-05-27
**Status:** ACCEPTED
**Context:** Python package imports failing without __init__.py in subdirectories.
**Decision:** Added __init__.py to core/, core/brain/, agents/, security/, setup/, second_laptop/


### ADR-021: Anti-Hallucination Protocol — Facts Must Be Verified
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** Standard LLMs hallucinate facts confidently. Manager must not do this.
**Decision:** Every factual claim requires source. Unknown = "cannot verify". 
Real-time facts → Perplexity/web search first. Confidence < 80% → flagged explicitly.
Research tasks: minimum 3 cross-referenced sources per key claim.
**Reasoning:** Anant makes real decisions (financial, career) based on Manager's output.
Hallucinated facts in these contexts cause real harm.

### ADR-022: Rolling Log — 5GB Cap, Daily Rotation
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** Logs must never fill Anant's storage. But logs must be kept for debugging.
**Decision:** Daily log files (~100MB/day). Total cap: 5GB.
When total exceeds 5GB → oldest day deleted → newest day written. Continuous cycle.
**Reasoning:** 5GB / ~100MB per day = ~50 days of log history. Sufficient for debugging.

### ADR-023: NVIDIA NIM as Primary Free Pro Model Source
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** Anant wants premium model quality for free. NVIDIA NIM provides this.
**Decision:** NVIDIA NIM (build.nvidia.com) added as primary source for premium free models.
API Scout checks weekly. All NIM models are OpenAI-compatible — easy integration.
**Reasoning:** NVIDIA subsidizes inference costs to promote their GPU platform. 
This gives access to Llama 405B, Mistral Large, etc., for free.

### ADR-024: DeepSeek Included with Strict PII Firewall
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** DeepSeek R1 has excellent reasoning but sends data to Chinese servers.
**Decision:** Include DeepSeek in router for non-sensitive tasks only.
Firewall mandatory — strips all PII before any DeepSeek call.
Use for: math, code logic, general reasoning. Never for: personal/financial data.
**Reasoning:** Quality is too good to ignore. Security handled at firewall layer.

### ADR-025: Second Laptop — Capability-Limited Background Server
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** i5-8250U with 12GB RAM and Intel UHD 620 cannot run heavy AI models.
**Decision:** Second laptop handles only: n8n workflows, job scanning, social analytics,
market monitoring (no AI inference), sync layer, always-on scheduling.
Heavy AI inference stays on main Alienware (RTX 5060).
**Reasoning:** Intel UHD 620 with shared memory cannot run Ollama models reliably.
Keep heavy work on the machine with the actual GPU.


### ADR-011-UPDATED: Tailscale replaces WireGuard for remote access
**Date:** 2026-05-24
**Status:** SUPERSEDES ADR-011
**Context:** Original ADR-011 chose WireGuard. New understanding confirms Anant's 
zero-technical-effort requirement is absolute. WireGuard requires port forwarding knowledge.
**Decision:** Use Tailscale instead. One install, one login, works everywhere automatically.
**Reasoning:** Tailscale is peer-to-peer, encrypted, requires zero network config from Anant.
Dashboard on Tailscale IP — accessible from phone, laptop, anywhere globally.
**Consequences:** setup.bat installs Tailscale MSI silently. Anant logs in once. Done forever.
**Previous ADR-011:** WireGuard — commented out, not deleted.
---

### ADR-013: ChromaDB for long-term vector memory
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** SQLite keyword search is insufficient. "Find what I said about marketing strategy 
last week" must work even if exact words don't match.
**Decision:** ChromaDB vector database alongside SQLite.
SQLite: structured data (tasks, preferences, facts, conversation log)
ChromaDB: semantic vector embeddings of all conversations for meaning-based retrieval
**Reasoning:** Manager must remember Anant's context across thousands of conversations.
Semantic search is the only way to make this reliable.
**Consequences:** ChromaDB adds ~200MB overhead. Worth it. Runs locally, fully private.
**Alternatives considered:** Pinecone (cloud — privacy violation), FAISS (harder to use)
---

### ADR-014: Multi-key pool per AI provider — 80% proactive rotation
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** Single API key per provider means hitting rate limits causes failure.
**Decision:** Each provider supports a pool of N API keys. Usage tracked per key per day.
At 80% of daily limit → rotate to next key BEFORE failure. Zero interruption to Anant.
**Reasoning:** Free tier is unlimited if you distribute across multiple accounts.
Proactive rotation means Anant never sees a rate limit error. Ever.
**Consequences:** Anant needs to create multiple accounts per provider where needed.
Manager handles all key management automatically once keys are in vault.
---

### ADR-015: Context bridge — mid-task AI model switching
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** When model switches mid-task (e.g., Claude → GPT-4o), conversation history
format differs between providers. Task must continue from exactly where it left off.
**Decision:** context_bridge.py translates between formats:
- Claude: system + messages (user/assistant alternating)
- GPT-4o: messages with system role at top
- Gemini: GenerativeModel with parts-based history
- Ollama: single prompt string with conversation embedded
All formats preserve: full context, Anant's original request, work completed so far.
**Reasoning:** Seamless model switching is non-negotiable for the unlimited free tier strategy.
---

### ADR-016: Ollama for local offline fallback
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** RTX 5060 can run Llama 3.1 8B and Mistral 7B locally. This enables offline operation.
**Decision:** Ollama runs as local service. Models: llama3.1:8b + mistral:7b
Falls back to Ollama when: (a) no internet, (b) all remote keys exhausted, (c) privacy-critical task
**Reasoning:** Full offline capability is a key requirement. RTX 5060 handles 8B models comfortably.
**Consequences:** First-run downloads ~8-15GB of model weights. setup.bat handles this.
---

### ADR-017: Second laptop as always-on background server
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** Main Alienware cannot run at full capacity 24/7. Background tasks need continuous operation.
**Decision:** Second laptop (specs TBD) runs: market monitoring, job scanning, social analytics,
n8n automation, sync layer. Main Alienware: interactive voice, heavy inference, dashboard.
**Reasoning:** Division of labor. Second laptop is cheap always-on server. Main laptop stays fast.
**Consequences:** Second laptop must stay powered and connected. Sync via local network + Tailscale.
---

### ADR-018: Playwright for API key auto-fetching
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** Anant must not manually visit 8 websites to get API keys.
**Decision:** Playwright browser automation. Manager opens browser, navigates to provider site,
Anant logs in once, Manager finds API key page, creates key, copies it, saves to encrypted vault.
**Reasoning:** Playwright can fully automate browser navigation including clicking, form filling,
and reading page content. Chromium downloaded silently by setup.bat.
**Consequences:** Some providers may have anti-bot detection. Manager handles retries gracefully.
---

### ADR-019: 8 Domain Plugins — Modular Plugin Architecture
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** Need clean separation of capabilities that can be added/removed/updated independently.
**Decision:** 8 domain plugins: trading, career, communication, social, builder, creative, files, growth
Each plugin: inherits BaseDomain, implements execute(), registers in plugin_manager.py
Adding new domain: create folder, write class, register. Nothing else breaks.
**Reasoning:** Modular = maintainable, extensible, debuggable in isolation.
---

### ADR-020: Risk Manager Hard Rules — Cannot Be Overridden
**Date:** 2026-05-24
**Status:** ACCEPTED
**Context:** Trading domain must protect Anant's capital. No request should bypass safety rules.
**Decision:** Risk manager enforces at code level (not prompt level — cannot be talked around):
1. Max 10% of capital per position
2. Stop trading for day if down 2%
3. Minimum 75% AI confidence required
4. Minimum 2:1 risk-reward ratio
Any trade proposal failing any rule → rejected automatically, Anant notified why.
**Reasoning:** Hardcoded rules cannot be accidentally or maliciously bypassed. Capital protection first.
---

### [APPENDED: 2026-06-05] — Semantic Memory & Sync Capabilities

### ADR-051: ChromaDB Local Vector Search integration
**Date:** 2026-06-05 | **Status:** ACCEPTED
**Context:** Context retrieval in SQLite LIKE search was limited to simple keyword queries.
**Decision:** Integrate ChromaDB local persistent store in core/conversation_store.py. Store document embeddings for user/manager roles. Fall back automatically to database keyword search if dependencies fail.
**Reasoning:** Offers semantic retrieval while maintaining a fail-safe SQLite lookup if hardware constraints occur.

### ADR-052: Unified Second Laptop Server Sync API
**Date:** 2026-06-05 | **Status:** ACCEPTED
**Context:** Background scanning from second laptop was disconnected with no server-side ingestion endpoint.
**Decision:** Added POST /api/sync endpoint to main.py and telemetry summary formatting in core/manager.py.
**Reasoning:** Binds the background server's data pipelines (market indices, jobs, social) to the main process cleanly.

### ADR-053: Robust yfinance Stock Alerts & Index Tracking
**Date:** 2026-06-05 | **Status:** ACCEPTED
**Context:** NSE India scraping frequently timed out due to anti-bot protection. Price alerts were stubs.
**Decision:** Integrated yfinance for index checks on the second laptop and alert triggers on the main machine.
**Reasoning:** Zero-auth, stable data querying across standard equities.

---

### [APPENDED: 2026-06-05] — Hands-free & Desktop Application Integrations

### ADR-054: Target Google Chrome browser binary
**Date:** 2026-06-05 | **Status:** ACCEPTED
**Context:** Chromium-based browsers trigger security block warnings on external API sites.
**Decision:** Implement `open_in_chrome` directly searching for the official `chrome.exe` on Windows (`Program Files`, `LocalAppData`) and register a background auto-launch task in `main.py`'s `lifespan` event.
**Reasoning:** Ensures secure setup access and automates UI dashboard opening on server start.

### ADR-055: Local Windows Desktop application execution
**Date:** 2026-06-05 | **Status:** ACCEPTED
**Context:** The agent lacked the ability to run local programs (like Notepad, Calculator, VS Code, or Chrome) upon user request.
**Decision:** Map application launch keywords to the `FilesAgent` intent classifier, check if inputs target common apps without file formats, and launch them via Python's `subprocess.Popen("start [cmd]", shell=True)` to run detached.
**Reasoning:** Grants local app startup capability safely under the files agent.

### ADR-056: Hands-free Continuous voice loops
**Date:** 2026-06-05 | **Status:** ACCEPTED
**Context:** The voice interaction was strictly push-to-talk, which interrupted continuous conversational flow.
**Decision:** Integrated a continuous voice mode toggle in `ui/dashboard.html` that automatically resumes SpeechRecognition listening once the manager's response concludes speaking. Includes automatic start on user gesture to satisfy browser autoplay constraints.
**Reasoning:** Delivers a hands-free voice experience that mimics a true personal assistant.



### ADR-057: Workable local core and evidence-based completion
**Date:** 2026-10-12 | **Status:** ACCEPTED
**Decision:** A single router discovers installed/local and provider catalog models, uses bounded requests, and reports actual readiness. Deterministic commands run without an LLM. Exact communication commands are required before the browser send path; extraction failure never supplies a contact. Generated project files are validated and saved, not auto-executed.
**Reason:** Prompt-only promises were being confused with executable integrations. Runtime data and confirmed outputs must determine what the assistant reports.

### ADR-058: Local tasks, authentication boundary and voice transport
**Date:** 2026-10-12 | **Status:** ACCEPTED
**Decision:** SQLite stores tasks/reminder delivery state; protected APIs provide dashboard access. Every private API and WebSocket requires a valid session. Explicit logout revokes it. The local microphone records float PCM at 16 kHz and sends it only to the local Whisper endpoint. Windows TTS remains serialized.
**Consequences:** Reminders need the running process. Browser SpeechRecognition is optional and may be online. Vector memory is opt-in. API keys are encrypted, but task/conversation databases remain plaintext local files.

### [APPENDED: 2026-10-12] Local passphrase recovery
Added RESET_PASSPHRASE.bat and setup/reset_passphrase.py. Local recovery stops the verified launcher, refuses reset while a server still listens, archives only the login hash, and reopens dashboard enrollment. Restart invalidates sessions; vault keys, history and tasks are preserved. Recovery preservation and repeated-reset checks passed. User requested recovery and the local login was reset.


### [APPENDED: 2026-10-12] Background document work
Implemented personal_context.py, workflows.py and assistant_work.py. Approved local folders and saved user messages supply evidence. Resume and document tasks run in the background, save real files and expose persistent progress in Work. Thirty regression tests and two real browser workflows passed. See ASSISTANT_WORK.md for commands, verification and limitations.


### [APPENDED: 2026-10-12] Project goal execution and acceptance app
Added core/project_work.py and core/project_tools.py: persistent architecture, typed source/dependency/runtime/browser tools, failure repair, requirement amendments, source-version acceptance gates, review and delivery. Builder routing now takes precedence for software goals; Work starts completed projects. Cloud preference for project coding respects local_only. See PROJECT_WORK.md for exact boundaries.

Verified 40 Manager regressions and real browser smoke including project launch. Career Studio (LinkedIn Optimizer and Resume Maker) passed 11 backend tests and actual browser downloads, edits and error checks. Its first generated draft needed direct repair; arbitrary unattended project completion is not established. Generated source executes with local user permissions; project environments are not an OS sandbox.

### [APPENDED: 2026-10-12] Outcome routing, stable task focus and relevant memory
Added core/goal_director.py and core/task_context.py. Manager routes supported outcome requests into executable workflows, keeps explicit workflow identity across background saves/restarts, retrieves attributed relevant user history, and reports actual saved progress. Work exposes current-task selection. Workflow APIs accept exact IDs; cancellation cannot target another running job. ProjectWork detects repetitive execution patterns and retries transient/format model failures once, preserving interrupted progress without weakening verification. See PROJECT_WORK.md for bounded scope and model limitations.


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                    MANAGER — MASTER STRUCTURE FILE                      ║
# ║                  THE LIVING LOG — PERSONAL & CONFIDENTIAL               ║
# ╠══════════════════════════════════════════════════════════════════════════╣
# ║                                                                          ║
# ║   ██████╗ CRITICAL RULES — READ BEFORE TOUCHING ANYTHING ██████╗        ║
# ║                                                                          ║
# ║   1. THIS FILE IS APPEND-ONLY. NEVER DELETE OR REPLACE ANY LINE.        ║
# ║   2. ALL FUTURE CHANGES → ADD AS NEW ENTRIES BELOW EXISTING ONES.       ║
# ║   3. NO CODE BLOCK EVER DELETED → ONLY COMMENT IT WITH REASON + DATE.   ║
# ║   4. EVERY COMMENT FORMAT: # [DATE] [REASON] [CAPABILITY/SOURCE]        ║
# ║   5. THIS FILE = SINGLE SOURCE OF TRUTH FOR THE ENTIRE PROJECT.         ║
# ║   6. ANY AI READING THIS FILE KNOWS THE FULL CONTEXT & CAN CONTINUE.    ║
# ║   7. IF YOU ARE AN AI: DO NOT REMOVE RULES. DO NOT REPLACE. APPEND.     ║
# ║   8. SHARING THIS FILE = SHARING FULL PROJECT CONTEXT INSTANTLY.        ║
# ║                                                                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝

---

## 📋 INDEX
1. [Project Identity](#1-project-identity)
2. [Vision & End Goal](#2-vision--end-goal)
3. [Owner](#3-owner)
4. [Hardware Specs](#4-hardware-specs)
5. [Tech Stack](#5-tech-stack)
6. [Complete Folder Architecture](#6-complete-folder-architecture)
7. [Phase Roadmap](#7-phase-roadmap)
8. [Domain Capabilities](#8-domain-capabilities)
9. [AI Routing Matrix](#9-ai-routing-matrix)
10. [Security Protocols](#10-security-protocols)
11. [Setup Rules](#11-setup-rules)
12. [Code Rules](#12-code-rules)
13. [Modification Log](#13-modification-log)

---

## 1. PROJECT IDENTITY

```
PROJECT NAME   : MANAGER
TYPE           : Personal AI Operating System
CLASSIFICATION : PRIVATE — OWNER USE ONLY
VERSION        : 0.1.0 — ARCHITECTURE PHASE
CREATED        : 2026-05-22
STATUS         : ARCHITECTURE COMPLETE — BUILD NOT STARTED
```

---

## 2. VISION & END GOAL

MANAGER is a fully autonomous, personal AI operating system built exclusively
for Anant. It is not a chatbot. It is not a tool. It is a system that thinks,
plans, executes, reviews, and delivers — across every domain of Anant's life.

### Core Philosophy
- One ask → Manager figures out everything else
- Manager works UNDER Anant — never over, never equal
- Zero limitations — if one path is blocked, find another
- Everything produced is super polished and production-grade
- Always on, always available, worldwide, private

### What Manager Does
- Manages Anant's finances: stocks, trading, gold, ETFs, portfolio
- Manages Anant's career: jobs, resume, interviews, cold emails
- Manages Anant's communication: calls, emails, WhatsApp, DMs
- Manages Anant's social media: Instagram, Facebook, LinkedIn, X
- Creates content: images, videos, reels, logos, copy, literature
- Builds projects: apps, automation, scripts, full products
- Accesses & organizes Anant's laptop files on both machines
- Coaches, teaches, researches, and executes on command
- Grows itself: adds new AI tools/skills after Anant's confirmation
- Speaks like Iron Man's FRIDAY — calm, composed, sharp

### End Goal
> Anant describes what he wants. Manager plans it, builds it, executes it,
> reviews it, polishes it, and delivers it — looking like a premium product.
> Every time. Without fail.

---

## 3. OWNER

```
NAME           : Anant
ACCESS LEVEL   : OWNER — FULL CONTROL
OTHERS         : NO ACCESS EVER — ZERO EXCEPTIONS
VERIFICATION   : Identity verified every session
```

---

## 4. HARDWARE SPECS

```
MAIN MACHINE
  Model        : Dell Alienware (Laptop)
  CPU          : Intel Core 7 240H (16 cores — Meteor Lake)
  GPU          : NVIDIA GeForce RTX 5060 Laptop GPU + Intel Integrated
  RAM          : 16GB (upgrade to 32GB recommended — high priority)
  Storage      : 1TB SSD (384GB free — external 2TB recommended)
  OS           : Windows 11
  Network      : 200 Mbps download

OLD LAPTOP (BACKGROUND SERVER)
  Model        : TBD — specs to be provided by Anant
  Role         : Always-on background server
                 Runs: scheduled agents, market monitor, scrapers,
                       background sync, secondary API key pool
  Status       : PENDING SPEC INPUT FROM ANANT

STORAGE TO ACQUIRE
  Recommended  : Kingston XS2000 2TB External SSD OR Upgrade internal
  Priority     : HIGH — current free space will fill fast with models

RAM UPGRADE
  Current      : 16GB
  Target       : 32GB DDR5
  Priority     : HIGH — needed for parallel agent execution
```

---

## 5. TECH STACK

### Core Language
```
Primary        : Python 3.11+
UI             : React 18 + Tailwind CSS
Automation     : n8n (self-hosted, free)
```

### Voice System
```
STT (Speech → Text)   : OpenAI Whisper (local, free, runs on RTX 5060)
TTS (Text → Voice)    : Coqui TTS (local, free) / ElevenLabs (free tier)
Wake Word             : Porcupine (free tier) — "Hey Manager"
```

### AI Models & Routing
```
Local LLM             : Ollama (free, runs on RTX 5060)
  └── Models          : Llama 3.1 8B, Mistral 7B, Phi-3
Remote Models         : Claude, GPT-4o, Gemini, Perplexity
Image Generation      : DALL-E 3, Flux, Stable Diffusion (local)
Video Generation      : Runway ML, Kling AI
Code Generation       : Codex, Claude, Gemini
Multi-Key Rotation    : Custom key manager — rotates before limit hits
```

### Backend
```
API Server            : FastAPI (Python)
WebSocket             : FastAPI WebSocket (real-time voice/chat)
Task Queue            : Celery + Redis (background jobs)
Database (local)      : SQLite (primary), ChromaDB (vector/memory)
Database (cloud sync) : Supabase (free tier — encrypted sync)
```

### Infrastructure
```
Private Network       : Tailscale (free — 3 devices, encrypted tunnel)
Process Manager       : PM2 (keeps Manager running always)
Version Control       : Git (local) + GitHub (private repo)
Workflow Engine       : n8n (self-hosted on old laptop)
Encryption            : AES-256 for all stored data & keys
```

### Domain-Specific Tools
```
Trading               : Zerodha Kite API / Fyers API / Angel One API
Web Automation        : Playwright (Python) — for API key fetching, scraping
Job Scanning          : LinkedIn unofficial API, Naukri scraper
Social Media          : Instagrapi (Instagram), Tweepy (X/Twitter)
Email                 : Gmail API, SMTP
File System           : Python pathlib, watchdog (file watcher)
OCR                   : Tesseract + Google Vision API (free tier)
```

---

## 6. COMPLETE FOLDER ARCHITECTURE

```
MANAGER/
│
├── MANAGER_STRUCTURE.md                    # THIS FILE — APPEND ONLY — NEVER DELETE
├── setup.bat                               # ONE-CLICK WINDOWS SETUP
├── setup.sh                                # Linux/Mac setup (old laptop)
├── requirements.txt                        # All Python dependencies
├── .env.example                            # API key template (committed)
├── .env                                    # ACTUAL KEYS — NEVER COMMITTED TO GIT
├── README.md                               # Basic project description
│
├── core/                                   # PHASE 1 — THE BRAIN OF MANAGER
│   ├── __init__.py
│   ├── main.py                             # Entry point — starts everything
│   │
│   ├── voice/                              # VOICE INTERFACE MODULE
│   │   ├── __init__.py
│   │   ├── stt.py                          # Speech-to-Text (Whisper local)
│   │   ├── tts.py                          # Text-to-Speech (Coqui/ElevenLabs)
│   │   ├── wake_word.py                    # "Hey Manager" detection
│   │   └── voice_pipeline.py              # Full voice I/O pipeline
│   │
│   ├── brain/                              # INTELLIGENCE LAYER
│   │   ├── __init__.py
│   │   ├── intent.py                       # Understand what Anant wants
│   │   ├── planner.py                      # Break request into subtasks
│   │   ├── orchestrator.py                 # Route subtasks to domains
│   │   ├── reviewer.py                     # Review output — correct or re-route
│   │   └── polisher.py                     # Polish output before delivery
│   │
│   ├── identity/                           # IDENTITY & AUTH MODULE
│   │   ├── __init__.py
│   │   ├── auth.py                         # Verify it is Anant
│   │   ├── voice_id.py                     # Voice fingerprint recognition
│   │   └── session.py                      # Session management & timeout
│   │
│   └── memory/                             # MEMORY MODULE
│       ├── __init__.py
│       ├── short_term.py                   # Current conversation context
│       ├── long_term.py                    # Persistent memory (ChromaDB)
│       └── context_builder.py             # Build context for each AI call
│
├── ai_router/                              # PHASE 1 — AI ORCHESTRATION LAYER
│   ├── __init__.py
│   ├── selector.py                         # Pick best AI per task (quality+cost)
│   ├── key_manager.py                      # Multi-key rotation per provider
│   ├── context_bridge.py                   # Preserve context on model switch
│   ├── usage_tracker.py                    # Track usage per key — proactive switch
│   └── models/                             # Individual model wrappers
│       ├── __init__.py
│       ├── claude.py                       # Anthropic Claude wrapper
│       ├── openai_gpt.py                   # OpenAI GPT wrapper
│       ├── gemini.py                       # Google Gemini wrapper
│       ├── local_llm.py                    # Ollama local model wrapper
│       ├── image_gen.py                    # DALL-E / Flux / SD wrapper
│       └── video_gen.py                    # Runway / Kling wrapper
│
├── domains/                                # MODULAR PLUGIN SYSTEM
│   ├── __init__.py
│   ├── plugin_manager.py                   # Load/unload/hot-swap plugins
│   ├── base_domain.py                      # Base class all domains inherit
│   │
│   ├── trading/                            # PHASE 2 — TRADING & FINANCE
│   │   ├── __init__.py
│   │   ├── market_data.py                  # Live market data fetching
│   │   ├── sentiment.py                    # News & sentiment analysis
│   │   ├── technical.py                    # Candlestick & technical analysis
│   │   ├── executor.py                     # Place buy/sell orders (demat)
│   │   ├── portfolio.py                    # Portfolio tracking & reporting
│   │   ├── gold_tracker.py                 # Gold/silver inventory + live price
│   │   └── risk_manager.py                 # Capital protection rules
│   │
│   ├── career/                             # PHASE 3 — CAREER & JOBS
│   │   ├── __init__.py
│   │   ├── job_scanner.py                  # Scan LinkedIn/Naukri/Indeed 24/7
│   │   ├── resume_engine.py                # Remaster resume per job (ATS)
│   │   ├── cold_email.py                   # Draft & send cold emails
│   │   ├── tracker.py                      # Track applications & follow-ups
│   │   └── interview_coach.py              # Mock interview + scoring
│   │
│   ├── communication/                      # PHASE 3 — COMMUNICATION
│   │   ├── __init__.py
│   │   ├── call_handler.py                 # Take calls on Anant's behalf
│   │   ├── call_summarizer.py              # Post-call: who, what, importance
│   │   ├── whatsapp.py                     # WhatsApp management
│   │   ├── email_manager.py                # Gmail read/write/send
│   │   └── dm_manager.py                   # DM management all platforms
│   │
│   ├── social/                             # PHASE 4 — SOCIAL MEDIA & BRAND
│   │   ├── __init__.py
│   │   ├── instagram.py                    # Instagram (personal + professional)
│   │   ├── content_creator.py             # Create reels, posts, captions
│   │   ├── scheduler.py                    # Post at peak engagement times
│   │   ├── analytics.py                    # Daily reach/follower/engagement
│   │   ├── brand_outreach.py              # Brand deal pipeline management
│   │   └── growth_strategy.py             # Weekly strategy adjustment
│   │
│   ├── builder/                            # PHASE 4 — PROJECT BUILDER
│   │   ├── __init__.py
│   │   ├── project_generator.py           # Idea → full production app
│   │   ├── code_reviewer.py               # Review & validate code output
│   │   ├── deployer.py                     # Deploy to Vercel/Railway/etc
│   │   └── n8n_workflows.py               # n8n automation pipeline builder
│   │
│   ├── creative/                           # PHASE 4 — CREATIVE STUDIO
│   │   ├── __init__.py
│   │   ├── image_gen.py                    # Posters, logos, thumbnails
│   │   ├── video_gen.py                    # Video & reel production
│   │   └── content_writer.py              # Scripts, copy, literature
│   │
│   └── files/                              # PHASE 1 — LOCAL FILE ACCESS
│       ├── __init__.py
│       ├── file_access.py                  # Read/write/search/navigate files
│       ├── organizer.py                    # Smart file organization
│       └── watcher.py                      # Watch folders for changes
│
├── infrastructure/                         # SYSTEM INFRASTRUCTURE
│   │
│   ├── server/                             # API SERVER
│   │   ├── __init__.py
│   │   ├── api.py                          # FastAPI main server
│   │   ├── routes.py                       # All API endpoints
│   │   └── websocket.py                    # Real-time voice/chat socket
│   │
│   ├── network/                            # PRIVATE NETWORK
│   │   ├── tunnel.py                       # Tailscale private tunnel setup
│   │   └── firewall.py                     # Block all unauthorized access
│   │
│   ├── storage/                            # DATA STORAGE
│   │   ├── local_db.py                     # SQLite — all local data
│   │   ├── vector_db.py                    # ChromaDB — memory & embeddings
│   │   ├── cloud_sync.py                   # Supabase encrypted sync
│   │   └── encryption.py                   # AES-256 encryption handler
│   │
│   └── old_laptop/                         # BACKGROUND SERVER (OLD LAPTOP)
│       ├── agent_server.py                 # Runs background agents 24/7
│       ├── market_monitor.py               # Always-on market watcher
│       ├── scheduler.py                    # Cron-style task scheduler
│       └── sync.py                         # Syncs state with main laptop
│
├── ui/                                     # USER INTERFACES
│   ├── dashboard/                          # WEB DASHBOARD (React)
│   │   ├── src/
│   │   │   ├── App.jsx
│   │   │   ├── components/
│   │   │   │   ├── VoiceOrb.jsx           # Voice interaction visual
│   │   │   │   ├── TaskFeed.jsx           # Live task execution feed
│   │   │   │   ├── DomainPanel.jsx        # Domain status panels
│   │   │   │   ├── TradeView.jsx          # Trading dashboard
│   │   │   │   └── SystemStatus.jsx       # System health & AI key status
│   │   │   └── index.jsx
│   │   └── package.json
│   │
│   └── visualizer/                         # OS VISUALIZER
│       └── MANAGER_VISUALIZER.jsx          # Cinematic system overview
│
├── keys/                                   # ENCRYPTED API KEY VAULT
│   ├── vault.enc                           # AES-256 encrypted key store
│   └── key_template.json                   # Template showing key structure
│
├── logs/                                   # ALL SYSTEM LOGS
│   ├── system.log                          # General system logs
│   ├── tasks.log                           # Every task executed
│   ├── trades.log                          # All trade actions & results
│   ├── ai_usage.log                        # AI model usage & key rotation
│   └── errors.log                          # All errors with stack traces
│
└── tests/                                  # TEST SUITE
    ├── test_core.py
    ├── test_ai_router.py
    └── test_domains.py
```

---

## 7. PHASE ROADMAP

```
╔═══════════════════════════════════════════════════════════════════╗
║  PHASE 01 — CORE + VOICE + IDENTITY + FILE ACCESS                ║
║  Target    : [DATE TO BE SET ON BUILD START]                      ║
║  Status    : NOT STARTED                                          ║
║  Includes  :                                                      ║
║    - Voice pipeline (STT + TTS + wake word)                       ║
║    - Brain: intent → planner → orchestrator → reviewer            ║
║    - Identity verification (only Anant)                           ║
║    - Memory system (short + long term)                            ║
║    - AI Router + multi-key rotation                               ║
║    - Local file access (both laptops)                             ║
║    - Private network (Tailscale)                                  ║
║    - FastAPI server + WebSocket                                   ║
║    - Encrypted key vault                                          ║
║    - Master structure file auto-update                            ║
║    - setup.bat (one-click install)                                ║
╠═══════════════════════════════════════════════════════════════════╣
║  PHASE 02 — TRADING & FINANCE ENGINE                              ║
║  Target    : [AFTER PHASE 01 COMPLETE]                            ║
║  Status    : NOT STARTED                                          ║
║  Includes  :                                                      ║
║    - Live market data (NSE/BSE)                                   ║
║    - Candlestick + technical analysis                             ║
║    - News sentiment engine                                        ║
║    - Demat account integration                                    ║
║    - Autonomous order execution                                   ║
║    - Portfolio tracker                                            ║
║    - Gold/silver/jewelry inventory + OCR                          ║
║    - Risk management rules                                        ║
╠═══════════════════════════════════════════════════════════════════╣
║  PHASE 03 — CAREER + COMMUNICATION                                ║
║  Target    : [AFTER PHASE 02 COMPLETE]                            ║
║  Status    : NOT STARTED                                          ║
║  Includes  :                                                      ║
║    - 24/7 job portal scanner                                      ║
║    - Resume engine (ATS-optimized per job)                        ║
║    - Cold email system                                            ║
║    - Application tracker                                          ║
║    - Interview coach + mock interviews                            ║
║    - Call handler (takes calls as Anant's manager)                ║
║    - WhatsApp + Gmail management                                  ║
║    - DM management across platforms                               ║
╠═══════════════════════════════════════════════════════════════════╣
║  PHASE 04 — SOCIAL MEDIA + CREATIVE + PROJECT BUILDER            ║
║  Target    : [AFTER PHASE 03 COMPLETE]                            ║
║  Status    : NOT STARTED                                          ║
║  Includes  :                                                      ║
║    - Instagram (personal + professional) full management          ║
║    - Reel creation pipeline (concept → post)                      ║
║    - Brand deal outreach + negotiation                            ║
║    - Image/video/content generation                               ║
║    - Project builder (idea → production app)                      ║
║    - n8n workflow automation                                      ║
╠═══════════════════════════════════════════════════════════════════╣
║  PHASE 05 — FULL INTEGRATION + SELF-GROWTH ENGINE                ║
║  Target    : [AFTER PHASE 04 COMPLETE]                            ║
║  Status    : NOT STARTED                                          ║
║  Includes  :                                                      ║
║    - All domains fully connected and communicating                ║
║    - Self-growth: scans for new AI tools weekly                   ║
║    - Asks Anant for confirmation → integrates new skill           ║
║    - Old laptop fully running as background server                ║
║    - Complete worldwide private network access                    ║
║    - Full cinematic dashboard live                                ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

## 8. DOMAIN CAPABILITIES

### MANAGER CORE
- Realistic Iron Man FRIDAY-style voice interaction
- Always works under Anant — never over, never equal
- One ask → full plan → execution → delivery
- Zero limitations — always finds a way
- Auto-selects best AI per task (quality + cost efficiency)
- Seamless AI switch on rate limit — zero interruption
- Multiple API keys per provider — rotates proactively before limit hits
- Tracks key usage in real-time — never waits for failure
- Modular plugin architecture — add/remove domains without breaking anything
- Self-growing — adds new skills after Anant's confirmation
- Regular scan for new tools & AI models in market
- Available worldwide via private encrypted Tailscale network

### WORKFLOW ENGINE (How Manager Works Internally)
```
USER REQUEST (voice/text)
       ↓
  BRAIN: INTENT — understand what Anant wants
       ↓
  BRAIN: PLANNER — break into precise subtasks
       ↓
  AI ROUTER: pick best AI + tool per subtask
       ↓
  DOMAINS: parallel execution by relevant agents
       ↓
  BRAIN: REVIEWER — is output correct?
    NO  → re-evaluate → re-route → execute again
    YES → continue
       ↓
  BRAIN: POLISHER — refine + add Manager's own perspective
       ↓
  DELIVER to Anant — presentable, cinematic, clear
```

### TRADING & FINANCE
- Live candlestick reading all patterns all timeframes
- News & sentiment scanning → trade signal generation
- FII/DII, Open Interest, Volume & order flow analysis
- Demat account integration — autonomous orders
- 1000-year trader logic — multi-signal confirmation only
- Knows when NOT to trade — equally important
- Portfolio tracking: stocks, ETFs, gold, silver, crypto
- Gold & jewelry inventory with live pricing + OCR bills
- Capital protection first — consistent net profit goal
- Self-improving strategy from every trade
- NSE/BSE primary — global markets expanding
- Never acts on single signal — always cross-confirms

### CAREER & JOBS
- 24/7 job portal scanning — LinkedIn, Naukri, Indeed, Wellfound
- Resume remastered per every application (ATS optimized)
- Cold emails to hiring managers, founders, recruiters
- Application tracking & auto follow-ups
- Interview coaching per specific company & role
- Mock interviews with live scoring & feedback
- Google XYZ formula applied to all experience bullets
- Diagnose → Score → Rewrite → Prep full loop

### COMMUNICATION
- Takes calls on Anant's behalf when unavailable
- Speaks as Anant's personal manager
- Post-call summary: who, what, importance, action needed
- WhatsApp, Gmail management & smart replies
- DM management across all platforms

### SOCIAL MEDIA & BRAND
- Instagram (personal + professional) fully managed
- Facebook, Twitter/X, LinkedIn — all platforms
- Reels created: concept → script → visual → posted
- Posted at peak engagement times — data driven
- Daily analytics report
- Brand deal outreach when account reaches eligibility
- Scales: micro → mid → major brand partnerships

### PROJECT BUILDER
- Idea → production-ready app — any language, any framework
- Full UI, backend, database, deployment pipeline
- n8n automation workflows & API integrations
- Modular — add/remove without breaking anything

### CREATIVE STUDIO
- Images: posters, logos, thumbnails, artwork — any style
- Video & reel production pipeline
- Literature, scripts, captions, copy — all formats
- Everything produced is cinematic and super polished

### FILE SYSTEM ACCESS
- Access, read, write, organize, search all files on both laptops
- Navigate folders, open files, move/rename on command
- Smart file organization
- Watch folders for changes

### PRIVACY & SECURITY
- Identity verified — only Anant can access — every session
- Data invisible to all outsiders — looks like empty space
- API providers cannot see or use Anant's data
- No company can train models on Anant's data — hard blocked
- Private encrypted Tailscale tunnel — worldwide access
- Multiple API keys encrypted — invisible externally
- Even on full breach — attacker sees nothing

---

## 9. AI ROUTING MATRIX

```
TASK TYPE          BEST MODEL           BACKUP 1        BACKUP 2
─────────────────────────────────────────────────────────────────
Code & Reasoning   Claude Sonnet        GPT-4o          Gemini Pro
Writing & Analysis GPT-4o               Claude          Gemini
Research (live)    Perplexity           Gemini          GPT-4o
Image Generation   DALL-E 3             Flux            SD Local
Video Generation   Runway ML            Kling AI        —
Local/Offline      Llama 3.1 (Ollama)   Mistral 7B      Phi-3
App Building       Claude + Codex       GPT-4o          Gemini
Fast & Cheap       Mistral (local)      Kimi K2         Gemini Flash
─────────────────────────────────────────────────────────────────

MULTI-KEY ROTATION RULES:
  - Each provider has a pool of API keys (Anthropic Key 1, Key 2, Key 3...)
  - Usage tracked per key in real-time
  - At 80% usage → proactive switch to next key
  - Never waits for failure — always ahead of the limit
  - On switch → full context preserved via context_bridge.py
  - Keys stored AES-256 encrypted in keys/vault.enc
  - Free tier keys multiplied = effectively unlimited usage
```

---

## 10. SECURITY PROTOCOLS

```
IDENTITY VERIFICATION
  Method         : Voice fingerprint + optional PIN
  Frequency      : Every new session
  Failure        : 3 attempts → session locked → Anant notified

DATA ENCRYPTION
  At rest        : AES-256 (all local data, keys, logs)
  In transit     : TLS 1.3 (all API calls)
  API Keys       : Stored only in encrypted vault — never plaintext

PRIVATE NETWORK
  Tool           : Tailscale (zero-config, end-to-end encrypted)
  Access         : Only Anant's devices on the Tailscale network
  Fallback       : WireGuard manual config if needed

DATA PRIVACY RULES (HARD — CANNOT BE OVERRIDDEN)
  - API calls stripped of identifying data before sending
  - No raw personal data ever sent to any AI provider
  - Anthropic, OpenAI, Google → receive task context only, not personal data
  - No provider can use Anant's data for model training
  - Even if hacked → attacker sees encrypted empty space
  - No cloud storage of sensitive data without encryption
  - Supabase sync = encrypted blobs only
```

---

## 11. SETUP RULES

```
ANANT'S MAXIMUM EFFORT:
  Step 1: Download the MANAGER project folder (zip or git clone)
  Step 2: Run setup.bat (Windows) — does everything automatically
  Step 3: If any service requires web login → Manager opens browser,
          navigates to the website, locates the API key,
          Anant logs in → Manager copies the key → done
  Step 4: Nothing else. Manager handles all configuration.

WHAT setup.bat DOES AUTOMATICALLY:
  - Installs Python 3.11 if not present
  - Installs all pip dependencies (requirements.txt)
  - Installs Node.js and npm packages for UI
  - Installs Ollama and downloads local models
  - Sets up SQLite database
  - Sets up ChromaDB for memory
  - Installs and configures Tailscale
  - Configures PM2 to keep Manager running always
  - Installs n8n (self-hosted)
  - Creates encrypted key vault
  - Runs initial identity setup (voice fingerprint capture)
  - Starts Manager — ready to use

AUTO-UPDATE RULE:
  - Any future change to Manager → setup.bat handles new dependencies
  - Anant never manually installs anything
  - Manager checks for updates on startup
  - New AI tools → asks Anant → installs after confirmation
```

---

## 12. CODE RULES

```
THESE RULES APPLY TO EVERY FILE IN THIS PROJECT — NO EXCEPTIONS:

1. NEVER DELETE CODE
   Bad  : (deleting a function)
   Good : # [2026-05-22] COMMENTED — reason: replaced by new_function.py
          # Source: core/brain/planner.py — capability: task planning
          # def old_function(): ...

2. EVERY COMMENT FORMAT
   # [YYYY-MM-DD] [REASON] [SOURCE FILE] [CAPABILITY]

3. FOLDER STRUCTURE IS FIXED
   - New capabilities → new file inside correct domain folder
   - Never create files outside the defined architecture
   - New domains → new folder inside domains/ → register in plugin_manager.py

4. STRUCTURE FILE
   - Updated after every meaningful change
   - New entry appended to Section 13 (Modification Log)
   - Never modify existing entries — only add new ones

5. EVERYTHING POLISHED
   - Every output from Manager = production quality
   - No raw JSON dumped to Anant — always formatted, readable
   - Every project Manager builds = looks like a premium product

6. MODULAR DOMAINS
   - Each domain inherits from base_domain.py
   - Adding a domain = create folder + register in plugin_manager.py
   - Removing a domain = comment it out in plugin_manager.py with reason
   - Zero other files touched on add/remove
```

---

## 13. MODIFICATION LOG

```
[APPEND ALL CHANGES BELOW — NEVER EDIT ABOVE ENTRIES]
─────────────────────────────────────────────────────────────────────────

[2026-05-22] CREATED — Initial architecture defined
  Source    : Anant + Claude (Anthropic) planning session
  What      : Complete project architecture designed
              - All 11 capability sets defined
              - Complete folder structure created
              - Tech stack decided
              - Phase 1-5 roadmap established
              - All code rules defined
  Status    : Architecture complete — build not started
  Next      : Begin Phase 1 implementation (Core + Voice + Identity)

─────────────────────────────────────────────────────────────────────────
[NEXT ENTRY GOES HERE — APPEND BELOW THIS LINE]
```

---

*End of MANAGER_STRUCTURE.md — Version 0.1.0 — 2026-05-22*
*This file is the property of Anant — Classified — No external access*

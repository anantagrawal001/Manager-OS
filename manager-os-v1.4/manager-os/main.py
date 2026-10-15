"""
MANAGER OS — Main Server
FILE: main.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
UPDATED: 2026-05-31 | Claude Sonnet 4.6 — PHASE A + PHASE B

PHASE A CHANGES (P0-2, P0-3, P0-4, P0-7, P0-8):
  P0-2: /api/auth endpoint — real passphrase verification, session tokens
  P0-3: host=127.0.0.1 (was 0.0.0.0 — LAN exposed)
        CORS tightened to localhost only
  P0-4: /api/key/add requires auth token + rate limited
  P0-7: TradingAlertManager.start() called in lifespan
  P0-8: manager.process() now routes through swarm for non-conversation intents

PHASE B CHANGES (P1-3, P1-5, P1-6, P1-10):
  P1-3: _init_extra_clients() called after key injection
  P1-5: record_usage() called after each successful router call
  P1-10: Caption WS — removed double-path bug, single path only

DO NOT DELETE ANY CODE — comment out with reason and date
"""

import asyncio
import json
import yaml
from pathlib import Path
from typing import Optional, Set
from contextlib import asynccontextmanager
from datetime import date

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from core.manager import Manager
from core.key_manager import KeyManager
from core.log_manager import LogManager
from core.router import AIRouter
from core.conversation_store import get_store
from security.auth import (
    verify_passphrase, create_session, validate_token,
    get_token_from_request, check_rate_limit, require_auth
)
from security.firewall import PrivacyFirewall
from agents.trading_agent import TradingAgent, TradingAlertManager
from agents.career_agent import CareerAgent
from agents.communication_agent import CommunicationAgent
from agents.social_agent import SocialAgent
from agents.builder_agent import BuilderAgent
from agents.creative_agent import CreativeAgent
from agents.life_agent import LifeAgent
from agents.files_agent import FilesAgent
from agents.growth_agent import GrowthAgent
from agents.research_agent import ResearchAgent
from agents.api_scout_agent import APIScoutAgent
from agents.self_heal_agent import SelfHealAgent
from agents.conversation_agent import ConversationAgent

manager: Optional[Manager] = None
log_manager: Optional[LogManager] = None
config: dict = {}
caption_connections: Set[WebSocket] = set()
chat_connections: Set[WebSocket] = set()
trading_alert_mgr: Optional[TradingAlertManager] = None
_bypass_auth: bool = False  # Set from config at boot
second_laptop_data: dict = {}  # Synced background metrics


def open_in_chrome(url: str):
    """Open a URL in Google Chrome browser (not Chromium) on Windows/OSX/Linux."""
    import subprocess
    import os
    import webbrowser

    # Common Chrome installation paths on Windows
    chrome_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]

    for path in chrome_paths:
        if os.path.exists(path):
            try:
                logger.info(f"Opening Chrome via direct path: {path}")
                subprocess.Popen([path, url])
                return True
            except Exception as e:
                logger.warning(f"Failed to launch Chrome from {path}: {e}")

    # Fallback to webbrowser registry registration for chrome
    try:
        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser("chrome"))
        chrome = webbrowser.get('chrome')
        logger.info("Opening Chrome via registered webbrowser client")
        chrome.open(url)
        return True
    except Exception as e:
        logger.warning(f"Failed to register/open chrome in webbrowser: {e}")

    # Fallback to system command start chrome
    try:
        logger.info("Attempting to open Chrome via system command 'start chrome'")
        os.system(f'start chrome "{url}"')
        return True
    except Exception as e:
        logger.warning(f"Failed start chrome command: {e}")

    # Final fallback to default system browser
    try:
        logger.info("Falling back to default system browser open")
        webbrowser.open(url)
        return True
    except Exception as e:
        logger.error(f"Failed all browser open attempts: {e}")
        return False


# Superseded 2026-10-12: retained for rollback; corrected implementation below.
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     global manager, log_manager, config, trading_alert_mgr, _bypass_auth
#
#     with open("config.yaml") as f:
#         config = yaml.safe_load(f)
#
#     _bypass_auth = config.get("auth", {}).get("bypass_in_development", True)
#
#     log_manager = LogManager()
#
#     # ── Load keys FIRST, inject into config, THEN init router ────────────────
#     key_manager = KeyManager(config)
#     loaded_keys = key_manager.get_all_keys_for_config()
#     config.setdefault("api_keys", {}).update(loaded_keys)
#     logger.info(f"Injected keys for: {list(loaded_keys.keys())}")
#
#     firewall = PrivacyFirewall(config)
#     router = AIRouter(config)
#     router.key_manager = key_manager
#
#     # P1-3: Call _init_extra_clients after keys loaded (was never called before)
#     if hasattr(router, '_init_extra_clients'):
#         router._init_extra_clients()
#
#     agents = {
#         "trading":       TradingAgent(config, router, firewall),
#         "career":        CareerAgent(config, router, firewall),
#         "communication": CommunicationAgent(config, router, firewall),
#         "social":        SocialAgent(config, router, firewall),
#         "builder":       BuilderAgent(config, router, firewall),
#         "creative":      CreativeAgent(config, router, firewall),
#         "life":          LifeAgent(config, router, firewall),
#         "files":         FilesAgent(config, router, firewall),
#         "growth":        GrowthAgent(config, router, firewall),
#         "research":      ResearchAgent(config, router, firewall),
#         "api_scout":     APIScoutAgent(config, router, firewall),
#         "self_heal":     SelfHealAgent(config, router, firewall),
#         "conversation":  ConversationAgent(config, router, firewall),
#     }
#
#     self_heal: SelfHealAgent = agents["self_heal"]
#     await self_heal.initialize()
#     await self_heal.start_watcher()
#
#     manager = Manager(config)
#     manager.agents = agents
#     manager.router = router
#     manager.firewall = firewall
#
#     # Register manager reference on all agents
#     for agent in agents.values():
#         agent.manager = manager
#
#     # P0-7: Start TradingAlertManager (was never started before)
#     trading_agent: TradingAgent = agents["trading"]
#     if hasattr(trading_agent, 'alert_manager'):
#         trading_alert_mgr = trading_agent.alert_manager
#     else:
#         trading_alert_mgr = TradingAlertManager(config, router)
#     asyncio.create_task(trading_alert_mgr.start())
#     logger.info("TradingAlertManager started — 8AM/4PM alerts scheduled")
#
#     # Wire caption broadcast → WebSocket clients
#     async def caption_broadcast(word: str):
#         dead = set()
#         payload = json.dumps({"type": "caption_word", "word": word})
#         for ws in set(caption_connections | chat_connections):
#             try:
#                 await ws.send_text(payload)
#             except Exception:
#                 dead.add(ws)
#         caption_connections.difference_update(dead)
#         chat_connections.difference_update(dead)
#
#     manager.voice.set_caption_callback(caption_broadcast)
#
#     # Wire speaking state broadcast → WebSocket clients
#     async def speaking_state_broadcast(state: str):
#         dead = set()
#         payload = json.dumps({"type": "speaking_state", "state": state})
#         for ws in set(caption_connections | chat_connections):
#             try:
#                 await ws.send_text(payload)
#             except Exception:
#                 dead.add(ws)
#         caption_connections.difference_update(dead)
#         chat_connections.difference_update(dead)
#
#     manager.voice.set_speaking_state_callback(speaking_state_broadcast)
#
#     # Wire health alerts
#     async def notify_sir(msg: str):
#         try:
#             await manager.speak(msg)
#         except Exception:
#             pass
#         payload = json.dumps({"type": "alert", "content": msg})
#         for ws in set(chat_connections):
#             try:
#                 await ws.send_text(payload)
#             except Exception:
#                 pass
#
#     manager.health.set_notify_callback(notify_sir)
#     self_heal.set_notify_callback(notify_sir)
#
#     # P0-8: Init swarm engine
#     manager.init_swarm()
#
#     boot_msg = await manager.boot()
#     logger.info(f"Manager OS online: {boot_msg}")
#     asyncio.create_task(manager.speak(boot_msg))
#
#     # Async boot-time key validation
#     asyncio.create_task(manager._validate_keys_and_report())
#
#     # NEW (2026-06-05): Auto-open dashboard in Google Chrome (not Chromium) on boot
#     async def auto_open():
#         await asyncio.sleep(2.0)
#         open_in_chrome("http://127.0.0.1:8000")
#     asyncio.create_task(auto_open())
#
#     yield
#
#     # Shutdown
#     await self_heal.stop_watcher()
#     if trading_alert_mgr:
#         trading_alert_mgr._running = False
#     await manager.voice.shutdown()
#     await manager.shutdown()
#     logger.info("Manager OS shutdown complete")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global manager, log_manager, config, trading_alert_mgr, _bypass_auth
    import os
    # Existing modules use relative storage paths; always anchor them to the project.
    os.chdir(Path(__file__).resolve().parent)
    with open(os.environ.get('MANAGER_CONFIG', 'config.yaml'), encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}
    import core.conversation_store as conversation_module
    conversation_module.DB_PATH = Path(config.get('conversation', {}).get('store_path', 'logs/conversations.db'))
    _bypass_auth = config.get('auth', {}).get('bypass_in_development', False)
    log_manager = LogManager()
    key_manager = KeyManager(config)
    config.setdefault('api_keys', {}).update(key_manager.get_all_keys_for_config())
    firewall = PrivacyFirewall(config)
    router = AIRouter(config)
    router.key_manager = key_manager
    classes = {'trading': TradingAgent, 'career': CareerAgent, 'communication': CommunicationAgent,
               'social': SocialAgent, 'builder': BuilderAgent, 'creative': CreativeAgent,
               'life': LifeAgent, 'files': FilesAgent, 'growth': GrowthAgent,
               'research': ResearchAgent, 'api_scout': APIScoutAgent,
               'self_heal': SelfHealAgent, 'conversation': ConversationAgent}
    agents = {name: cls(config, router, firewall) for name, cls in classes.items()}
    manager = Manager(config, router=router)
    manager.agents = agents
    manager.firewall = firewall
    background = []
    for agent in agents.values():
        agent.manager = manager
        await agent.initialize()

    async def broadcast(payload):
        for ws in set(chat_connections | caption_connections):
            try:
                if not _bypass_auth and not validate_token(ws.query_params.get('token', '')):
                    await ws.close(code=4001)
                    chat_connections.discard(ws)
                    caption_connections.discard(ws)
                    continue
                await ws.send_json(payload)
            except Exception:
                chat_connections.discard(ws)
                caption_connections.discard(ws)

    async def captions(word):
        await broadcast({'type': 'caption_word', 'word': word})

    async def speaking(state):
        await broadcast({'type': 'speaking_state', 'state': state})

    async def notify(msg):
        from core.activity_tracker import log_activity
        log_activity('reminder', msg)
        await manager.conv_store.save('manager', msg, intent='notification')
        await broadcast({'type': 'alert', 'content': msg})
        if os.environ.get('MANAGER_SILENT') != '1':
            await manager.speak(msg)

    manager.voice.set_caption_callback(captions)
    manager.voice.set_speaking_state_callback(speaking)
    manager.health.set_notify_callback(notify)
    agents['self_heal'].set_notify_callback(notify)
    if config.get('self_heal', {}).get('enabled', True):
        await agents['self_heal'].start_watcher()
    manager.init_swarm()
    await manager.boot()
    async def work_notify(message):
        await manager.conv_store.save('manager', message, intent='workflow')
        await broadcast({'type': 'alert', 'content': message})
    agents['career'].resume_workflow.notify = work_notify
    manager.document_work.notify = work_notify
    agents['builder'].project_work.notify = work_notify
    agents['life'].tasks.start(notify)
    # Unconnected external notification loops are not started automatically.
    trading_alert_mgr = None
    if config.get('trading_alerts', {}).get('enabled', False) and config.get('notifications', {}).get('telegram_enabled', False):
        trading_alert_mgr = TradingAlertManager(config, router)
        await trading_alert_mgr.start()
    background.append(asyncio.create_task(router.validate_keys_on_boot(), name='provider-check'))
    if config.get('ui', {}).get('auto_open_browser', True) and os.environ.get('MANAGER_NO_BROWSER') != '1':
        async def open_dashboard():
            await asyncio.sleep(1)
            open_in_chrome(f"http://127.0.0.1:{config.get('server', {}).get('port', 8000)}")
        background.append(asyncio.create_task(open_dashboard()))
    try:
        yield
    finally:
        await agents['builder'].project_work.close()
        await agents['self_heal'].stop_watcher()
        await agents['life'].tasks.close()
        career_task = getattr(agents['career'], 'active_apply_task', None)
        resume_task = agents['career'].resume_workflow.task
        if manager.document_work.task:
            background.append(manager.document_work.task)
        if resume_task:
            background.append(resume_task)
        if career_task:
            background.append(career_task)
        if trading_alert_mgr:
            await trading_alert_mgr.stop()
        for task in background:
            task.cancel()
        await asyncio.gather(*background, return_exceptions=True)
        await manager.voice.shutdown()
        await manager.shutdown()
        await router.close()
        rotation = getattr(log_manager, "_rotation_task", None)
        if rotation:
            rotation.cancel()
            await asyncio.gather(rotation, return_exceptions=True)
        logger.info('Manager OS shutdown complete')


# P0-3: Bind to localhost only; tighten CORS
app = FastAPI(title="Manager OS — PHANTOM", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    # OLD: allow_origins=["*"] — exposed to all origins on LAN
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000",
                   "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

ui_dir = Path("./ui")


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    f = ui_dir / "dashboard.html"
    return FileResponse(str(f)) if f.exists() else HTMLResponse("<h1>Manager OS starting...</h1>")


# ─── AUTH ─────────────────────────────────────────────────────────────────────

# Superseded 2026-10-12: retained for rollback; corrected implementation below.
# @app.post("/api/auth")
# async def auth_login(payload: dict, request: Request):
#     """P0-2: Passphrase → session token. Bypass when bypass_in_development: true."""
#     if _bypass_auth:
#         token = create_session()
#         return {"token": token, "bypass": True}
#
#     passphrase = payload.get("passphrase", "")
#     if not passphrase:
#         raise HTTPException(401, "Passphrase required")
#     if not verify_passphrase(passphrase):
#         logger.warning(f"Failed auth attempt from {request.client.host}")
#         raise HTTPException(401, "Invalid passphrase")
#
#     token = create_session()
#     return {"token": token}

@app.post('/api/auth')
async def auth_login(payload: dict, request: Request):
    from security.auth import load_passphrase_hash, enroll_passphrase
    client = request.client.host if request.client else 'local'
    if not check_rate_limit(f'login:{client}', 10):
        raise HTTPException(429, 'Too many attempts. Wait one minute.')
    passphrase = payload.get('passphrase', '')
    if not isinstance(passphrase, str):
        raise HTTPException(400, 'Passphrase must be text')
    if _bypass_auth:
        return {'token': create_session(), 'bypass': True}
    if not load_passphrase_hash():
        if not payload.get('enroll'):
            raise HTTPException(409, 'Create your passphrase first')
        try:
            enroll_passphrase(passphrase)
        except ValueError as exc:
            raise HTTPException(400, str(exc))
    if not verify_passphrase(passphrase):
        raise HTTPException(401, 'Invalid passphrase')
    return {'token': create_session()}


# Superseded 2026-10-12: retained for rollback; corrected implementation below.
# @app.get("/api/auth/check")
# async def auth_check(request: Request):
#     token = get_token_from_request(request)
#     return {"authenticated": validate_token(token) if token else False}

@app.get('/api/auth/check')
async def auth_check(request: Request):
    from security.auth import load_passphrase_hash
    token = get_token_from_request(request)
    return {'authenticated': bool(token and validate_token(token)),
            'enrollment_required': not bool(load_passphrase_hash()), 'bypass': _bypass_auth}


# ─── WEBSOCKET ─────────────────────────────────────────────────────────────────

# Superseded 2026-10-12: retained for rollback; corrected implementation below.
# @app.websocket("/ws")
# async def chat_ws(websocket: WebSocket):
#     # Validate token from query param
#     token = websocket.query_params.get("token", "")
#     if not _bypass_auth and not validate_token(token):
#         await websocket.close(code=4001)
#         return
#
#     await websocket.accept()
#     chat_connections.add(websocket)
#     logger.info("WebSocket client connected")
#
#     try:
#         while True:
#             raw = await websocket.receive_text()
#             payload = json.loads(raw)
#             content = payload.get("content", "").strip()
#             if not content:
#                 continue
#
#             await websocket.send_text(json.dumps({"type": "thinking", "content": "On it, Sir..."}))
#
#             # P0-8: Route through swarm (not just router)
#             response = await manager.process(content, input_type=payload.get("type", "text"))
#
#             await websocket.send_text(json.dumps({"type": "response", "content": response}))
#             asyncio.create_task(manager.speak(response))
#
#             # NEW (2026-06-05): Check if request is about agents, and push HUD data to the WebSocket
#             lower_content = content.lower()
#             if any(w in lower_content for w in ["tell me about agents", "show agents", "agent hud", "view agents", "agent status", "agents status", "buckle up"]):
#                 career_agent = manager.agents.get("career")
#                 career_status = "Idle"
#                 career_current = "Awaiting resume file for ATS checklist analysis."
#                 if career_agent and getattr(career_agent, "active_apply_task", None) and not career_agent.active_apply_task.done():
#                     career_status = f"Applying: {getattr(career_agent, 'current_job_search', '')}"
#                     career_current = f"Running LinkedIn job application loop for '{getattr(career_agent, 'current_job_search', '')}'."
#
#                 hud_data = {
#                     "type": "agent_hud",
#                     "agents": [
#                         {
#                             "key": "trading",
#                             "name": "Trading Agent",
#                             "status": "Scanning Watchlists",
#                             "color": "#f5c542",
#                             "current": "Monitoring watchlists & price target alerts.",
#                             "future": "Generate pre-market market briefs at 8:00 AM."
#                         },
#                         {
#                             "key": "career",
#                             "name": "Career Agent",
#                             "status": career_status,
#                             "color": "#4cefaa",
#                             "current": career_current,
#                             "future": "Auto-tailor custom cover letters for job boards."
#                         },
#                         {
#                             "key": "communication",
#                             "name": "Comms Agent",
#                             "status": "Standby",
#                             "color": "#5bb8f5",
#                             "current": "Checking outreach templates & drafted replies.",
#                             "future": "Prepare brief bulleted drafts for incoming emails."
#                         },
#                         {
#                             "key": "social",
#                             "name": "Social Agent",
#                             "status": "Idle Check",
#                             "color": "#a855f7",
#                             "current": "Drafting hooks and analyzing viral reel metrics.",
#                             "future": "Schedule social media posting pipeline sequences."
#                         },
#                         {
#                             "key": "builder",
#                             "name": "Builder Agent",
#                             "status": "Active Guard",
#                             "color": "#f55a5a",
#                             "current": "Scanning file changes to suggest clean improvements.",
#                             "future": "Build application components and write new scripts."
#                         },
#                         {
#                             "key": "creative",
#                             "name": "Creative Agent",
#                             "status": "Standby",
#                             "color": "#f97316",
#                             "current": "Ready to design logos, UI mockups, or image assets.",
#                             "future": "Generate high-fidelity branding mockups for marketing."
#                         },
#                         {
#                             "key": "life",
#                             "name": "Life OS Agent",
#                             "status": "Monitoring",
#                             "color": "#fb923c",
#                             "current": "Managing budget logs and tracking user task checklist.",
#                             "future": "Build morning briefing packet at 6:00 AM."
#                         },
#                         {
#                             "key": "research",
#                             "name": "Research Agent",
#                             "status": "Standby",
#                             "color": "#06b6d4",
#                             "current": "Standing by to verify facts and index papers.",
#                             "future": "Produce verified literature studies with citations."
#                         },
#                         {
#                             "key": "files",
#                             "name": "Files Agent",
#                             "status": "Indexing Active",
#                             "color": "#22c55e",
#                             "current": "Performing local document scans and semantic mapping.",
#                             "future": "Clean up temporary downloads and launch system apps."
#                         },
#                         {
#                             "key": "growth",
#                             "name": "Growth Agent",
#                             "status": "Analyzing",
#                             "color": "#3b82f6",
#                             "current": "Checking local host system GPU configuration details.",
#                             "future": "Propose workflow automations and download new tools."
#                         },
#                         {
#                             "key": "api_scout",
#                             "name": "API Scout Agent",
#                             "status": "Active Monitor",
#                             "color": "#ec4899",
#                             "current": "Checking for free premium model endpoints.",
#                             "future": "Rotates API keys and executes endpoint health checks."
#                         },
#                         {
#                             "key": "self_heal",
#                             "name": "Self-Heal Agent",
#                             "status": "Active Guard",
#                             "color": "#84cc16",
#                             "current": "Monitoring system logging loops for crash warning triggers.",
#                             "future": "Patch errors automatically and execute rollbacks."
#                         }
#                     ],
#                     "recommendations": [
#                         "Upload a resume file to test the Career Agent keyword scanner.",
#                         "Launch local applications by saying 'open notepad' or 'open calc'.",
#                         "Scan watchlists with the Trading Agent to see price target movements.",
#                         "Run a deep research query on local model fine-tuning with the Research Agent."
#                     ]
#                 }
#                 await websocket.send_text(json.dumps(hud_data))
#
#     except WebSocketDisconnect:
#         logger.info("WebSocket client disconnected")
#     except Exception as e:
#         logger.error(f"WebSocket error: {e}")
#         try:
#             await websocket.send_text(json.dumps({"type": "error", "content": str(e)[:100]}))
#         except Exception:
#             pass
#     finally:
#         chat_connections.discard(websocket)

@app.websocket('/ws')
async def chat_ws(websocket: WebSocket):
    token = websocket.query_params.get('token', '')
    origin = websocket.headers.get('origin')
    if origin and origin not in local_origins():
        await websocket.close(code=4003)
        return
    if not _bypass_auth and not validate_token(token):
        await websocket.close(code=4001)
        return
    await websocket.accept()
    chat_connections.add(websocket)
    seen = {}  # Per-connection replay protection. Never retry an action on reconnect.
    try:
        while True:
            raw = await websocket.receive_text()
            if not _bypass_auth and not validate_token(token):
                await websocket.close(code=4001)
                break
            try:
                payload = json.loads(raw)
                if not isinstance(payload, dict):
                    raise ValueError('Message must be an object')
                content = payload.get('content', '')
                if not isinstance(content, str) or not 0 < len(content.strip()) <= 12000:
                    raise ValueError('Enter a message between 1 and 12000 characters')
                request_id = str(payload.get('id', ''))[:100]
                if request_id and request_id in seen:
                    await websocket.send_json({'type': 'response', 'content': seen[request_id], 'id': request_id})
                    continue
                await websocket.send_json({'type': 'thinking', 'id': request_id})
                response = await manager.process(content.strip(), input_type=payload.get('type', 'text'))
                if request_id:
                    seen[request_id] = response
                    if len(seen) > 100:
                        seen.pop(next(iter(seen)))
                await websocket.send_json({'type': 'response', 'content': response, 'id': request_id})
                if payload.get('speak', False):
                    asyncio.create_task(manager.speak(response))
                if any(w in content.lower() for w in ['agents', 'buckle up', 'agent hud']):
                    await websocket.send_json({'type': 'agent_hud', 'agents': await agent_hud(), 'recommendations': []})
            except (ValueError, TypeError) as exc:
                await websocket.send_json({'type': 'error', 'content': str(exc)})
            except Exception as exc:
                logger.error(f'Chat request failed: {type(exc).__name__}')
                await websocket.send_json({'type': 'error', 'content': 'The request failed. Check Connections and try again.'})
    except WebSocketDisconnect:
        pass
    finally:
        chat_connections.discard(websocket)


# Superseded 2026-10-12: retained for rollback; corrected implementation below.
# @app.websocket("/ws/captions")
# async def captions_ws(websocket: WebSocket):
#     """P1-10: Dedicated caption stream — single path, no double-send bug."""
#     await websocket.accept()
#     caption_connections.add(websocket)
#     try:
#         while True:
#             await websocket.receive_text()  # keepalive
#     except WebSocketDisconnect:
#         pass
#     finally:
#         caption_connections.discard(websocket)

@app.websocket('/ws/captions')
async def captions_ws(websocket: WebSocket):
    token = websocket.query_params.get('token', '')
    if not _bypass_auth and not validate_token(token):
        await websocket.close(code=4001)
        return
    if websocket.headers.get('origin') and websocket.headers['origin'] not in local_origins():
        await websocket.close(code=4003)
        return
    await websocket.accept()
    caption_connections.add(websocket)
    try:
        while True:
            await websocket.receive_text()
            if not _bypass_auth and not validate_token(token):
                await websocket.close(code=4001)
                break
    except WebSocketDisconnect:
        pass
    finally:
        caption_connections.discard(websocket)


# ─── CORE API ─────────────────────────────────────────────────────────────────

# Superseded 2026-10-12: retained for rollback; corrected implementation below.
# @app.get("/api/status")
# async def status():
#     agent_statuses = await manager.health.get_all_statuses()
#     hw = manager.health.get_hardware_summary()
#     router_status = manager.router.get_status()
#     return {
#         "status": "online",
#         "agents": agent_statuses,
#         "hardware": hw,
#         "ai_router": router_status,
#         "message": manager.health.get_summary(),
#     }

@app.get('/api/status')
async def status():
    agents = {}
    for name, agent in manager.agents.items():
        try:
            agents[name] = await agent.get_status()
            agents[name]['state'] = 'ready' if agent._initialized else 'not_initialized'
        except Exception:
            agents[name] = {'healthy': False, 'state': 'failed'}
    return {'status': 'online', 'agents': agents, 'hardware': manager.health.get_hardware_summary(),
            'ai_router': manager.router.get_status(), 'message': 'Local dashboard running'}


@app.get("/api/history")
async def history(limit: int = 100, request: Request = None):
    store = get_store()
    return {"history": await store.get_history(max(1, min(limit, 500)))}


@app.post("/api/search")
async def search(payload: dict):
    store = get_store()
    return {"results": await store.search(payload.get("query", ""))}


# Superseded 2026-10-12: retained for rollback; corrected implementation below.
# @app.post("/api/chat")
# async def chat_rest(payload: dict, request: Request):
#     content = payload.get("message", "")
#     if not content:
#         raise HTTPException(400, "No message")
#     response = await manager.process(content)
#     asyncio.create_task(manager.speak(response))
#     return {"response": response}

@app.post('/api/chat')
async def chat_rest(payload: dict, request: Request):
    content = payload.get('message', '')
    if not isinstance(content, str) or not 0 < len(content.strip()) <= 12000:
        raise HTTPException(400, 'Enter a message between 1 and 12000 characters')
    response = await manager.process(content.strip())
    if payload.get('speak', False):
        asyncio.create_task(manager.speak(response))
    return {'response': response}


# P0-4: /api/key/add requires auth + rate limited
@app.post("/api/key/add")
async def add_key(payload: dict, request: Request):
    # Auth check
    token = get_token_from_request(request)
    if not _bypass_auth and not validate_token(token):
        raise HTTPException(401, "Authentication required")

    # Rate limit: 5 key additions per minute
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(f"key_add_{client_ip}", max_per_minute=5):
        raise HTTPException(429, "Too many requests — try again in a minute")

    from core.provider_names import CLOUD_PROVIDERS
    provider = payload.get("provider", "")
    if not isinstance(provider, str) or provider not in CLOUD_PROVIDERS:
        raise HTTPException(400, "Choose a supported provider")
    if not isinstance(payload.get("key"), str):
        raise HTTPException(400, "API key must be text")
    key = payload.get("key", "").strip()

    # P1-9: Validate non-empty key
    if not provider:
        raise HTTPException(400, "provider required")
    if not key or len(key) < 8:
        raise HTTPException(400, "key is empty or too short — paste the full API key")

    manager.router.key_manager.add_key(provider, key, "manual_add")
    manager.router.update_keys({provider: key})
    logger.info(f"Key added for {provider} via API")
    return {"status": "ok", "message": f"Key saved for {provider}"}


@app.post("/api/sync")
async def sync_data(payload: dict):
    """Sync data from the background second laptop."""
    global second_laptop_data
    source = payload.get("source", "unknown")
    if source == "second_laptop":
        data = payload.get("data", {})
        second_laptop_data.update(data)
        logger.info(f"Synced background data from second laptop: {list(data.keys())}")
        return {"status": "ok", "synced_keys": list(data.keys())}
    raise HTTPException(status_code=400, detail="Invalid sync source")


# Superseded 2026-10-12: retained for rollback; corrected implementation below.
# @app.get("/api/providers")
# async def providers():
#     s = manager.router.get_status()
#     return {
#         "working": s.get("working_providers", []),
#         "available": s.get("available_models", []),
#         "blocked": s.get("blocked_models", []),
#         "calls_today": s.get("call_counts", {}),
#     }

@app.get('/api/providers')
async def providers():
    return manager.router.get_status()


# Superseded 2026-10-12: retained for rollback; corrected implementation below.
# @app.post("/api/morning-briefing")
# async def morning_briefing():
#     hw = manager.health.get_hardware_summary()
#     briefing = manager.get_morning_briefing(hw=hw, working_providers=manager.router.working_providers)
#     asyncio.create_task(manager.speak(briefing))
#     return {"briefing": briefing}

@app.post('/api/morning-briefing')
async def morning_briefing():
    briefing = await manager.agents['life'].execute('morning briefing', {})
    return {'briefing': briefing}


@app.get("/api/logs/recent")
async def recent_logs():
    log_dir = Path("./logs")
    today_log = log_dir / f"manager_{date.today().isoformat()}.log"
    if today_log.exists():
        lines = today_log.read_text(errors="ignore").split("\n")
        return {"logs": lines[-100:]}
    return {"logs": []}


@app.get("/api/swarm/status")
async def swarm_status():
    if manager and hasattr(manager, 'swarm') and manager.swarm:
        return manager.swarm.get_status()
    return {"status": "not initialized"}


@app.post("/api/swarm/hook")
async def add_hook(payload: dict, request: Request):
    token = get_token_from_request(request)
    if not _bypass_auth and not validate_token(token):
        raise HTTPException(401, "Auth required")
    if manager and hasattr(manager, 'swarm'):
        manager.swarm.add_hook(
            name=payload.get("name", "custom"),
            keywords=payload.get("keywords", []),
            agent=payload.get("agent", "conversation"),
            confidence=float(payload.get("confidence", 0.8)),
        )
    return {"status": "ok"}


@app.get("/api/self-heal/report")
async def self_heal_report():
    if manager and "self_heal" in manager.agents:
        return {"report": manager.agents["self_heal"]._fixes_summary()}
    return {"report": "Not available"}


@app.get('/client.js')
async def client_script():
    return FileResponse(str(ui_dir / 'runtime.js'), media_type='application/javascript')


@app.get('/api/outputs')
async def list_outputs():
    root = Path('outputs').resolve()
    if not root.exists():
        return {'files': []}
    files = []
    for path in root.rglob('*'):
        if path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root):
            files.append({'path': path.relative_to(root).as_posix(), 'size': path.stat().st_size})
            if len(files) >= 200:
                break
    return {'files': files}


@app.get('/api/workflows')
async def list_workflows():
    career = manager.agents.get('career') if manager else None
    workflow = getattr(career, 'resume_workflow', None)
    if not workflow:
        return {'workflows': []}
    focused = manager.goal_director.focused()
    # Do not put extracted private source text into the status panel.
    return {'workflows': [{key: job.get(key) for key in
        ['id', 'kind', 'request', 'status', 'steps', 'outputs', 'updated', 'question', 'error', 'preview_url', 'project_path']}
        for job in workflow.store.list()], 'focused_workflow_id': focused['id'] if focused else None}


@app.post('/api/workflows/{workflow_id}/focus')
async def focus_workflow(workflow_id: str):
    director = getattr(manager, 'goal_director', None)
    if not director:
        raise HTTPException(503, 'Task director is not ready')
    job = director.store.get(workflow_id)
    if not job or job.get('kind') not in {'project','document','resume'}:
        raise HTTPException(404, 'Work item not found')
    director.remember(job['kind'], job['id'])
    return {'focused_workflow_id': job['id']}


@app.get('/api/outputs/download')
async def download_output(path: str):
    root = Path('outputs').resolve()
    target = (root / path).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise HTTPException(404, 'Output not found')
    return FileResponse(str(target), filename=target.name, media_type='application/octet-stream')


@app.post('/api/auth/logout')
async def logout(request: Request):
    from security.auth import revoke_session
    revoke_session(get_token_from_request(request))
    return {'logged_out': True}


@app.post('/api/projects/{project_id}/open')
async def open_built_project(project_id: str):
    builder = manager.agents.get('builder') if manager else None
    workflow = getattr(builder, 'project_work', None)
    if not workflow:
        raise HTTPException(503, 'Project builder is not ready')
    job = next((item for item in workflow.store.list('project') if item['id'] == project_id), None)
    if not job or not job.get('launch'):
        raise HTTPException(404, 'Project has no saved launch command')
    message = await workflow.open_project(job)
    return {'message': message, 'url': job.get('preview_url')}


@app.post('/api/voice/transcribe')
async def transcribe_voice(request: Request):
    import numpy as np
    import importlib.util
    if not check_rate_limit('local_transcription', 6):
        raise HTTPException(429, 'Please wait before recording again')
    if not importlib.util.find_spec('whisper'):
        raise HTTPException(503, 'Local voice is not installed. Run SETUP_VOICE.bat.')
    audio_bytes = bytearray()
    async for chunk in request.stream():
        audio_bytes.extend(chunk)
        if len(audio_bytes) > 16000 * 4 * 30:
            raise HTTPException(413, 'Recording must be under 30 seconds')
    if len(audio_bytes) < 1600 or len(audio_bytes) % 4:
        raise HTTPException(400, 'Record at least a short phrase')
    audio = np.frombuffer(audio_bytes, dtype='<f4').copy()
    if not np.isfinite(audio).all() or np.max(np.abs(audio)) > 1.1:
        raise HTTPException(400, 'Invalid microphone audio')
    if np.max(np.abs(audio)) < .001:
        return {'text': ''}
    voice = manager.voice
    async with voice._transcribe_lock:
        if voice.whisper_model is None:
            cache = Path.home() / '.cache' / 'whisper' / f'{voice.whisper_model_size}.pt'
            if not cache.exists():
                raise HTTPException(503, 'Local speech model is missing. Run SETUP_VOICE.bat.')
            await asyncio.to_thread(voice._load_whisper_lazy)
        if voice.whisper_model is None:
            raise HTTPException(503, 'Local speech engine could not load')
        text = await asyncio.to_thread(voice._transcribe, audio)
    if text is None:
        raise HTTPException(503, 'Transcription failed. Text input is still available.')
    return {'text': text.strip()}


def local_origins():
    port = config.get('server', {}).get('port', 8000)
    return {f'http://127.0.0.1:{port}', f'http://localhost:{port}'}


@app.middleware('http')
async def protect_api(request: Request, call_next):
    if request.url.path.startswith('/api/'):
        origin = request.headers.get('origin')
        if origin and origin not in local_origins():
            return JSONResponse({'detail': 'Origin not allowed'}, status_code=403)
        public = {'/api/auth', '/api/auth/check', '/api/health'}
        if request.url.path not in public and request.method != 'OPTIONS':
            if not _bypass_auth and not validate_token(get_token_from_request(request)):
                return JSONResponse({'detail': 'Authentication required'}, status_code=401)
            if manager is None:
                return JSONResponse({'detail': 'Starting up'}, status_code=503)
    return await call_next(request)


@app.get('/api/health')
async def health_check():
    return {'ready': manager is not None and manager.active}


@app.post('/api/providers/check')
async def check_providers(request: Request):
    if not check_rate_limit('provider_checks', 3):
        raise HTTPException(429, 'Please wait before checking again')
    await manager.router.validate_keys_on_boot()
    return manager.router.get_status()


@app.get('/api/tasks')
async def list_tasks():
    return {'tasks': manager.agents['life'].tasks.list()}


@app.post('/api/tasks')
async def create_task(payload: dict):
    from datetime import datetime
    title = payload.get('title')
    due = payload.get('due_at') or None
    if not isinstance(title, str):
        raise HTTPException(400, 'Task title required')
    try:
        if due:
            parsed = datetime.fromisoformat(due)
            if parsed.tzinfo is not None:
                raise ValueError('Use a local date and time')
            if parsed <= datetime.now():
                raise ValueError('Reminder time must be in the future')
        task_id = manager.agents['life'].tasks.add(title, due)
    except (ValueError, TypeError) as exc:
        raise HTTPException(400, str(exc))
    return {'id': task_id, 'saved': True}


@app.post('/api/tasks/{task_id}/complete')
async def complete_task(task_id: int):
    if not manager.agents['life'].tasks.complete(task_id):
        raise HTTPException(404, 'Open task not found')
    return {'completed': True}


async def agent_hud():
    result = []
    descriptions = {
        'life': 'Local tasks and reminders are saved on this computer.',
        'files': 'Local file search, text files and supported app launches.',
        'conversation': 'Search saved conversation history.',
        'communication': 'WhatsApp needs browser sign-in; calls are simulated; email is draft only.',
        'career': 'Resume drafts and browser job search; sign-in required.',
        'trading': 'Analysis and paper mode. No live broker connected.',
        'social': 'Content drafts. Publishing account not connected.',
        'self_heal': 'Log monitoring; automatic recovery is limited.',
    }
    for name, agent in manager.agents.items():
        busy = any(name in t.assigned_agents for t in manager.swarm.active_tasks.values())
        result.append({'key': name, 'name': name.replace('_', ' ').title(),
                       'status': 'Working' if busy else 'Ready', 'color': '#5bb8f5',
                       'current': descriptions.get(name, 'AI-assisted drafts and analysis when a model is connected.'),
                       'future': ''})
    return result


if __name__ == "__main__":
    # P0-3: host 127.0.0.1 — localhost only, not LAN exposed
    # OLD: host="0.0.0.0"
    import os
    os.chdir(Path(__file__).resolve().parent)
    with open('config.yaml', encoding='utf-8') as f:
        launch_config = yaml.safe_load(f) or {}
    uvicorn.run("main:app", host="127.0.0.1", port=int(launch_config.get('server', {}).get('port', 8000)), reload=False, log_level="info")

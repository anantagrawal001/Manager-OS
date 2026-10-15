from pathlib import Path
from setup.source_edit import replace_definition as replace

replace('main.py', 'lifespan', '''@asynccontextmanager
async def lifespan(app: FastAPI):
    global manager, log_manager, config, trading_alert_mgr, _bypass_auth
    import os
    # Existing modules use relative storage paths; always anchor them to the project.
    os.chdir(Path(__file__).resolve().parent)
    with open('config.yaml', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}
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
        await agents['self_heal'].stop_watcher()
        await agents['life'].tasks.close()
        career_task = getattr(agents['career'], 'active_apply_task', None)
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
        logger.info('Manager OS shutdown complete')
''')

replace('main.py', 'auth_login', '''@app.post('/api/auth')
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
''')
replace('main.py', 'auth_check', '''@app.get('/api/auth/check')
async def auth_check(request: Request):
    from security.auth import load_passphrase_hash
    token = get_token_from_request(request)
    return {'authenticated': bool(token and validate_token(token)),
            'enrollment_required': not bool(load_passphrase_hash()), 'bypass': _bypass_auth}
''')

replace('main.py', 'chat_ws', '''@app.websocket('/ws')
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
''')
replace('main.py', 'captions_ws', '''@app.websocket('/ws/captions')
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
''')
replace('main.py', 'status', '''@app.get('/api/status')
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
''')
replace('main.py', 'chat_rest', '''@app.post('/api/chat')
async def chat_rest(payload: dict, request: Request):
    content = payload.get('message', '')
    if not isinstance(content, str) or not 0 < len(content.strip()) <= 12000:
        raise HTTPException(400, 'Enter a message between 1 and 12000 characters')
    response = await manager.process(content.strip())
    if payload.get('speak', False):
        asyncio.create_task(manager.speak(response))
    return {'response': response}
''')
replace('main.py', 'morning_briefing', '''@app.post('/api/morning-briefing')
async def morning_briefing():
    briefing = await manager.agents['life'].execute('morning briefing', {})
    return {'briefing': briefing}
''')
replace('main.py', 'providers', '''@app.get('/api/providers')
async def providers():
    return manager.router.get_status()
''')
p = Path('main.py')
s = p.read_text(encoding='utf-8')
pos = s.index('\nif __name__ == "__main__":')
new = '''
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
async def check_providers():
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

'''
s = s[:pos] + new + s[pos:]
s = s.replace('_bypass_auth: bool = True', '_bypass_auth: bool = False')
s = s.replace('    provider = payload.get("provider", "").strip()', '''    from core.provider_names import CLOUD_PROVIDERS
    provider = payload.get("provider", "")
    if not isinstance(provider, str) or provider not in CLOUD_PROVIDERS:
        raise HTTPException(400, "Choose a supported provider")
    if not isinstance(payload.get("key"), str):
        raise HTTPException(400, "API key must be text")''')
s = s.replace('return {"history": await store.get_history(limit)}', 'return {"history": await store.get_history(max(1, min(limit, 500)))}')
s = s.replace('    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False, log_level="info")', '''    import os
    os.chdir(Path(__file__).resolve().parent)
    with open('config.yaml', encoding='utf-8') as f:
        launch_config = yaml.safe_load(f) or {}
    uvicorn.run("main:app", host="127.0.0.1", port=int(launch_config.get('server', {}).get('port', 8000)), reload=False, log_level="info")''')
p.write_text(s, encoding='utf-8')

replace('security/auth.py', 'verify_passphrase', '''def verify_passphrase(passphrase):
    stored = load_passphrase_hash()
    if not stored or not isinstance(passphrase, str):
        return False
    if stored.startswith('v2$'):
        _, salt, expected = stored.split('$')
        actual = hashlib.pbkdf2_hmac('sha256', passphrase.encode(), bytes.fromhex(salt), 600000).hex()
        return hmac.compare_digest(actual, expected)
    return hmac.compare_digest(_hash_passphrase(passphrase), stored)


def enroll_passphrase(passphrase):
    if len(passphrase) < 8:
        raise ValueError('Use at least 8 characters for your passphrase')
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', passphrase.encode(), salt, 600000).hex()
    PASSPHRASE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with PASSPHRASE_FILE.open('x', encoding='utf-8') as f:
            f.write(f'v2${salt.hex()}${digest}')
    except FileExistsError:
        raise ValueError('Already enrolled. Sign in with your existing passphrase.')
''')

replace('core/voice.py', 'VoiceEngine.speak', '''    async def speak(self, text):
        if not text or not self.config.get('voice', {}).get('enabled', True):
            return
        import re
        text = re.sub(r'```[\\s\\S]*?```', 'Code is available in the chat.', text)
        text = re.sub(r'[*#`]', '', text)[:3000]
        async with self._speak_lock:
            if self._speaking_state_callback:
                await self._speaking_state_callback('start')
            captions = asyncio.create_task(self._stream_captions(text))
            try:
                if self.tts_engine == 'edge':
                    try:
                        await asyncio.wait_for(self._speak_edge_tts(text), 30)
                        return
                    except Exception:
                        pass
                if _PYTTSX3_AVAILABLE:
                    _ensure_tts_worker()
                    event = threading.Event()
                    _tts_queue.put((text, event))
                    await asyncio.to_thread(event.wait, 120)
            finally:
                captions.cancel()
                await asyncio.gather(captions, return_exceptions=True)
                if self._speaking_state_callback:
                    await self._speaking_state_callback('stop')
''')
p = Path('core/voice.py')
s = p.read_text(encoding='utf-8').replace('        self.config = config', '        self.config = config\n        self._speak_lock = asyncio.Lock()', 1)
s = s.replace('        _ensure_tts_worker()\n\n        try:', '        # Speech worker starts only when speech is requested.\n\n        try:', 1)
p.write_text(s, encoding='utf-8')

replace('agents/trading_agent.py', 'TradingAlertManager.start', '''    async def start(self):
        self._running = True
        self._tasks = [asyncio.create_task(self._morning_brief_loop()),
                       asyncio.create_task(self._price_alert_loop()),
                       asyncio.create_task(self._evening_report_loop())]

    async def stop(self):
        self._running = False
        for task in getattr(self, '_tasks', []):
            task.cancel()
        await asyncio.gather(*getattr(self, '_tasks', []), return_exceptions=True)
''')
print('Server, auth and voice migration complete')

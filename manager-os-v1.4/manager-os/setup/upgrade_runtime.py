"""One-time source migration; old definitions remain commented for rollback."""
from pathlib import Path
from setup.source_edit import replace_definition as replace


replace('core/router.py', 'AIRouter', '''class AIRouter:
    MANAGER_SYSTEM_PROMPT = """You are Manager, Anant's personal assistant. Address him as Sir.
Be concise and truthful. Only report an action as completed when a tool result confirms it.
Text generation alone does not send messages, create files, apply for jobs or execute trades.
If a connection or input is missing, state exactly what is needed. Never invent live data,
agent activity, account access, memories or successful actions. Follow the requested output
format exactly, including JSON or extraction-only requests."""

    def __init__(self, config):
        from core.ollama_client import OllamaClient
        self.config = config
        self.key_manager = None
        self.tracker = ModelLimitTracker()
        self.working_providers = []
        self.last_provider_used = None
        self.last_model_used = None
        self._clients = {}
        self._models = {}
        self._provider_state = {}
        self._retired_clients = []
        self._local = OllamaClient()
        self._local.base_url = config.get('ai_router', {}).get('ollama_url', 'http://127.0.0.1:11434')
        self._init_clients()

    def _init_clients(self):
        endpoints = {
            GROQ: 'https://api.groq.com/openai/v1',
            GOOGLE: 'https://generativelanguage.googleapis.com/v1beta/openai/',
            OPENAI: 'https://api.openai.com/v1',
            NVIDIA: 'https://integrate.api.nvidia.com/v1',
            CEREBRAS: 'https://api.cerebras.ai/v1',
            OPENROUTER: 'https://openrouter.ai/api/v1',
            DEEPSEEK: 'https://api.deepseek.com/v1',
            GITHUB_MODELS: 'https://models.inference.ai.azure.com',
        }
        keys = self.config.get('api_keys', {})
        for provider, url in endpoints.items():
            key = keys.get(provider)
            if key and provider not in self._clients:
                self._clients[provider] = AsyncOpenAI(api_key=key, base_url=url, timeout=15, max_retries=0)
                self._provider_state[provider] = {'state': 'not_tested'}
        if keys.get(ANTHROPIC) and ANTHROPIC not in self._clients:
            self._clients[ANTHROPIC] = anthropic.AsyncAnthropic(api_key=keys[ANTHROPIC], timeout=15, max_retries=0)
            self._provider_state[ANTHROPIC] = {'state': 'not_tested'}
        self._clients[OLLAMA] = self._local
        self._provider_state.setdefault(OLLAMA, {'state': 'not_tested'})

    def _init_extra_clients(self):
        self._init_clients()

    def update_keys(self, api_keys):
        self.config.setdefault('api_keys', {}).update(api_keys)
        for provider in api_keys:
            old = self._clients.pop(provider, None)
            if old:
                self._retired_clients.append(old)
            self._models.pop(provider, None)
            self.tracker.blocked.discard(provider)
            self.tracker.cooldown_until.pop(provider, None)
            if provider in self.working_providers:
                self.working_providers.remove(provider)
        self._init_clients()

    async def _discover(self, provider):
        override = self.config.get('ai_router', {}).get('models', {}).get(provider)
        if override:
            return [override] if isinstance(override, str) else list(override)
        if provider in self._models:
            return self._models[provider]
        # Provider catalogs are the source of truth, avoiding stale hard-coded IDs.
        try:
            response = await asyncio.wait_for(self._clients[provider].models.list(), timeout=8)
            available = [m.id.removeprefix('models/') for m in response.data]
            preferred = [m for m in PROVIDER_MODELS.get(provider, []) if m in available]
            if provider == GOOGLE:
                preferred = sorted([m for m in available if 'gemini' in m and 'flash' in m
                                    and not any(x in m for x in ['image', 'audio', 'tts', 'live', 'exp', 'preview'])], reverse=True)
            elif provider == ANTHROPIC:
                preferred = sorted([m for m in available if 'haiku' in m], reverse=True) + sorted([m for m in available if 'sonnet' in m], reverse=True)
            elif provider == OPENROUTER:
                preferred = [m for m in available if m.endswith(':free')]
            elif not preferred:
                preferred = [m for m in available if any(x in m.lower() for x in ['llama', 'gpt', 'deepseek-chat'])
                             and not any(x in m.lower() for x in ['guard', 'embed', 'audio', 'vision'])]
            models = preferred[:2]
            if not models:
                raise ValueError('No compatible chat model in catalog')
        except Exception:
            models = PROVIDER_MODELS.get(provider, [])[:1]
        self._models[provider] = models
        return models

    def _failure(self, provider, error):
        code = getattr(error, 'status_code', None)
        if code in (401, 403):
            state = 'credentials_rejected'
            self.tracker.blocked.add(provider)
        elif code == 429:
            state = 'quota_or_rate_limit'
            self.tracker.cooldown_until[provider] = time.time() + 120
        else:
            state = 'unavailable'
            self.tracker.cooldown_until[provider] = time.time() + 60
        self._provider_state[provider] = {'state': state, 'error': type(error).__name__, 'http_status': code}
        if provider in self.working_providers:
            self.working_providers.remove(provider)
        logger.warning(f'{provider}: {state} ({type(error).__name__})')

    async def validate_keys_on_boot(self):
        async def probe(provider):
            try:
                if provider == OLLAMA:
                    ok = await self._local.ensure_running()
                    models = self._local.chat_models()
                    ok = ok and bool(models)
                    self._models[provider] = models
                    self._provider_state[provider] = {'state': 'ready' if ok else 'needs_local_model', 'models': models}
                    if ok and provider not in self.working_providers:
                        self.working_providers.append(provider)
                    return provider, ok
                result = await asyncio.wait_for(self._call_provider(provider, 'Reply only OK.',
                                               [{'role': 'user', 'content': 'Reply only OK.'}], 64, 0), timeout=20)
                if not result.strip():
                    raise ValueError('Empty response')
                self._provider_state[provider] = {'state': 'ready', 'models': self._models.get(provider, [])}
                if provider not in self.working_providers:
                    self.working_providers.append(provider)
                return provider, True
            except Exception as exc:
                self._failure(provider, exc)
                return provider, False
        results = await asyncio.gather(*(probe(p) for p in self._clients))
        return dict(results)

    async def complete(self, system, messages, task_type='conversation', max_tokens=2048, temperature=0.7):
        self.last_provider_used = None
        self.last_model_used = None
        opts = self.config.get('ai_router', {})
        chain = list(self._clients)
        if opts.get('local_first', True):
            chain = [OLLAMA] + [p for p in chain if p != OLLAMA]
        else:
            chain = [p for p in chain if p in self.working_providers] + [p for p in chain if p not in self.working_providers]
        if opts.get('local_only', False):
            chain = [OLLAMA]
        started = time.monotonic()
        for provider in chain:
            if not self.tracker.is_available(provider):
                continue
            remaining = opts.get('request_timeout_seconds', 90) - (time.monotonic() - started)
            if remaining <= 0:
                break
            try:
                deadline = min(remaining, 70 if provider == OLLAMA else 20)
                result = await asyncio.wait_for(self._call_provider(provider, system, messages, max_tokens, temperature), deadline)
                if not result or not result.strip():
                    raise ValueError('Empty response')
                self.last_provider_used = provider
                self.tracker.record_call(provider, len(result.split()))
                if self.key_manager:
                    self.key_manager.record_usage(provider, requests=1, tokens=len(result.split()))
                if provider not in self.working_providers:
                    self.working_providers.append(provider)
                self._provider_state[provider] = {'state': 'ready', 'models': self._models.get(provider, [])}
                return result
            except Exception as exc:
                self._failure(provider, exc)
        return ('Sir, no AI provider responded. Open Connections to check providers or add a working key. '
                'Local commands such as "add task", "list tasks", "find file" and "status" still work.')

    async def _call_provider(self, provider, system, messages, max_tokens, temperature):
        if provider == OLLAMA:
            model = self.config.get('ai_router', {}).get('local_model')
            result = await self._local.complete(messages=messages, system=system or self.MANAGER_SYSTEM_PROMPT,
                                                model=model, max_tokens=max_tokens, temperature=temperature)
            self.last_model_used = self._local.last_model
            return result or ''
        if self.key_manager:
            key = self.key_manager.get_key(provider)
            if not key:
                raise ValueError('No usable key')
            self._clients[provider].api_key = key
        last_error = None
        for model in await self._discover(provider):
            try:
                if provider == ANTHROPIC:
                    response = await self._clients[provider].messages.create(model=model, system=system,
                                   messages=messages, max_tokens=max_tokens, temperature=temperature)
                    result = ''.join(b.text for b in response.content if getattr(b, 'type', '') == 'text')
                else:
                    response = await self._clients[provider].chat.completions.create(model=model,
                                   messages=[{'role': 'system', 'content': system or self.MANAGER_SYSTEM_PROMPT}] + messages,
                                   max_tokens=max_tokens, temperature=temperature)
                    result = response.choices[0].message.content
                self.last_model_used = model
                return result or ''
            except Exception as exc:
                last_error = exc
                if getattr(exc, 'status_code', None) not in (400, 404):
                    raise
        raise last_error or ValueError('No chat model configured')

    def get_status(self):
        return {'available_models': list(self._clients), 'working_providers': list(self.working_providers),
                'blocked_models': list(self.tracker.blocked), 'call_counts': dict(self.tracker.calls),
                'last_provider': self.last_provider_used, 'last_model': self.last_model_used,
                'providers': dict(self._provider_state), 'local_models': self._local.chat_models(),
                'local_first': self.config.get('ai_router', {}).get('local_first', True)}

    async def close(self):
        for client in list(self._clients.values()) + self._retired_clients:
            try:
                await client.close()
            except Exception:
                pass
''')
p = Path('core/router.py')
s = p.read_text(encoding='utf-8').replace('import google.generativeai as genai', '# Deprecated SDK removed 2026-10-12; Gemini uses its supported compatible endpoint.\n# import google.generativeai as genai')
p.write_text(s, encoding='utf-8')

replace('core/ollama_client.py', 'OllamaClient.ensure_running', '''    async def ensure_running(self) -> bool:
        async def probe():
            response = await self._client.get(f'{self.base_url}/api/tags', timeout=3)
            response.raise_for_status()
            self.available_models = [m['name'] for m in response.json().get('models', [])]
            return True
        try:
            return await probe()
        except Exception:
            pass
        try:
            subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            for _ in range(8):
                await asyncio.sleep(.5)
                try:
                    return await probe()
                except Exception:
                    pass
        except (OSError, FileNotFoundError):
            pass
        return False

    def chat_models(self):
        return [m for m in self.available_models if not any(x in m.lower() for x in ['embed', 'nomic', 'bge-', 'all-minilm'])]
''')
replace('core/ollama_client.py', 'OllamaClient.complete', '''    async def complete(self, prompt=None, messages=None, system='', model=None, max_tokens=2048, temperature=.7):
        self.last_model = None
        if not await self.ensure_running():
            raise ConnectionError('Ollama is not running')
        models = self.chat_models()
        if model and model not in models:
            raise ValueError('Configured local model is not installed')
        if not models:
            raise ValueError('No local chat model installed')
        model = model or next((m for m in DEFAULT_MODELS if m in models), models[0])
        self.last_model = model
        chat = ([{'role': 'system', 'content': system}] if system else [])
        chat += messages or [{'role': 'user', 'content': prompt or ''}]
        response = await self._client.post(f'{self.base_url}/api/chat', json={
            'model': model, 'messages': chat, 'stream': False,
            'options': {'temperature': temperature, 'num_predict': max_tokens, 'num_ctx': 4096}}, timeout=70)
        response.raise_for_status()
        return response.json().get('message', {}).get('content', '')
''')
p = Path('core/ollama_client.py')
s = p.read_text(encoding='utf-8').replace('self.available_models: List[str] = []', 'self.available_models: List[str] = []\n        self.last_model = None')
p.write_text(s, encoding='utf-8')

replace('core/manager.py', 'Manager._classify_intent', '''    def _classify_intent(self, text):
        from core.routing import classify
        return classify(text, self.INTENT_MAP)
''')
replace('core/manager.py', 'Manager.process', '''    async def process(self, user_input, input_type='text'):
        user_input = user_input.strip()
        if not user_input:
            return 'Sir, enter a message or command.'
        async with self._process_lock:
            # Snapshot BEFORE saving the new user turn, so it appears once in the prompt.
            context = self.conv_store.get_context_messages(20)
            await self.conv_store.save('user', user_input)
            intent = self._classify_intent(user_input)
            try:
                if user_input.lower().strip(" .!,") in ["lets buckle up", "let's buckle up", "buckle up"]:
                    result = await self._handle_buckle_up()
                elif intent == 'system':
                    result = await self._handle_system_query(user_input)
                elif intent == 'conversation_memory':
                    result = await self.agents['conversation'].execute(user_input, {'history': context})
                elif intent == 'conversation':
                    result = await self._handle_conversation(user_input, context)
                elif self.swarm:
                    result = await self.swarm.dispatch(user_input, intent, {'history': context})
                else:
                    result = await self.agents[intent].execute(user_input, {'history': context})
                final = result or 'Sir, the action returned no result.'
            except Exception as exc:
                logger.error(f'Task failed ({intent}): {type(exc).__name__}')
                final = f'Sir, the {intent} task failed ({type(exc).__name__}). No completion was confirmed.'
            # Preserve actual tool output. A second LLM review cannot validate an action.
            await self.conv_store.save('manager', final, intent=intent,
                                       model_used=str(self.router.last_provider_used or 'local command'))
            return final
''')
replace('core/manager.py', 'Manager._handle_buckle_up', '''    async def _handle_buckle_up(self):
        from core.activity_tracker import get_recent_activities
        activities = get_recent_activities(8)
        lines = ['Welcome back, Sir.', await self._handle_system_query('status')]
        if activities:
            lines.append('Recorded activity (historical entries may predate this session):')
            lines.extend(f"- {a.get('timestamp', '')}: {a.get('agent', '')}: {a.get('activity', '')}" for a in activities)
        else:
            lines.append('No background activity recorded.')
        return '\\n'.join(lines)
''')
replace('core/manager.py', 'Manager._handle_system_query', '''    async def _handle_system_query(self, user_input):
        state = self.router.get_status()
        lower = user_input.lower()
        if any(w in lower for w in ['which api', 'which model', 'what model', 'providers']):
            return (f"Sir, last provider: {state.get('last_provider') or 'none used yet'}. "
                    f"Model: {state.get('last_model') or 'none used yet'}.\\n"
                    f"Verified available: {', '.join(state['working_providers']) or 'none yet'}. "
                    'Open Connections for each provider’s current state.')
        if any(w in lower for w in ['capabilities', 'what can you']):
            return ('Sir, I can save tasks and timed reminders, search/read/create text files, open supported apps, '
                    'retrieve conversation history, and generate drafts, code and plans with a connected AI. '
                    'WhatsApp and LinkedIn automation need browser sign-in. Recruiter calls are a simulation; '
                    'live trading, email sending and social publishing are not connected.')
        lines = ['Sir, Manager OS is running.',
                 f"AI verified available: {', '.join(state['working_providers']) or 'none yet'}.",
                 f'Agents loaded: {len(self.agents)}. Loaded does not mean an external account is connected.']
        if self.swarm:
            lines.append(f'Active requests: {len(self.swarm.active_tasks)}.')
        life = self.agents.get('life')
        if life and hasattr(life, 'tasks'):
            lines.append(f'Open tasks: {len(life.tasks.list())}.')
        career = self.agents.get('career')
        running = career and getattr(career, 'active_apply_task', None)
        lines.append('Career browser loop: ' + ('running' if running and not running.done() else 'stopped') + '.')
        return '\\n'.join(lines)
''')
p = Path('core/manager.py')
s = p.read_text(encoding='utf-8').replace('def __init__(self, config: dict):', 'def __init__(self, config: dict, router=None):', 1)
s = s.replace('self.router = AIRouter(config)', 'self.router = router or AIRouter(config)\n        self._process_lock = asyncio.Lock()', 1)
start = s.index('    PERSONALITY_SYSTEM_PROMPT = """')
end = s.index('"""', start + len('    PERSONALITY_SYSTEM_PROMPT = """')) + 3
old = s[start:end]
s = s[:start] + '\n'.join('    # ' + line.lstrip() for line in old.splitlines()) + '\n    PERSONALITY_SYSTEM_PROMPT = AIRouter.MANAGER_SYSTEM_PROMPT' + s[end:]
s = s.replace('All systems online. ', 'Dashboard online. ')
s = s.replace('asyncio.create_task(self.health.start_monitoring(self.agents))', 'await self.health.start_monitoring(self.agents)')
p.write_text(s, encoding='utf-8')

replace('core/swarm.py', 'SwarmEngine._single_dispatch', '''    async def _single_dispatch(self, task):
        # The explicit classifier wins. Hooks must not redirect a concrete action.
        name = task.intent if task.intent in self.agents else self.match_hook(task.request)
        if not name or name not in self.agents:
            return 'Sir, no executable agent is registered for this command.'
        task.assigned_agents = [name]
        task.status = 'running'
        return await self.agents[name].execute(task.request, task.context)
''')
p = Path('core/swarm.py')
s = p.read_text(encoding='utf-8').replace('require_consensus=intent in self.CONSENSUS_TASKS,', '# Old consensus invoked unrelated action agents and could duplicate side effects.\n            require_consensus=False,')
p.write_text(s, encoding='utf-8')

replace('agents/life_agent.py', 'LifeAgent.execute', '''    def __init__(self, config, router, firewall):
        super().__init__(config, router, firewall)
        from core.local_tasks import LocalTasks
        self.tasks = LocalTasks(config.get('storage', {}).get('tasks_path', 'logs/tasks.db'))

    async def execute(self, request, context):
        import re
        from datetime import datetime, timedelta
        text = request.strip()
        match = re.search(r'\\b(?:complete|finish|done) task\\s+#?(\\d+)\\b', text, re.I)
        if match:
            found = self.tasks.complete(int(match[1]))
            return 'Sir, task completed.' if found else 'Sir, that open task was not found.'
        match = re.search(r'\\badd task\\s*:?\\s*(.+)', text, re.I)
        if match:
            number = self.tasks.add(match[1])
            return f'Sir, saved task #{number}: {match[1]}'
        match = re.search(r'\\bremind me (?:in (\\d+) (seconds?|minutes?|hours?|days?) to (.+)|to (.+) in (\\d+) (seconds?|minutes?|hours?|days?))$', text, re.I)
        if match:
            count, unit, title = (match[1], match[2], match[3]) if match[1] else (match[5], match[6], match[4])
            seconds = int(count) * {'second': 1, 'minute': 60, 'hour': 3600, 'day': 86400}[unit.lower().rstrip('s')]
            due = (datetime.now() + timedelta(seconds=seconds)).isoformat(timespec='seconds')
            number = self.tasks.add(title, due)
            return f'Sir, reminder #{number} saved for {due.replace("T", " ")}: {title}. Keep Manager OS running for the alert.'
        if re.search(r'\\b(list tasks|show tasks|my tasks|morning|briefing|today)\\b', text, re.I):
            tasks = self.tasks.list()
            if not tasks:
                return 'Sir, you have no open tasks. Say "add task" followed by your task.'
            return 'Your open tasks, Sir:\\n' + '\\n'.join(f"#{t['id']} {t['title']}" + (f" — due {t['due_at']}" if t['due_at'] else '') for t in tasks)
        if re.search(r'\\b(remind|reminder|schedule|calendar)\\b', text, re.I):
            return 'Sir, use "remind me in 10 minutes to take a break", or add a task and time in the Tasks panel. External calendars are not connected.'
        return await self._ask_ai(request, system=self.LIFE_SYSTEM + '\\nNo finance, health or calendar accounts are connected. Do not claim to save or access them.')
''')

# Semantic embeddings must be explicitly enabled, avoiding startup downloads and blocking inserts.
p = Path('core/conversation_store.py')
s = p.read_text(encoding='utf-8').replace('def __init__(self):', 'def __init__(self):', 1)
s = s.replace('            import chromadb\n', "            import os\n            if os.environ.get('MANAGER_ENABLE_VECTOR_MEMORY') != '1':\n                return\n            import chromadb\n", 1)
p.write_text(s, encoding='utf-8')
print('Router, routing, local tasks and memory migration complete')

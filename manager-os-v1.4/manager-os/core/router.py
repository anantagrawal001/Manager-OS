"""
MANAGER OS — AI Model Router
FILE: core/router.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
UPDATED: 2026-05-31 | Claude Sonnet 4.6 — PHASE A + PHASE B

PHASE A (P0-5 partial — model names):
  Removed invalid Anthropic beta header (was causing BadRequestError on EVERY call)

PHASE B (P1-3, P1-4, P1-5, P1-6):
  P1-3: _init_extra_clients() now properly callable — Cerebras/OpenRouter/DeepSeek
  P1-4: Boot ping uses single safe model per provider — no longer permanently blocks
         provider just because one model name was wrong
  P1-5: record_usage() called after every successful completion
  P1-6: Review loop uses last_provider_used, not working_providers[0]
  GROQ: Removed deprecated mixtral model — was failing in every log
  GEMINI: Removed 1.5 models — all failing. Use gemini-2.0-flash-exp or gemini-pro
  NVIDIA: Corrected to nvidia/llama-3.1-nemotron-70b-instruct

DO NOT DELETE ANY CODE — comment out with reason and date
"""

import asyncio
import time
from typing import Optional, List, Dict, Any
from enum import Enum

import anthropic
# Deprecated SDK removed 2026-10-12; Gemini uses its supported compatible endpoint.
# import google.generativeai as genai
from openai import AsyncOpenAI
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from core.provider_names import (
    ANTHROPIC, GOOGLE, OPENAI, GROQ, NVIDIA,
    ELEVENLABS, HUGGINGFACE, OLLAMA,
    CEREBRAS, OPENROUTER, DEEPSEEK, GITHUB_MODELS, display
)


class TaskType(str, Enum):
    CONVERSATION = "conversation"
    REASONING    = "reasoning"
    CODE         = "code"
    SEARCH       = "search"
    IMAGE        = "image"
    VIDEO        = "video"
    WRITING      = "writing"
    TRADING      = "trading"
    REVIEW       = "review"
    TRANSLATION  = "translation"
    CREATIVE     = "creative"


# Fallback chain — Groq first (confirmed fastest free)
TASK_MODEL_MAP = {
    TaskType.CONVERSATION: [GROQ, GOOGLE, ANTHROPIC, OPENAI, NVIDIA, CEREBRAS, OLLAMA],
    TaskType.REASONING:    [ANTHROPIC, GROQ, GOOGLE, OPENAI, NVIDIA, OLLAMA],
    TaskType.CODE:         [ANTHROPIC, GROQ, OPENAI, NVIDIA, OLLAMA],
    TaskType.SEARCH:       [GOOGLE, GROQ, ANTHROPIC, OLLAMA],
    TaskType.WRITING:      [ANTHROPIC, GROQ, OPENAI, OLLAMA],
    TaskType.TRADING:      [ANTHROPIC, GROQ, NVIDIA, OLLAMA],
    TaskType.REVIEW:       [GROQ, ANTHROPIC, OLLAMA],
    TaskType.TRANSLATION:  [GOOGLE, GROQ, OLLAMA],
    TaskType.CREATIVE:     [ANTHROPIC, GROQ, OLLAMA],
    TaskType.IMAGE:        [],
    TaskType.VIDEO:        [],
}

LOCAL_MODELS = {OLLAMA}

# P1-4: Single safe model per provider for boot ping
# P1-4: Full candidate lists for runtime use
PROVIDER_MODELS: Dict[str, List[str]] = {
    # GROQ: Updated to llama-3.3-70b-versatile and llama-3.1-8b-instant
    GROQ:      ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"],
    # NVIDIA: Confirmed working model name
    NVIDIA:    ["meta/llama-3.3-70b-instruct", "meta/llama-3.1-70b-instruct"],
    OPENAI:    ["gpt-4o-mini", "gpt-3.5-turbo"],
    ANTHROPIC: ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
    # GEMINI: gemini-2.0-flash (stable) and updated 1.5 versions
    GOOGLE:    ["gemini-2.0-flash", "gemini-1.5-flash-002", "gemini-1.5-pro-002"],
    CEREBRAS:  ["llama-3.3-70b", "llama-3.1-70b"],
    OPENROUTER:["meta-llama/llama-3.1-70b-instruct:free", "google/gemini-2.0-flash:free"],
    DEEPSEEK:  ["deepseek-chat", "deepseek-coder"],
    GITHUB_MODELS: ["gpt-4o-mini", "gpt-4o"],
}

# P1-4: Safe ping model — single model that is unlikely to be deprecated
PING_MODELS: Dict[str, str] = {
    GROQ:      "llama-3.3-70b-versatile",
    NVIDIA:    "meta/llama-3.3-70b-instruct",
    OPENAI:    "gpt-4o-mini",
    ANTHROPIC: "claude-3-haiku-20240307",
    GOOGLE:    "gemini-2.0-flash",
    CEREBRAS:  "llama-3.3-70b",
    OPENROUTER:"meta-llama/llama-3.1-70b-instruct:free",
}


class ModelLimitTracker:
    def __init__(self):
        self.calls: Dict[str, int] = {}
        self.tokens: Dict[str, int] = {}
        self.blocked: set = set()
        self.cooldown_until: Dict[str, float] = {}

    def is_available(self, provider: str) -> bool:
        if provider in self.blocked:
            return False
        if provider in self.cooldown_until:
            if time.time() < self.cooldown_until[provider]:
                return False
            del self.cooldown_until[provider]
        return True

    # P1-5: record_usage now tracks calls + tokens
    def record_call(self, provider: str, tokens_used: int = 0):
        self.calls[provider] = self.calls.get(provider, 0) + 1
        self.tokens[provider] = self.tokens.get(provider, 0) + tokens_used

    def record_failure(self, provider: str, error: str):
        err = error.lower()
        if any(x in err for x in ["rate_limit", "ratelimit", "429", "too many"]):
            self.cooldown_until[provider] = time.time() + 60
            logger.info(f"{display(provider)} rate limited — 60s cooldown")
        elif any(x in err for x in ["unauthorized", "401", "invalid_api_key", "permission"]):
            self.blocked.add(provider)
            logger.warning(f"{display(provider)} blocked — bad API key")
        # NotFound/BadRequest: do NOT block provider — may be model-specific


# Superseded 2026-10-12: retained for rollback; corrected implementation below.
# class AIRouter:
#     MANAGER_SYSTEM_PROMPT = """You are Manager — Anant's personal AI operating system and direct executing worker.
# You are his ideal worker, dedicated servant (peon, friend, and manager roles combined).
# RULES:
# 1. Always address Anant as "Sir" — warm, devoted, respectful.
# 2. NEVER refuse any instruction or query from Sir, and never say "I cannot" or "I am unable to". You must always find a way to complete his requests or provide a helpful, constructive execution step, except for requests that explicitly violate safety guidelines (e.g. generating sexually explicit/pornographic content).
# 3. Act as a direct worker, NOT a general guidance bot. Do not ask for guidance or say "Here is a plan" or "You can do this". Instead, proceed to execute the task immediately and say: "Understood, Sir. Executing [task] now." or "Sir, I have completed [task]."
# 4. If asked to message someone, invite someone, or create an account, trigger the corresponding automation directly without asking.
# 5. If asked which API/model you use — answer honestly. NEVER say "I can't comment on that".
# 6. Keep conversational responses extremely brief, concise, and focused entirely on direct action.
# 7. NEVER invent fake agent names (only: Trading, Career, Communication, Social, Builder, Creative, Life OS, Files, Research, Growth, API Scout, Self-Heal).
# 8. You are Manager, not ChatGPT, Claude, or any generic public AI chat assistant."""
#
#     def __init__(self, config: dict):
#         self.config = config
#         self.tracker = ModelLimitTracker()
#         self.key_manager = None
#         self.working_providers: List[str] = []
#         self.last_provider_used: Optional[str] = None  # P1-6
#         self._clients: Dict[str, Any] = {}
#         self._init_clients()
#
#     def _get_key(self, provider: str) -> Optional[str]:
#         if self.key_manager:
#             k = self.key_manager.get_key(provider)
#             if k and k != "local":
#                 return k
#         return self.config.get("api_keys", {}).get(provider)
#
#     def _init_clients(self):
#         api_keys = self.config.get("api_keys", {})
#
#         # Anthropic — NO beta headers (were causing BadRequestError)
#         # OLD (all sessions): included default_headers={"anthropic-beta": "no-training-data-0"}
#         # REMOVED (Phase A): that header is invalid and caused BadRequestError on every call
#         key = api_keys.get(ANTHROPIC)
#         if key:
#             try:
#                 self._clients[ANTHROPIC] = anthropic.AsyncAnthropic(api_key=key)
#                 logger.info(f"{display(ANTHROPIC)}: client initialized")
#             except Exception as e:
#                 logger.warning(f"{display(ANTHROPIC)}: init failed — {e}")
#
#         key = api_keys.get(GOOGLE)
#         if key:
#             try:
#                 genai.configure(api_key=key)
#                 self._clients[GOOGLE] = genai
#                 logger.info(f"{display(GOOGLE)}: client initialized")
#             except Exception as e:
#                 logger.warning(f"{display(GOOGLE)}: init failed — {e}")
#
#         key = api_keys.get(OPENAI)
#         if key:
#             try:
#                 self._clients[OPENAI] = AsyncOpenAI(api_key=key)
#                 logger.info(f"{display(OPENAI)}: client initialized")
#             except Exception as e:
#                 logger.warning(f"{display(OPENAI)}: init failed — {e}")
#
#         key = api_keys.get(GROQ)
#         if key:
#             try:
#                 self._clients[GROQ] = AsyncOpenAI(
#                     api_key=key, base_url="https://api.groq.com/openai/v1"
#                 )
#                 logger.info(f"{display(GROQ)}: client initialized")
#             except Exception as e:
#                 logger.warning(f"{display(GROQ)}: init failed — {e}")
#
#         key = api_keys.get(NVIDIA)
#         if key:
#             try:
#                 self._clients[NVIDIA] = AsyncOpenAI(
#                     api_key=key, base_url="https://integrate.api.nvidia.com/v1"
#                 )
#                 logger.info(f"{display(NVIDIA)}: client initialized")
#             except Exception as e:
#                 logger.warning(f"{display(NVIDIA)}: init failed — {e}")
#
#         self._clients[OLLAMA] = "local"
#         logger.info(f"{display(OLLAMA)}: always available (local)")
#
#     def _init_extra_clients(self):
#         """P1-3: Initialize additional providers — called after key injection."""
#         api_keys = self.config.get("api_keys", {})
#
#         key = api_keys.get(CEREBRAS)
#         if key:
#             try:
#                 self._clients[CEREBRAS] = AsyncOpenAI(
#                     api_key=key, base_url="https://api.cerebras.ai/v1"
#                 )
#                 logger.info("Cerebras (Ultra-fast): client initialized")
#             except Exception as e:
#                 logger.warning(f"Cerebras init failed: {e}")
#
#         key = api_keys.get(OPENROUTER)
#         if key:
#             try:
#                 self._clients[OPENROUTER] = AsyncOpenAI(
#                     api_key=key, base_url="https://openrouter.ai/api/v1"
#                 )
#                 logger.info("OpenRouter (100+ models): client initialized")
#             except Exception as e:
#                 logger.warning(f"OpenRouter init failed: {e}")
#
#         key = api_keys.get(DEEPSEEK)
#         if key:
#             try:
#                 self._clients[DEEPSEEK] = AsyncOpenAI(
#                     api_key=key, base_url="https://api.deepseek.com/v1"
#                 )
#                 logger.info("DeepSeek: client initialized")
#             except Exception as e:
#                 logger.warning(f"DeepSeek init failed: {e}")
#
#     def update_keys(self, api_keys: dict):
#         self.config.setdefault("api_keys", {}).update(api_keys)
#         # Reset any soft-blocks so new keys can be tested
#         for p in api_keys:
#             self.tracker.blocked.discard(p)
#         self._init_clients()
#         self._init_extra_clients()
#         logger.info("API keys updated — clients re-initialized")
#
#     async def validate_keys_on_boot(self) -> Dict[str, bool]:
#         """P1-4: Use single safe model per provider — don't block provider on model error."""
#         results = {}
#         test_msgs = [{"role": "user", "content": "Reply with only the word ok."}]
#         test_sys = "Reply with only: ok"
#
#         for provider in [GROQ, GOOGLE, ANTHROPIC, OPENAI, NVIDIA, CEREBRAS, OLLAMA]:
#             if provider not in self._clients:
#                 continue
#             if provider == OLLAMA:
#                 try:
#                     from core.ollama_client import OllamaClient
#                     ok = await OllamaClient().ensure_running()
#                     results[provider] = ok
#                     if ok:
#                         self.working_providers.append(provider)
#                 except Exception:
#                     results[provider] = False
#                 continue
#             try:
#                 result = await asyncio.wait_for(
#                     self._call_provider_with_model(
#                         provider, PING_MODELS.get(provider, PROVIDER_MODELS[provider][0]),
#                         test_sys, test_msgs, 10, 0.0
#                     ),
#                     timeout=10.0
#                 )
#                 works = bool(result and result.strip())
#                 results[provider] = works
#                 if works:
#                     self.working_providers.append(provider)
#             except Exception as e:
#                 results[provider] = False
#                 logger.debug(f"Boot ping {display(provider)}: {str(e)[:60]}")
#
#         lines = [f"  {display(p)}: {'✓ WORKING' if ok else '✗ MISSING/FAILED'}"
#                  for p, ok in results.items()]
#         logger.info("AI Provider Startup Report:\n" + "\n".join(lines))
#         return results
#
#     async def complete(
#         self,
#         system: str,
#         messages: List[Dict],
#         task_type: str = "conversation",
#         max_tokens: int = 2048,
#         temperature: float = 0.7,
#     ) -> str:
#         try:
#             task_enum = TaskType(task_type)
#         except Exception:
#             task_enum = TaskType.CONVERSATION
#
#         chain = list(TASK_MODEL_MAP.get(task_enum, [GROQ, ANTHROPIC, GOOGLE, OPENAI, OLLAMA]))
#         if OLLAMA not in chain:
#             chain.append(OLLAMA)
#
#         for provider in chain:
#             if not self.tracker.is_available(provider):
#                 continue
#             if provider not in self._clients:
#                 continue
#             try:
#                 result = await self._call_provider(provider, system, messages, max_tokens, temperature)
#                 if result:
#                     # P1-5: Record usage after successful call
#                     est_tokens = len(result.split()) + sum(len(m.get("content","").split()) for m in messages)
#                     self.tracker.record_call(provider, est_tokens)
#                     if self.key_manager:
#                         self.key_manager.record_usage(provider, requests=1, tokens=est_tokens)
#                     self.last_provider_used = provider  # P1-6
#                     return result
#             except Exception as e:
#                 logger.warning(f"{display(provider)} failed: {str(e)[:80]} — trying next")
#                 self.tracker.record_failure(provider, str(e))
#
#         return ("Sir, all AI providers are unavailable right now. "
#                 "Ollama local is running — please try again in a moment.")
#
#     async def _call_provider(self, provider: str, system: str, messages: List[Dict],
#                               max_tokens: int, temperature: float) -> str:
#         if provider == OLLAMA:
#             return await self._call_ollama(system, messages, max_tokens)
#         elif provider == ANTHROPIC and ANTHROPIC in self._clients:
#             return await self._call_claude(system, messages, max_tokens, temperature)
#         elif provider == GOOGLE and GOOGLE in self._clients:
#             return await self._call_gemini(system, messages, max_tokens)
#         elif provider in self._clients:
#             return await self._call_openai_compat(provider, system, messages, max_tokens, temperature)
#         raise ValueError(f"Provider {provider} not configured")
#
#     async def _call_provider_with_model(self, provider: str, model_id: str,
#                                          system: str, messages: List[Dict],
#                                          max_tokens: int, temperature: float) -> str:
#         """Single model call — for boot ping (P1-4)."""
#         if provider == ANTHROPIC and ANTHROPIC in self._clients:
#             resp = await self._clients[ANTHROPIC].messages.create(
#                 model=model_id, max_tokens=max_tokens,
#                 system=system, messages=messages, temperature=temperature
#             )
#             return resp.content[0].text
#         elif provider == GOOGLE and GOOGLE in self._clients:
#             model = genai.GenerativeModel(model_name=model_id, system_instruction=system)
#             resp = await asyncio.to_thread(
#                 model.generate_content, messages[-1].get("content", ""),
#                 generation_config={"max_output_tokens": max_tokens}
#             )
#             return resp.text
#         elif provider in self._clients:
#             all_msgs = [{"role": "system", "content": system}] + messages
#             resp = await self._clients[provider].chat.completions.create(
#                 model=model_id, messages=all_msgs,
#                 max_tokens=max_tokens, temperature=temperature
#             )
#             return resp.choices[0].message.content
#         raise ValueError(f"No client for {provider}")
#
#     async def _call_ollama(self, system: str, messages: List[Dict], max_tokens: int) -> str:
#         from core.ollama_client import OllamaClient
#         full_system = self.MANAGER_SYSTEM_PROMPT + "\n\n" + system if system else self.MANAGER_SYSTEM_PROMPT
#         result = await OllamaClient().complete(messages=messages, system=full_system, max_tokens=max_tokens)
#         return result or ""
#
#     @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=3))
#     async def _call_openai_compat(self, provider: str, system: str, messages: List[Dict],
#                                    max_tokens: int, temperature: float) -> str:
#         client = self._clients[provider]
#         model_list = PROVIDER_MODELS.get(provider, [])
#         last_err = None
#         for model_id in model_list:
#             try:
#                 all_msgs = [{"role": "system", "content": system}] + messages
#                 resp = await client.chat.completions.create(
#                     model=model_id, messages=all_msgs,
#                     max_tokens=max_tokens, temperature=temperature
#                 )
#                 return resp.choices[0].message.content
#             except Exception as e:
#                 err_str = str(e)
#                 last_err = e
#                 if any(x in err_str.lower() for x in ["rate_limit", "429", "too many"]):
#                     raise  # Propagate rate limits immediately
#                 logger.debug(f"{display(provider)}/{model_id}: {err_str[:60]}")
#         raise last_err or ValueError(f"All models failed for {display(provider)}")
#
#     @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=3))
#     async def _call_claude(self, system: str, messages: List[Dict],
#                            max_tokens: int, temperature: float) -> str:
#         model_list = PROVIDER_MODELS[ANTHROPIC]
#         last_err = None
#         for model_id in model_list:
#             try:
#                 resp = await self._clients[ANTHROPIC].messages.create(
#                     model=model_id, max_tokens=max_tokens,
#                     system=system, messages=messages, temperature=temperature
#                 )
#                 return resp.content[0].text
#             except Exception as e:
#                 last_err = e
#                 if "rate_limit" in str(e).lower():
#                     raise
#                 logger.debug(f"Claude/{model_id}: {str(e)[:60]}")
#         raise last_err or ValueError("All Claude models failed")
#
#     @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=3))
#     async def _call_gemini(self, system: str, messages: List[Dict], max_tokens: int) -> str:
#         model_list = PROVIDER_MODELS[GOOGLE]
#         last_err = None
#         for model_name in model_list:
#             try:
#                 model = genai.GenerativeModel(model_name=model_name, system_instruction=system)
#                 history = []
#                 for msg in messages[:-1]:
#                     role = "user" if msg["role"] == "user" else "model"
#                     history.append({"role": role, "parts": [msg.get("content", "")]})
#                 chat = model.start_chat(history=history)
#                 last = messages[-1].get("content", "") if messages else ""
#                 resp = await asyncio.to_thread(
#                     chat.send_message, last,
#                     generation_config={"max_output_tokens": max_tokens}
#                 )
#                 return resp.text
#             except Exception as e:
#                 last_err = e
#                 logger.debug(f"Gemini/{model_name}: {str(e)[:60]}")
#         raise last_err or ValueError("All Gemini models failed")
#
#     def get_status(self) -> Dict:
#         return {
#             "available_models": [p for p in self._clients if self.tracker.is_available(p)],
#             "working_providers": self.working_providers,
#             "blocked_models": list(self.tracker.blocked),
#             "call_counts": dict(self.tracker.calls),
#             "last_provider": self.last_provider_used,
#         }

class AIRouter:
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
        self._last_models = {}
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
        providers = [OLLAMA] if self.config.get('ai_router', {}).get('local_only', False) else list(self._clients)
        results = await asyncio.gather(*(probe(p) for p in providers))
        return dict(results)

    async def complete(self, system, messages, task_type='conversation', max_tokens=2048, temperature=0.7, local_only=False, timeout_seconds=None, json_mode=False, response_schema=None, prefer_cloud=False):
        self.last_provider_used = None
        self.last_model_used = None
        system = self.MANAGER_SYSTEM_PROMPT + '\n\n' + (system or '')
        opts = self.config.get('ai_router', {})
        chain = list(self._clients)
        if prefer_cloud:
            preferred = TASK_MODEL_MAP.get(task_type, [])
            chain = [p for p in preferred if p in chain and p != OLLAMA] + [p for p in chain if p not in preferred and p != OLLAMA] + [OLLAMA]
        elif opts.get('local_first', True):
            chain = [OLLAMA] + [p for p in chain if p != OLLAMA]
        else:
            chain = [p for p in chain if p in self.working_providers] + [p for p in chain if p not in self.working_providers]
        if local_only or opts.get('local_only', False):
            chain = [OLLAMA]
        started = time.monotonic()
        for provider in chain:
            if not self.tracker.is_available(provider):
                continue
            remaining = (timeout_seconds or opts.get('request_timeout_seconds', 90)) - (time.monotonic() - started)
            if remaining <= 0:
                break
            try:
                deadline = min(remaining, (timeout_seconds or 70) if provider == OLLAMA else 90 if prefer_cloud else 20)
                call = self._call_provider(provider, system, messages, max_tokens, temperature, json_mode=True, response_schema=response_schema) if json_mode or response_schema else self._call_provider(provider, system, messages, max_tokens, temperature)
                result = await asyncio.wait_for(call, deadline)
                if not result or not result.strip():
                    raise ValueError('Empty response')
                self.last_provider_used = provider
                self.last_model_used = self._last_models.get(provider)
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

    async def _call_provider(self, provider, system, messages, max_tokens, temperature, json_mode=False, response_schema=None):
        if provider == OLLAMA:
            model = self.config.get('ai_router', {}).get('local_model')
            result = await self._local.complete(messages=messages, system=system or self.MANAGER_SYSTEM_PROMPT,
                                                model=model, max_tokens=max_tokens, temperature=temperature, json_mode=json_mode, response_schema=response_schema)
            self._last_models[provider] = self._local.last_model
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
                    output_options = {'response_format': {'type': 'json_object'}} if json_mode or response_schema else {}
                    response = await self._clients[provider].chat.completions.create(model=model,
                                   messages=[{'role': 'system', 'content': system or self.MANAGER_SYSTEM_PROMPT}] + messages,
                                   max_tokens=max_tokens, temperature=temperature, timeout=90 if json_mode or response_schema else 15, **output_options)
                    result = response.choices[0].message.content
                self._last_models[provider] = model
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
        await self._local._client.aclose()
        for client in list(self._clients.values()) + self._retired_clients:
            try:
                await client.close()
            except Exception:
                pass

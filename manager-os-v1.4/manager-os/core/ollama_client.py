"""
MANAGER OS — Ollama Local Model Client
════════════════════════════════════════
FILE: core/ollama_client.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: Runs Llama 3.1 8B + Mistral 7B locally on RTX 5060.
         Used when: no internet, all remote keys exhausted, privacy-critical task.
         Fully offline. No data leaves the machine. Free forever.

DO NOT DELETE ANY CODE — comment out with reason and date
"""

import asyncio
import subprocess
import time
from typing import Optional, List, Dict
import httpx
from loguru import logger


OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODELS = ["llama3.1:8b", "mistral:7b"]


class OllamaClient:
    """
    Client for local Ollama models.
    Runs Llama 3.1 8B and Mistral 7B on RTX 5060.
    Auto-starts Ollama service if not running.
    """

    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.available_models: List[str] = []
        self.last_model = None
        self._client = httpx.AsyncClient(timeout=120.0)  # Local inference can be slow

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # async def ensure_running(self) -> bool:
    #     """Ensure Ollama service is running. Start it if not."""
    #     try:
    #         response = await self._client.get(f"{self.base_url}/api/tags")
    #         if response.status_code == 200:
    #             data = response.json()
    #             self.available_models = [m["name"] for m in data.get("models", [])]
    #             logger.info(f"Ollama running — {len(self.available_models)} models available")
    #             return True
    #     except Exception:
    #         pass
    #
    #     # Try to start Ollama
    #     logger.info("Ollama not running — attempting to start...")
    #     try:
    #         subprocess.Popen(
    #             ["ollama", "serve"],
    #             stdout=subprocess.DEVNULL,
    #             stderr=subprocess.DEVNULL,
    #             creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
    #         )
    #
    #         # Wait for startup
    #         for _ in range(10):
    #             await asyncio.sleep(2)
    #             try:
    #                 response = await self._client.get(f"{self.base_url}/api/tags")
    #                 if response.status_code == 200:
    #                     logger.info("Ollama started successfully")
    #                     return True
    #             except Exception:
    #                 continue
    #
    #     except FileNotFoundError:
    #         logger.error("Ollama not installed — local fallback unavailable")
    #         return False
    #     except Exception as e:
    #         logger.error(f"Failed to start Ollama: {e}")
    #         return False
    #
    #     return False

    async def ensure_running(self) -> bool:
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

    async def pull_model_if_needed(self, model_name: str) -> bool:
        """Download model if not already present"""
        if model_name in self.available_models:
            return True

        logger.info(f"Downloading model: {model_name} (this will take a while first time)")

        try:
            async with self._client.stream(
                "POST",
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=3600  # 1 hour for large models
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        # Log download progress
                        import json
                        try:
                            data = json.loads(line)
                            if "status" in data:
                                logger.debug(f"Model pull: {data['status']}")
                        except Exception:
                            pass

            self.available_models.append(model_name)
            logger.info(f"Model {model_name} ready")
            return True

        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # async def complete(
    #     self,
    #     prompt: str = None,
    #     messages: List[Dict] = None,
    #     system: str = "",
    #     model: str = "llama3.1:8b",
    #     max_tokens: int = 2048,
    #     temperature: float = 0.7
    # ) -> Optional[str]:
    #     """
    #     Generate completion using local Ollama model.
    #     Supports both prompt-string and messages formats.
    #     """
    #     if not await self.ensure_running():
    #         return None
    #
    #     # Pull model if needed
    #     await self.pull_model_if_needed(model)
    #
    #     try:
    #         if messages:
    #             # Use chat endpoint (better for multi-turn)
    #             ollama_messages = []
    #             if system:
    #                 ollama_messages.append({"role": "system", "content": system})
    #             ollama_messages.extend(messages)
    #
    #             payload = {
    #                 "model": model,
    #                 "messages": ollama_messages,
    #                 "stream": False,
    #                 "options": {
    #                     "temperature": temperature,
    #                     "num_predict": max_tokens,
    #                     "num_gpu": 99,  # Use all GPU layers (RTX 5060)
    #                 }
    #             }
    #
    #             response = await self._client.post(
    #                 f"{self.base_url}/api/chat",
    #                 json=payload,
    #                 timeout=120.0
    #             )
    #
    #             if response.status_code == 200:
    #                 data = response.json()
    #                 return data.get("message", {}).get("content", "")
    #
    #         else:
    #             # Use generate endpoint (single prompt)
    #             full_prompt = f"System: {system}\n\n{prompt}" if system else prompt
    #
    #             payload = {
    #                 "model": model,
    #                 "prompt": full_prompt,
    #                 "stream": False,
    #                 "options": {
    #                     "temperature": temperature,
    #                     "num_predict": max_tokens,
    #                     "num_gpu": 99,
    #                 }
    #             }
    #
    #             response = await self._client.post(
    #                 f"{self.base_url}/api/generate",
    #                 json=payload,
    #                 timeout=120.0
    #             )
    #
    #             if response.status_code == 200:
    #                 data = response.json()
    #                 return data.get("response", "")
    #
    #     except Exception as e:
    #         logger.error(f"Ollama completion failed: {e}")
    #
    #     return None

    async def complete(self, prompt=None, messages=None, system='', model=None, max_tokens=2048, temperature=.7, json_mode=False, response_schema=None):
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
        payload = {
            'model': model, 'messages': chat, 'stream': False, 'think': False,
            **({'format': response_schema or 'json'} if json_mode or response_schema else {}),
            # Resume evidence plus cited output must fit together; 4096 silently truncated sources.
            'options': {'temperature': temperature, 'num_predict': max_tokens,
                        'num_ctx': min(32768, max(8192, ((sum(len(m.get('content', '')) for m in chat) // 3 + max_tokens + 2048 + 4095) // 4096) * 4096))}}
        for attempt in range(2):
            response = await self._client.post(f'{self.base_url}/api/chat', json=payload, timeout=180)
            if response.status_code not in (500, 502, 503) or attempt:
                break
            await asyncio.sleep(.5)
        response.raise_for_status()
        return response.json().get('message', {}).get('content', '')

    async def get_best_available_model(self) -> str:
        """Return the best available local model"""
        await self.ensure_running()

        # Prefer llama3.1 for best quality
        for preferred in ["llama3.1:8b", "llama3:8b", "mistral:7b", "mistral"]:
            if preferred in self.available_models:
                return preferred

        # Return first available
        if self.available_models:
            return self.available_models[0]

        return "llama3.1:8b"  # Will attempt to download

    async def get_status(self) -> dict:
        """Get Ollama status"""
        running = await self.ensure_running()
        return {
            "healthy": running,
            "state": "running" if running else "stopped",
            "available_models": self.available_models,
        }

    async def close(self):
        await self._client.aclose()

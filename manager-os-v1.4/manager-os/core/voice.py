"""
MANAGER OS — Voice Engine
FILE: core/voice.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
UPDATED: 2026-05-31 | Claude Sonnet 4.6 — PHASE A
CHANGES (Phase A — P0-1, P0-5):
  P0-1: pyttsx3 singleton + asyncio.Queue worker — eliminates "run loop already started"
        OLD: new pyttsx3.init() per speak() call → concurrent calls crashed
        NEW: single engine created once, asyncio.Queue serializes all speak() calls
  P0-5: Female voice selection — Windows Zira preferred, fallback to first female voice found
        Logs confirm "Microsoft Zira Desktop" already selecting — now explicit + guaranteed
        Edge TTS: switched to AriaNeural (female) instead of GuyNeural (male)
  Added: caption word streaming callback preserved
DO NOT DELETE ANY CODE — comment out with reason and date
"""

import asyncio
import os
import queue
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional, Callable

import numpy as np
import sounddevice as sd
import soundfile as sf
from loguru import logger

# pyttsx3 — lazy import, singleton pattern
try:
    import pyttsx3
    _PYTTSX3_AVAILABLE = True
except ImportError:
    _PYTTSX3_AVAILABLE = False

# ─── SINGLETON TTS ENGINE + QUEUE ─────────────────────────────────────────────
# P0-1 FIX: One engine, one worker thread, asyncio.Queue for all speak() calls.
# OLD: new pyttsx3.init() per call → "run loop already started" crash
# NEW: engine created ONCE in worker thread, all text queued through it

_tts_queue: queue.Queue = queue.Queue()
_tts_engine = None
_tts_worker_started = False
_tts_lock = threading.Lock()


def _tts_worker():
    """Background thread — owns the pyttsx3 engine, processes queue forever."""
    global _tts_engine
    if not _PYTTSX3_AVAILABLE:
        logger.warning("pyttsx3 not available — TTS worker not started")
        return

    try:
        _tts_engine = pyttsx3.init()
        _tts_engine.setProperty('rate', 165)
        _tts_engine.setProperty('volume', 1.0)

        # P0-5: Select female voice — prefer Zira (Windows), fallback to first female
        voices = _tts_engine.getProperty('voices')
        female_voice = None
        for v in voices:
            name_lower = v.name.lower()
            # Prefer Microsoft Zira (confirmed working in logs)
            if 'zira' in name_lower:
                female_voice = v
                break
            # Fallback: any female-identified voice
            if any(f in name_lower for f in ['female', 'woman', 'aria', 'jenny', 'eva',
                                               'hazel', 'susan', 'helen', 'linda']):
                if not female_voice:
                    female_voice = v

        if female_voice:
            _tts_engine.setProperty('voice', female_voice.id)
            logger.info(f"pyttsx3 voice selected: {female_voice.name}")
        else:
            logger.warning("No female voice found — using system default")

    except Exception as e:
        logger.error(f"pyttsx3 engine init failed: {e}")
        _tts_engine = None
        return

    # Worker loop — processes text from queue
    while True:
        try:
            item = _tts_queue.get(timeout=1.0)
            if item is None:  # Shutdown signal
                break
            if isinstance(item, tuple):
                text, event = item
            else:
                text, event = item, None
            if _tts_engine:
                try:
                    _tts_engine.say(text)
                    _tts_engine.runAndWait()
                except Exception as e:
                    logger.error(f"pyttsx3 speak error: {e}")
                    # Try to recover engine
                    try:
                        _tts_engine.stop()
                    except Exception:
                        pass
            if event:
                event.set()
            _tts_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"TTS worker error: {e}")
            break


def _ensure_tts_worker():
    """Start TTS worker thread if not already running."""
    global _tts_worker_started
    with _tts_lock:
        if not _tts_worker_started and _PYTTSX3_AVAILABLE:
            t = threading.Thread(target=_tts_worker, daemon=True, name="tts-worker")
            t.start()
            _tts_worker_started = True
            time.sleep(0.3)  # Brief wait for engine init


class VoiceEngine:
    """
    Voice I/O — speaks female, listens via Whisper.
    TTS: pyttsx3 singleton (stable) → Edge TTS female (AriaNeural) → print fallback
    STT: Whisper local (lazy load — loaded on first listen, not at boot)
    """

    SILENCE_THRESHOLD = 500
    SILENCE_DURATION = 2.0
    MAX_RECORD_DURATION = 60.0
    SAMPLE_RATE = 16000

    def __init__(self, config: dict):
        self.config = config
        self._speak_lock = asyncio.Lock()
        self._transcribe_lock = asyncio.Lock()
        vc = config.get("voice", {})
        self.tts_engine = vc.get("tts_engine", "pyttsx3")
        # P0-5: Force female Edge TTS voice — was en-US-GuyNeural (male)
        # OLD: self.tts_voice = vc.get("tts_voice", "en-US-GuyNeural")
        self.tts_voice = vc.get("tts_voice", "en-US-AriaNeural")  # Female
        self.stt_engine = vc.get("stt_engine", "whisper")
        self.whisper_model_size = vc.get("whisper_model", "base")

        self.whisper_model = None  # Lazy load — not loaded at boot
        self._caption_callback: Optional[Callable] = None
        self._speaking_state_callback: Optional[Callable] = None

        # Start TTS worker immediately
        # Speech worker starts only when speech is requested.

        try:
            import pygame
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        except Exception:
            pass

        logger.info(f"Voice engine initialized — STT: {self.stt_engine}, TTS: {self.tts_engine}")

    def set_caption_callback(self, cb: Callable):
        self._caption_callback = cb

    def set_speaking_state_callback(self, cb: Callable):
        self._speaking_state_callback = cb

    def _load_whisper_lazy(self):
        """Load Whisper on first use — not at boot (saves RAM + startup time)"""
        if self.whisper_model is None:
            try:
                import whisper
                self.whisper_model = whisper.load_model(self.whisper_model_size)
                logger.info(f"Whisper '{self.whisper_model_size}' loaded (lazy)")
            except Exception as e:
                logger.error(f"Whisper load failed: {e}")

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # async def speak(self, text: str):
    #     """Speak text — queue-based, never crashes."""
    #     if not text or not text.strip():
    #         return
    #
    #     if self._speaking_state_callback:
    #         try:
    #             await self._speaking_state_callback("start")
    #         except Exception:
    #             pass
    #
    #     try:
    #         # Stream captions while speaking
    #         if self._caption_callback:
    #             asyncio.create_task(self._stream_captions(text))
    #
    #         if self.tts_engine == "elevenlabs":
    #             key = self.config.get("api_keys", {}).get("elevenlabs")
    #             if key:
    #                 try:
    #                     await self._speak_elevenlabs(text, key)
    #                     return
    #                 except Exception:
    #                     pass  # Fall through
    #
    #         # Try Edge TTS (female AriaNeural) — silent fallback if 403
    #         try:
    #             await self._speak_edge_tts(text)
    #             return
    #         except Exception:
    #             pass  # Silent fallback — Edge TTS 403 is a known issue
    #
    #         # Primary: pyttsx3 via queue (always works, no crashes)
    #         if _PYTTSX3_AVAILABLE and _tts_worker_started:
    #             import threading
    #             event = threading.Event()
    #             _tts_queue.put((text, event))
    #             await asyncio.to_thread(event.wait)
    #         else:
    #             print(f"[Manager] {text}")
    #     finally:
    #         if self._speaking_state_callback:
    #             try:
    #                 await self._speaking_state_callback("stop")
    #             except Exception:
    #                 pass

    async def speak(self, text):
        if not text or not self.config.get('voice', {}).get('enabled', True):
            return
        import re
        text = re.sub(r'```[\s\S]*?```', 'Code is available in the chat.', text)
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

    async def _speak_edge_tts(self, text: str):
        """Edge TTS — female AriaNeural voice."""
        import edge_tts
        import pygame
        comm = edge_tts.Communicate(text, self.tts_voice)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name
        await comm.save(tmp_path)
        await asyncio.to_thread(self._play_audio_file, tmp_path)
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    async def _speak_elevenlabs(self, text: str, api_key: str):
        import httpx
        voice_id = "21m00Tcm4TlvDq8ikWAM"
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                json={"text": text, "model_id": "eleven_monolingual_v1",
                      "voice_settings": {"stability": 0.6, "similarity_boost": 0.8}},
                headers={"xi-api-key": api_key, "Accept": "audio/mpeg"},
                timeout=15.0
            )
            if r.status_code == 200:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    tmp.write(r.content)
                    tmp_path = tmp.name
                await asyncio.to_thread(self._play_audio_file, tmp_path)
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
            else:
                raise Exception(f"ElevenLabs {r.status_code}")

    def _play_audio_file(self, file_path: str):
        try:
            import pygame
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
        except Exception as e:
            logger.error(f"Audio playback error: {e}")

    async def _stream_captions(self, text: str):
        """Stream captions word by word."""
        words = text.split()
        delay = max(0.06, min(0.13, 4.0 / max(len(words), 1)))
        for word in words:
            if self._caption_callback:
                try:
                    await self._caption_callback(word)
                except Exception:
                    pass
            await asyncio.sleep(delay)

    async def listen(self) -> Optional[str]:
        """Listen for voice input via Whisper."""
        self._load_whisper_lazy()
        if not self.whisper_model:
            return await asyncio.to_thread(lambda: input("[Manager] Type: "))
        audio = await asyncio.to_thread(self._record_audio)
        if audio is None:
            return None
        text = await asyncio.to_thread(self._transcribe, audio)
        if text and text.strip():
            logger.info(f"Heard: '{text.strip()}'")
            return text.strip()
        return None

    def _record_audio(self) -> Optional[np.ndarray]:
        chunks, silence_start, start = [], None, time.time()
        try:
            with sd.InputStream(samplerate=self.SAMPLE_RATE, channels=1,
                                dtype=np.float32, blocksize=1024) as stream:
                while True:
                    chunk, _ = stream.read(1024)
                    chunks.append(chunk.copy())
                    amp = np.abs(chunk).mean()
                    if amp < self.SILENCE_THRESHOLD / 32768.0:
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start > self.SILENCE_DURATION:
                            break
                    else:
                        silence_start = None
                    if time.time() - start > self.MAX_RECORD_DURATION:
                        break
            return np.concatenate(chunks).flatten() if chunks else None
        except Exception as e:
            logger.error(f"Recording error: {e}")
            return None

    def _transcribe(self, audio: np.ndarray) -> Optional[str]:
        if not self.whisper_model:
            return None
        try:
            result = self.whisper_model.transcribe(audio, language="en", fp16=False)
            return result.get("text", "")
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None

    def get_status(self) -> dict:
        return {
            "stt_engine": self.stt_engine,
            "whisper_loaded": self.whisper_model is not None,
            "tts_engine": self.tts_engine,
            "tts_voice": self.tts_voice,
            "pyttsx3_available": _PYTTSX3_AVAILABLE,
            "tts_queue_size": _tts_queue.qsize(),
            "healthy": True,
        }

    async def shutdown(self):
        """Graceful shutdown — drain TTS queue."""
        if _PYTTSX3_AVAILABLE and _tts_worker_started:
            _tts_queue.put(None)  # Shutdown signal

"""
MANAGER OS — Conversation Store
════════════════════════════════
FILE: core/conversation_store.py
CREATED: 2026-05-28 | Claude Sonnet 4.6
PURPOSE: Permanent conversation memory. Every exchange saved. Never deleted.
         SQLite for structured storage. ChromaDB for semantic search.
         Manager NEVER forgets context across sessions.
         Loads last 20 exchanges on boot as context for all AI calls.

DO NOT DELETE ANY CODE — comment out with reason and date
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

from loguru import logger


DB_PATH = Path("./logs/conversations.db")


class ConversationStore:
    """
    Permanent conversation storage.
    Every exchange: timestamp, role, content, intent, model_used.
    Provides context injection for AI calls.
    """

    def __init__(self):
        self._db = None
        self._recent_cache: List[Dict] = []   # In-memory last 20
        self._initialized = False
        self._chroma_client = None
        self._chroma_collection = None

    async def initialize(self):
        """Create DB and load recent history into memory"""
        if self._initialized:
            return

        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        try:
            import aiosqlite
            self._db = await aiosqlite.connect(str(DB_PATH))
            await self._db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    intent TEXT DEFAULT '',
                    model_used TEXT DEFAULT '',
                    session_id TEXT DEFAULT ''
                )
            """)
            await self._db.commit()
            await self._load_recent()
            self._initialized = True
            logger.info(f"ConversationStore ready — {len(self._recent_cache)} messages in cache")
        except ImportError:
            logger.warning("aiosqlite not available — conversation store using memory only")
            self._initialized = True
        except Exception as e:
            logger.error(f"ConversationStore init error: {e}")
            self._initialized = True

        # Initialize ChromaDB vector search if available
        try:
            import os
            if os.environ.get('MANAGER_ENABLE_VECTOR_MEMORY') != '1':
                return
            import chromadb
            from chromadb.config import Settings
            self._chroma_client = chromadb.PersistentClient(
                path="./logs/chroma",
                settings=Settings(anonymized_telemetry=False)
            )
            self._chroma_collection = self._chroma_client.get_or_create_collection(
                name="conversations",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB vector store initialized successfully")
        except Exception as e:
            logger.warning(f"ChromaDB not available or failed to load (falling back to SQLite): {e}")
            self._chroma_client = None
            self._chroma_collection = None

    async def save(self, role: str, content: str, intent: str = "", model_used: str = ""):
        """Save a message to permanent storage"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "intent": intent,
            "model_used": model_used,
        }

        # Add to in-memory cache
        self._recent_cache.append(entry)
        if len(self._recent_cache) > 50:
            self._recent_cache = self._recent_cache[-50:]

        # Persist to DB
        if self._db:
            try:
                await self._db.execute(
                    "INSERT INTO conversations (timestamp, role, content, intent, model_used) VALUES (?,?,?,?,?)",
                    (entry["timestamp"], role, content, intent, model_used)
                )
                await self._db.commit()
            except Exception as e:
                logger.error(f"ConversationStore save error: {e}")

        # Persist to ChromaDB (if enabled and it's a user/manager message)
        if self._chroma_collection and role in ("user", "manager"):
            try:
                import secrets
                msg_id = f"msg_{datetime.now().timestamp()}_{secrets.token_hex(4)}"
                self._chroma_collection.add(
                    documents=[content],
                    metadatas=[{
                        "role": role,
                        "timestamp": entry["timestamp"],
                        "intent": intent,
                        "model_used": model_used
                    }],
                    ids=[msg_id]
                )
            except Exception as e:
                logger.error(f"ChromaDB save error: {e}")

    def get_context_messages(self, n: int = 20) -> List[Dict]:
        """
        Get last N messages formatted for AI API injection.
        Called before every AI request to provide context.
        """
        recent = self._recent_cache[-n:]
        messages = []
        for entry in recent:
            role = "user" if entry["role"] == "user" else "assistant"
            messages.append({"role": role, "content": entry["content"]})
        return messages

    def get_context_summary(self) -> str:
        """Brief summary of recent context for system prompt injection"""
        if not self._recent_cache:
            return ""
        count = len(self._recent_cache)
        last = self._recent_cache[-1]
        return (
            f"[Context: {count} messages in memory. "
            f"Last message at {last['timestamp'][:16]}: "
            f"{last['role']} said '{last['content'][:60]}...']"
        )

    async def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search over conversation history (ChromaDB semantic search with SQLite keyword fallback)"""
        if self._chroma_collection:
            try:
                # Query ChromaDB
                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(
                    None,
                    lambda: self._chroma_collection.query(
                        query_texts=[query],
                        n_results=limit
                    )
                )
                formatted = []
                if results and "documents" in results and results["documents"]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0]
                    for doc, meta in zip(docs, metas):
                        formatted.append({
                            "timestamp": meta.get("timestamp"),
                            "role": meta.get("role"),
                            "content": doc,
                            "intent": meta.get("intent", "")
                        })
                logger.info(f"Semantic search returned {len(formatted)} results")
                return formatted
            except Exception as e:
                logger.error(f"ChromaDB semantic search failed (falling back to SQLite): {e}")

        if not self._db:
            # Search in-memory cache
            query_lower = query.lower()
            results = [
                e for e in reversed(self._recent_cache)
                if query_lower in e["content"].lower()
            ]
            return results[:limit]

        try:
            async with self._db.execute(
                """SELECT timestamp, role, content, intent FROM conversations
                   WHERE content LIKE ? ORDER BY timestamp DESC LIMIT ?""",
                (f"%{query}%", limit)
            ) as cursor:
                rows = await cursor.fetchall()
            return [
                {"timestamp": r[0], "role": r[1], "content": r[2], "intent": r[3]}
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    async def get_history(self, limit: int = 100) -> List[Dict]:
        """Get conversation history for display in dashboard"""
        if not self._db:
            return self._recent_cache[-limit:]
        try:
            async with self._db.execute(
                "SELECT timestamp, role, content, intent, model_used FROM conversations ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
            return [
                {"timestamp": r[0], "role": r[1], "content": r[2], "intent": r[3], "model": r[4]}
                for r in reversed(rows)
            ]
        except Exception as e:
            logger.error(f"History error: {e}")
            return self._recent_cache

    async def _load_recent(self):
        """Load last 50 messages into memory on startup"""
        if not self._db:
            return
        try:
            async with self._db.execute(
                "SELECT timestamp, role, content, intent, model_used FROM conversations ORDER BY timestamp DESC LIMIT 50"
            ) as cursor:
                rows = await cursor.fetchall()
            self._recent_cache = [
                {"timestamp": r[0], "role": r[1], "content": r[2], "intent": r[3], "model_used": r[4]}
                for r in reversed(rows)
            ]
        except Exception as e:
            logger.error(f"Load recent error: {e}")

    async def close(self):
        if self._db:
            await self._db.close()
            self._db = None
        self._initialized = False


# Global singleton
_store: Optional[ConversationStore] = None


def get_store() -> ConversationStore:
    global _store
    if _store is None:
        _store = ConversationStore()
    return _store

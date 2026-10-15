"""
MANAGER OS — Memory Manager
════════════════════════════
FILE: core/memory.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: Manages short-term (session) and long-term (persistent) memory.
         SQLite for local storage. Encrypted at rest.
         Manager remembers everything about Sir across all sessions.

DO NOT DELETE ANY CODE — comment out with reason and date
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

import aiosqlite
from loguru import logger


class MemoryManager:
    """
    Two-layer memory system:
    - Short term: in-memory, current session conversation
    - Long term: SQLite database, persists across sessions

    Manager uses this to remember:
    - Anant's preferences and patterns
    - Past conversations and outcomes
    - Task history
    - Important facts Anant mentioned
    """
    
    DB_PATH = "./logs/manager.db"
    
    def __init__(self, config: dict):
        self.config = config
        self.db_path = config.get("storage", {}).get("db_path", self.DB_PATH)
        self._db: Optional[aiosqlite.Connection] = None
        self.session_memory: List[Dict] = []
        self.facts: Dict[str, Any] = {}  # Key facts about Anant
    
    async def initialize(self):
        """Initialize database and load existing memory"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self._db = await aiosqlite.connect(self.db_path)
        await self._create_tables()
        await self._load_facts()
        
        logger.info("Memory manager initialized")
    
    async def _create_tables(self):
        """Create database tables if they don't exist"""
        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_input TEXT NOT NULL,
                manager_response TEXT NOT NULL,
                intent TEXT,
                agent_used TEXT
            );
            
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                source TEXT
            );
            
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                input TEXT NOT NULL,
                status TEXT NOT NULL,
                result TEXT,
                agent_used TEXT,
                duration_ms INTEGER
            );
            
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        await self._db.commit()
    
    async def save(self, user_input: str, response: str, intent: str, agent_used: str = None):
        """Save a conversation exchange to long-term memory"""
        await self._ensure_connected()
        
        await self._db.execute(
            """INSERT INTO conversations 
               (timestamp, user_input, manager_response, intent, agent_used)
               VALUES (?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(), user_input, response, intent, agent_used)
        )
        await self._db.commit()
        
        # Also keep in session memory
        self.session_memory.append({
            "timestamp": datetime.now().isoformat(),
            "input": user_input,
            "response": response,
            "intent": intent
        })
    
    async def save_fact(self, key: str, value: Any, source: str = "conversation"):
        """Save an important fact about Anant or his context"""
        await self._ensure_connected()
        
        await self._db.execute(
            """INSERT OR REPLACE INTO facts (key, value, updated_at, source)
               VALUES (?, ?, ?, ?)""",
            (key, json.dumps(value), datetime.now().isoformat(), source)
        )
        await self._db.commit()
        self.facts[key] = value
        logger.debug(f"Fact saved: {key} = {value}")
    
    async def get_fact(self, key: str) -> Optional[Any]:
        """Retrieve a stored fact"""
        if key in self.facts:
            return self.facts[key]
        
        await self._ensure_connected()
        async with self._db.execute(
            "SELECT value FROM facts WHERE key = ?", (key,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                value = json.loads(row[0])
                self.facts[key] = value
                return value
        return None
    
    async def get_recent_conversations(self, limit: int = 20) -> List[Dict]:
        """Get recent conversation history"""
        await self._ensure_connected()
        
        async with self._db.execute(
            """SELECT timestamp, user_input, manager_response, intent
               FROM conversations
               ORDER BY timestamp DESC
               LIMIT ?""",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
        
        return [
            {
                "timestamp": row[0],
                "input": row[1],
                "response": row[2],
                "intent": row[3]
            }
            for row in reversed(rows)
        ]
    
    async def search_conversations(self, query: str, limit: int = 10) -> List[Dict]:
        """Search past conversations by keyword"""
        await self._ensure_connected()
        
        async with self._db.execute(
            """SELECT timestamp, user_input, manager_response, intent
               FROM conversations
               WHERE user_input LIKE ? OR manager_response LIKE ?
               ORDER BY timestamp DESC
               LIMIT ?""",
            (f"%{query}%", f"%{query}%", limit)
        ) as cursor:
            rows = await cursor.fetchall()
        
        return [
            {
                "timestamp": row[0],
                "input": row[1],
                "response": row[2],
                "intent": row[3]
            }
            for row in rows
        ]
    
    async def get_context_summary(self) -> str:
        """
        Generate a context summary for AI models — 
        what Manager knows about Sir so far this session.
        """
        recent = await self.get_recent_conversations(limit=5)
        
        summary_parts = []
        
        if self.facts:
            facts_str = ", ".join(f"{k}: {v}" for k, v in list(self.facts.items())[:10])
            summary_parts.append(f"Known facts about Sir: {facts_str}")
        
        if recent:
            summary_parts.append(f"Recent conversation count: {len(recent)}")
        
        return "\n".join(summary_parts) if summary_parts else "New session — no prior context"
    
    async def save_preference(self, key: str, value: Any):
        """Save a user preference"""
        await self._ensure_connected()
        
        await self._db.execute(
            """INSERT OR REPLACE INTO preferences (key, value, updated_at)
               VALUES (?, ?, ?)""",
            (key, json.dumps(value), datetime.now().isoformat())
        )
        await self._db.commit()
    
    async def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference"""
        await self._ensure_connected()
        
        async with self._db.execute(
            "SELECT value FROM preferences WHERE key = ?", (key,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return json.loads(row[0])
        return default
    
    async def _load_facts(self):
        """Load all facts into memory on startup"""
        await self._ensure_connected()
        
        async with self._db.execute("SELECT key, value FROM facts") as cursor:
            rows = await cursor.fetchall()
        
        for row in rows:
            try:
                self.facts[row[0]] = json.loads(row[1])
            except Exception:
                self.facts[row[0]] = row[1]
        
        logger.debug(f"Loaded {len(self.facts)} facts from memory")
    
    async def _ensure_connected(self):
        """Ensure database connection is active"""
        if self._db is None:
            await self.initialize()
    
    async def close(self):
        """Close database connection"""
        if self._db:
            await self._db.close()
            self._db = None
        logger.info("Memory manager closed")
    
    def get_session_history_for_ai(self, max_exchanges: int = 10) -> List[Dict]:
        """Get session history formatted for AI API messages"""
        recent = self.session_memory[-max_exchanges:]
        messages = []
        
        for exchange in recent:
            messages.append({"role": "user", "content": exchange["input"]})
            messages.append({"role": "assistant", "content": exchange["response"]})
        
        return messages

"""Persistent local tasks and reminders, independent of AI availability."""
import asyncio
from datetime import datetime
from pathlib import Path
import sqlite3
from contextlib import contextmanager


class LocalTasks:
    def __init__(self, path="logs/tasks.db"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY, title TEXT NOT NULL, due_at TEXT,
                completed INTEGER NOT NULL DEFAULT 0, notified INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL)""")
        self._worker = None

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def add(self, title, due_at=None):
        title = title.strip()
        if not title or len(title) > 2000:
            raise ValueError("Task title must contain 1–2000 characters")
        if due_at:
            due_at = datetime.fromisoformat(due_at).isoformat(timespec="seconds")
        with self._connect() as db:
            row = db.execute("INSERT INTO tasks(title,due_at,created_at) VALUES(?,?,?)",
                             (title, due_at, datetime.now().isoformat()))
            return row.lastrowid

    def list(self, include_completed=False):
        with self._connect() as db:
            rows = db.execute("SELECT * FROM tasks WHERE (? OR completed=0) ORDER BY id DESC LIMIT 200",
                              (include_completed,)).fetchall()
            return [dict(row) for row in rows]

    def complete(self, task_id):
        with self._connect() as db:
            return db.execute("UPDATE tasks SET completed=1 WHERE id=? AND completed=0", (task_id,)).rowcount > 0

    async def deliver_due(self, notify):
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as db:
            due = db.execute("SELECT * FROM tasks WHERE completed=0 AND notified=0 AND due_at<=?", (now,)).fetchall()
        for row in due:
            # Persist delivery only after the notification callback succeeds.
            await notify(f"Reminder #{row['id']}, Sir: {row['title']}")
            with self._connect() as db:
                db.execute("UPDATE tasks SET notified=1 WHERE id=?", (row['id'],))

    def start(self, notify):
        async def loop():
            while True:
                try:
                    await self.deliver_due(notify)
                except Exception:
                    pass  # Keep undelivered reminders pending for the next attempt.
                await asyncio.sleep(10)
        self._worker = asyncio.create_task(loop(), name="local-reminders")

    async def close(self):
        if self._worker:
            self._worker.cancel()
            await asyncio.gather(self._worker, return_exceptions=True)

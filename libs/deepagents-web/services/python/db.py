import aiosqlite
import json
import time
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Any

from deepagents_cli.config import settings

def get_db_path():
    db_dir = settings.deepagents_home
    db_dir.mkdir(parents=True, exist_ok=True)
    return str(db_dir / "sessions.db")

async def init_db():
    db_path = get_db_path()
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            name TEXT,
            config TEXT,
            created_at INTEGER,
            updated_at INTEGER
        )
        ''')

        await conn.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            tool_calls TEXT,
            tool_call_id TEXT,
            timestamp INTEGER,
            FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
        ''')

        await conn.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            content TEXT,
            timestamp INTEGER,
            FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
        ''')

        await conn.commit()

async def create_session_db(config: Dict[str, Any], sid: Optional[str] = None, name: str = "New Session") -> str:
    if not sid:
        sid = uuid.uuid4().hex[:16]

    async with aiosqlite.connect(get_db_path()) as conn:
        now = int(time.time() * 1000)
        await conn.execute(
            "INSERT OR IGNORE INTO sessions (id, name, config, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (sid, name, json.dumps(config), now, now)
        )
        await conn.commit()
    return sid

async def get_session_db(sid: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(get_db_path()) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT * FROM sessions WHERE id = ?", (sid,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            session = dict(row)
            session['config'] = json.loads(session['config']) if session['config'] else {}

            # Get messages
            async with conn.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC", (sid,)) as msg_cursor:
                msgs = []
                async for m in msg_cursor:
                    msg = dict(m)
                    if msg['tool_calls']:
                        msg['tool_calls'] = json.loads(msg['tool_calls'])
                    msgs.append(msg)
                session['messages'] = msgs

            # Get logs
            async with conn.execute("SELECT * FROM logs WHERE session_id = ? ORDER BY id ASC", (sid,)) as log_cursor:
                logs = [dict(l) async for l in log_cursor]
                session['logs'] = logs

            return session

async def list_sessions_db() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(get_db_path()) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT id, name, created_at, updated_at FROM sessions ORDER BY updated_at DESC") as cursor:
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                r = dict(row)
                # Get message count efficiently
                async with conn.execute("SELECT COUNT(*) FROM messages WHERE session_id = ?", (r['id'],)) as count_cursor:
                    count_row = await count_cursor.fetchone()
                    r['message_count'] = count_row[0] if count_row else 0
                results.append(r)
            return results

async def update_session_db(sid: str, name: Optional[str] = None, config: Optional[Dict] = None):
    async with aiosqlite.connect(get_db_path()) as conn:
        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if config is not None:
            updates.append("config = ?")
            params.append(json.dumps(config))

        if updates:
            updates.append("updated_at = ?")
            params.append(int(time.time() * 1000))
            params.append(sid)
            sql = f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?"
            await conn.execute(sql, params)
            await conn.commit()

async def update_session_timestamp(sid: str):
    async with aiosqlite.connect(get_db_path()) as conn:
        await conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (int(time.time() * 1000), sid))
        await conn.commit()

async def add_message_db(sid: str, role: str, content: str, tool_calls: Optional[List] = None, tool_call_id: Optional[str] = None):
    async with aiosqlite.connect(get_db_path()) as conn:
        await conn.execute(
            "INSERT INTO messages (session_id, role, content, tool_calls, tool_call_id, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (sid, role, content, json.dumps(tool_calls) if tool_calls else None, tool_call_id, int(time.time() * 1000))
        )
        # Update session timestamp
        await conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (int(time.time() * 1000), sid))
        await conn.commit()

async def delete_session_db(sid: str):
    async with aiosqlite.connect(get_db_path()) as conn:
        await conn.execute("DELETE FROM sessions WHERE id = ?", (sid,))
        # Cascade delete should handle messages and logs, but let's be safe
        await conn.execute("DELETE FROM messages WHERE session_id = ?", (sid,))
        await conn.execute("DELETE FROM logs WHERE session_id = ?", (sid,))
        await conn.commit()

async def delete_sessions_batch_db(sids: List[str]):
    if not sids:
        return
    async with aiosqlite.connect(get_db_path()) as conn:
        placeholders = ','.join('?' for _ in sids)

        # Execute deletions
        await conn.execute(f"DELETE FROM sessions WHERE id IN ({placeholders})", sids)
        await conn.execute(f"DELETE FROM messages WHERE session_id IN ({placeholders})", sids)
        await conn.execute(f"DELETE FROM logs WHERE session_id IN ({placeholders})", sids)

        await conn.commit()

async def add_log_db(sid: str, content: str):
    async with aiosqlite.connect(get_db_path()) as conn:
        await conn.execute(
            "INSERT INTO logs (session_id, content, timestamp) VALUES (?, ?, ?)",
            (sid, content, int(time.time() * 1000))
        )
        await conn.commit()

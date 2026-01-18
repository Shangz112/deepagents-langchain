import sqlite3
import json
import time
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Any

DB_PATH = Path(__file__).parent.parent.parent / "assemble_agents" / "sessions.db"

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        name TEXT,
        config TEXT,
        created_at INTEGER,
        updated_at INTEGER
    )
    ''')
    
    c.execute('''
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
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        content TEXT,
        timestamp INTEGER,
        FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
    )
    ''')
    
    conn.commit()
    conn.close()

def create_session_db(config: Dict[str, Any], sid: Optional[str] = None, name: str = "New Session") -> str:
    if not sid:
        sid = uuid.uuid4().hex[:16]
        
    conn = get_connection()
    c = conn.cursor()
    now = int(time.time() * 1000)
    c.execute(
        "INSERT OR IGNORE INTO sessions (id, name, config, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (sid, name, json.dumps(config), now, now)
    )
    conn.commit()
    conn.close()
    return sid

def get_session_db(sid: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM sessions WHERE id = ?", (sid,))
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    
    session = dict(row)
    session['config'] = json.loads(session['config']) if session['config'] else {}
    
    # Get messages
    c.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC", (sid,))
    msgs = []
    for m in c.fetchall():
        msg = dict(m)
        if msg['tool_calls']:
            msg['tool_calls'] = json.loads(msg['tool_calls'])
        msgs.append(msg)
    session['messages'] = msgs
    
    # Get logs
    c.execute("SELECT * FROM logs WHERE session_id = ? ORDER BY id ASC", (sid,))
    logs = [dict(l) for l in c.fetchall()]
    session['logs'] = logs
    
    conn.close()
    return session

def list_sessions_db() -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, created_at, updated_at FROM sessions ORDER BY updated_at DESC")
    rows = c.fetchall()
    results = []
    for row in rows:
        r = dict(row)
        # Get message count efficiently
        c.execute("SELECT COUNT(*) FROM messages WHERE session_id = ?", (r['id'],))
        r['message_count'] = c.fetchone()[0]
        results.append(r)
    conn.close()
    return results

def update_session_db(sid: str, name: Optional[str] = None, config: Optional[Dict] = None):
    conn = get_connection()
    c = conn.cursor()
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
        c.execute(sql, params)
        conn.commit()
    conn.close()

def update_session_timestamp(sid: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (int(time.time() * 1000), sid))
    conn.commit()
    conn.close()

def add_message_db(sid: str, role: str, content: str, tool_calls: Optional[List] = None, tool_call_id: Optional[str] = None):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO messages (session_id, role, content, tool_calls, tool_call_id, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (sid, role, content, json.dumps(tool_calls) if tool_calls else None, tool_call_id, int(time.time() * 1000))
    )
    # Update session timestamp
    c.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (int(time.time() * 1000), sid))
    conn.commit()
    conn.close()

def delete_session_db(sid: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE id = ?", (sid,))
    # Cascade delete should handle messages and logs, but let's be safe if foreign keys aren't enabled by default in some sqlite versions
    c.execute("DELETE FROM messages WHERE session_id = ?", (sid,))
    c.execute("DELETE FROM logs WHERE session_id = ?", (sid,))
    conn.commit()
    conn.close()

def delete_sessions_batch_db(sids: List[str]):
    if not sids:
        return
    conn = get_connection()
    c = conn.cursor()
    placeholders = ','.join('?' for _ in sids)
    
    # Execute deletions
    c.execute(f"DELETE FROM sessions WHERE id IN ({placeholders})", sids)
    c.execute(f"DELETE FROM messages WHERE session_id IN ({placeholders})", sids)
    c.execute(f"DELETE FROM logs WHERE session_id IN ({placeholders})", sids)
    
    conn.commit()
    conn.close()

def add_log_db(sid: str, content: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO logs (session_id, content, timestamp) VALUES (?, ?, ?)",
        (sid, content, int(time.time() * 1000))
    )
    conn.commit()
    conn.close()

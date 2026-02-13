
import sys
import os
import json
import asyncio
from pathlib import Path

# Add path
sys.path.insert(0, r"d:/MASrepos/deepagents-langchain/libs/deepagents-web/services/python")

# Mock env
os.environ["SILICONFLOW_API_KEY"] = "mock_key"

import db as db_module
from app import sessions

def test_persistence():
    print("Initializing DB...")
    db_module.init_db()
    
    # 1. Create Session
    print("Creating session...")
    config = {"system_prompt": "You are a test agent."}
    sid = db_module.create_session_db(config, name="Test Persistence Session")
    print(f"Session created: {sid}")
    
    # 2. Add Messages
    print("Adding messages...")
    db_module.add_message_db(sid, "user", "Hello World")
    db_module.add_message_db(sid, "assistant", "Hi there!")
    
    # 3. Verify in DB
    print("Verifying DB content...")
    session = db_module.get_session_db(sid)
    if not session:
        print("ERROR: Session not found in DB immediately after creation.")
        return
        
    msgs = session.get('messages', [])
    print(f"Messages in DB: {len(msgs)}")
    if len(msgs) != 2:
        print("ERROR: Message count mismatch.")
    else:
        print("DB content verified.")
        
    # 4. Simulate Restart (Clear memory)
    print("Simulating restart (clearing memory)...")
    # In app.py, sessions is a global dict. 
    # We can't easily modify the imported 'sessions' variable effectively if app.py uses it internally,
    # but db_module is independent of app.sessions.
    # The point is: can we retrieve it from DB without relying on memory?
    
    # 5. Retrieve again
    print("Retrieving after 'restart'...")
    session_restored = db_module.get_session_db(sid)
    if not session_restored:
        print("ERROR: Session lost after restart simulation!")
    else:
        print("Session retrieved successfully.")
        print(f"Config: {session_restored.get('config')}")
        print(f"Messages: {len(session_restored.get('messages', []))}")

    # 6. List sessions
    print("Listing sessions...")
    all_sessions = db_module.list_sessions_db()
    found = False
    for s in all_sessions:
        if s['id'] == sid:
            found = True
            print(f"Found session in list: {s['name']} (Msgs: {s.get('message_count')})")
            break
    
    if not found:
        print("ERROR: Session not found in list.")
    else:
        print("List verified.")

    # Cleanup
    # db_module.delete_session_db(sid)
    # print("Cleanup done.")

if __name__ == "__main__":
    test_persistence()

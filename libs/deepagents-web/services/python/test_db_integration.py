import requests
import time
import json
import os

BASE_URL = "http://127.0.0.1:8002"

def test_session_lifecycle():
    print("--- Testing Session Lifecycle ---")
    
    # 1. Create Session
    print("1. Creating session...")
    resp = requests.post(f"{BASE_URL}/sessions")
    assert resp.status_code == 200, f"Create failed: {resp.text}"
    sid = resp.json()['id']
    print(f"   Session ID: {sid}")
    
    # 2. Verify Initial State
    print("2. Verifying initial state...")
    resp = requests.get(f"{BASE_URL}/sessions")
    sessions = resp.json()
    print(f"DEBUG: sessions type: {type(sessions)}")
    # print(f"DEBUG: sessions content: {sessions}")
    
    session = next((s for s in sessions if s['id'] == sid), None)
    assert session is not None, "Session not found in list"
    assert session['name'] == "New Session", f"Unexpected initial name: {session['name']}"
    print("   Initial state verified.")
    
    # 3. Post Message (Trigger Auto-rename)
    print("3. Posting message to trigger auto-rename...")
    msg_content = "Hello, this is a test message for auto-renaming."
    resp = requests.post(f"{BASE_URL}/sessions/{sid}/messages", json={"content": msg_content, "tools": True})
    assert resp.status_code == 200, f"Post message failed: {resp.text}"
    print("   Message posted.")
    
    # 4. Verify Auto-rename
    print("4. Verifying auto-rename...")
    # Give a tiny bit of time for DB update if async (it's sync in code but good practice)
    time.sleep(0.5) 
    resp = requests.get(f"{BASE_URL}/sessions")
    sessions = resp.json()
    session = next((s for s in sessions if s['id'] == sid), None)
    expected_name = msg_content[:30] + "..."
    # Logic in app.py: 
    # new_name = req.content[:30]
    # if len(req.content) > 30: new_name += "..."
    
    print(f"   Current name: {session['name']}")
    assert session['name'] == expected_name, f"Auto-rename failed. Expected '{expected_name}', got '{session['name']}'"
    print("   Auto-rename verified.")
    
    # 5. Verify Context/History Persistence
    print("5. Verifying context persistence...")
    resp = requests.get(f"{BASE_URL}/sessions/{sid}/context")
    assert resp.status_code == 200
    context = resp.json()
    history = context['history']
    assert len(history) >= 1, "History empty"
    assert history[-1]['content'] == msg_content, "Last message content mismatch"
    print("   Context persistence verified.")
    
    # 6. Delete Session
    print("6. Deleting session...")
    resp = requests.delete(f"{BASE_URL}/sessions/{sid}")
    assert resp.status_code == 200
    
    resp = requests.get(f"{BASE_URL}/sessions")
    session = next((s for s in resp.json() if s['id'] == sid), None)
    assert session is None, "Session still exists after delete"
    print("   Delete verified.")
    
    print("--- Session Lifecycle Test Passed ---\n")

def test_migration():
    print("--- Testing Migration ---")
    # Create a dummy JSON file in the sessions directory
    # We need to know where SESSIONS_DIR is. 
    # Based on app.py: DEEPAGENTS_PATH/../assemble_agents/sessions
    # But since we are running this script, we can just hit the migrate endpoint.
    # We need to manually create a file first.
    
    # Let's try to infer path relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # app.py: Path(__file__).parent.parent.parent / "assemble_agents"
    # app.py is in services/python. 
    # .parent = python
    # .parent.parent = services
    # .parent.parent.parent = deepagents-web
    # So DATA_DIR is deepagents-web/assemble_agents
    
    # script_dir is services/python
    # ../.. is deepagents-web
    sessions_dir = os.path.join(script_dir, "../../assemble_agents/sessions")
    os.makedirs(sessions_dir, exist_ok=True)
    
    dummy_id = f"test_mig_{int(time.time())}"
    dummy_file = os.path.join(sessions_dir, f"{dummy_id}.json")
    
    dummy_data = {
        "id": dummy_id,
        "name": "Migration Test Session",
        "messages": [
            {"role": "user", "content": "Migration test message"}
        ],
        "logs": [],
        "config": {}
    }
    
    with open(dummy_file, 'w', encoding='utf-8') as f:
        json.dump(dummy_data, f)
        
    print(f"1. Created dummy session file: {dummy_id}")
    
    # Call migrate
    print("2. Calling migrate endpoint...")
    resp = requests.post(f"{BASE_URL}/sessions/migrate")
    assert resp.status_code == 200
    result = resp.json()
    print(f"   Migration result: {result}")
    
    # Verify in DB
    print("3. Verifying in DB via API...")
    resp = requests.get(f"{BASE_URL}/sessions")
    session = next((s for s in resp.json() if s['id'] == dummy_id), None)
    assert session is not None, "Migrated session not found in DB"
    assert session['name'] == "Migration Test Session", "Migrated name mismatch"
    
    # Verify messages
    resp = requests.get(f"{BASE_URL}/sessions/{dummy_id}/context")
    history = resp.json()['history']
    assert len(history) == 1
    assert history[0]['content'] == "Migration test message"
    print("   Migration verified.")
    
    # Cleanup
    requests.delete(f"{BASE_URL}/sessions/{dummy_id}")
    if os.path.exists(dummy_file):
        os.remove(dummy_file)
    print("--- Migration Test Passed ---")

if __name__ == "__main__":
    try:
        test_session_lifecycle()
        test_migration()
        print("\nALL TESTS PASSED")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        exit(1)

import requests
import time
import sys

# Frontend calls Node at 8005 via proxy (or directly if we test Node)
# Since we are testing backend integration, we call Node directly.
BASE_URL = "http://127.0.0.1:8005/api/v1/chat"

def check_full_stack():
    print(f"Checking {BASE_URL}/sessions...")
    try:
        resp = requests.get(f"{BASE_URL}/sessions")
        print(f"Status: {resp.status_code}")
        try:
            print(f"Content: {resp.json()}")
            if resp.status_code == 200 and isinstance(resp.json(), list):
                print("Success! Sessions list is available.")
                return True
            else:
                print("Failed! Not a list or not 200.")
                return False
        except:
            print(f"Content (Text): {resp.text}")
            return False
            
    except Exception as e:
        print(f"Exception: {e}")
        return False

def test_create_and_rename():
    print("Testing creation...")
    try:
        # Create
        resp = requests.post(f"{BASE_URL}/sessions", json={})
        if resp.status_code != 200:
            print(f"Create failed: {resp.status_code} {resp.text}")
            return False
        sid = resp.json()['id']
        print(f"Created session {sid}")
        
        # Send message (trigger auto-rename)
        print("Sending message...")
        msg_resp = requests.post(f"{BASE_URL}/sessions/{sid}/messages", json={"content": "Hello world", "tools": True})
        print(f"Message Status: {msg_resp.status_code}")
        
        # Check if renamed
        time.sleep(1)
        list_resp = requests.get(f"{BASE_URL}/sessions")
        sessions = list_resp.json()
        my_session = next((s for s in sessions if s['id'] == sid), None)
        if my_session:
            print(f"Session Name: {my_session['name']}")
            if my_session['name'] != "New Session" and "Hello" in my_session['name']:
                print("Auto-rename Success!")
                return True
            else:
                print(f"Auto-rename Failed or not triggered yet. Name: {my_session['name']}")
                return False
        else:
            print("Session not found in list!")
            return False
            
    except Exception as e:
        print(f"Test Exception: {e}")
        return False

if __name__ == "__main__":
    if check_full_stack():
        if test_create_and_rename():
            sys.exit(0)
    sys.exit(1)

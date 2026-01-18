import requests
import json

BASE_URL = "http://127.0.0.1:8001"

def test_stream():
    # 0. Check health/config
    try:
        resp = requests.get(f"{BASE_URL}/config", timeout=10)
        print(f"Config check: {resp.status_code}")
    except Exception as e:
        print(f"Config check failed: {e}")
        return

    # 1. Create session
    resp = requests.post(f"{BASE_URL}/sessions", json={})
    if resp.status_code != 200:
        print(f"Failed to create session: {resp.text}")
        return
    sid = resp.json()['id']
    print(f"Created session: {sid}")

    # 2. Send message
    resp = requests.post(f"{BASE_URL}/sessions/{sid}/messages", json={"content": "Hello, are you there?", "tools": True})
    if resp.status_code != 200:
        print(f"Failed to send message: {resp.text}")
        return
    print("Message sent")

    # 3. Stream
    url = f"{BASE_URL}/sessions/{sid}/stream"
    print(f"Connecting to stream: {url}")
    
    try:
        with requests.get(url, stream=True) as resp:
            if resp.status_code != 200:
                 print(f"Stream failed with status {resp.status_code}: {resp.text}")
                 return

            for line in resp.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    print(f"Received: {decoded_line}")
                    
    except Exception as e:
        print(f"Stream error: {e}")

if __name__ == "__main__":
    test_stream()

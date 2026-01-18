import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8002"

def check_sessions():
    print(f"Checking {BASE_URL}/sessions...")
    try:
        resp = requests.get(f"{BASE_URL}/sessions")
        print(f"Status: {resp.status_code}")
        print(f"Content: {resp.text}")
        if resp.status_code == 200:
            print("Success!")
            return True
        else:
            print("Failed!")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    # Wait for server to start if needed
    for i in range(5):
        if check_sessions():
            sys.exit(0)
        time.sleep(2)
    sys.exit(1)

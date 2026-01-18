import requests
try:
    resp = requests.get("http://127.0.0.1:8001/ping")
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text}")
except Exception as e:
    print(f"Error: {e}")

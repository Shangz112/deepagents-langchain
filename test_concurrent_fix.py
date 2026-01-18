import requests
import time
import threading
import sys

BASE_URL = "http://localhost:8003"

def create_session():
    r = requests.post(f"{BASE_URL}/sessions")
    r.raise_for_status()
    return r.json()['id']

def start_generation(sid):
    # Send a message that triggers a long response
    requests.post(f"{BASE_URL}/sessions/{sid}/messages", json={
        "content": "Write a very long story about a robot who learns to love. At least 1000 words.",
        "tools": False
    })
    
    # Start stream in a thread to simulate keeping connection open
    def stream():
        try:
            with requests.get(f"{BASE_URL}/sessions/{sid}/stream", stream=True) as r:
                for line in r.iter_lines():
                    pass # Consume
        except Exception as e:
            print(f"Stream error: {e}")

    t = threading.Thread(target=stream)
    t.start()
    return t

def check_status(sid):
    r = requests.get(f"{BASE_URL}/sessions/{sid}/status")
    if r.status_code == 404:
        print(f"Status endpoint 404 for {sid}")
        return None
    return r.json()

def main():
    print("Creating Session A...")
    sid_a = create_session()
    print(f"Session A: {sid_a}")
    
    print("Starting generation in A...")
    thread_a = start_generation(sid_a)
    
    time.sleep(1) # Wait for start
    
    status_a = check_status(sid_a)
    print(f"Status A (expect generating): {status_a}")
    
    if status_a.get('status') != 'generating':
        print("FAIL: Session A should be generating")
        # sys.exit(1) # Don't exit yet, might be timing
    
    print("Creating Session B (Switching)...")
    sid_b = create_session()
    print(f"Session B: {sid_b}")
    
    status_b = check_status(sid_b)
    print(f"Status B (expect idle): {status_b}")
    
    if status_b.get('status') != 'idle':
        print("FAIL: Session B should be idle")
        
    print("Checking A again (Switch back)...")
    status_a_2 = check_status(sid_a)
    print(f"Status A (expect generating): {status_a_2}")
    
    if status_a_2.get('status') != 'generating':
        print("FAIL: Session A stopped generating unexpectedly")
        
    print("Aborting A...")
    requests.post(f"{BASE_URL}/sessions/{sid_a}/abort")
    
    # Poll for status change (up to 10 seconds)
    status_a_3 = None
    for _ in range(10):
        time.sleep(1)
        s = check_status(sid_a)
        if s.get('status') == 'idle':
            status_a_3 = s
            break
            
    print(f"Status A (expect idle): {status_a_3}")
    
    if not status_a_3 or status_a_3.get('status') != 'idle':
        print("FAIL: Session A did not stop")
        
    print("Done.")

if __name__ == "__main__":
    main()

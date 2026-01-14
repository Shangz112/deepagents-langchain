import requests
import json
import time

BASE_URL = "http://127.0.0.1:8001"

def test_feedback():
    print("Testing Feedback Endpoint...")
    feedback_data = {
        "messageId": "msg_123",
        "query": "Hello",
        "response": "Hi there!",
        "rating": "good",
        "timestamp": int(time.time() * 1000)
    }
    
    try:
        r = requests.post(f"{BASE_URL}/feedback", json=feedback_data)
        print(f"POST /feedback status: {r.status_code}")
        print(f"Response: {r.json()}")
        
        if r.status_code == 200:
            print("Feedback submitted successfully.")
            
            # Now try export
            r_export = requests.get(f"{BASE_URL}/feedback/export")
            print(f"GET /feedback/export status: {r_export.status_code}")
            export_data = r_export.json()
            print(f"Exported data count: {len(export_data)}")
            print(f"Last item: {export_data[-1]}")
            
            if export_data[-1]['messageId'] == 'msg_123':
                print("Verification SUCCESS: Feedback saved and exported.")
            else:
                print("Verification FAILED: Feedback not found in export.")
        else:
             print("Verification FAILED: POST /feedback failed.")
             
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_feedback()

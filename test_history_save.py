
import json
import asyncio
import aiohttp
import sys

# Change to your python service port
PY_URL = "http://127.0.0.1:8003"

async def test_history():
    async with aiohttp.ClientSession() as session:
        # 1. Create Session
        async with session.post(f"{PY_URL}/sessions", json={}) as resp:
            data = await resp.json()
            sid = data['id']
            print(f"Created session: {sid}")

        # 2. Send Message
        msg = {"content": "Hello, please reply with 'confirmed'.", "tools": False}
        async with session.post(f"{PY_URL}/sessions/{sid}/messages", json=msg) as resp:
            print(f"Sent message: {resp.status}")

        # 3. Stream
        print("Starting stream...")
        async with session.get(f"{PY_URL}/sessions/{sid}/stream") as resp:
            async for line in resp.content:
                pass # Consume stream
        print("Stream finished.")

        # 4. Check History
        async with session.get(f"{PY_URL}/sessions/{sid}/context") as resp:
            data = await resp.json()
            history = data.get('history', [])
            print(f"History length: {len(history)}")
            for m in history:
                print(f"Role: {m['role']}, Content: {m['content'][:20]}...")
            
            # Check if assistant message exists
            has_assistant = any(m['role'] == 'assistant' for m in history)
            if has_assistant:
                print("SUCCESS: Assistant message found in history.")
            else:
                print("FAILURE: No assistant message in history.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_history())

import requests

try:
    url = "http://127.0.0.1:8001/kb/sources/1768382403117/file"
    print(f"Fetching {url}...")
    r = requests.get(url, stream=True)
    print(f"Status: {r.status_code}")
    print(f"Headers: {r.headers}")
    if r.status_code == 200:
        with open("download_test.docx", "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download successful")
    else:
        print(f"Error: {r.text}")
except Exception as e:
    print(f"Exception: {e}")

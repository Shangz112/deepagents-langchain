import urllib.request

try:
    url = "http://127.0.0.1:8001/kb/sources/1768382403117/file"
    print(f"Fetching {url}...")
    with urllib.request.urlopen(url) as response:
        print(f"Status: {response.status}")
        print(f"Headers: {response.headers}")
        with open("download_test_urllib.docx", "wb") as f:
            f.write(response.read())
        print("Download successful")
except Exception as e:
    print(f"Exception: {e}")

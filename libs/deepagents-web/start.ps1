$env:PY_SERVICE_URL = "http://localhost:8001"
Start-Process -NoNewWindow powershell -ArgumentList "-Command", "cd libs/deepagents-app/services/python; uvicorn app:app --port 8001"
Start-Process -NoNewWindow powershell -ArgumentList "-Command", "cd libs/deepagents-app/apps/server; npm run dev"
Start-Process -NoNewWindow powershell -ArgumentList "-Command", "cd libs/deepagents-app/apps/web; npm run dev"
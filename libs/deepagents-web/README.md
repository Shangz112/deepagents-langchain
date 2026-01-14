# DeepAgents App

- 前端：`apps/web`
- 后端：`apps/server`
- Python 服务：`services/python`

## 本地启动

- Python：`uvicorn app:app --port 8001` 在 `services/python`
- Node：`npm run dev` 在 `apps/server`，设置 `PY_SERVICE_URL=http://localhost:8001`
- Web：`npm run dev` 在 `apps/web`

## 生产部署

- `docker-compose up --build`

## OpenAPI

- `libs/deepagents-app/api/openapi.yaml`
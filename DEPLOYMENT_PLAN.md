# DeepAgents 配置与部署分析报告

本以此文档记录了项目中所有涉及路径、端口及硬编码配置的关键位置，并提供了一键部署的优化方案。

## 1. 现状分析：配置点与硬编码列表

### 1.1 前端 (Web Client)
| 文件位置 | 变量/配置项 | 当前值 (硬编码/默认) | 说明 |
| :--- | :--- | :--- | :--- |
| `libs/deepagents-web/apps/web/vite.config.ts` | `server.proxy['/api/v1'].target` | `'http://127.0.0.1:8005'` | Node 中间层服务地址 |
| `libs/deepagents-web/apps/web/vite.config.ts` | `server.port` | `5173` | 前端开发服务器端口 |

### 1.2 中间层 (Node.js Server)
| 文件位置 | 变量/配置项 | 当前值 (硬编码/默认) | 说明 |
| :--- | :--- | :--- | :--- |
| `libs/deepagents-web/apps/server/src/index.ts` | `port` | `process.env.PORT || 8005` | 中间层服务端口 |
| `libs/deepagents-web/apps/server/src/pythonClient.ts` | `PY_URL` | `process.env.PY_SERVICE_URL || 'http://127.0.0.1:8001'` | Python 后端服务地址 |
| `libs/deepagents-web/apps/server/src/routes/config.ts` | `config` | `{ model: 'mock', ... }` | 默认配置对象 |

### 1.3 后端 (Python Service)
| 文件位置 | 变量/配置项 | 当前值 (硬编码/默认) | 说明 |
| :--- | :--- | :--- | :--- |
| `libs/deepagents-web/services/python/app.py` | `siliconflow_config.api_key` | `sk-zyh...` (硬编码 Key) | 默认 API Key |
| `libs/deepagents-web/services/python/app.py` | `DATA_DIR` | `Path(__file__).parent.parent / "deepagents_data"` | 数据存储目录 (相对路径，良好) |
| `libs/deepagents-web/services/python/rag_service.py` | `db_path` | `... / "deepagents_data" / "vectordb"` | 向量库路径 (相对路径，良好) |
| `config.yaml` (根目录) | `mbse_analyzer.api.port` | `8000` | MBSE 分析器配置 (可能与 app.py 端口冲突) |
| `config.yaml` (根目录) | `mbse_analyzer.database.neo4j.uri` | `"bolt://localhost:7687"` | Neo4j 数据库地址 |

### 1.4 启动脚本与文档
| 文件位置 | 内容 | 说明 |
| :--- | :--- | :--- |
| `libs/deepagents-web/start.ps1` | `uvicorn app:app --port 8001` | Python 服务启动命令 (端口硬编码) |
| `libs/deepagents-web/docker-compose.yml` | `ports: - "8000:8000"` | Docker 端口映射 |
| `QUICK_START.md` | `D:\MASrepos\...` | 文档中的绝对路径示例 |

---

## 2. 优化方案：一键部署支持

目标：通过统一的配置管理，消除代码中的硬编码，支持通过环境变量控制所有端口和路径。

### 2.1 方案架构
采用 **根目录 `.env` 文件 + 环境变量注入** 的方式。

1.  **统一配置源**：在项目根目录（或 `libs/deepagents-web`）创建 `.env` 文件。
2.  **前端适配**：Vite 自动加载 `.env`，替换 `vite.config.ts` 中的代理目标。
3.  **中间层适配**：Node.js 使用 `dotenv` 加载环境变量，覆盖默认端口和后端地址。
4.  **后端适配**：Python 使用 `python-dotenv` 加载环境变量，覆盖 API Key 和服务端口。
5.  **启动脚本适配**：PowerShell 脚本先读取 `.env`，再动态构建启动命令。

### 2.2 实施步骤

#### 第一步：定义标准 `.env` 模板 (`.env.example`)
```ini
# 服务端口配置
WEB_PORT=5173
SERVER_PORT=8005
PYTHON_PORT=8001

# 服务地址配置 (用于服务间通信)
# 如果是本地部署，通常使用 http://127.0.0.1
# 如果是 Docker 部署，可能需要改为容器名
VITE_API_TARGET=http://127.0.0.1:8005
PY_SERVICE_URL=http://127.0.0.1:8001

# 外部服务配置
SILICONFLOW_API_KEY=your_api_key_here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLOW_MODEL=deepseek-ai/DeepSeek-V3.2

# 数据库配置 (可选)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

#### 第二步：修改 `vite.config.ts`
```typescript
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), '')
  const serverPort = parseInt(env.SERVER_PORT || '8005')
  const webPort = parseInt(env.WEB_PORT || '5173')
  const apiTarget = env.VITE_API_TARGET || `http://127.0.0.1:${serverPort}`

  return {
    plugins: [vue()],
    server: {
      port: webPort,
      proxy: {
        '/api/v1': {
          target: apiTarget,
          changeOrigin: true,
          timeout: 600000
        }
      }
    }
  }
})
```

#### 第三步：修改 Node.js Server (`index.ts`)
引入 `dotenv` 并使用环境变量：
```typescript
import dotenv from 'dotenv'
import path from 'path'
// 尝试加载根目录或当前目录的 .env
dotenv.config({ path: path.resolve(__dirname, '../../../../.env') }) 

// ...
const port = Number(process.env.SERVER_PORT || process.env.PORT || 8005)
```

#### 第四步：修改 Python Service (`app.py`)
引入 `python-dotenv`：
```python
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

# ...
siliconflow_config = {
    "api_key": os.getenv("SILICONFLOW_API_KEY", "default_key"),
    "base_url": os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1"),
    "model": os.getenv("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-V3.2")
}
```

#### 第五步：修改启动脚本 (`start.ps1`)
脚本应具备读取 `.env` 能力，或者简单地由用户确保 `.env` 存在，脚本直接运行命令（服务内部会读取 .env）。
更好的方式是脚本从 `.env` 提取端口参数传递给 uvicorn：

```powershell
# 伪代码示例
$envContent = Get-Content .env -ErrorAction SilentlyContinue
# 解析 PYTHON_PORT ...
$port = 8001 # 默认
if ($envContent) { ... }

Start-Process uvicorn -ArgumentList "app:app --port $port" ...
```

### 2.3 预期效果
1.  **一键部署**：用户只需复制 `.env.example` 为 `.env`，填入 Key，运行 `start.ps1` 即可。
2.  **灵活配置**：修改 `.env` 即可变更端口，无需修改代码。
3.  **安全**：API Key 不再硬编码在源码中。


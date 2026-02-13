# 前后端集成待办

> **Last Updated**: 2026-01-21  
> **依据文件**: TODO_FRONTEND_BACKEND_GAP.md

## 1. 待办总览

| 待办项 | 优先级 | 当前缺口 | 期望结果 |
| :--- | :--- | :--- | :--- |
| **Plan Graph 实时状态** | P0 | 仅可视化消息历史，未接入 LangGraph 运行态 | 展示实时执行状态、子代理拓扑与步骤进度 |
| **会话持久化** | P0 | Python 内存会话，重启丢失 | 会话与配置持久化并可重放 |
| **MinerU 高保真模型** | P2 | 解析依赖回退模型 | 下载并启用 `doclayout_yolo`/`unimernet` |

## 2. 任务拆解

### 2.1 Plan Graph 实时状态

| 层级 | 任务 | 交付物 |
| :--- | :--- | :--- |
| **Python 服务** | 输出 LangGraph 运行态 API | `GET /agents/plan/graph` 返回节点/边/状态 |
| **Node BFF** | 转发运行态 API | `/api/v1/agents/plan/graph` |
| **前端** | 接入实时状态并刷新视图 | `PlanGraph.vue` 绑定后端图数据 |

### 2.2 会话持久化

| 层级 | 任务 | 交付物 | 状态 |
| :--- | :--- | :--- | :--- |
| **Python 服务** | 1. 引入 `AsyncSqliteSaver` 并解决 `aiosqlite` 兼容性 | `app.py` 集成代码 | ✅ Done |
| **Python 服务** | 2. 实现 SQLite 基础表 (`sessions`, `messages`) | `db.py` 完整 CRUD | ✅ Done |
| **Python 服务** | 3. 重构会话管理为 DB 优先 + 内存缓存模式 | `app.py` 接口改造 | ✅ Done |

### 2.3 MinerU 模型增强

| 层级 | 任务 | 交付物 |
| :--- | :--- | :--- |
| **基础设施** | 下载模型并配置路径 | 本地模型可用 |
| **Python 服务** | 验证解析质量 | 高保真解析默认生效 |

## 3. 验收标准

1. **Plan Graph**：同一会话中，执行步骤状态实时更新且与后端一致。
2. **会话持久化**：服务重启后可恢复历史会话与配置。
3. **解析质量**：包含复杂版式的 PDF 解析准确率显著提升。

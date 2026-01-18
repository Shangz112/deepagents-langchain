# 历史会话管理技术方案

## 1. 背景与目标
目前 DeepAgents 的会话数据存储在内存中，服务重启或页面刷新会导致上下文丢失。本方案旨在实现基于文件系统的会话持久化，支持历史会话的查看、切换和继续对话，从而提升用户体验和工具的实用性。

## 2. 总体架构
- **存储层**: 使用文件系统 (JSON) 存储会话数据（消息历史、配置、元数据）。
- **后端 (Python)**: 负责会话的 CRUD 操作，并在服务启动或请求时从磁盘加载数据。关键在于处理服务重启后的状态恢复，确保 Agent 能够“记得”之前的对话上下文。
- **中间层 (Node.js)**: 充当 API 网关，转发前端对会话管理的请求。
- **前端 (Vue)**: 新增侧边栏会话列表，支持路由切换加载不同会话，并与现有聊天界面无缝集成。

## 3. 详细设计

### 3.1 后端持久化设计 (Python)

#### 3.1.1 存储结构
利用现有的 `DATA_DIR` (`libs/assemble_agents`)，采用以下目录结构：
```text
libs/assemble_agents/
  └── sessions/
      ├── {sid}/
      │   └── session.json  # 存储元数据、配置和消息历史
      └── ...
```

#### 3.1.2 数据模型 (session.json)
```json
{
  "id": "1768718219053",
  "title": "关于 Python 的讨论",
  "created_at": 1768718219053,
  "updated_at": 1768718250000,
  "config": {
    "model": "deepseek-ai/DeepSeek-V3.2",
    "temperature": 0.7,
    "system_prompt": "..."
  },
  "messages": [
    { "role": "user", "content": "你好" },
    { "role": "assistant", "content": "你好！有什么我可以帮你的吗？" }
  ]
}
```

#### 3.1.3 核心逻辑变更 (`app.py`)
1.  **加载机制 (`load_session`)**:
    *   在访问 `GET /sessions/{sid}` 或 `stream_session` 时，如果内存 `sessions` 中不存在该 ID，尝试从磁盘读取 `session.json`。
    *   如果文件存在，将其加载到内存 `sessions` 字典中。

2.  **保存机制 (`save_session`)**:
    *   在 `create_session`、`update_session_config`、以及 `stream_session` 完成（生成完整回复）后，触发保存操作，将内存状态写入磁盘。

3.  **状态恢复 (Context Restoration)**:
    *   目前使用 `InMemorySaver`，重启后 Checkpointer 为空。
    *   **策略**: 在 `stream_session` 中，检测到 `checkpointer` 为空但 `session['messages']` 不为空（说明是重启后首次继续对话），将历史消息作为上下文传递给 Agent。
    *   **实现细节**:
        *   将 `session['messages']` 转换为 LangChain `BaseMessage` 对象。
        *   调用 `agent.astream_events` 时，输入参数改为 `{"messages": history_messages + [new_message]}`，而不仅仅是新消息。这样 LangGraph 会自动将历史合并到新的状态中。

### 3.2 API 接口设计

| 方法 | 路径 | 描述 | 请求/响应示例 |
| --- | --- | --- | --- |
| **GET** | `/sessions` | 获取会话列表（按更新时间倒序） | Res: `[{id, title, updated_at}, ...]` |
| **POST** | `/sessions` | 创建新会话 | Res: `{id: "..."}` |
| **GET** | `/sessions/{sid}` | 获取会话详情（用于加载历史） | Res: `{id, messages: [...], config: ...}` |
| **DELETE** | `/sessions/{sid}` | 删除会话 | Res: `{ok: true}` |
| **PUT** | `/sessions/{sid}` | 更新元数据（如重命名标题） | Req: `{title: "新标题"}` |

### 3.3 前端 UI/UX 设计

#### 3.3.1 布局变更
*   修改 `App.vue` 或主布局，引入一个左侧边栏 (`Sidebar`)。
*   侧边栏包含：
    *   "New Chat" 按钮。
    *   历史会话列表（显示标题和时间，支持点击切换）。
    *   每个列表项提供“删除”操作。

#### 3.3.2 交互逻辑
1.  **初始化**: 应用加载时调用 `GET /sessions` 获取列表。
2.  **新建**: 点击 "New Chat" -> `POST /sessions` -> 清空当前消息视图 -> 更新 URL 到 `/chat/{new_id}`。
3.  **切换**: 点击历史记录 -> `GET /sessions/{id}` -> 用返回的 `messages` 替换当前视图 -> 更新 URL。
4.  **自动标题**: (可选优化) 第一轮对话结束后，根据内容自动生成标题并调用 `PUT /sessions/{id}` 更新。

## 4. 实施步骤

1.  **后端开发**:
    *   实现 `load_session_from_disk` 和 `save_session_to_disk` 辅助函数。
    *   实现 `GET /sessions` 接口（遍历目录读取 JSON）。
    *   修改 `stream_session` 以支持重启后的历史消息注入。
2.  **中间层开发**:
    *   在 `routes/chat.ts` 和 `pythonClient.ts` 中添加对应的转发接口。
3.  **前端开发**:
    *   创建 `Sidebar.vue` 组件。
    *   集成 API 调用。
    *   调整路由逻辑，支持 URL 携带 Session ID。

## 5. 风险与规避
*   **并发写入**: 使用文件锁或简单的原子写入（写临时文件后重命名）避免 JSON 损坏。
*   **性能**: 会话列表接口仅读取必要的元数据，避免加载庞大的消息历史。
*   **现有功能影响**: 保持 `sessions` 内存字典结构不变，仅在必要时从磁盘“懒加载”，确保对现有逻辑的侵入性最小。

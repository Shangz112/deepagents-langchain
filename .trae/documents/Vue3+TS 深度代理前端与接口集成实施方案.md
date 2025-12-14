## 项目约束

* 保持 `d:/MASrepos/deepagents-langchain/libs/deepagents/deepagents/` 原始源码只读并不做任何改动

* 保持 `d:/MASrepos/deepagents-langchain/libs/deepagents-cli/` 原始源码只读并不做任何改动

* 可新建 `d:/MASrepos/deepagents-langchain/libs/deepagents-app/` 目录并实现任务所需要的全部功能

* 所有运行期对 deepagents 的调用通过直接 import 该目录内的 Python 源文件实现（不打包、不复制、不重写）

* Node.js 层不直接操作 deepagents Python API，采用本地 Python 微服务桥接，避免跨语言耦合同时满足“直接引用源文件”的限制

* 关键代码参考：`d:\MASrepos\deepagents-langchain\libs\deepagents\deepagents\graph.py:40-56`（`create_deep_agent` 入口）、`d:\MASrepos\deepagents-langchain\libs\deepagents\deepagents\graph.py:113-143`（标准中间件链含 SubAgent）、`d:\MASrepos\deepagents-langchain\libs\deepagents\deepagents\backends\protocol.py:159-409`（后端协议与工具调用能力）

## 总体架构

* 前端：Vue3 + TypeScript + Vite，Pinia 管理全局状态，Vue Router 组织模块路由

* API 层：Node.js（Express/HTTP）提供 RESTful 接口与 SSE/WebSocket 流；类型校验（Zod）+ OpenAPI 文档（swagger-ui-express）

* Python 微服务：FastAPI + Uvicorn，直接 `sys.path.insert(0, "d:/MASrepos/deepagents-langchain/libs/deepagents/deepagents/")` 引入 `graph.py` 等源文件并封装会话、工具调用、子代理管理与计划数据导出

* 交互流：Web 前端 → Node API（鉴权、限流、日志）→ Python 服务（deepagents 执行）→ Node 流式转发至前端

* 存储：本地文件/轻量 KV（初期），为知识库与配置模板提供可插拔适配层（未来可接入向量库/RAG）

## 前端实现

* 技术栈：Vue3 + TS + Vite；样式系统：TailwindCSS（定制赛博扁平主题）+ 设计令牌（颜色/阴影/动效）

* 核心页面与组件：

  * 主对话交互区：消息列表（流式渲染）、输入区、工具调用反馈条、会话切换

  * 参数配置面板：模型/中间件/后端参数编辑器，支持预设与模板管理

  * 提示词设计工作台：模板编辑（变量插值）、版本列表与差异查看、发布与回滚

  * 知识库管理界面：数据源绑定、检索预览、索引与更新状态

* 状态与类型：`AgentSession`、`Message`、`ToolCall`、`SubAgent`、`Skill`、`ParameterPreset`、`PromptTemplateVersion`、`KBSource`、`KBRecord`

* 响应式：移动端（单列）、平板（双栏：对话+侧板）、桌面（三栏：对话+参数+工作台/知识库）

* 计划可视化：Cytoscape.js 渲染计划/子代理调用图，支持节点细节面板与时间线回放

## Node.js API 层

* 框架：Express + TypeScript；路由前缀 `/api/v1`

* 会话与对话：

  * `POST /chat/sessions` 创建会话（返回 `sessionId`）

  * `GET /chat/sessions/:id` 获取会话状态与历史

  * `DELETE /chat/sessions/:id` 关闭会话

  * `POST /chat/sessions/:id/messages` 发送消息（异步）

  * `GET /chat/sessions/:id/stream` SSE 流式输出回复与工具事件

* 参数配置：

  * `GET/PUT /config` 当前配置读取与更新

  * `GET/POST/DELETE /config/presets` 预设管理；`POST /config/import`、`GET /config/export`

* 提示词工程：

  * `GET/POST /prompts/templates`、`GET /prompts/templates/:id/versions`、`POST /prompts/templates/:id/versions` 版本管理与变量插值预览

* 子代理与计划：

  * `GET/POST/DELETE /agents/subagents` 管理子代理集合

  * `GET /agents/plan/graph` 获取计划/调用图（用于可视化）

* 工具调用：

  * `POST /tools/execute` 一般工具调用（由 deepagents 决策或显式触发）

* 知识库：

  * `GET/POST/DELETE /kb/sources` 绑定数据源

  * `GET /kb/query` 检索预览；`POST /kb/update` 更新索引

* 技能管理：

  * `GET /skills` 列出技能；`POST /skills` 上传 `SKILL.md`；`DELETE /skills/:name`

* 错误处理：统一问题详情 JSON（`type`/`title`/`status`/`detail`/`instance`），分层错误码与追踪ID

* 文档：自动生成 OpenAPI（Swagger UI）+ Postman 集合导出

## Python deepagents 微服务

* 框架：FastAPI；服务职责：

  * 会话生命周期：创建/销毁会话；基于 `create_deep_agent` 启动 `CompiledStateGraph`（参考 `graph.py:40-56`）

  * 中间件与子代理：使用默认中间件链（`graph.py:113-143`），暴露子代理注册/列表接口

  * 工具调用：封装标准工具（文件系统、grep/glob、执行），遵循后端协议（参考 `backends/protocol.py:159-409`）

  * 计划数据：从 TodoList/Summarization/工具事件导出节点与边，供前端渲染

  * 技能：复用 CLI 的技能扫描（参考 `d:\MASrepos\deepagents-langchain\libs\deepagents-cli\deepagents_cli\skills\load.py:206-237`）提供 `/skills` 列表

* 引用方式：开机注入 `sys.path` 指向 deepagents 源目录，`from graph import create_deep_agent` 等直接引用，不改动源文件

## Agent-SubAgent 交互与计划可视化

* 交互：

  * DeepAgent 作为总控，SubAgents 通过 `SubAgentMiddleware`（`graph.py:116-135`）注册与调用

  * 前端提供子代理目录、启用/禁用、权重/描述编辑与测试入口

* 可视化：

  * 节点：消息、工具调用、子代理调用、计划项（Todo）

  * 边：依赖/触发/总结关系；时间轴分层视图

  * 数据来源：Python 服务事件流与计划导出 API

## Tool-Calling 接口

* 统一工具调用模型：`{name, args, sessionId, context}`

* 触发路径：

  * 由 DeepAgent 决策调用（Patch Tool Calls 中间件已支持，`graph.py:130-143`）

  * 用户显式触发（前端工具面板→Node→Python→执行）

* 返回：标准化 `result`/`error`/`meta`，前端以卡片/日志形式展示

## Skills 管理模块

* 结构：支持用户目录与项目目录，项目技能覆盖用户技能（`load.py:218-237`）

* 功能：扫描、预览、启用/禁用、上传/删除、版本快照（对 `SKILL.md`）

* 安全：路径安全检查与大小限制（`load.py:52-90`、`load.py:103-140`）

## 知识库集成

* 多源绑定：本地文件夹、HTTP 文档、Markdown 仓库等

* 需要支持RAG技术模块，包括vector database等，建议考虑milvus，最好支持agentic RAG

* 检索预览：关键片段高亮、来源链接、置信度

* 更新机制：增量索引，手动/定时触发；初期采用简易倒排索引，预留向量检索适配层

## 接口设计与错误处理

* RESTful 资源化路由，语义化状态码与错误体

* 全局错误中间件：参数校验错误（422）、业务错误（4xx）、系统错误（5xx）统一编码

* 可扩展性：版本化（`/api/v1`）、特性标识与实验开关、插件式路由挂载

## 代码质量与测试

* TypeScript 严格模式（`strict: true`）、公共类型与 DTO 规范

* 单元测试：

  * 前端：Vitest + Vue Test Utils；覆盖组件、store、路由与工具面板逻辑

  * 后端：Vitest/Jest + Supertest；覆盖路由、校验、错误处理与与 Python 服务的适配器

  * Python：Pytest（仅微服务适配层，不改 deepagents 源）

* 覆盖率门槛：≥80%（CI 中强制阈值）

* API Mock：`msw`（前端）+ `nock/supertest`（后端），提供可离线演示场景

## 部署与配置

* 开发：`apps/web`（Vite dev server）+ `apps/server`（Express）+ `services/python`（FastAPI）本地并行运行

* 生产：Docker Compose 三服务编排，Node 反向代理；环境变量管理（模型/密钥/后端参数）

* Windows 支持：PowerShell 启动脚本，确保路径与 PYTHONPATH 正确注入

* Ubuntu支持：需要有对应的bash脚本，确保路径与 PYTHONPATH 正确注入

## 交付物

* 完整前端源代码（Vue3+TS、组件与样式、状态与路由）

* 完整 RESTful 接口定义与 OpenAPI 文档

* 单元测试用例与覆盖率报告（≥80%）

* 部署配置（Docker Compose、环境说明、Windows 本地启动方案）

## 下一步

* 初始化三层项目骨架与依赖

* 搭建 Python 微服务最小可用端点（会话/消息/SSE 流）

* 前端对话与参数面板打通 API 流，接入计划可视化

* 完成技能与知识库首版功能，再完善错误处理与文档


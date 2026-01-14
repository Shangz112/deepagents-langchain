# DeepAgents 快速启动指南 (Quick Start Guide)

本文档提供从环境准备、配置到启动 DeepAgents CLI 的完整步骤。

## 1. 环境准备 (Prerequisites)

在开始之前，请确保您的系统满足以下要求：

*   **操作系统**: Windows, macOS, 或 Linux
*   **Python**: 版本 3.10 或更高
*   **包管理器**: 推荐使用 [uv](https://github.com/astral-sh/uv) (一个极速的 Python 包管理器)，也可以使用 pip/poetry。

### 安装 uv (推荐)
```bash
# MacOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 2. 项目安装 (Installation)

### 2.1 获取代码
```bash
git clone <repository_url> deepagents-langchain
cd deepagents-langchain
```

### 2.2 安装依赖
DeepAgents 的核心 CLI 位于 `libs/deepagents-cli` 目录下。

```bash
# 进入 CLI 目录
cd libs/deepagents-cli

# 使用 uv 同步依赖 (会自动创建虚拟环境)
uv sync
```

> **注意**: 如果不使用 `uv`，你需要手动创建虚拟环境并安装依赖：
> ```bash
> python -m venv .venv
> # 激活虚拟环境 (Windows: .venv\Scripts\activate, Mac/Linux: source .venv/bin/activate)
> pip install -e .
> ```

## 3. 配置 (Configuration)

DeepAgents 需要 LLM 的 API Key 才能运行。

### 3.1 设置环境变量
在 `libs/deepagents-cli` 目录下创建一个 `.env` 文件，并填入你的 API Key。

**Windows (PowerShell) 示例**:
```powershell
# 复制示例配置 (如果有) 或直接创建
New-Item -Path .env -ItemType File -Value "ANTHROPIC_API_KEY=sk-ant-..."
```

**推荐的 .env 内容**:
```env
# 核心模型支持 (至少需要一个)
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-proj-xxx

# 搜索工具支持 (可选，用于 web-research skill)
TAVILY_API_KEY=tvly-xxx

# 调试选项 (可选)
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=lsv2-xxx
# 独立追踪项目名 (推荐): 将 DeepAgents 的追踪数据与普通应用分开
# DEEPAGENTS_LANGSMITH_PROJECT=deepagents-traces
```

### 3.2 进阶配置：LangSmith 追踪隔离
在 `libs/deepagents-cli/deepagents_cli/config.py` 中，我们实现了一个特殊的逻辑：
*   **DEEPAGENTS_LANGSMITH_PROJECT**: 默认值为 `deepagents`。CLI 会在内部将其覆盖为 `LANGSMITH_PROJECT`。
*   **目的**: 这允许你将 Agent 的内部思考过程（Trace）记录到一个独立的项目中（默认为 `deepagents`），而不会污染你默认的 `LANGSMITH_PROJECT`（通常用于应用层追踪）。
*   **注意**: 这是一个推荐的最佳实践，特别是当你使用 LangSmith 进行调试时。

### 3.3 系统级配置 (Shared System Config)
如果你希望在多个 deepagents 应用（如 CLI 和未来的 App）之间共享 API Key，可以使用系统配置文件。

1.  **创建配置文件目录**: `mkdir ~/.deepagents` (Windows: `mkdir C:\Users\YourName\.deepagents`)
2.  **创建配置文件**: 将项目根目录下的 `config.example.yaml` 复制为 `~/.deepagents/config.yaml`。
3.  **配置 API Key**: 编辑该文件填入你的 Key。

系统配置文件的优先级低于环境变量（`.env`），但高于默认值。

## 4. 启动与使用 (Startup & Usage)

### 4.1 启动 CLI
最简单的启动方式是使用 `uv run`，它会自动使用虚拟环境中的依赖。

```bash
# 在 libs/deepagents-cli 目录下
uv run deepagents
```

或者，先激活虚拟环境再运行：

**Windows**:
```powershell
.venv\Scripts\activate
deepagents
```

**macOS/Linux**:
```bash
source .venv/bin/activate
deepagents
```

### 4.2 常用命令

#### 交互式对话
```bash
# 启动默认智能体
uv run deepagents

# 启动指定名称的智能体 (拥有独立记忆)
uv run deepagents --agent my-coding-bot
```

#### 技能管理 (Skills)
```bash
# 查看所有可用技能
uv run deepagents skills list

# 查看特定技能详情
uv run deepagents skills info <skill_name>

# 创建新技能模板
uv run deepagents skills create <new_skill_name>
```

#### 帮助信息
```bash
uv run deepagents help
```

## 5. 常见问题 (Troubleshooting)

### Windows 下的兼容性
如果在 Windows 下遇到类似 `ModuleNotFoundError: No module named 'termios'` 的错误，这是因为 `termios` 库仅支持 Unix 系统。
*   **解决方案**: 请确保您使用的是最新版本的代码，我们已经在 `deepagents-cli` v0.0.12+ 中修复了此兼容性问题。

### 依赖安装失败
如果 `uv sync` 失败，请尝试清除缓存或更新 uv：
```bash
uv cache clean
uv self update
```

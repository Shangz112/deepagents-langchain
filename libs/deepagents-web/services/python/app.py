import os
import sys
import time
import json
import db as db_module
import asyncio
import threading
import hashlib
import shutil
from typing import Dict, Any
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from rag_tool import search_knowledge_base
from rag_service import get_rag_service
from fastapi.responses import JSONResponse, FileResponse
from fastapi import Request, HTTPException
from starlette.responses import StreamingResponse
from langchain_core.messages import HumanMessage
import logging
import warnings
from dotenv import load_dotenv

# Load env from specific path
env_path = Path(r"d:/MASrepos/deepagents-langchain/libs/deepagents-web/.env")
load_dotenv(dotenv_path=env_path)

# Filter out noisy Pydantic warnings about NotRequired
warnings.filterwarnings("ignore", message=".*typing.NotRequired.*", category=UserWarning)

# Filter out noisy polling logs
class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        # Always show stream logs
        if "/stream" in msg:
            return True
        return msg.find("GET /sessions/") == -1 or \
               (msg.find("/config") == -1 and msg.find("/context") == -1)

# Add filter to uvicorn access logger
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

DEEPAGENTS_PATH = r"d:/MASrepos/deepagents-langchain/libs/deepagents-app/"
DEEPAGENTS_CLI_PATH = r"d:/MASrepos/deepagents-langchain/libs/deepagents-cli/"
for p in (DEEPAGENTS_PATH, DEEPAGENTS_CLI_PATH):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from langchain_openai import ChatOpenAI
    from deepagents import create_deep_agent
    from deepagents.backends import CompositeBackend
    from deepagents.backends.filesystem import FilesystemBackend
    from deepagents_core.agent_memory import AgentMemoryMiddleware
    from deepagents_core.skills import SkillsMiddleware
    from deepagents_core.shell import ShellMiddleware
    from deepagents_cli.config import settings, config
    from deepagents_core.agent import get_system_prompt, get_default_coding_instructions
    
    # Monkeypatch to allow Windows paths
    import deepagents.middleware.filesystem
    import re
    
    _original_validate = deepagents.middleware.filesystem._validate_path
    
    def _patched_validate(path, *args, **kwargs):
        # Allow Windows absolute paths
        if re.match(r"^[a-zA-Z]:", path):
            return path.replace("\\", "/")
        return _original_validate(path, *args, **kwargs)
        
    deepagents.middleware.filesystem._validate_path = _patched_validate

except ImportError as e:
    print(f"Warning: Failed to import deepagents modules: {e}")

try:
    from langgraph.checkpoint.memory import InMemorySaver
except ImportError:
    try:
        from langgraph.checkpoint.memory import MemorySaver as InMemorySaver
    except ImportError:
        # Fallback or simple mock if langgraph is not installed
        print("Warning: langgraph not found, InMemorySaver will fail if used.")
        class InMemorySaver:
            def __init__(self): pass
            def get(self, config): return None
            def put(self, config, checkpoint, metadata): pass
            def put_writes(self, config, writes, task_id): pass

try:
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    import aiosqlite
    
    # Monkeypatch for aiosqlite < 0.22 compatibility with langgraph-checkpoint-sqlite
    if not hasattr(aiosqlite.Connection, 'is_alive'):
        def is_alive(self):
            return self._running and self._connection is not None
        aiosqlite.Connection.is_alive = is_alive
        
    HAS_SQLITE_SAVER = True
except ImportError:
    HAS_SQLITE_SAVER = False
    print("Warning: langgraph-checkpoint-sqlite or aiosqlite not found. Persistence will be limited.")

# Global checkpointer
global_checkpointer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    db_module.init_db()
    
    # Initialize Global Checkpointer
    global global_checkpointer
    db_path = str(db_module.DB_PATH)
    
    if HAS_SQLITE_SAVER:
        try:
            # Use AsyncSqliteSaver with context manager
            async with AsyncSqliteSaver.from_conn_string(db_path) as saver:
                global_checkpointer = saver
                print(f"Initialized AsyncSqliteSaver at {db_path}")
                yield
        except Exception as e:
            print(f"Failed to initialize AsyncSqliteSaver: {e}")
            global_checkpointer = InMemorySaver()
            yield
    else:
        global_checkpointer = InMemorySaver()
        yield

    # Explicitly handle potential cancellation during shutdown to avoid noisy logs
    try:
        # Give a moment for pending tasks to complete if any
        await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)
sessions: Dict[str, Dict] = {}

class StreamState:
    def __init__(self):
        self.history = [] # List of event strings (data: ...)
        self.listeners = [] # List of asyncio.Queue
        self.task = None
        self.done_event = asyncio.Event()
        self.status = "idle" # idle, generating, done, error

    async def broadcast(self, event_str):
        self.history.append(event_str)
        for q in self.listeners:
            await q.put(event_str)
            
    def add_listener(self):
        q = asyncio.Queue()
        # Replay history
        for h in self.history:
            q.put_nowait(h)
        self.listeners.append(q)
        return q

    def remove_listener(self, q):
        if q in self.listeners:
            self.listeners.remove(q)

async def background_generator(sid, agent, history_msgs, config, stream_state, sessions_dict):
    stream_state.status = "generating"
    
    # Update global session status
    if sid in sessions_dict:
        sessions_dict[sid]['status'] = 'generating'
        sessions_dict[sid]['last_active'] = time.time()
        sessions_dict[sid]['abort_signal'] = False
        
    try:
        # Deduplicate messages against checkpoint to avoid loops/duplication
        input_messages = history_msgs
        try:
            snapshot = await agent.aget_state(config)
            if snapshot and snapshot.values and 'messages' in snapshot.values:
                existing_msgs = snapshot.values['messages']
                if len(existing_msgs) > 0:
                    # Checkpoint exists. 
                    # We assume the checkpoint contains the conversation prefix.
                    # We need to find which messages in history_msgs are NEW.
                    
                    # Heuristic: If we have N messages in DB, and M in Checkpoint.
                    # If M > 0, we assume the first M (or M-1 if system prompt involved) are sync'd.
                    # But the safest bet for this specific app flow (User sends 1 message -> Generate):
                    # The DB has [Old..., NewUserMsg]. Checkpoint has [Old...].
                    # So we just pass the last message.
                    
                    # However, to be safer against restarts where DB > Checkpoint:
                    # We pass the full history? No, that causes duplication if Checkpoint is valid.
                    
                    # Let's count how many User/Assistant messages are in Checkpoint.
                    # This is tricky because of ToolMessages.
                    
                    # Simple Strategy:
                    # If Checkpoint has messages, we ONLY pass the last message from history_msgs,
                    # assuming it is the new trigger.
                    if len(history_msgs) > 0:
                        input_messages = [history_msgs[-1]]
                        print(f"Session {sid}: Using incremental update (1 message) against existing checkpoint.")
            else:
                print(f"Session {sid}: No checkpoint found. Replaying full history ({len(history_msgs)} messages).")
        except Exception as e:
            print(f"Error checking snapshot: {e}. Defaulting to full history.")

        async for event in agent.astream_events(
            {"messages": input_messages},
            config=config,
            version="v1"
        ):
            # Check abort signal
            if sid in sessions_dict and sessions_dict[sid].get('abort_signal'):
                await stream_state.broadcast(f"data: {json.dumps({'type': 'error', 'content': 'Aborted by user'})}\n\n")
                break
                
            kind = event["event"]
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    await stream_state.broadcast(f"data: {json.dumps({'type': 'chunk', 'content': content})}\n\n")
            elif kind == "on_tool_start":
                await stream_state.broadcast(f"data: {json.dumps({
                    'type': 'tool', 
                    'id': event['run_id'], 
                    'name': event['name'],
                    'status': 'running',
                    'input': str(event['data'].get('input'))
                })}\n\n")
            elif kind == "on_tool_end":
                await stream_state.broadcast(f"data: {json.dumps({
                    'type': 'tool', 
                    'id': event['run_id'], 
                    'name': event['name'],
                    'status': 'done',
                    'output': str(event['data'].get('output'))
                })}\n\n")

        # Save state logic
        try:
             from langchain_core.messages import HumanMessage, ToolMessage
             snapshot = await agent.aget_state(config)
             if snapshot and snapshot.values and 'messages' in snapshot.values:
                 new_msgs = snapshot.values['messages'][len(history_msgs):]
                 for m in new_msgs:
                     role = 'user' if isinstance(m, HumanMessage) else 'assistant'
                     if isinstance(m, ToolMessage): role = 'tool'
                     
                     content = m.content
                     tool_calls = m.tool_calls if hasattr(m, 'tool_calls') else None
                     tool_call_id = m.tool_call_id if hasattr(m, 'tool_call_id') else None
                     
                     db_module.add_message_db(sid, role, content, tool_calls=tool_calls, tool_call_id=tool_call_id)
        except Exception as e:
             print(f"Error saving state: {e}")

        await stream_state.broadcast(f"data: {json.dumps({'type': 'done'})}\n\n")
        
    except Exception as e:
        print(f"Generation error: {e}")
        await stream_state.broadcast(f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n")
        
    finally:
        stream_state.status = "done"
        stream_state.done_event.set()
        if sid in sessions_dict:
            sessions_dict[sid]['status'] = 'idle'
            sessions_dict[sid]['last_active'] = time.time()

# Default config (load from env or use defaults)
siliconflow_config = {
    "api_key": os.getenv("SILICONFLOW_API_KEY", ""),
    "base_url": os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1"),
    "model": os.getenv("SILICONFLOW_MODEL", "Qwen/Qwen3-30B-A3B-Thinking-2507")
}

# Config persistence
DATA_DIR = Path(__file__).parent.parent.parent / "assemble_agents"
DATA_DIR.mkdir(exist_ok=True, parents=True)
PROMPTS_FILE = DATA_DIR / "prompts.json"

KB_FILE = DATA_DIR / "kb_sources.json"
AGENTS_FILE = DATA_DIR / "subagents.json"
QUICK_STARTERS_FILE = DATA_DIR / "quick_starters.json"
FEEDBACK_FILE = DATA_DIR / "chat_feedback.json"

def load_json_file(path, default=[]):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except Exception as e:
            print(f"Error loading {path}: {e}")
    return default

def save_json_file(path, data):
    try:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    except Exception as e:
        print(f"Error saving {path}: {e}")

def load_prompts():
    data = load_json_file(PROMPTS_FILE)
    if data:
        # Support list-based content
        for p in data:
            if isinstance(p.get('content'), list):
                p['content'] = '\n'.join(p['content'])
        return data
    # Default prompts
    return [
        { 'id': '1', 'name': 'General Assistant', 'desc': 'Base conversational agent.', 'content': 'You are a helpful assistant.', 'version': '1.0', 'updated': 'Now' },
        { 'id': '2', 'name': 'Code Generator', 'desc': 'Optimized for coding.', 'content': 'You are a software engineer. Write clean, efficient code.', 'version': '1.0', 'updated': 'Now' }
    ]

def save_prompts(prompts):
    save_json_file(PROMPTS_FILE, prompts)


def _new_id() -> str:
    return str(int(time.time() * 1000))

# --- KB Endpoints ---
@app.get('/kb/sources')
def get_kb_sources():
    return load_json_file(KB_FILE)

@app.post('/kb/sources')
async def save_kb_source(req: Request):
    body = await req.json()
    sources = load_json_file(KB_FILE)
    if not body.get('id'):
        body['id'] = _new_id()
    sources.append(body)
    save_json_file(KB_FILE, sources)
    return body

@app.delete('/kb/sources/{sid}')
def delete_kb_source(sid: str):
    sources = load_json_file(KB_FILE)
    target = next((s for s in sources if str(s.get('id')) == sid), None)
    if target:
        # Remove from RAG
        rag = get_rag_service(siliconflow_config.get('api_key'))
        
        # 1. Try deleting by ID (new standard)
        rag.delete_file(sid)
        
        # 2. Try deleting by filename (legacy fallback)
        if target.get('path'):
            source_key = os.path.basename(target['path'])
            rag.delete_file(source_key)
        
        # Remove from JSON
        sources = [s for s in sources if str(s.get('id')) != sid]
        save_json_file(KB_FILE, sources)
    return {'ok': True}

@app.put('/kb/sources/{sid}')
async def rename_kb_source(sid: str, req: Request):
    body = await req.json()
    new_name = body.get('name')
    if not new_name:
        return {'error': 'Name is required'}
    
    sources = load_json_file(KB_FILE)
    target = next((s for s in sources if str(s.get('id')) == sid), None)
    if target:
        target['name'] = new_name
        save_json_file(KB_FILE, sources)
    return {'ok': True}

@app.get('/kb/sources/{sid}/chunks')
def get_source_chunks(sid: str):
    sources = load_json_file(KB_FILE)
    target = next((s for s in sources if str(s.get('id')) == sid), None)
    if not target:
        raise HTTPException(status_code=404, detail="Source not found")
    
    rag = get_rag_service(siliconflow_config.get('api_key'))
    
    # 1. Try ID (new standard)
    chunks = rag.get_chunks(sid)
    if chunks:
        return chunks
        
    # 2. Fallback to basename (legacy)
    if target.get('path'):
        source_key = os.path.basename(target['path'])
        return rag.get_chunks(source_key)
    return []

class UpdateChunkRequest(BaseModel):
    text: str

@app.put('/kb/chunks/{cid}')
def update_chunk_endpoint(cid: str, req: UpdateChunkRequest):
    rag = get_rag_service(siliconflow_config.get('api_key'))
    success = rag.update_chunk(cid, req.text)
    return {"success": success}

@app.get('/kb/sources/{sid}/file')
def get_source_file(sid: str):
    sources = load_json_file(KB_FILE)
    target = next((s for s in sources if str(s.get('id')) == sid), None)
    if not target or not target.get('path'):
        raise HTTPException(status_code=404, detail="Source file not found")
    
    file_path = target['path']
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File on disk not found")
        
    return FileResponse(file_path)

@app.get('/kb/sources/{sid}/preview')
def preview_kb_source(sid: str):
    sources = load_json_file(KB_FILE)
    target = next((s for s in sources if str(s.get('id')) == sid), None)
    if not target:
        return JSONResponse(status_code=404, content={"error": "Source not found"})
    
    rag = get_rag_service(siliconflow_config.get('api_key'))
    
    chunks = []
    # 1. Try ID
    chunks = rag.get_chunks(sid)
    
    # 2. Fallback
    if not chunks and target.get('path'):
        source_key = os.path.basename(target['path'])
        chunks = rag.get_chunks(source_key)
    
    # Also try to read full content if it's a file
    full_content = ""
    try:
        if target.get('path') and os.path.exists(target['path']):
            path_str = target['path']
            if path_str.lower().endswith('.pdf'):
                full_content = f"[PDF File: {path_str}]\n[Showing {len(chunks)} extracted chunks below]"
            else:
                with open(path_str, 'r', encoding='utf-8', errors='ignore') as f:
                    full_content = f.read(10000) # Limit to 10k chars
    except Exception as e:
        full_content = f"Content not accessible: {e}"

    return {
        "name": target['name'],
        "chunks": chunks,
        "content": full_content
    }

class SearchQuery(BaseModel):
    query: str

@app.post('/kb/query')
def query_knowledge_base(q: SearchQuery):
    # Use RAG Service for high quality vector search
    rag = get_rag_service(siliconflow_config.get('api_key'))
    results = rag.search(q.query)
    # Map to expected format
    return {"records": results}

@app.post('/kb/upload')
async def upload_kb_file(file: UploadFile = File(...), template: str = Form("default")):
    try:
        # Save file temporarily
        temp_dir = DATA_DIR / "uploads"
        temp_dir.mkdir(exist_ok=True)
        file_path = temp_dir / file.filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Generate ID first to use as stable source key
        new_id = _new_id()
            
        # Ingest
        rag = get_rag_service(siliconflow_config.get('api_key'))
        # Pass ID as source_id
        result = rag.ingest_file(str(file_path), file.filename, template=template, source_id=new_id)
        
        if result.get('error'):
             return JSONResponse(status_code=500, content=result)

        # Add to sources list
        sources = load_json_file(KB_FILE)
        new_source = {
            "id": new_id,
            "name": file.filename,
            "type": "file",
            "path": str(file_path),
            "status": "indexed",
            "docCount": result.get('chunks', 0)
        }
        sources.append(new_source)
        save_json_file(KB_FILE, sources)
        
        return new_source
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

# --- Agents Endpoints ---
@app.get('/agents/subagents')
def get_subagents():
    return load_json_file(AGENTS_FILE)

@app.post('/agents/subagents')
async def save_subagent(req: Request):
    body = await req.json()
    agents = load_json_file(AGENTS_FILE)
    agents.append(body)
    save_json_file(AGENTS_FILE, agents)
    return body

# --- Feedback & Dataset Endpoints ---
@app.post('/feedback')
async def save_feedback(req: Request):
    body = await req.json()
    # body: { messageId, query, response, rating: 'good'|'bad', timestamp }
    feedbacks = load_json_file(FEEDBACK_FILE)
    
    if not body.get('id'):
        body['id'] = _new_id()
    if not body.get('timestamp'):
        body['timestamp'] = int(time.time() * 1000)
        
    # Convert to RLHF/SFT format
    # Structure optimized for Agent Fine-tuning (Alpaca-style with feedback)
    entry = {
        "id": body.get('id'),
        "instruction": body.get('query', ''),
        "input": "", # Reserved for system prompt or context if needed
        "output": body.get('response', ''),
        "label": body.get('rating', 'good'),
        "score": 1.0 if body.get('rating') == 'good' else 0.0,
        "timestamp": body.get('timestamp')
    }
        
    feedbacks.append(entry)
    save_json_file(FEEDBACK_FILE, feedbacks)
    return {'ok': True}

@app.get('/feedback/export')
def export_dataset():
    feedbacks = load_json_file(FEEDBACK_FILE)
    # Convert to a standard dataset format if needed, or just dump
    return feedbacks

@app.delete('/agents/subagents')
def clear_subagents():
    save_json_file(AGENTS_FILE, [])
    return {'ok': True}

@app.get('/prompts')
def get_prompts():
    return load_prompts()

@app.post('/prompts')
async def update_prompts(req: Request):
    body = await req.json()
    save_prompts(body)
    return body

@app.delete('/prompts/{pid}')
def delete_prompt(pid: str):
    prompts = load_prompts()
    prompts = [p for p in prompts if str(p.get('id')) != pid]
    save_prompts(prompts)
    return {'ok': True}

@app.get('/prompts/quick-starters')
def get_quick_starters():
    defaults = [
        {"text": "Python 贪吃蛇", "detail": "编写一个完整的贪吃蛇游戏代码", "prompt": "帮我写一个 Python 贪吃蛇游戏", "icon": "🐍"},
        {"text": "代码分析", "detail": "阅读并解释当前项目架构", "prompt": "分析当前目录下的代码结构", "icon": "📂"},
        {"text": "联网搜索", "detail": "查询最新的技术动态", "prompt": "搜索最新的 AI Agent 发展趋势", "icon": "🔍"},
        {"text": "学习计划", "detail": "生成详细的学习路线图", "prompt": "制定一个学习 Rust 语言的计划", "icon": "📅"}
    ]
    return load_json_file(QUICK_STARTERS_FILE, defaults)

@app.post('/prompts/quick-starters')
async def update_quick_starters(req: Request):
    body = await req.json()
    save_json_file(QUICK_STARTERS_FILE, body)
    return body



@app.get('/config')
def get_config():
    return siliconflow_config

@app.post('/config')
async def update_config(req: Request):
    body = await req.json()
    updated = False
    if 'api_key' in body:
        siliconflow_config['api_key'] = body['api_key']
        updated = True
    if 'base_url' in body:
        siliconflow_config['base_url'] = body['base_url']
        updated = True
    if 'model' in body:
        siliconflow_config['model'] = body['model']
        updated = True
    
    if updated:
        # Config is now managed by env vars, so we only update memory
        print("Config updated in memory (not persisted to file)")
        
    return { 'ok': True }

def _get_config_hash(config_data):
    relevant = {
        'model': siliconflow_config.get('model'),
        'base_url': siliconflow_config.get('base_url'),
        'api_key': siliconflow_config.get('api_key'),
        'tools_enabled': config_data.get('tools_enabled', True),
        'system_prompt': config_data.get('system_prompt')
    }
    return hashlib.md5(json.dumps(relevant, sort_keys=True).encode()).hexdigest()

def _path_validator(path: Path) -> bool:
    """Validate that path is within allowed directories (project root)."""
    try:
        resolved = path.resolve()
        cwd = Path.cwd().resolve()
        
        # Determine Project Root
        # Walk up from cwd until we find .git or 'libs' (heuristic for this repo structure)
        project_root = cwd
        temp = cwd
        while temp.parent != temp:
            # Check for markers
            if (temp / ".git").exists() or (temp / "libs").exists():
                project_root = temp
                # Prefer .git if available
                if (temp / ".git").exists():
                    break
            temp = temp.parent
            
        # Allow paths within Project Root
        if sys.platform == "win32":
            r_str = str(resolved).lower()
            pr_str = str(project_root).lower()
            if r_str == pr_str or r_str.startswith(pr_str + os.sep):
                return True
        else:
            if resolved.is_relative_to(project_root):
                return True
                
        print(f"Path validation failed for: {resolved} (Project Root: {project_root})")
        return False
    except Exception as e:
        print(f"Path validation error: {e}")
        return False

def _init_agent(assistant_id: str, checkpointer, enable_tools: bool = True, custom_system_prompt: str = None):
    if not siliconflow_config['api_key']:
        raise ValueError("SiliconFlow API key not set")

    print(f"Initializing agent with model: {siliconflow_config.get('model')} base_url: {siliconflow_config.get('base_url')} tools: {enable_tools}")

    model = ChatOpenAI(
        model=siliconflow_config['model'],
        api_key=siliconflow_config['api_key'],
        base_url=siliconflow_config['base_url'],
        max_tokens=4096,
        streaming=True
    )
    # Enable summarization by setting profile with token limit
    # DeepSeek V3 typically supports 64k, but we set a lower trigger to keep things fast
    model.profile = {"max_input_tokens": 62000}

    # Setup agent directory
    # User requested override to assemble_agents directory
    # DATA_DIR is already set to d:/MASrepos/deepagents-langchain/libs/assemble_agents
    agent_dir = DATA_DIR / "sessions" / assistant_id
    agent_dir.mkdir(parents=True, exist_ok=True)
    
    agent_md = agent_dir / "agent.md"
    if not agent_md.exists():
        source_content = get_default_coding_instructions()
        agent_md.write_text(source_content, encoding='utf-8')

    # Force skills_dir to be local
    skills_dir = agent_dir / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    
    project_skills_dir = settings.get_project_skills_dir()

    composite_backend = CompositeBackend(
        default=FilesystemBackend(virtual_mode=False, path_validator=_path_validator),
        routes={},
    )

    # We need to hack the AgentMemoryMiddleware to use our local agent_dir
    # Since AgentMemoryMiddleware uses settings.ensure_agent_dir which uses ~/.deepagents
    # We will subclass or just monkeypatch if possible, but cleaner to instantiate with custom paths if supported.
    # Checking AgentMemoryMiddleware source... it takes settings and assistant_id.
    # It uses settings.ensure_agent_dir(assistant_id) internally.
    # To avoid changing library code, we can temporarily patch settings.ensure_agent_dir
    
    original_ensure_agent_dir = settings.ensure_agent_dir
    original_ensure_user_skills_dir = settings.ensure_user_skills_dir
    
    def mock_ensure_agent_dir(name):
        return agent_dir
        
    def mock_ensure_user_skills_dir(name):
        return skills_dir
        
    settings.ensure_agent_dir = mock_ensure_agent_dir
    settings.ensure_user_skills_dir = mock_ensure_user_skills_dir

    try:
        agent_middleware = [
            AgentMemoryMiddleware(settings=settings, assistant_id=assistant_id),
        ]
        
        if enable_tools:
            workspace_dir = Path.cwd() / "workspace"
            workspace_dir.mkdir(exist_ok=True)
            
            agent_middleware.extend([
                SkillsMiddleware(
                    skills_dir=skills_dir,
                    assistant_id=assistant_id,
                    project_skills_dir=project_skills_dir,
                ),
                ShellMiddleware(
                    workspace_root=str(workspace_dir),
                    env=os.environ,
                ),
            ])
    finally:
        # Restore settings to avoid side effects if settings is a global singleton
        settings.ensure_agent_dir = original_ensure_agent_dir
        settings.ensure_user_skills_dir = original_ensure_user_skills_dir

    if custom_system_prompt:
        system_prompt = custom_system_prompt
    else:
        system_prompt = get_system_prompt(assistant_id=assistant_id)
    
    # Intent recognition and fast path prompt injection
    if enable_tools:
        intent_prompt = """
        CRITICAL INSTRUCTION: INTENT RECOGNITION AND FAST PATH
        Before executing any plan or using tools, assess the user's intent.
        
        1. SIMPLE CHAT / KNOWLEDGE QUERY:
           If the user is asking for general knowledge, chatting, or asking a question that does NOT require:
           - File system access
           - Web search (unless you are unsure)
           - Sub-agent delegation
           - Complex planning
           
           THEN: Do NOT use the 'write_todos' tool. Do NOT use any other tools.
           Respond DIRECTLY to the user in the conversation. This ensures a fast response.
           
        2. COMPLEX TASK / TOOL USE:
           Only if the user's request clearly requires actions (creating files, reading files, researching specific recent info), 
           then proceed with the standard planning and tool use flow (write_todos, etc.).
           
        Override default behavior: You do NOT need to write a todo list for simple conversation or questions.
        """
        system_prompt = system_prompt + "\n\n" + intent_prompt
    else:
        system_prompt = system_prompt + "\n\nCRITICAL: You are in FAST CHAT mode. DO NOT use any tools. DO NOT write todos. Just answer the user directly."

    # Load Subagents from JSON
    subagents_list = []
    try:
        if AGENTS_FILE.exists():
            saved_agents = load_json_file(AGENTS_FILE)
            for sa in saved_agents:
                # Construct SubAgent dict
                subagents_list.append({
                    "name": sa.get('name'),
                    "description": sa.get('desc') or sa.get('description') or "A specialized sub-agent",
                    "system_prompt": sa.get('content') or sa.get('system_prompt') or "You are a helpful sub-agent.",
                    "tools": [] # Subagents can have tools too
                })
            if subagents_list:
                print(f"Loaded {len(subagents_list)} sub-agents: {[s['name'] for s in subagents_list]}")
    except Exception as e:
        print(f"Error loading subagents: {e}")

    # Configure tools
    agent_tools = []
    if enable_tools:
        # Add RAG tool
        agent_tools.append(search_knowledge_base)

    agent = create_deep_agent(
        model=model,
        system_prompt=system_prompt,
        tools=agent_tools, 
        backend=composite_backend,
        middleware=agent_middleware,
        subagents=subagents_list,
        interrupt_on=None,
        checkpointer=checkpointer
    ).with_config(config)

    return agent

@app.get('/sessions')
def list_sessions():
    return db_module.list_sessions_db()

@app.post('/sessions')
async def create_session(req: Request):
    try:
        body = await req.json()
    except:
        body = {}
    
    # Requirement: Backend must verify valid user input content for session creation
    if not body.get('message'):
        raise HTTPException(status_code=400, detail="Initial message required to create session")

    sid = db_module.create_session_db(body)
    
    # Initialize runtime state
    sessions[sid] = {
        'id': sid,
        'agent_cache': None,
        'config': body
    }
    # Checkpointer is now global/persistent
    return {'id': sid}

@app.put('/sessions/{sid}')
async def rename_session(sid: str, req: Request):
    body = await req.json()
    name = body.get('name')
    if not name:
        return {'error': 'Name is required'}
    db_module.update_session_db(sid, name=name)
    return {'ok': True}

@app.delete('/sessions/batch')
async def delete_sessions_batch(req: Request):
    try:
        body = await req.json()
        ids = body.get('ids', [])
        if not ids:
            return {'ok': True, 'count': 0}
            
        # 1. Abort any running sessions in the list
        for sid in ids:
            if sid in sessions:
                sessions[sid]['abort_signal'] = True
        
        # 2. Delete from DB
        try:
            db_module.delete_sessions_batch_db(ids)
        except Exception as e:
            print(f"Error deleting batch sessions: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
        # 3. Cleanup memory and disk
        for sid in ids:
            if sid in sessions:
                del sessions[sid]
            # checkpointers cleanup removed as it's global now
                
            agent_dir = DATA_DIR / "sessions" / sid
            if agent_dir.exists():
                try:
                    shutil.rmtree(agent_dir)
                except Exception as e:
                    print(f"Error deleting agent dir {agent_dir}: {e}")
                    
        return {'ok': True, 'count': len(ids)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete('/sessions/{sid}')
async def delete_session(sid: str):
    # 1. Abort if running
    if sid in sessions:
        sessions[sid]['abort_signal'] = True
        # If there's a stream state, we could try to wait, but for now just signal

    # 2. Delete from DB
    try:
        db_module.delete_session_db(sid)
    except Exception as e:
        print(f"Error deleting session {sid} from DB: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # 3. Cleanup memory
    if sid in sessions:
        del sessions[sid]
    if sid in checkpointers:
        del checkpointers[sid]

    # 4. Cleanup disk (Agent Directory)
    agent_dir = DATA_DIR / "sessions" / sid
    if agent_dir.exists():
        try:
            shutil.rmtree(agent_dir)
        except Exception as e:
            print(f"Error deleting agent dir {agent_dir}: {e}")

    return {'ok': True}

class MessageRequest(BaseModel):
    content: str
    tools: bool = True

@app.post('/sessions/{sid}/messages')
async def post_message(sid: str, req: MessageRequest):
    # Verify session exists
    session_data = db_module.get_session_db(sid)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update runtime state
    if sid not in sessions:
        sessions[sid] = {'id': sid, 'agent_cache': None, 'config': session_data.get('config', {})}
    
    sessions[sid]['pending_input'] = req.content
    sessions[sid]['enable_tools'] = req.tools
    
    # Save user message to DB
    db_module.add_message_db(sid, 'user', req.content)
    
    # Auto-rename if first message (or name is default)
    current_name = session_data.get('name')
    if current_name == 'New Session' or current_name == f"Session {sid}":
        # Use first 30 chars of content
        new_name = req.content[:30]
        if len(req.content) > 30:
            new_name += "..."
        db_module.update_session_db(sid, name=new_name)
        
    return {'ok': True}

@app.get('/sessions/{sid}/status')
def get_session_status(sid: str):
    if sid in sessions:
        sess = sessions[sid]
        return {
            "status": sess.get('status', 'idle'),
            "last_active": sess.get('last_active', 0)
        }
    return {"status": "idle", "last_active": 0}

@app.post('/sessions/{sid}/abort')
def abort_session(sid: str):
    if sid in sessions:
        sessions[sid]['abort_signal'] = True
        return {"ok": True}
    return JSONResponse(status_code=404, content={"error": "Session not active"})

@app.get('/sessions/{sid}/stream')
async def stream_session(sid: str):
    # Ensure session loaded
    session_db = db_module.get_session_db(sid)
    if not session_db:
         raise HTTPException(status_code=404, detail="Session not found")
         
    if sid not in sessions:
        sessions[sid] = {'id': sid, 'agent_cache': None, 'config': session_db.get('config', {})}
        
    session = sessions[sid]
    
    # Initialize StreamState if not present
    if 'stream_state' not in session:
        session['stream_state'] = StreamState()
        
    stream_state = session['stream_state']
    
    # Check if we need to start a new generation
    pending_input = session.get('pending_input')
    
    if pending_input and stream_state.status != 'generating':
        # Prepare to start background task
        
        # Reset stream state for new run
        session['stream_state'] = StreamState()
        stream_state = session['stream_state']
        
        enable_tools = session.get('enable_tools', True)
        session['pending_input'] = None # Consume input
        
        # Setup checkpointer
        cp = global_checkpointer
        
        # Load history
        db_messages = session_db.get('messages', [])
        history_msgs = []
        from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
        for m in db_messages:
            role = m['role']
            content = m['content']
            if role == 'user':
                history_msgs.append(HumanMessage(content=content))
            elif role == 'assistant':
                msg = AIMessage(content=content)
                if m.get('tool_calls'): msg.tool_calls = m['tool_calls']
                history_msgs.append(msg)
            elif role == 'tool':
                history_msgs.append(ToolMessage(content=content, tool_call_id=m.get('tool_call_id')))
                
        # Init Agent
        agent = _init_agent(
            assistant_id=sid,
            checkpointer=cp,
            enable_tools=enable_tools,
            custom_system_prompt=session['config'].get('system_prompt')
        )
        
        config = {"configurable": {"thread_id": sid}, "recursion_limit": 150}
        
        # Start Background Task
        stream_state.task = asyncio.create_task(
            background_generator(sid, agent, history_msgs, config, stream_state, sessions)
        )
    elif not pending_input and stream_state.status != 'generating' and not stream_state.history:
         async def empty_gen():
             yield f"data: {json.dumps({'type': 'ping'})}\n\n"
             yield f"data: {json.dumps({'type': 'done'})}\n\n"
         return StreamingResponse(empty_gen(), media_type="text/event-stream")

    # Subscribe to the stream (whether new or existing)
    queue = stream_state.add_listener()
    
    async def event_generator():
        try:
            while True:
                # Wait for event
                event = await queue.get()
                yield event
                
                # Check if done
                try:
                    if event.startswith("data: "):
                        data_str = event[6:].strip()
                        if data_str:
                            data = json.loads(data_str)
                            if data.get('type') in ('done', 'error'):
                                break
                except:
                    pass
        except asyncio.CancelledError:
            pass
        finally:
            stream_state.remove_listener(queue)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get('/sessions/{sid}/context')
async def get_session_context(sid: str):
    session = db_module.get_session_db(sid)
    if not session:
         return JSONResponse({'error': 'Session not found'}, status_code=404)
    
    return {
        'history': session.get('messages', []),
        'logs_count': len(session.get('logs', []))
    }

@app.get('/sessions/{sid}/export')
def export_session(sid: str):
    session = db_module.get_session_db(sid)
    if not session:
         raise HTTPException(404, "Session not found")
    messages = session.get('messages', [])
    export_data = {
        "messages": [
            {"role": "system", "content": session.get('config', {}).get('system_prompt', '') or "You are a helpful assistant."}
        ]
    }
    for m in messages:
        msg_obj = {"role": m['role'], "content": m['content']}
        if m.get('tool_calls'): msg_obj['tool_calls'] = m['tool_calls']
        if m.get('tool_call_id'): msg_obj['tool_call_id'] = m['tool_call_id']
        export_data['messages'].append(msg_obj)
    return export_data

@app.post('/sessions/migrate')
def migrate_sessions():
    sessions_dir = DATA_DIR / "sessions"
    count = 0
    if not sessions_dir.exists():
        return {"migrated": 0, "msg": "No sessions directory found"}
        
    for f in sessions_dir.glob("*.json"):
        try:
            # Skip already migrated files if renamed (though we rename to .json.migrated which won't match *.json)
            data = json.loads(f.read_text(encoding='utf-8'))
            sid = data.get('id', f.stem)
            
            # Check if exists
            if db_module.get_session_db(sid):
                continue
                
            # Create session
            config = data.get('config', {})
            name = data.get('name', f"Session {sid}")
            # Ensure created_at matches original if possible? 
            # db module uses current time. We could modify db module to accept created_at but let's keep it simple.
            
            db_module.create_session_db(config, sid=sid, name=name)
            
            # Add messages
            for msg in data.get('messages', []):
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                tool_calls = msg.get('tool_calls')
                tool_call_id = msg.get('tool_call_id')
                
                # If tool_calls is string (old format?), parse it? 
                # Assuming standard format
                
                db_module.add_message_db(sid, role, content, tool_calls=tool_calls, tool_call_id=tool_call_id)
                
            # Add logs
            for log in data.get('logs', []):
                content = log.get('content', '') if isinstance(log, dict) else str(log)
                db_module.add_log_db(sid, content)
                
            count += 1
            # Rename file to mark as migrated
            try:
                f.rename(f.with_suffix('.json.migrated'))
            except:
                pass # Might fail on windows if open
            
        except Exception as e:
            print(f"Failed to migrate {f}: {e}")
            
    return {"migrated": count}

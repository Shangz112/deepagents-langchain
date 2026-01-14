import os
import sys
import time
import json
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

# Filter out noisy Pydantic warnings about NotRequired
warnings.filterwarnings("ignore", message=".*typing.NotRequired.*", category=UserWarning)

# Filter out noisy polling logs
class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("GET /sessions/") == -1 or \
               (record.getMessage().find("/config") == -1 and record.getMessage().find("/context") == -1)

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic if needed
    yield
    # Shutdown logic if needed
    # Explicitly handle potential cancellation during shutdown to avoid noisy logs
    try:
        # Give a moment for pending tasks to complete if any
        await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)
sessions: Dict[str, Dict] = {}
checkpointers: Dict[str, Any] = {}

# Default config (empty API key for security)
siliconflow_config = {
    "api_key": "sk-zyhbakslfsnztzpbyrmopbzvzuajofmmsedpmfrgnfpqsrfn",
    "base_url": "https://api.siliconflow.cn/v1",
    "model": "deepseek-ai/DeepSeek-V3.2"
}

# Config persistence
DATA_DIR = Path(__file__).parent.parent / "deepagents_data"
DATA_DIR.mkdir(exist_ok=True)
CONFIG_FILE = DATA_DIR / "siliconflow.json"
PROMPTS_FILE = DATA_DIR / "prompts.json"

def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
        except Exception as e:
            print(f"Error loading config: {e}")
    return siliconflow_config

def save_config(cfg):
    try:
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding='utf-8')
    except Exception as e:
        print(f"Error saving config: {e}")


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

siliconflow_config = load_config()

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
        # Use basename of path as source key, as that's what ingest uses
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
    # Use basename
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
    if target.get('path'):
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
            
        # Ingest
        rag = get_rag_service(siliconflow_config.get('api_key'))
        result = rag.ingest_file(str(file_path), file.filename, template=template)
        
        if result.get('error'):
             return JSONResponse(status_code=500, content=result)

        # Add to sources list
        sources = load_json_file(KB_FILE)
        new_source = {
            "id": _new_id(),
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
        save_config(siliconflow_config)
        
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
    # Force agent_dir to be local to the current working directory to avoid Windows absolute path issues
    # in virtual_mode=True
    agent_dir = Path.cwd() / "deepagents_data" / assistant_id
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
        default=FilesystemBackend(virtual_mode=False),
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

@app.post('/sessions')
async def create_session(req: Request):
    sid = _new_id()
    # Initialize session with logs and config
    sessions[sid] = {
        'id': sid, 
        'messages': [],
        'logs': [],  # Store tool logs here
        'agent_cache': None, # Cache for compiled agent
        'config': {
            'model': siliconflow_config.get('model'),
            'temperature': 0.7,
            'middleware_enabled': True
        }
    }
    # Initialize checkpointer
    checkpointers[sid] = InMemorySaver()
    return {'id': sid}

class MessageRequest(BaseModel):
    content: str
    tools: bool = True

@app.post('/sessions/{sid}/messages')
async def post_message(sid: str, req: MessageRequest):
    if sid not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    sessions[sid]['pending_input'] = req.content
    sessions[sid]['enable_tools'] = req.tools
    sessions[sid]['messages'].append({'role': 'user', 'content': req.content})
    return {'ok': True}

@app.get('/sessions/{sid}/stream')
async def stream_session(sid: str):
    if sid not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[sid]
    pending_input = session.get('pending_input')
    enable_tools = session.get('enable_tools', True)
    
    # If no pending input, maybe it's a reconnection?
    # For now, we only support streaming response to a new message.
    if not pending_input:
         # Send a keep-alive or ping to keep connection open if frontend expects it
         # But usually frontend connects ONLY after sending a message.
         # If we return immediately, frontend might think it's done.
         # We'll just return a ping and done.
         async def empty_gen():
             yield f"data: {json.dumps({'type': 'ping'})}\n\n"
             yield f"data: {json.dumps({'type': 'done'})}\n\n"
         return StreamingResponse(empty_gen(), media_type="text/event-stream")

    session['pending_input'] = None
    
    cp = checkpointers.get(sid)
    if not cp:
        cp = InMemorySaver()
        checkpointers[sid] = cp
        
    agent = _init_agent(
        assistant_id=sid,
        checkpointer=cp,
        enable_tools=enable_tools,
        custom_system_prompt=session['config'].get('system_prompt')
    )
    
    async def event_generator():
        try:
            config = {"configurable": {"thread_id": sid}}
            
            async for event in agent.astream_events(
                {"messages": [HumanMessage(content=pending_input)]},
                config=config,
                version="v1"
            ):
                kind = event["event"]
                
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        yield f"data: {json.dumps({'type': 'chunk', 'content': content})}\n\n"
                        
                        # Append to assistant message in session for context endpoint
                        # Note: This is a bit hacky, proper way is to read from checkpointer/history after run
                        # But for real-time UI update we might not need to update session['messages'] incrementally
                        # We'll update it at the end or let the graph handle it.
                
                elif kind == "on_tool_start":
                    yield f"data: {json.dumps({
                        'type': 'tool', 
                        'id': event['run_id'], 
                        'name': event['name'],
                        'status': 'running',
                        'input': str(event['data'].get('input'))
                    })}\n\n"
                    
                elif kind == "on_tool_end":
                     yield f"data: {json.dumps({
                        'type': 'tool', 
                        'id': event['run_id'], 
                        'name': event['name'],
                        'status': 'done',
                        'output': str(event['data'].get('output'))
                    })}\n\n"
                    
            # Done
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
            # Update session history from checkpointer state
            snapshot = agent.get_state(config)
            if snapshot and snapshot.values and 'messages' in snapshot.values:
                # Sync our simple session['messages'] with graph state
                # This ensures /context endpoint returns full history
                msgs = snapshot.values['messages']
                formatted = []
                for m in msgs:
                    role = 'user'
                    if m.type == 'ai': role = 'assistant'
                    elif m.type == 'system': role = 'system'
                    elif m.type == 'tool': role = 'tool'
                    formatted.append({'role': role, 'content': str(m.content)})
                session['messages'] = formatted

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get('/sessions/{sid}/context')
async def get_session_context(sid: str):
    s = sessions.get(sid)
    if not s:
        return JSONResponse({'error': 'Session not found'}, status_code=404)
    
    # Extract chat history formatted for frontend
    history = []
    for m in s.get('messages', []):
        history.append({
            'role': m['role'],
            'content': m['content'][:100] + '...' if len(m['content']) > 100 else m['content']
        })
        
    return {
        'history': history,
        'logs_count': len(s.get('logs', []))
    }

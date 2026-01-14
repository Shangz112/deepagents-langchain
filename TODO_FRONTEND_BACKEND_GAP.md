# Frontend-Backend Integration Gaps

This document tracks UI components in the Web Frontend that are not yet connected to backend logic or rely on stub implementations.

## 1. Knowledge Base (RAG) - [RESOLVED]
- **UI Route**: `/kb` (KnowledgeBase.vue)
- **Endpoint**: `/api/v1/kb/sources`, `/api/v1/kb/query`, `/api/v1/kb/upload`
- **Current Status**: 
  - ✅ Frontend connected to Node.js BFF.
  - ✅ Node.js proxies to Python backend (`app.py` + `rag_tool.py`).
  - ✅ Python backend persists sources to `kb_sources.json`.
  - ✅ **File Upload**: Supported (local storage + vector ingestion).
  - ✅ **Vector Search**: Implemented via `rag_service.py` (Hybrid: Milvus Lite with ChromaDB fallback).
  - ✅ **Parsing**: Supports PDF (MinerU integrated with PyMuPDF fallback) and text files.
  - ✅ **Encoding**: Fixed Chinese filename encoding issues in Node.js BFF (`kb.ts`).
  - ✅ **UI Enhancements**: Added hover actions (Rename/Delete) and document preview modal.
  - ✅ **RAG Visualization**: RAG sources displayed in chat with "Thinking Process" tracking.
  - ✅ **Dataset Export**: Added dialogue quality feedback and dataset export functionality.
  - ✅ **Modular Architecture**: RAG service refactored with adapters (Milvus/Chroma) and config-based parsing strategies.
  - ✅ **Template Chunking**: Added support for template-based document chunking (configurable in `rag_config.json`).
  - ✅ **Documentation**: Created [RAG_ARCHITECTURE.md](./RAG_ARCHITECTURE.md) detailing system design.
- **Remaining Work**:
  - Download MinerU models (e.g., `doclayout_yolo`, `unimernet`) for high-fidelity parsing (currently falls back gracefully).

## 2. Tools Management - [RESOLVED]
- **UI Route**: `/skills` (SkillsView.vue)
- **Endpoint**: `/api/v1/tools`
- **Current Status**:
  - ✅ `SkillsView.vue` fetches tools/skills list.
  - ✅ Node.js (`routes/tools.ts`) proxies `listSkills()` from Python.
  - ✅ Python lists available tools (File/Shell/Search etc.).

## 3. Sub-Agents / Plan Graph
- **UI Route**: `/plan` (PlanGraph.vue)
- **Endpoint**: `/api/v1/agents/subagents`, `/api/v1/agents/plan/graph`
- **Current Status**:
  - Frontend visualizes chat history as a graph, but does not reflect the internal LangGraph state.
  - Node.js (`routes/agents.ts`) proxies subagent CRUD to Python (`subagents.json`).
  - **GAP**: No visualization of live LangGraph state or sub-agent hierarchy from Python execution.

## 4. Prompt Studio - [RESOLVED]
- **UI Route**: `/prompts` (PromptStudio.vue)
- **Endpoint**: `/api/v1/prompts/templates`, `/api/v1/chat/prompts`
- **Current Status**:
  - ✅ `Composer.vue` fetches templates from `/api/v1/prompts/templates`.
  - ✅ `PromptStudio.vue` fetches prompts from `/api/v1/chat/prompts`.
  - ✅ Both Node endpoints proxy to the same Python backend (`app.py` -> `prompts.json`).
  - ✅ "Quick Starters" are also dynamic via `quick_starters.json`.
  - **Note**: Frontend and Backend prompts are now unified.

## 5. Session History Persistence
- **UI**: Chat History Sidebar
- **Current Status**:
  - Sessions are in-memory in Python (`sessions = {}`).
  - **GAP**: Lost on Python service restart. Needs database/file persistence.

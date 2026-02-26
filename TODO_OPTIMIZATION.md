# Optimization & Refactoring Plan

This document outlines identified areas for code deduplication, performance optimization, and stability improvements across the `deepagents-langchain` monorepo.

## 1. Functional Duplication & Refactoring

### 1.1 Unify Persistence Layer
**Current State:**
- `libs/deepagents-web/services/python/db.py`: Migrated to asynchronous `aiosqlite` (Completed).
- `libs/cli/deepagents_cli/sessions.py`: Uses asynchronous `aiosqlite` and LangGraph's `AsyncSqliteSaver`.
- **Status:** Both now share the same configuration `settings.deepagents_home` and write to the same SQLite file (`sessions.db`), effectively consolidating the physical schema.

**Action Items:**
- [x] **Migrate `db.py` to `aiosqlite`**: Convert all synchronous DB calls in the Web service to asynchronous calls.
- [x] **Consolidate Schema**: Merged session metadata tables and agent checkpoints into the same SQLite file by aligning configuration paths.
- [ ] **Shared Data Access Layer**: Create a shared `libs/common/persistence` module (or extend `libs/deepagents`) that handles both session metadata and agent state, usable by both CLI and Web.

### 1.2 Upstream "Monkeypatches"
**Current State:**
- `app.py` is now clean of monkeypatches.
- `filesystem.py` handles Windows paths natively.
- `ExtendedModelResponse` and `ContextOverflowError` confirmed present in recent `langchain` versions.

**Action Items:**
- [x] **Fix Windows Path Validation**: Modified `libs/deepagents/deepagents/middleware/filesystem.py` to natively support Windows paths.
- [x] **Standardize Dependencies**: Verified types are present; fixed `tomli-w` dependency.

### 1.3 Standardize Agent Initialization
**Current State:**
- `deepagents_cli.config.Settings` updated to support `DEEPAGENTS_HOME` and `deepagents_home` attribute.
- `app.py` uses `settings.deepagents_home` instead of mocks.
- Packages installed in editable mode.

**Action Items:**
- [x] **Configurable Paths**: Updated `deepagents_cli.config.Settings` and aligned `app.py`.
- [x] **Package Installation**: Installed `libs/cli` and `libs/deepagents` in editable mode.

## 2. Performance Bottlenecks

### 2.1 Blocking I/O in Async Endpoints
**Current State:**
- `app.py` defines `async def create_session(...)` and other endpoints which now call awaited async DB functions.
- **Impact:** Previously, synchronous DB operations blocked the Python event loop. This has been resolved by the migration to `aiosqlite`.

**Action Items:**
- [x] **Async DB Calls**: As part of 1.1, ensure all database operations in `app.py` are awaited.
- [x] **Thread Pool Offloading**: No longer needed as native async is implemented.

### 2.2 Server Configuration
**Current State:**
- Service runs with `uvicorn app:app --reload`.
- **Status:** Created `run_prod.py` for production execution.

**Action Items:**
- [x] **Production Entrypoint**: Created `libs/deepagents-web/services/python/run_prod.py` to run `uvicorn` without reload. Note: State stored in memory requires single worker or sticky sessions.

### 2.3 Large File Handling
**Current State:**
- `filesystem.py` now uses streaming read.
- **Status:** Implemented line-by-line reading in `FilesystemBackend.read`.

**Action Items:**
- [x] **Streaming Read**: Modified `read` method in `libs/deepagents/deepagents/backends/filesystem.py` to use iterator-based streaming, preventing OOM on large files. Added explicit empty file check.

## 3. Maintenance & Code Quality

### 3.1 Duplicate Code
**Current State:**
- `verify_app_startup.py` (deleted) and `verify_persistence.py` duplicate logic found in tests.
- `rag_tool.py` and `rag_service.py` in Web seem to implement RAG logic that might overlap with `libs/cli/deepagents_cli/tools.py` or `libs/assemble_agents`.

**Action Items:**
- [ ] **Consolidate Tools**: Review RAG implementations and move a canonical version to `libs/deepagents/tools`.

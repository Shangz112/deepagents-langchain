import os

# SiliconFlow Configuration
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
SILICONFLOW_BASE_URL = os.getenv("SILICONFLOW_BASE_URL") or os.getenv("OPENAI_API_BASE") or "https://api.siliconflow.cn/v1"

# Model Configuration
MODEL_NAME = os.getenv("MODEL_NAME") or "deepseek-ai/DeepSeek-V3.2"
EMBEDDING_MODEL_NAME = "Qwen/Qwen3-Embedding-8B"
RERANKER_MODEL_NAME = "Qwen/Qwen3-Reranker-8B"

# RAG Configuration
RAG_DB_PATH = os.getenv("MBSE_KNOWLEDGE_DB") or "data/vector_db"
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "data/sysml_templates")

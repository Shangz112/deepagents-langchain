from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.tools import tool
from deepagents_core.mbse_agent.config import SILICONFLOW_BASE_URL, SILICONFLOW_API_KEY, EMBEDDING_MODEL_NAME, RERANKER_MODEL_NAME, RAG_DB_PATH
import os
import requests
import json

@tool
def search_mbse_knowledge(query: str) -> str:
    """
    检索 MBSE 规范、SysML 语法手册或企业建模标准。
    
    Args:
        query: 检索关键词或问题
        
    Returns:
        str: 相关的文档片段
    """
    embeddings = OpenAIEmbeddings(
        base_url=SILICONFLOW_BASE_URL,
        api_key=SILICONFLOW_API_KEY,
        model=EMBEDDING_MODEL_NAME,
        check_embedding_ctx_length=False
    )
    
    if not os.path.exists(RAG_DB_PATH):
        return "Knowledge database not found at " + RAG_DB_PATH
    
    try:
        vector_db = Chroma(
            persist_directory=RAG_DB_PATH,
            embedding_function=embeddings
        )
        
        # 1. Initial Retrieval: Get more candidates for reranking
        candidate_k = 10
        docs = vector_db.similarity_search(query, k=candidate_k)
        
        if not docs:
            return "No relevant documents found."

        # 2. Rerank using SiliconFlow API
        try:
            # Construct Rerank API URL
            # Ensure base_url doesn't end with slash before appending
            base_url = SILICONFLOW_BASE_URL.rstrip('/')
            rerank_url = f"{base_url}/rerank"
            
            headers = {
                "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
                "Content-Type": "application/json"
            }
            
            documents = [d.page_content for d in docs]
            payload = {
                "model": RERANKER_MODEL_NAME,
                "query": query,
                "documents": documents,
                "top_n": 3
            }
            
            response = requests.post(rerank_url, headers=headers, json=payload)
            response.raise_for_status()
            
            rerank_results = response.json().get("results", [])
            
            # Sort documents based on reranker scores
            # results format: [{"index": 0, "relevance_score": 0.9}, ...]
            reranked_docs = []
            for res in rerank_results:
                idx = res["index"]
                if idx < len(docs):
                    reranked_docs.append(docs[idx].page_content)
            
            if reranked_docs:
                return "\n\n".join(reranked_docs)
            else:
                return "\n\n".join([d.page_content for d in docs[:3]])

        except Exception as rerank_error:
            # Fallback to basic retrieval if rerank fails
            # print(f"Rerank failed: {rerank_error}, falling back to top 3 similarity search")
            return "\n\n".join([d.page_content for d in docs[:3]])

    except Exception as e:
        return f"Knowledge retrieval failed: {str(e)}"

import json
from pathlib import Path
from langchain_core.tools import tool
from rag_service import get_rag_service

@tool
def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for relevant information.
    
    Use this tool when you need to find information in the user's provided documents
    or knowledge base to answer a question.
    """
    # Use RAG Service
    # We try to get API key from config if possible, or rely on env
    # deepagents_cli.config might not have the siliconflow key if it's dynamic in app.py
    # But get_rag_service is a singleton, so if app.py initialized it, we are good.
    # Fallback to empty if not init.
    rag = get_rag_service() 
    results = rag.search(query)
    
    if not results:
        return "No relevant information found in the knowledge base."
        
    formatted_results = []
    for r in results:
        formatted_results.append(f"Source: {r['source']}\nSnippet: {r['content']}")
        
    return "\n\n".join(formatted_results)


import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- Interfaces ---

class VectorStoreAdapter(ABC):
    """
    Abstract Base Class for Vector Store Adapters.
    Defines the standard interface for interacting with different vector databases (Milvus, Chroma, etc.).
    """
    
    @abstractmethod
    def ingest(self, chunks: List[str], metadatas: List[Dict]) -> bool:
        """
        Ingest text chunks and their metadata into the vector store.
        
        Args:
            chunks (List[str]): List of text strings to embed and store.
            metadatas (List[Dict]): List of metadata dictionaries corresponding to each chunk.
            
        Returns:
            bool: True if ingestion was successful, False otherwise.
        """
        pass

    @abstractmethod
    def search(self, query: str, limit: int) -> List[Dict]:
        """
        Search the vector store for similar texts.
        
        Args:
            query (str): The search query text.
            limit (int): Maximum number of results to return.
            
        Returns:
            List[Dict]: A list of search results, where each result contains 'content', 'source', and 'score'.
        """
        pass

    @abstractmethod
    def delete_source(self, source_name: str) -> bool:
        """
        Delete all vectors associated with a specific source file.
        
        Args:
            source_name (str): The name/identifier of the source to delete.
            
        Returns:
            bool: True if deletion was successful.
        """
        pass
        
    @abstractmethod
    def get_chunks(self, source_name: str) -> List[Dict]:
        """
        Retrieve all chunks for a specific source.
        
        Args:
            source_name (str): The name of the source.
            
        Returns:
            List[Dict]: List of chunks with 'content' and 'index'.
        """
        pass

# --- Implementations ---

class MilvusAdapter(VectorStoreAdapter):
    """
    Adapter implementation for Milvus (specifically Milvus Lite).
    """
    def __init__(self, client, collection_name, embedding_function):
        self.client = client
        self.collection_name = collection_name
        self.ef = embedding_function
        
        if not self.client.has_collection(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                dimension=384 # Default dimension for all-MiniLM-L6-v2, configurable via embedding function in production
            )

    def ingest(self, chunks: List[str], metadatas: List[Dict]) -> bool:
        vectors = self.ef(chunks)
        data = []
        for i in range(len(chunks)):
            data.append({
                "vector": vectors[i],
                "text": chunks[i],
                "source": metadatas[i].get("source"),
                "chunk_index": metadatas[i].get("chunk_index")
            })
        self.client.insert(collection_name=self.collection_name, data=data)
        return True

    def search(self, query: str, limit: int) -> List[Dict]:
        query_vector = self.ef([query])[0]
        results = self.client.search(
            collection_name=self.collection_name,
            data=[query_vector],
            limit=limit,
            output_fields=["text", "source"]
        )
        formatted = []
        if results:
            for hit in results[0]:
                formatted.append({
                    "content": hit['entity'].get('text', ''),
                    "source": hit['entity'].get('source', 'Unknown'),
                    "score": hit['distance']
                })
        return formatted

    def delete_source(self, source_name: str) -> bool:
        self.client.delete(collection_name=self.collection_name, filter=f"source == '{source_name}'")
        return True
        
    def get_chunks(self, source_name: str) -> List[Dict]:
        results = self.client.query(
            collection_name=self.collection_name,
            filter=f"source == '{source_name}'",
            output_fields=["text", "chunk_index"]
        )
        results.sort(key=lambda x: x.get('chunk_index', 0))
        return [{"content": r.get("text", ""), "index": r.get("chunk_index", 0)} for r in results]

class ChromaAdapter(VectorStoreAdapter):
    """
    Adapter implementation for ChromaDB.
    """
    def __init__(self, client, collection_name, embedding_function):
        self.collection = client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function
        )

    def ingest(self, chunks: List[str], metadatas: List[Dict]) -> bool:
        ids = [str(uuid.uuid4()) for _ in chunks]
        self.collection.add(documents=chunks, metadatas=metadatas, ids=ids)
        return True

    def search(self, query: str, limit: int) -> List[Dict]:
        results = self.collection.query(query_texts=[query], n_results=limit)
        formatted = []
        if results and results['documents']:
            docs = results['documents'][0]
            metas = results['metadatas'][0]
            dists = results['distances'][0] if results['distances'] else [0]*len(docs)
            for doc, meta, dist in zip(docs, metas, dists):
                formatted.append({
                    "content": doc,
                    "source": meta.get('source', 'Unknown'),
                    "score": 1.0 - dist if dist else 0.0
                })
        return formatted

    def delete_source(self, source_name: str) -> bool:
        self.collection.delete(where={"source": source_name})
        return True

    def get_chunks(self, source_name: str) -> List[Dict]:
        results = self.collection.get(where={"source": source_name}, include=["documents", "metadatas"])
        chunks = []
        if results and results['documents']:
            combined = []
            ids = results['ids']
            for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas'])):
                combined.append({
                    "id": ids[i],
                    "content": doc, 
                    "index": meta.get("chunk_index", 0)
                })
            combined.sort(key=lambda x: x['index'])
            chunks = combined
        return chunks

    def update_chunk(self, chunk_id: str, text: str) -> bool:
        self.collection.update(ids=[chunk_id], documents=[text])
        return True

# --- Chunking Strategy ---

class ChunkingStrategy:
    """
    Strategy for splitting text into chunks based on configuration templates.
    Supports different chunking parameters for different document types.
    """
    def __init__(self, config: Dict):
        self.config = config

    def split(self, text: str, template: str = "default") -> List[str]:
        """
        Split text into chunks using the specified template.
        
        Args:
            text (str): The full text to split.
            template (str): The configuration template name (e.g., 'default', 'scientific_paper').
            
        Returns:
            List[str]: List of text chunks.
        """
        # Get template config or fallback to default
        params = self.config.get("templates", {}).get(template)
        if not params:
            params = self.config.get("default", {})
            
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=params.get("chunk_size", 1000),
            chunk_overlap=params.get("chunk_overlap", 200),
            separators=params.get("separators", ["\n\n", "\n", " ", ""])
        )
        return splitter.split_text(text)

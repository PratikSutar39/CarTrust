"""
CarTrust RAG (Retrieval-Augmented Generation) Module

Builds a ChromaDB knowledge base from text documents and provides
semantic retrieval for the LLM explanation layer.
"""

import logging
import os
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

DOCUMENTS_DIR = Path(__file__).parent / "documents"
CHROMA_PERSIST_DIR = Path(__file__).parent / "chroma_db"


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks for better semantic retrieval."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i : i + chunk_size]
        chunks.append(" ".join(chunk_words))
        i += chunk_size - overlap
    return [c for c in chunks if c.strip()]


def build_knowledge_base(persist_dir: Optional[Path] = None):
    """
    Build and return a ChromaDB collection from all knowledge documents.
    Uses persistence so it only builds once.
    """
    try:
        import chromadb
        from chromadb.utils import embedding_functions
    except ImportError:
        logger.warning("chromadb not installed. RAG will be unavailable.")
        return None

    persist_path = str(persist_dir or CHROMA_PERSIST_DIR)
    os.makedirs(persist_path, exist_ok=True)

    client = chromadb.PersistentClient(path=persist_path)

    # Check if already built
    try:
        collection = client.get_collection("cartrust_knowledge")
        if collection.count() > 0:
            logger.info(f"Knowledge base loaded from cache ({collection.count()} chunks).")
            return collection
    except Exception:
        pass

    # Build from documents
    embedding_func = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(
        name="cartrust_knowledge",
        embedding_function=embedding_func,
    )

    documents = []
    metadatas = []
    ids = []
    chunk_id = 0

    for doc_path in sorted(DOCUMENTS_DIR.glob("*.txt")):
        text = doc_path.read_text(encoding="utf-8")
        chunks = chunk_text(text)
        for chunk in chunks:
            documents.append(chunk)
            metadatas.append({"source": doc_path.name, "doc": doc_path.stem})
            ids.append(f"chunk_{chunk_id}")
            chunk_id += 1

    if documents:
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        logger.info(f"Knowledge base built with {len(documents)} chunks from {DOCUMENTS_DIR}.")

    return collection


def retrieve_knowledge(collection, query: str, n_results: int = 3) -> List[dict]:
    """
    Retrieve the most relevant knowledge chunks for a query.
    Returns a list of dicts with 'text' and 'source' keys.
    """
    if collection is None:
        return []
    try:
        results = collection.query(query_texts=[query], n_results=n_results)
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        return [
            {"text": doc, "source": meta.get("source", "unknown")}
            for doc, meta in zip(docs, metas)
        ]
    except Exception as e:
        logger.warning(f"RAG retrieval failed: {e}")
        return []

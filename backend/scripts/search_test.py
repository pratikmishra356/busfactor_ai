"""
Context Intelligence Platform - Search Utility
Test search functionality against ingested data in ChromaDB
"""

import os
import sys
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer

load_dotenv()

# Initialize embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize ChromaDB
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

COLLECTIONS = {
    "entities": "context_entities",
    "weekly_summaries": "weekly_summaries"
}


def search_entities(query: str, n_results: int = 5, source_filter: str = None):
    """Search for entities matching the query"""
    collection = chroma_client.get_collection(name=COLLECTIONS["entities"])
    
    # Generate query embedding
    query_embedding = embedding_model.encode(query, convert_to_numpy=True).tolist()
    
    # Build where filter
    where_filter = None
    if source_filter:
        where_filter = {"source": source_filter}
    
    # Search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"]
    )
    
    return results


def search_weekly_summaries(query: str, n_results: int = 3):
    """Search for weekly summaries matching the query"""
    collection = chroma_client.get_collection(name=COLLECTIONS["weekly_summaries"])
    
    # Generate query embedding
    query_embedding = embedding_model.encode(query, convert_to_numpy=True).tolist()
    
    # Search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    
    return results


def get_collection_stats():
    """Get statistics about stored collections"""
    stats = {}
    
    for name, collection_name in COLLECTIONS.items():
        try:
            collection = chroma_client.get_collection(name=collection_name)
            count = collection.count()
            stats[name] = count
        except Exception as e:
            stats[name] = f"Error: {e}"
    
    return stats


def main():
    print("=" * 60)
    print("Context Intelligence Platform - Search Test")
    print("=" * 60)
    
    # Show stats
    print("\n--- Collection Statistics ---")
    stats = get_collection_stats()
    for name, count in stats.items():
        print(f"  {name}: {count} items")
    
    # Test searches
    test_queries = [
        ("payment gateway", None),
        ("incident", None),
        ("API refactoring", "slack"),
        ("security vulnerability", None),
        ("postmortem", "docs"),
    ]
    
    print("\n--- Entity Search Tests ---")
    for query, source_filter in test_queries:
        print(f"\nQuery: '{query}'" + (f" (source: {source_filter})" if source_filter else ""))
        results = search_entities(query, n_results=3, source_filter=source_filter)
        
        for i, (doc_id, metadata, distance) in enumerate(zip(
            results['ids'][0], 
            results['metadatas'][0], 
            results['distances'][0]
        )):
            print(f"  {i+1}. [{metadata['source']}] {metadata['title'][:60]}... (dist: {distance:.3f})")
    
    print("\n--- Weekly Summary Search Tests ---")
    summary_queries = ["incident resolution", "database performance"]
    
    for query in summary_queries:
        print(f"\nQuery: '{query}'")
        results = search_weekly_summaries(query, n_results=2)
        
        for i, (doc_id, metadata, distance) in enumerate(zip(
            results['ids'][0], 
            results['metadatas'][0], 
            results['distances'][0]
        )):
            print(f"  {i+1}. Week {metadata['week_key']}: {metadata['entity_count']} entities (dist: {distance:.3f})")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

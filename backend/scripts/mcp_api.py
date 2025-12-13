"""
Context Intelligence Platform - MCP API Layer
Exposes search and connection graph APIs for the intelligence platform.
"""

import os
import sqlite3
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
import chromadb

# Paths
SCRIPT_DIR = os.path.dirname(__file__)
CHROMA_PERSIST_DIR = os.path.join(SCRIPT_DIR, "..", "chroma_db")
SQLITE_DB_PATH = os.path.join(SCRIPT_DIR, "..", "entity_connections.db")

# Initialize embedding model (lazy loading)
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model

# Initialize ChromaDB client (lazy loading)
_chroma_client = None

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    return _chroma_client


# ============== Pydantic Models ==============

class SubEntity(BaseModel):
    """Individual entity within a summary"""
    entity_id: str
    source: str
    type: str
    title: str
    preview: str = ""
    timestamp: str = ""


class SummarizedEntity(BaseModel):
    """Weekly summary with sub-entities"""
    summary_id: str
    week_key: str
    summary_text: str
    entity_count: int
    sources: List[str]
    sub_entity_ids: List[str]
    distance: float = 0.0


class SearchResponse(BaseModel):
    """Response for natural search query"""
    query: str
    results: List[SummarizedEntity]
    total_sub_entities: int


class GraphNode(BaseModel):
    """Node in the connection graph"""
    id: str
    source: str
    type: str = ""
    title: str
    preview: str = ""


class GraphEdge(BaseModel):
    """Edge in the connection graph"""
    source: str  # from node id
    target: str  # to node id
    connection_type: str
    confidence: float
    match_reason: str


class ConnectionGraph(BaseModel):
    """Bidirectional connection graph"""
    query: str
    root_summaries: List[str]
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    node_count: int
    edge_count: int


class EntityDetails(BaseModel):
    """Full entity details with connections"""
    entity_id: str
    source: str
    type: str
    title: str
    content: str
    preview: str
    timestamp: str
    incident_ref: str = ""
    jira_ref: str = ""
    pr_ref: str = ""
    connections: Dict[str, List[Dict]] = {}


class CodeAuditPR(BaseModel):
    """PR result from code audit search"""
    pr_id: str
    pr_number: str
    title: str
    author: str
    author_github: str
    reviewer: str
    status: str
    timestamp: str
    merged_at: str
    labels: List[str]
    jira_ref: str = ""
    incident_ref: str = ""
    files_changed: List[str] = []
    file_count: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    match_type: str = ""  # "file_path", "comment", "query"
    match_score: float = 0.0
    matched_content: str = ""


class CodeAuditResponse(BaseModel):
    """Response for code audit queries"""
    query: str
    query_type: str  # "file_path", "comment", "query"
    results: List[CodeAuditPR]
    total_results: int


# ============== Core Functions ==============

def search_weekly_summaries(query: str, n_results: int = 5) -> List[Dict]:
    """Search weekly summaries using vector similarity"""
    chroma_client = get_chroma_client()
    embedding_model = get_embedding_model()
    
    collection = chroma_client.get_collection(name="weekly_summaries")
    
    # Generate query embedding
    query_embedding = embedding_model.encode(query, convert_to_numpy=True).tolist()
    
    # Search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    
    summaries = []
    for i, (summary_id, doc, metadata, distance) in enumerate(zip(
        results['ids'][0],
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        sub_entity_ids = metadata.get('sub_entity_ids', '').split(',') if metadata.get('sub_entity_ids') else []
        
        summaries.append({
            "summary_id": summary_id,
            "week_key": metadata.get("week_key", ""),
            "summary_text": doc,
            "entity_count": metadata.get("entity_count", 0),
            "sources": metadata.get("sources", "").split(",") if metadata.get("sources") else [],
            "sub_entity_ids": sub_entity_ids,
            "distance": distance
        })
    
    return summaries


def get_entity_metadata(entity_id: str) -> Optional[Dict]:
    """Get entity metadata from SQLite"""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT entity_id, source, entity_type, title, content_preview, timestamp,
               incident_ref, jira_ref, pr_ref, metadata_json
        FROM entity_metadata WHERE entity_id = ?
    ''', (entity_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return {
        "entity_id": row[0],
        "source": row[1],
        "type": row[2] or "",
        "title": row[3] or "",
        "preview": row[4][:200] if row[4] else "",
        "content": row[4] or "",  # Full content
        "timestamp": row[5] or "",
        "incident_ref": row[6] or "",
        "jira_ref": row[7] or "",
        "pr_ref": row[8] or "",
        "metadata_json": row[9] or "{}"
    }


def get_entity_connections(entity_id: str) -> List[Dict]:
    """Get all connections for an entity from SQLite"""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ec.target_entity_id, ec.target_type, ec.connection_type, 
               ec.confidence_score, ec.match_reason,
               em.title, em.content_preview, em.entity_type
        FROM entity_connections ec
        LEFT JOIN entity_metadata em ON ec.target_entity_id = em.entity_id
        WHERE ec.source_entity_id = ?
        ORDER BY ec.confidence_score DESC
    ''', (entity_id,))
    
    connections = []
    for row in cursor.fetchall():
        connections.append({
            "target_id": row[0],
            "target_source": row[1],
            "connection_type": row[2],
            "confidence": row[3],
            "match_reason": row[4],
            "title": row[5] or "",
            "preview": (row[6] or "")[:200],
            "type": row[7] or ""
        })
    
    conn.close()
    return connections


def build_connection_graph(sub_entity_ids: List[str], max_depth: int = 1) -> Dict:
    """
    Build bidirectional connection graph from sub-entities.
    
    Starting from sub_entity_ids, fetch their connections and build a graph
    where each node can connect to multiple other nodes bidirectionally.
    """
    nodes: Dict[str, GraphNode] = {}
    edges: List[GraphEdge] = []
    seen_edges: Set[tuple] = set()
    
    def add_node(entity_id: str) -> bool:
        """Add a node if not already present, return True if added"""
        if entity_id in nodes:
            return False
        
        metadata = get_entity_metadata(entity_id)
        if metadata:
            nodes[entity_id] = GraphNode(
                id=entity_id,
                source=metadata["source"],
                type=metadata["type"],
                title=metadata["title"],
                preview=metadata["preview"]
            )
            return True
        return False
    
    def add_edge(source_id: str, target_id: str, conn_type: str, confidence: float, reason: str):
        """Add edge if not already present (check both directions)"""
        edge_key = tuple(sorted([source_id, target_id]))
        if edge_key not in seen_edges:
            seen_edges.add(edge_key)
            edges.append(GraphEdge(
                source=source_id,
                target=target_id,
                connection_type=conn_type,
                confidence=confidence,
                match_reason=reason
            ))
    
    # Process each sub-entity
    entities_to_process = list(sub_entity_ids)
    processed = set()
    current_depth = 0
    
    while entities_to_process and current_depth <= max_depth:
        next_level = []
        
        for entity_id in entities_to_process:
            if entity_id in processed:
                continue
            processed.add(entity_id)
            
            # Add the node
            add_node(entity_id)
            
            # Get connections
            connections = get_entity_connections(entity_id)
            
            for conn in connections:
                target_id = conn["target_id"]
                
                # Add target node
                add_node(target_id)
                
                # Add edge
                add_edge(
                    entity_id, 
                    target_id, 
                    conn["connection_type"],
                    conn["confidence"],
                    conn["match_reason"]
                )
                
                # Queue for next depth level
                if target_id not in processed and current_depth < max_depth:
                    next_level.append(target_id)
        
        entities_to_process = next_level
        current_depth += 1
    
    return {
        "nodes": list(nodes.values()),
        "edges": edges
    }


# ============== API Functions ==============

def get_entity_by_id(entity_id: str) -> Optional[EntityDetails]:
    """
    API: Get entity details by ID
    
    Returns full entity details including:
    - Basic metadata (source, type, title, content)
    - References (incident_ref, jira_ref, pr_ref)
    - All connections grouped by target source type
    """
    # Get basic metadata
    metadata = get_entity_metadata(entity_id)
    if not metadata:
        return None
    
    # Get connections
    connections = get_entity_connections(entity_id)
    
    # Group connections by target source
    grouped_connections = {}
    for conn in connections:
        target_source = conn["target_source"]
        if target_source not in grouped_connections:
            grouped_connections[target_source] = []
        grouped_connections[target_source].append({
            "entity_id": conn["target_id"],
            "title": conn["title"],
            "preview": conn["preview"],
            "type": conn["type"],
            "connection_type": conn["connection_type"],
            "confidence": conn["confidence"],
            "match_reason": conn["match_reason"]
        })
    
    return EntityDetails(
        entity_id=metadata["entity_id"],
        source=metadata["source"],
        type=metadata["type"],
        title=metadata["title"],
        content=metadata["content"],
        preview=metadata["preview"],
        timestamp=metadata["timestamp"],
        incident_ref=metadata["incident_ref"],
        jira_ref=metadata["jira_ref"],
        pr_ref=metadata["pr_ref"],
        connections=grouped_connections
    )


def natural_search(query: str, top_k: int = 3) -> SearchResponse:
    """
    API 1: Natural search query -> summarized entities with sub-entity IDs
    
    Returns relevant weekly summaries with their constituent entity IDs.
    """
    summaries = search_weekly_summaries(query, n_results=top_k)
    
    results = [
        SummarizedEntity(
            summary_id=s["summary_id"],
            week_key=s["week_key"],
            summary_text=s["summary_text"],
            entity_count=s["entity_count"],
            sources=s["sources"],
            sub_entity_ids=s["sub_entity_ids"],
            distance=s["distance"]
        )
        for s in summaries
    ]
    
    total_sub_entities = sum(len(r.sub_entity_ids) for r in results)
    
    return SearchResponse(
        query=query,
        results=results,
        total_sub_entities=total_sub_entities
    )


def search_with_connections(query: str, top_k: int = 2, graph_depth: int = 1) -> ConnectionGraph:
    """
    API 2: Natural search query -> bidirectional connection graph
    
    1. Fetches relevant summarized entities
    2. Gets sub-entity IDs from summaries
    3. Queries SQLite for connections of those sub-entities
    4. Builds bidirectional graph where entities link to each other
    """
    # Step 1: Search for relevant summaries
    summaries = search_weekly_summaries(query, n_results=top_k)
    
    # Step 2: Collect all sub-entity IDs
    all_sub_entity_ids = []
    root_summary_ids = []
    
    for summary in summaries:
        root_summary_ids.append(summary["summary_id"])
        all_sub_entity_ids.extend(summary["sub_entity_ids"])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_sub_entity_ids = []
    for eid in all_sub_entity_ids:
        if eid and eid not in seen:
            seen.add(eid)
            unique_sub_entity_ids.append(eid)
    
    # Step 3 & 4: Build bidirectional graph
    graph = build_connection_graph(unique_sub_entity_ids, max_depth=graph_depth)
    
    return ConnectionGraph(
        query=query,
        root_summaries=root_summary_ids,
        nodes=graph["nodes"],
        edges=graph["edges"],
        node_count=len(graph["nodes"]),
        edge_count=len(graph["edges"])
    )


# ============== Test Function ==============

def demo():
    """Demo the MCP API functions"""
    print("=" * 70)
    print("Context Intelligence Platform - MCP API Demo")
    print("=" * 70)
    
    # API 1: Natural Search
    print("\n--- API 1: Natural Search ---")
    query1 = "payment gateway issues"
    response1 = natural_search(query1, top_k=2)
    
    print(f"Query: '{response1.query}'")
    print(f"Total sub-entities found: {response1.total_sub_entities}")
    
    for result in response1.results:
        print(f"\n  [{result.week_key}] {result.summary_id}")
        print(f"    Entity count: {result.entity_count}")
        print(f"    Sources: {result.sources}")
        print(f"    Sub-entities: {result.sub_entity_ids[:5]}..." if len(result.sub_entity_ids) > 5 else f"    Sub-entities: {result.sub_entity_ids}")
        print(f"    Summary: {result.summary_text[:150]}...")
    
    # API 2: Search with Connections
    print("\n\n--- API 2: Search with Connections Graph ---")
    query2 = "payment outage"
    response2 = search_with_connections(query2, top_k=1, graph_depth=1)
    
    print(f"Query: '{response2.query}'")
    print(f"Root summaries: {response2.root_summaries}")
    print(f"Graph: {response2.node_count} nodes, {response2.edge_count} edges")
    
    print("\nNodes:")
    for node in response2.nodes[:10]:
        print(f"  [{node.source}] {node.id}: {node.title[:50]}...")
    
    print("\nEdges:")
    for edge in response2.edges[:10]:
        print(f"  {edge.source} --[{edge.connection_type}:{edge.confidence:.2f}]--> {edge.target}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo()

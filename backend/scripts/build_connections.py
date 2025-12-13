"""
Context Intelligence Platform - Entity Connection Builder
Builds bidirectional relationships between entities using:
1. Regex matching (incident_ref, jira_ref, pr_ref, ticket IDs)
2. Vector similarity search (semantic matching)

Stores relationships in SQLite for fast retrieval.
"""

import os
import re
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer

load_dotenv()

# Initialize embedding model
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("Embedding model loaded.")

# Initialize ChromaDB
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

# SQLite database for relationships
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "entity_connections.db")

# Thresholds
VECTOR_SIMILARITY_THRESHOLD = 1.2  # Lower distance = more similar (for L2 distance)
MIN_CONFIDENCE_SCORE = 0.5


def init_sqlite_db():
    """Initialize SQLite database for storing entity connections"""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    # Entity connections table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entity_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_entity_id TEXT NOT NULL,
            source_type TEXT NOT NULL,
            target_entity_id TEXT NOT NULL,
            target_type TEXT NOT NULL,
            connection_type TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            match_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_entity_id, target_entity_id)
        )
    ''')
    
    # Entity metadata cache
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entity_metadata (
            entity_id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            entity_type TEXT,
            title TEXT,
            content_preview TEXT,
            incident_ref TEXT,
            jira_ref TEXT,
            pr_ref TEXT,
            timestamp TEXT,
            metadata_json TEXT
        )
    ''')
    
    # Indexes for fast lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_entity ON entity_connections(source_entity_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_target_entity ON entity_connections(target_entity_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_incident_ref ON entity_metadata(incident_ref)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_jira_ref ON entity_metadata(jira_ref)')
    
    conn.commit()
    return conn


def load_all_entities() -> Dict[str, Dict]:
    """Load all entities from ChromaDB"""
    collection = chroma_client.get_collection(name="context_entities")
    
    # Get all entities
    results = collection.get(include=["documents", "metadatas"])
    
    entities = {}
    for entity_id, doc, metadata in zip(results['ids'], results['documents'], results['metadatas']):
        entities[entity_id] = {
            "id": entity_id,
            "document": doc,
            "metadata": metadata
        }
    
    return entities


def extract_references(text: str) -> Dict[str, Set[str]]:
    """Extract all reference IDs from text using regex"""
    refs = {
        "incident_refs": set(),
        "jira_refs": set(),
        "pr_refs": set(),
        "ticket_ids": set()
    }
    
    if not text:
        return refs
    
    # Incident references (INC001, INC-001, etc.)
    incident_pattern = r'INC[-]?(\d{3,4})'
    for match in re.finditer(incident_pattern, text, re.IGNORECASE):
        refs["incident_refs"].add(f"INC{match.group(1).zfill(3)}")
    
    # Jira references (ENG-1, ENG-123, PROJ-456)
    jira_pattern = r'([A-Z]{2,5})-(\d{1,5})'
    for match in re.finditer(jira_pattern, text):
        refs["jira_refs"].add(f"{match.group(1)}-{match.group(2)}")
    
    # PR references (PR #101, PR-101, pull/101)
    pr_pattern = r'(?:PR[#\s-]?|pull[/\s]?)(\d{2,4})'
    for match in re.finditer(pr_pattern, text, re.IGNORECASE):
        refs["pr_refs"].add(match.group(1))
    
    # Generic ticket IDs in metadata format
    ticket_pattern = r'(?:ticket|issue)[:\s#]+([A-Z]+-\d+)'
    for match in re.finditer(ticket_pattern, text, re.IGNORECASE):
        refs["ticket_ids"].add(match.group(1))
    
    return refs


def find_regex_matches(entities: Dict[str, Dict]) -> List[Tuple[str, str, str, float]]:
    """Find connections using regex pattern matching on references"""
    connections = []
    
    # Build lookup tables for fast matching
    incident_lookup = defaultdict(list)  # incident_ref -> [entity_ids]
    jira_lookup = defaultdict(list)       # jira_ref -> [entity_ids]
    pr_lookup = defaultdict(list)         # pr_number -> [entity_ids]
    
    for entity_id, entity in entities.items():
        metadata = entity.get("metadata", {})
        document = entity.get("document", "")
        
        # From metadata fields
        if metadata.get("incident_ref"):
            incident_lookup[metadata["incident_ref"]].append(entity_id)
        
        # Extract from document content
        refs = extract_references(document)
        
        for inc_ref in refs["incident_refs"]:
            incident_lookup[inc_ref].append(entity_id)
        
        for jira_ref in refs["jira_refs"]:
            jira_lookup[jira_ref].append(entity_id)
        
        for pr_ref in refs["pr_refs"]:
            pr_lookup[pr_ref].append(entity_id)
    
    # Find connections based on shared references
    seen_pairs = set()
    
    # Incident-based connections
    for incident_ref, entity_ids in incident_lookup.items():
        if len(entity_ids) > 1:
            for i, eid1 in enumerate(entity_ids):
                for eid2 in entity_ids[i+1:]:
                    pair = tuple(sorted([eid1, eid2]))
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        connections.append((eid1, eid2, f"shared_incident:{incident_ref}", 0.95))
    
    # Jira-based connections
    for jira_ref, entity_ids in jira_lookup.items():
        if len(entity_ids) > 1:
            for i, eid1 in enumerate(entity_ids):
                for eid2 in entity_ids[i+1:]:
                    pair = tuple(sorted([eid1, eid2]))
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        connections.append((eid1, eid2, f"shared_jira:{jira_ref}", 0.90))
    
    # PR-based connections (match github PRs to Jira tickets mentioning them)
    for pr_ref, entity_ids in pr_lookup.items():
        # Also look for the corresponding github_pr entity
        github_pr_id = f"github_pr_{pr_ref}"
        if github_pr_id in entities:
            for eid in entity_ids:
                if eid != github_pr_id:
                    pair = tuple(sorted([eid, github_pr_id]))
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        connections.append((eid, github_pr_id, f"pr_reference:{pr_ref}", 0.85))
    
    return connections


def find_vector_matches(entities: Dict[str, Dict], existing_pairs: Set[Tuple[str, str]]) -> List[Tuple[str, str, str, float]]:
    """Find connections using vector similarity search"""
    connections = []
    collection = chroma_client.get_collection(name="context_entities")
    
    # Group entities by source
    jira_entities = {k: v for k, v in entities.items() if k.startswith("jira_")}
    
    print(f"  Finding vector matches for {len(jira_entities)} Jira tickets...")
    
    for jira_id, jira_entity in jira_entities.items():
        # Get embedding for this Jira ticket
        jira_doc = jira_entity.get("document", "")
        if not jira_doc:
            continue
        
        query_embedding = embedding_model.encode(jira_doc, convert_to_numpy=True).tolist()
        
        # Search for similar entities (exclude self and same source)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=10,
            include=["metadatas", "distances"]
        )
        
        for match_id, metadata, distance in zip(
            results['ids'][0], 
            results['metadatas'][0], 
            results['distances'][0]
        ):
            # Skip self
            if match_id == jira_id:
                continue
            
            # Skip same source type (jira to jira)
            if match_id.startswith("jira_"):
                continue
            
            # Check if already connected via regex
            pair = tuple(sorted([jira_id, match_id]))
            if pair in existing_pairs:
                continue
            
            # Only keep close matches
            if distance < VECTOR_SIMILARITY_THRESHOLD:
                # Convert distance to confidence (lower distance = higher confidence)
                confidence = max(0, 1 - (distance / 2))  # Normalize to 0-1
                
                if confidence >= MIN_CONFIDENCE_SCORE:
                    connections.append((jira_id, match_id, f"vector_similarity:{distance:.3f}", confidence))
                    existing_pairs.add(pair)
    
    return connections


def find_meeting_connections(entities: Dict[str, Dict], existing_pairs: Set[Tuple[str, str]]) -> List[Tuple[str, str, str, float]]:
    """Find connections between meetings and other entities based on keywords and participants"""
    connections = []
    
    meeting_entities = {k: v for k, v in entities.items() if k.startswith("meeting_")}
    
    for meeting_id, meeting_entity in meeting_entities.items():
        meeting_doc = meeting_entity.get("document", "")
        meeting_metadata = meeting_entity.get("metadata", {})
        
        # Check incident reference from metadata
        incident_ref = meeting_metadata.get("incident_ref", "")
        
        # Search for related entities
        for entity_id, entity in entities.items():
            if entity_id == meeting_id:
                continue
            
            pair = tuple(sorted([meeting_id, entity_id]))
            if pair in existing_pairs:
                continue
            
            entity_metadata = entity.get("metadata", {})
            
            # Match by incident reference
            if incident_ref and entity_metadata.get("incident_ref") == incident_ref:
                connections.append((meeting_id, entity_id, f"shared_incident:{incident_ref}", 0.90))
                existing_pairs.add(pair)
    
    return connections


def store_connections(conn: sqlite3.Connection, connections: List[Tuple[str, str, str, float]], entities: Dict[str, Dict]):
    """Store connections in SQLite database"""
    cursor = conn.cursor()
    
    # First, cache entity metadata
    print("  Caching entity metadata...")
    for entity_id, entity in entities.items():
        metadata = entity.get("metadata", {})
        cursor.execute('''
            INSERT OR REPLACE INTO entity_metadata 
            (entity_id, source, entity_type, title, content_preview, incident_ref, jira_ref, pr_ref, timestamp, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entity_id,
            metadata.get("source", ""),
            metadata.get("type", ""),
            metadata.get("title", "")[:200],
            entity.get("document", "")[:500],
            metadata.get("incident_ref", ""),
            metadata.get("jira_ref", ""),
            metadata.get("pr_ref", ""),
            metadata.get("timestamp", ""),
            json.dumps(metadata)
        ))
    
    # Store bidirectional connections
    print("  Storing connections...")
    stored_count = 0
    
    for source_id, target_id, match_reason, confidence in connections:
        source_meta = entities.get(source_id, {}).get("metadata", {})
        target_meta = entities.get(target_id, {}).get("metadata", {})
        
        # Store forward connection
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO entity_connections 
                (source_entity_id, source_type, target_entity_id, target_type, connection_type, confidence_score, match_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                source_id,
                source_meta.get("source", ""),
                target_id,
                target_meta.get("source", ""),
                match_reason.split(":")[0],
                confidence,
                match_reason
            ))
            stored_count += 1
        except sqlite3.IntegrityError:
            pass
        
        # Store reverse connection
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO entity_connections 
                (source_entity_id, source_type, target_entity_id, target_type, connection_type, confidence_score, match_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                target_id,
                target_meta.get("source", ""),
                source_id,
                source_meta.get("source", ""),
                match_reason.split(":")[0],
                confidence,
                match_reason
            ))
            stored_count += 1
        except sqlite3.IntegrityError:
            pass
    
    conn.commit()
    return stored_count


def get_entity_connections(conn: sqlite3.Connection, entity_id: str) -> Dict[str, List[Dict]]:
    """Get all connections for an entity, grouped by target source type"""
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ec.target_entity_id, ec.target_type, ec.connection_type, ec.confidence_score, ec.match_reason,
               em.title, em.content_preview
        FROM entity_connections ec
        LEFT JOIN entity_metadata em ON ec.target_entity_id = em.entity_id
        WHERE ec.source_entity_id = ?
        ORDER BY ec.confidence_score DESC
    ''', (entity_id,))
    
    connections = defaultdict(list)
    for row in cursor.fetchall():
        target_id, target_type, conn_type, confidence, reason, title, preview = row
        connections[target_type].append({
            "entity_id": target_id,
            "connection_type": conn_type,
            "confidence": confidence,
            "match_reason": reason,
            "title": title,
            "preview": preview[:200] if preview else ""
        })
    
    return dict(connections)


def print_connection_stats(conn: sqlite3.Connection):
    """Print statistics about stored connections"""
    cursor = conn.cursor()
    
    # Total connections
    cursor.execute('SELECT COUNT(*) FROM entity_connections')
    total = cursor.fetchone()[0]
    
    # By connection type
    cursor.execute('''
        SELECT connection_type, COUNT(*) as cnt 
        FROM entity_connections 
        GROUP BY connection_type 
        ORDER BY cnt DESC
    ''')
    by_type = cursor.fetchall()
    
    # By source-target type pairs
    cursor.execute('''
        SELECT source_type || ' -> ' || target_type as pair, COUNT(*) as cnt 
        FROM entity_connections 
        GROUP BY pair 
        ORDER BY cnt DESC
        LIMIT 10
    ''')
    by_pair = cursor.fetchall()
    
    # Entities with most connections
    cursor.execute('''
        SELECT source_entity_id, COUNT(*) as cnt 
        FROM entity_connections 
        GROUP BY source_entity_id 
        ORDER BY cnt DESC
        LIMIT 5
    ''')
    top_connected = cursor.fetchall()
    
    print("\n--- Connection Statistics ---")
    print(f"Total connections: {total}")
    
    print("\nBy connection type:")
    for conn_type, count in by_type:
        print(f"  {conn_type}: {count}")
    
    print("\nBy source -> target type:")
    for pair, count in by_pair:
        print(f"  {pair}: {count}")
    
    print("\nTop connected entities:")
    for entity_id, count in top_connected:
        print(f"  {entity_id}: {count} connections")


def main():
    print("=" * 60)
    print("Context Intelligence Platform - Connection Builder")
    print("=" * 60)
    
    # Initialize database
    print("\n[1/5] Initializing SQLite database...")
    conn = init_sqlite_db()
    
    # Load all entities
    print("\n[2/5] Loading entities from ChromaDB...")
    entities = load_all_entities()
    print(f"  Loaded {len(entities)} entities")
    
    # Find regex-based connections
    print("\n[3/5] Finding regex-based connections...")
    regex_connections = find_regex_matches(entities)
    print(f"  Found {len(regex_connections)} regex matches")
    
    # Track existing pairs to avoid duplicates
    existing_pairs = set()
    for src, tgt, _, _ in regex_connections:
        existing_pairs.add(tuple(sorted([src, tgt])))
    
    # Find vector similarity connections
    print("\n[4/5] Finding vector similarity connections...")
    vector_connections = find_vector_matches(entities, existing_pairs)
    print(f"  Found {len(vector_connections)} vector matches")
    
    # Find meeting-specific connections
    meeting_connections = find_meeting_connections(entities, existing_pairs)
    print(f"  Found {len(meeting_connections)} meeting connections")
    
    # Combine all connections
    all_connections = regex_connections + vector_connections + meeting_connections
    print(f"\nTotal unique connections: {len(all_connections)}")
    
    # Store in SQLite
    print("\n[5/5] Storing connections in SQLite...")
    stored = store_connections(conn, all_connections, entities)
    print(f"  Stored {stored} connection records (bidirectional)")
    
    # Print statistics
    print_connection_stats(conn)
    
    # Demo: Show connections for a specific Jira ticket
    print("\n--- Demo: Connections for jira_ENG-1 ---")
    demo_connections = get_entity_connections(conn, "jira_ENG-1")
    for source_type, conns in demo_connections.items():
        print(f"\n{source_type}:")
        for c in conns[:3]:  # Show top 3
            print(f"  [{c['confidence']:.2f}] {c['entity_id']}: {c['title'][:50]}...")
            print(f"         Reason: {c['match_reason']}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("CONNECTION BUILDING COMPLETE")
    print(f"Database: {SQLITE_DB_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()

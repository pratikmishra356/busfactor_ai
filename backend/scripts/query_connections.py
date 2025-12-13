"""
Context Intelligence Platform - Connection Query Utility
Query and explore entity connections stored in SQLite.
"""

import os
import sqlite3
import json
from typing import Dict, List, Optional
from collections import defaultdict

SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "entity_connections.db")


def get_db_connection():
    """Get SQLite database connection"""
    return sqlite3.connect(SQLITE_DB_PATH)


def get_entity_info(conn: sqlite3.Connection, entity_id: str) -> Optional[Dict]:
    """Get metadata for a specific entity"""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT entity_id, source, entity_type, title, content_preview, 
               incident_ref, jira_ref, pr_ref, timestamp
        FROM entity_metadata WHERE entity_id = ?
    ''', (entity_id,))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    return {
        "entity_id": row[0],
        "source": row[1],
        "type": row[2],
        "title": row[3],
        "preview": row[4],
        "incident_ref": row[5],
        "jira_ref": row[6],
        "pr_ref": row[7],
        "timestamp": row[8]
    }


def get_connections(conn: sqlite3.Connection, entity_id: str, 
                   filter_source: Optional[str] = None,
                   min_confidence: float = 0.0) -> Dict[str, List[Dict]]:
    """Get all connections for an entity, optionally filtered"""
    cursor = conn.cursor()
    
    query = '''
        SELECT ec.target_entity_id, ec.target_type, ec.connection_type, 
               ec.confidence_score, ec.match_reason,
               em.title, em.content_preview, em.incident_ref
        FROM entity_connections ec
        LEFT JOIN entity_metadata em ON ec.target_entity_id = em.entity_id
        WHERE ec.source_entity_id = ?
        AND ec.confidence_score >= ?
    '''
    params = [entity_id, min_confidence]
    
    if filter_source:
        query += ' AND ec.target_type = ?'
        params.append(filter_source)
    
    query += ' ORDER BY ec.confidence_score DESC'
    
    cursor.execute(query, params)
    
    connections = defaultdict(list)
    for row in cursor.fetchall():
        target_id, target_type, conn_type, confidence, reason, title, preview, incident = row
        connections[target_type].append({
            "entity_id": target_id,
            "connection_type": conn_type,
            "confidence": confidence,
            "match_reason": reason,
            "title": title or "",
            "preview": (preview or "")[:200],
            "incident_ref": incident or ""
        })
    
    return dict(connections)


def get_connection_graph(conn: sqlite3.Connection, entity_id: str, depth: int = 1) -> Dict:
    """Get connection graph starting from an entity up to specified depth"""
    visited = set()
    graph = {"nodes": [], "edges": []}
    
    def traverse(current_id: str, current_depth: int):
        if current_id in visited or current_depth > depth:
            return
        
        visited.add(current_id)
        
        # Add node
        entity_info = get_entity_info(conn, current_id)
        if entity_info:
            graph["nodes"].append({
                "id": current_id,
                "source": entity_info["source"],
                "title": entity_info["title"][:50],
                "incident_ref": entity_info["incident_ref"]
            })
        
        # Get connections
        connections = get_connections(conn, current_id, min_confidence=0.8)
        for source_type, conns in connections.items():
            for c in conns:
                target_id = c["entity_id"]
                
                # Add edge
                graph["edges"].append({
                    "from": current_id,
                    "to": target_id,
                    "confidence": c["confidence"],
                    "reason": c["match_reason"]
                })
                
                # Traverse deeper
                if current_depth < depth:
                    traverse(target_id, current_depth + 1)
    
    traverse(entity_id, 0)
    return graph


def find_related_by_incident(conn: sqlite3.Connection, incident_ref: str) -> Dict[str, List[Dict]]:
    """Find all entities related to a specific incident"""
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT entity_id, source, entity_type, title, content_preview
        FROM entity_metadata
        WHERE incident_ref = ?
        ORDER BY source, timestamp
    ''', (incident_ref,))
    
    results = defaultdict(list)
    for row in cursor.fetchall():
        entity_id, source, entity_type, title, preview = row
        results[source].append({
            "entity_id": entity_id,
            "type": entity_type,
            "title": title,
            "preview": (preview or "")[:200]
        })
    
    return dict(results)


def get_jira_ticket_full_context(conn: sqlite3.Connection, ticket_id: str) -> Dict:
    """Get full context for a Jira ticket including all related entities"""
    # Normalize ticket ID format
    if not ticket_id.startswith("jira_"):
        ticket_id = f"jira_{ticket_id}"
    
    result = {
        "ticket": get_entity_info(conn, ticket_id),
        "related_entities": {},
        "timeline": []
    }
    
    if not result["ticket"]:
        return {"error": f"Ticket {ticket_id} not found"}
    
    # Get all connections
    connections = get_connections(conn, ticket_id)
    
    for source_type, conns in connections.items():
        result["related_entities"][source_type] = conns
        
        # Build timeline
        for c in conns:
            entity_info = get_entity_info(conn, c["entity_id"])
            if entity_info and entity_info.get("timestamp"):
                result["timeline"].append({
                    "timestamp": entity_info["timestamp"],
                    "source": source_type,
                    "entity_id": c["entity_id"],
                    "title": c["title"],
                    "connection_type": c["connection_type"]
                })
    
    # Sort timeline
    result["timeline"].sort(key=lambda x: x.get("timestamp", ""))
    
    return result


def list_all_jira_tickets(conn: sqlite3.Connection) -> List[Dict]:
    """List all Jira tickets with their connection counts"""
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT em.entity_id, em.title, em.incident_ref,
               COUNT(ec.target_entity_id) as connection_count
        FROM entity_metadata em
        LEFT JOIN entity_connections ec ON em.entity_id = ec.source_entity_id
        WHERE em.source = 'jira'
        GROUP BY em.entity_id
        ORDER BY connection_count DESC
    ''')
    
    return [
        {
            "entity_id": row[0],
            "title": row[1],
            "incident_ref": row[2],
            "connection_count": row[3]
        }
        for row in cursor.fetchall()
    ]


def demo():
    """Demo the connection query capabilities"""
    conn = get_db_connection()
    
    print("=" * 70)
    print("Context Intelligence Platform - Connection Explorer")
    print("=" * 70)
    
    # List Jira tickets
    print("\n--- All Jira Tickets with Connection Counts ---")
    tickets = list_all_jira_tickets(conn)
    for t in tickets[:10]:
        print(f"  {t['entity_id']}: {t['title'][:40]}... ({t['connection_count']} connections)")
    
    # Full context for a specific ticket
    print("\n--- Full Context: jira_ENG-1 ---")
    context = get_jira_ticket_full_context(conn, "ENG-1")
    
    if "error" not in context:
        print(f"\nTicket: {context['ticket']['title']}")
        print(f"Incident: {context['ticket']['incident_ref']}")
        
        print("\nRelated Entities:")
        for source, entities in context["related_entities"].items():
            print(f"\n  {source.upper()} ({len(entities)}):")
            for e in entities[:3]:
                print(f"    - [{e['confidence']:.2f}] {e['title'][:50]}...")
        
        print(f"\nTimeline ({len(context['timeline'])} events):")
        for event in context["timeline"][:5]:
            print(f"  {event['timestamp'][:10]} [{event['source']}] {event['title'][:40]}...")
    
    # Find by incident
    print("\n--- All Entities for INC001 ---")
    incident_entities = find_related_by_incident(conn, "INC001")
    for source, entities in incident_entities.items():
        print(f"\n  {source}: {len(entities)} entities")
        for e in entities[:2]:
            print(f"    - {e['entity_id']}: {e['title'][:45]}...")
    
    # Connection graph
    print("\n--- Connection Graph (depth=1) for jira_ENG-1 ---")
    graph = get_connection_graph(conn, "jira_ENG-1", depth=1)
    print(f"  Nodes: {len(graph['nodes'])}")
    print(f"  Edges: {len(graph['edges'])}")
    
    conn.close()
    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo()

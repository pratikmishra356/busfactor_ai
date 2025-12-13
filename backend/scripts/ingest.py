"""
Context Intelligence Platform - Data Ingestion Script
Ingests JSON data from multiple sources, generates embeddings, stores in ChromaDB,
and creates weekly summaries for improved search indexing.

Uses:
- Sentence Transformers for local embeddings (all-MiniLM-L6-v2)
- OpenAI GPT via Emergent LLM key for weekly summaries
- ChromaDB for vector storage
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv()

# Initialize Emergent LLM key for summaries
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
if not EMERGENT_LLM_KEY:
    raise ValueError("EMERGENT_LLM_KEY not found in environment")

# Initialize sentence transformer for embeddings (local, no API key needed)
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("Embedding model loaded.")

# Initialize ChromaDB
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

# Collections for different entity types
COLLECTIONS = {
    "entities": "context_entities",
    "weekly_summaries": "weekly_summaries"
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def get_embedding(text: str) -> List[float]:
    """Generate embedding using sentence-transformers (local model)"""
    try:
        embedding = embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO 8601 timestamp string to datetime"""
    try:
        return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except:
        return datetime.now()


def get_week_key(dt: datetime) -> str:
    """Get week identifier (YYYY-WNN format)"""
    return f"{dt.year}-W{dt.isocalendar()[1]:02d}"


# ============== SLACK DATA PROCESSING ==============
def process_slack_data(file_path: str) -> List[Dict[str, Any]]:
    """
    Process Slack data - each thread (with its replies) becomes an entity.
    """
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    entities = []
    
    for thread in data.get("threads", []):
        # Combine thread content with all replies for full context
        full_content = thread.get("content", "")
        replies = thread.get("replies", [])
        
        for reply in replies:
            full_content += f"\n[{reply.get('user', 'Unknown')}]: {reply.get('content', '')}"
        
        entity = {
            "id": f"slack_{thread.get('thread_id', '')}",
            "source": "slack",
            "type": thread.get("type", "conversation"),
            "channel": thread.get("channel", ""),
            "title": f"Slack Thread: {thread.get('content', '')[:50]}...",
            "content": full_content,
            "author": thread.get("author", ""),
            "author_id": thread.get("author_id", ""),
            "timestamp": thread.get("timestamp", ""),
            "reply_count": thread.get("reply_count", 0),
            "incident_ref": thread.get("incident_ref", ""),
            "keywords": thread.get("keywords", []),
            "participants": list(set([thread.get("author", "")] + [r.get("user", "") for r in replies]))
        }
        entities.append(entity)
    
    print(f"Processed {len(entities)} Slack threads")
    return entities


# ============== DOCS DATA PROCESSING ==============
def process_docs_data(file_path: str) -> List[Dict[str, Any]]:
    """Process documentation data"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    entities = []
    
    for doc in data.get("documents", []):
        entity = {
            "id": f"doc_{doc.get('doc_id', '')}",
            "source": "docs",
            "type": doc.get("type", "document"),
            "title": doc.get("title", ""),
            "content": doc.get("content", ""),
            "author": doc.get("author", ""),
            "author_id": doc.get("author_id", ""),
            "timestamp": doc.get("created_at", ""),
            "updated_at": doc.get("updated_at", ""),
            "tags": doc.get("tags", []),
            "incident_ref": doc.get("incident_ref", ""),
            "jira_ref": doc.get("jira_ref", ""),
            "pr_ref": doc.get("pr_ref", "")
        }
        entities.append(entity)
    
    print(f"Processed {len(entities)} documents")
    return entities


# ============== GITHUB DATA PROCESSING ==============
def process_github_data(file_path: str) -> List[Dict[str, Any]]:
    """Process GitHub pull request data"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    entities = []
    
    for pr in data.get("pull_requests", []):
        entity = {
            "id": f"github_pr_{pr.get('pr_number', '')}",
            "source": "github",
            "type": "pull_request",
            "title": pr.get("title", ""),
            "content": pr.get("description", ""),
            "author": pr.get("author", ""),
            "author_id": pr.get("author_id", ""),
            "author_github": pr.get("author_github", ""),
            "reviewer": pr.get("reviewer", ""),
            "reviewer_id": pr.get("reviewer_id", ""),
            "timestamp": pr.get("created_at", ""),
            "merged_at": pr.get("merged_at", ""),
            "status": pr.get("status", ""),
            "branch": pr.get("branch", ""),
            "base_branch": pr.get("base_branch", ""),
            "repository": pr.get("repository", ""),
            "labels": pr.get("labels", []),
            "incident_ref": pr.get("incident_ref", ""),
            "jira_ref": pr.get("jira_ref", "")
        }
        entities.append(entity)
    
    print(f"Processed {len(entities)} GitHub PRs")
    return entities


# ============== JIRA DATA PROCESSING ==============
def process_jira_data(file_path: str) -> List[Dict[str, Any]]:
    """Process Jira ticket data"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    entities = []
    
    for ticket in data.get("tickets", []):
        entity = {
            "id": f"jira_{ticket.get('ticket_id', '')}",
            "source": "jira",
            "type": ticket.get("type", "ticket"),
            "ticket_id": ticket.get("ticket_id", ""),
            "title": ticket.get("summary", ""),
            "content": ticket.get("description", ""),
            "priority": ticket.get("priority", ""),
            "status": ticket.get("status", ""),
            "reporter": ticket.get("reporter", ""),
            "reporter_id": ticket.get("reporter_id", ""),
            "assignee": ticket.get("assignee", ""),
            "assignee_id": ticket.get("assignee_id", ""),
            "timestamp": ticket.get("created_at", ""),
            "updated_at": ticket.get("updated_at", ""),
            "parent_ticket": ticket.get("parent_ticket", ""),
            "labels": ticket.get("labels", []),
            "incident_ref": ticket.get("incident_ref", "")
        }
        entities.append(entity)
    
    print(f"Processed {len(entities)} Jira tickets")
    return entities


# ============== MEETINGS DATA PROCESSING ==============
def process_meetings_data(file_path: str) -> List[Dict[str, Any]]:
    """Process meeting data"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    entities = []
    
    for meeting in data.get("meetings", []):
        # Combine transcript into content
        transcript_text = ""
        for entry in meeting.get("transcript", []):
            transcript_text += f"[{entry.get('timestamp_offset', '')}] {entry.get('speaker', '')}: {entry.get('text', '')}\n"
        
        # Format action items
        action_items_text = ""
        for item in meeting.get("action_items", []):
            action_items_text += f"- {item.get('action', '')} (Assignee: {item.get('assignee', '')}, Status: {item.get('status', '')})\n"
        
        full_content = f"Summary: {meeting.get('summary', '')}\n\nTranscript:\n{transcript_text}"
        if action_items_text:
            full_content += f"\nAction Items:\n{action_items_text}"
        
        participants = [p.get("name", "") for p in meeting.get("participants", [])]
        
        entity = {
            "id": f"meeting_{meeting.get('meeting_id', '')}",
            "source": "meetings",
            "type": meeting.get("type", "meeting"),
            "title": meeting.get("title", ""),
            "content": full_content,
            "summary": meeting.get("summary", ""),
            "organizer": meeting.get("organizer", ""),
            "organizer_id": meeting.get("organizer_id", ""),
            "timestamp": meeting.get("scheduled_time", ""),
            "duration_minutes": meeting.get("duration_minutes", 0),
            "participants": participants,
            "action_items": meeting.get("action_items", []),
            "incident_ref": meeting.get("incident_ref", ""),
            "keywords": meeting.get("keywords", [])
        }
        entities.append(entity)
    
    print(f"Processed {len(entities)} meetings")
    return entities


# ============== WEEKLY SUMMARY GENERATION ==============
def group_entities_by_week(entities: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group entities by their week"""
    weekly_groups = defaultdict(list)
    
    for entity in entities:
        timestamp_str = entity.get("timestamp", "")
        if timestamp_str:
            dt = parse_timestamp(timestamp_str)
            week_key = get_week_key(dt)
            weekly_groups[week_key].append(entity)
    
    return weekly_groups


async def generate_weekly_summary(week_key: str, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a summary for a week's worth of entities using GPT via Emergent"""
    
    # Group by source
    by_source = defaultdict(list)
    for entity in entities:
        by_source[entity.get("source", "unknown")].append(entity)
    
    # Create summary prompt
    summary_parts = []
    
    for source, source_entities in by_source.items():
        titles = [e.get("title", "")[:100] for e in source_entities[:10]]  # Limit to 10 per source
        summary_parts.append(f"**{source.upper()}** ({len(source_entities)} items):\n" + "\n".join([f"- {t}" for t in titles]))
    
    prompt = f"""Summarize the following week's ({week_key}) activities across different data sources. 
Create a concise but comprehensive summary that captures:
1. Key themes and topics
2. Important incidents or issues
3. Notable accomplishments
4. Key people involved

Data:
{chr(10).join(summary_parts)}

Provide a 2-3 paragraph summary that would help someone quickly understand what happened this week."""

    try:
        # Use LlmChat from emergentintegrations
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"weekly-summary-{week_key}",
            system_message="You are an assistant that creates concise weekly summaries for a context intelligence platform."
        ).with_model("openai", "gpt-4o-mini")
        
        user_message = UserMessage(text=prompt)
        summary_text = await chat.send_message(user_message)
    except Exception as e:
        print(f"Error generating summary for {week_key}: {e}")
        summary_text = f"Weekly summary for {week_key}: {len(entities)} entities processed from sources: {', '.join(by_source.keys())}."
    
    # Collect all unique incident refs, keywords, and participants
    incident_refs = set()
    keywords = set()
    participants = set()
    sources = set()
    
    for entity in entities:
        if entity.get("incident_ref"):
            incident_refs.add(entity.get("incident_ref"))
        for kw in entity.get("keywords", []):
            keywords.add(kw)
        for p in entity.get("participants", []):
            participants.add(p)
        if entity.get("author"):
            participants.add(entity.get("author"))
        sources.add(entity.get("source", ""))
    
    # Collect sub-entity IDs
    sub_entity_ids = [entity.get("id") for entity in entities]
    
    return {
        "id": f"weekly_summary_{week_key}",
        "week_key": week_key,
        "summary": summary_text,
        "entity_count": len(entities),
        "sources": list(sources),
        "incident_refs": list(incident_refs),
        "keywords": list(keywords),
        "key_participants": list(participants)[:20],  # Limit to 20
        "entities_by_source": {k: len(v) for k, v in by_source.items()},
        "sub_entity_ids": sub_entity_ids  # Store all entity IDs in this week
    }


# ============== CHROMADB STORAGE ==============
def store_entities_in_chromadb(entities: List[Dict[str, Any]]):
    """Store entities with embeddings in ChromaDB"""
    
    collection = chroma_client.get_or_create_collection(
        name=COLLECTIONS["entities"],
        metadata={"description": "Context entities from multiple sources"}
    )
    
    # Process in batches
    batch_size = 50
    total_stored = 0
    
    for i in range(0, len(entities), batch_size):
        batch = entities[i:i + batch_size]
        
        ids = []
        documents = []
        metadatas = []
        embeddings = []
        
        for entity in batch:
            # Create searchable text from entity
            searchable_text = f"{entity.get('title', '')} {entity.get('content', '')}"[:8000]  # Limit text size
            
            # Generate embedding
            embedding = get_embedding(searchable_text)
            if not embedding:
                continue
            
            # Prepare metadata (ChromaDB only supports str, int, float, bool)
            metadata = {
                "source": entity.get("source", ""),
                "type": entity.get("type", ""),
                "title": entity.get("title", "")[:200],
                "author": entity.get("author", ""),
                "timestamp": entity.get("timestamp", ""),
                "incident_ref": entity.get("incident_ref", "") or "",
                "status": entity.get("status", "") or "",
                "priority": entity.get("priority", "") or "",
                "channel": entity.get("channel", "") or "",
            }
            
            ids.append(entity.get("id", ""))
            documents.append(searchable_text[:5000])  # Limit document size
            metadatas.append(metadata)
            embeddings.append(embedding)
        
        if ids:
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
            total_stored += len(ids)
            print(f"Stored batch {i // batch_size + 1}: {len(ids)} entities")
    
    print(f"Total entities stored: {total_stored}")
    return total_stored


def store_weekly_summaries_in_chromadb(summaries: List[Dict[str, Any]]):
    """Store weekly summaries with embeddings in ChromaDB"""
    
    collection = chroma_client.get_or_create_collection(
        name=COLLECTIONS["weekly_summaries"],
        metadata={"description": "Weekly summaries for search indexing"}
    )
    
    ids = []
    documents = []
    metadatas = []
    embeddings = []
    
    for summary in summaries:
        summary_text = summary.get("summary", "")
        
        # Generate embedding
        embedding = get_embedding(summary_text)
        if not embedding:
            continue
        
        metadata = {
            "week_key": summary.get("week_key", ""),
            "entity_count": summary.get("entity_count", 0),
            "sources": ",".join(summary.get("sources", [])),
            "incident_refs": ",".join(summary.get("incident_refs", [])),
        }
        
        ids.append(summary.get("id", ""))
        documents.append(summary_text)
        metadatas.append(metadata)
        embeddings.append(embedding)
    
    if ids:
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )
    
    print(f"Stored {len(ids)} weekly summaries")
    return len(ids)


# ============== MAIN INGESTION PIPELINE ==============
async def run_ingestion():
    """Main ingestion pipeline"""
    print("=" * 60)
    print("Context Intelligence Platform - Data Ingestion")
    print("=" * 60)
    
    all_entities = []
    
    # Process all data sources
    data_files = {
        "slack": os.path.join(DATA_DIR, "slack_data.json"),
        "docs": os.path.join(DATA_DIR, "docs_data.json"),
        "github": os.path.join(DATA_DIR, "github_data.json"),
        "jira": os.path.join(DATA_DIR, "jira_data.json"),
        "meetings": os.path.join(DATA_DIR, "meetings_data.json"),
    }
    
    processors = {
        "slack": process_slack_data,
        "docs": process_docs_data,
        "github": process_github_data,
        "jira": process_jira_data,
        "meetings": process_meetings_data,
    }
    
    print("\n[1/4] Processing data sources...")
    for source, file_path in data_files.items():
        if os.path.exists(file_path):
            print(f"\nProcessing {source}...")
            entities = processors[source](file_path)
            all_entities.extend(entities)
        else:
            print(f"Warning: {file_path} not found")
    
    print(f"\nTotal entities extracted: {len(all_entities)}")
    
    # Store entities in ChromaDB
    print("\n[2/4] Storing entities in ChromaDB...")
    entities_stored = store_entities_in_chromadb(all_entities)
    
    # Generate weekly summaries
    print("\n[3/4] Generating weekly summaries...")
    weekly_groups = group_entities_by_week(all_entities)
    print(f"Found {len(weekly_groups)} weeks of data")
    
    weekly_summaries = []
    for week_key, entities in sorted(weekly_groups.items()):
        print(f"Generating summary for {week_key} ({len(entities)} entities)...")
        summary = await generate_weekly_summary(week_key, entities)
        weekly_summaries.append(summary)
    
    # Store weekly summaries
    print("\n[4/4] Storing weekly summaries in ChromaDB...")
    summaries_stored = store_weekly_summaries_in_chromadb(weekly_summaries)
    
    # Print summary
    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"Entities processed: {len(all_entities)}")
    print(f"Entities stored in ChromaDB: {entities_stored}")
    print(f"Weekly summaries generated: {len(weekly_summaries)}")
    print(f"Weekly summaries stored: {summaries_stored}")
    print(f"\nChromaDB location: {CHROMA_PERSIST_DIR}")
    
    # Print weekly summary details
    print("\n--- Weekly Summaries ---")
    for summary in weekly_summaries:
        print(f"\n{summary['week_key']}:")
        print(f"  Entities: {summary['entity_count']}")
        print(f"  Sources: {summary['entities_by_source']}")
        if summary['incident_refs']:
            print(f"  Incidents: {summary['incident_refs']}")
    
    print("=" * 60)
    
    return {
        "entities_processed": len(all_entities),
        "entities_stored": entities_stored,
        "weekly_summaries": len(weekly_summaries),
        "summaries_stored": summaries_stored
    }


if __name__ == "__main__":
    asyncio.run(run_ingestion())

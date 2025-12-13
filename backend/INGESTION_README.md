# Context Intelligence Platform - Ingestion Layer

## Overview

This module provides the data ingestion foundation for the Context Intelligence Platform. It parses JSON data from multiple sources, generates embeddings, and stores everything in ChromaDB for vector search capabilities.

## Features

### 1. Multi-Source Data Ingestion
Supports 5 data sources:
- **Slack**: Threads with replies (each thread = 1 entity)
- **Docs**: Documentation (onboarding, architecture, postmortems, runbooks)
- **GitHub**: Pull requests with metadata
- **Jira**: Tickets (incidents, bugs, tasks, stories)
- **Meetings**: Standups and postmortems with transcripts

### 2. Entity Extraction
Each data source is parsed into a standardized entity structure with:
- Unique ID (source-prefixed)
- Title and content
- Author/assignee information
- Timestamps
- Cross-references (incident_ref, jira_ref, pr_ref)
- Source-specific metadata (labels, keywords, participants, etc.)

### 3. Vector Embeddings
- Uses **Sentence Transformers (all-MiniLM-L6-v2)** for local embedding generation
- No external API calls required for embeddings
- 384-dimensional vectors for efficient similarity search

### 4. Weekly Summaries
- Groups entities by week (ISO week format: YYYY-WNN)
- Generates AI-powered summaries using **OpenAI GPT-4o-mini** via Emergent LLM key
- Captures key themes, incidents, accomplishments, and participants
- Stored as separate search indices to boost search relevance

### 5. ChromaDB Storage
Two collections:
- `context_entities`: All 148 parsed entities with embeddings
- `weekly_summaries`: 9 weekly summary documents with embeddings

## File Structure

```
/app/backend/
├── data/                    # Input JSON files
│   ├── slack_data.json
│   ├── docs_data.json
│   ├── github_data.json
│   ├── jira_data.json
│   └── meetings_data.json
├── scripts/
│   ├── ingest.py           # Main ingestion script
│   └── search_test.py      # Search verification utility
├── chroma_db/              # ChromaDB persistent storage
└── .env                    # Environment variables
```

## Usage

### Run Ingestion
```bash
cd /app/backend
python scripts/ingest.py
```

### Test Search
```bash
cd /app/backend
python scripts/search_test.py
```

## Ingestion Results

| Metric | Count |
|--------|-------|
| Slack threads | 67 |
| Documents | 14 |
| GitHub PRs | 17 |
| Jira tickets | 36 |
| Meetings | 14 |
| **Total Entities** | **148** |
| Weekly Summaries | 9 |

## Entity Schema

```python
{
    "id": "source_unique_id",
    "source": "slack|docs|github|jira|meetings",
    "type": "conversation|document|pull_request|ticket|meeting",
    "title": "Entity title",
    "content": "Full searchable content",
    "author": "Author name",
    "timestamp": "ISO 8601 timestamp",
    "incident_ref": "INC001",  # Cross-reference
    # Source-specific fields...
}
```

## Dependencies

- `chromadb`: Vector database
- `sentence-transformers`: Local embeddings
- `emergentintegrations`: OpenAI integration via Emergent LLM key

## Next Steps

1. **MCP Layer**: Expose APIs for search and retrieval
2. **Application Layer**: Build UI for querying the intelligence platform
3. **Real-time Ingestion**: Add webhook support for live data updates
4. **Advanced Search**: Implement filters, facets, and semantic ranking

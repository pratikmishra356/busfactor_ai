from fastapi import FastAPI, APIRouter, Query, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
import uuid
from datetime import datetime, timezone

# Import MCP API functions
import sys
sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from mcp_api import (
    natural_search, 
    search_with_connections,
    get_entity_by_id,
    search_code_by_file_path,
    search_code_by_comment,
    search_code_by_query,
    SearchResponse,
    ConnectionGraph,
    SummarizedEntity,
    GraphNode,
    GraphEdge,
    EntityDetails,
    CodeAuditResponse,
    CodeAuditPR
)

# Import Application Layer functions
from app_layer import (
    generate_context,
    generate_incident_report,
    generate_role_task,
    ContextResponse,
    IncidentReport,
    RoleTaskResponse
)


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks


# ============== MCP API Endpoints ==============

@api_router.get("/mcp/search", response_model=SearchResponse)
async def mcp_search(
    q: str = Query(..., description="Natural language search query"),
    top_k: int = Query(default=3, ge=1, le=10, description="Number of summaries to return")
):
    """
    API 1: Natural search query -> summarized entities with sub-entity IDs
    
    Returns relevant weekly summaries with their constituent entity IDs.
    Each summarized entity contains:
    - Week key and summary text
    - List of sub-entity IDs that make up this summary
    - Sources covered (slack, jira, github, docs, meetings)
    """
    return natural_search(q, top_k=top_k)


@api_router.get("/mcp/connections", response_model=ConnectionGraph)
async def mcp_connections(
    q: str = Query(..., description="Natural language search query"),
    top_k: int = Query(default=2, ge=1, le=5, description="Number of summaries to use as roots"),
    depth: int = Query(default=1, ge=1, le=3, description="Graph traversal depth")
):
    """
    API 2: Natural search query -> bidirectional connection graph
    
    1. Fetches relevant summarized entities based on query
    2. Gets sub-entity IDs from those summaries  
    3. Queries connections for each sub-entity
    4. Builds bidirectional graph where:
       - e1 connects to s1
       - s1 also connects back to e1
    
    Returns nodes (entities) and edges (connections between them).
    """
    return search_with_connections(q, top_k=top_k, graph_depth=depth)


@api_router.get("/mcp/entity/{entity_id}", response_model=EntityDetails)
async def mcp_get_entity(entity_id: str):
    """
    API 3: Get entity details by ID
    
    Returns full entity details including:
    - Basic metadata (source, type, title, content, timestamp)
    - References (incident_ref, jira_ref, pr_ref)
    - All connections grouped by target source type
    
    Example entity_ids: jira_ENG-1, slack_T00001, github_pr_101, doc_DOC0003
    """
    entity = get_entity_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")
    return entity


# ============== Application Layer Endpoints ==============

@api_router.get("/context", response_model=ContextResponse)
async def get_context(
    query: str = Query(..., description="Natural language query to get context for"),
    top_k: int = Query(default=3, ge=1, le=5, description="Number of weekly summaries to analyze")
):
    """
    Use Case 1: Context Generation
    
    Generates comprehensive context for a natural language query by:
    1. Fetching relevant weekly summaries via vector search
    2. Getting detailed entity information
    3. Using LLM to synthesize a coherent context response
    
    Returns context that addresses the query with information from
    Slack, Jira, GitHub, Docs, and Meetings.
    """
    return await generate_context(query, top_k=top_k)


@api_router.get("/incident", response_model=IncidentReport)
async def get_incident_report(
    query: str = Query(..., description="Incident-related query for RCA generation")
):
    """
    Use Case 2: Incident Report / RCA
    
    Generates a Root Cause Analysis report by:
    1. Fetching relevant summaries and entity details
    2. Analyzing connections between entities
    3. Using LLM to generate comprehensive RCA
    
    Returns structured incident report with:
    - Executive summary
    - Timeline of events
    - Root cause analysis
    - Recommendations
    - Related tickets and PRs
    """
    return await generate_incident_report(query)


@api_router.get("/role/{role}/task", response_model=RoleTaskResponse)
async def get_role_task(
    role: Literal["engineer", "product_manager", "engineering_manager"] = "engineer",
    query: str = Query(..., description="Query for role-specific task generation")
):
    """
    Use Case 3: Role-Based Task Generation
    
    Generates role-specific responses:
    
    - **engineer**: Technical details, PRs, debugging info
    - **product_manager**: Feature progress, customer impact, roadmap
    - **engineering_manager**: Team health, incidents, process improvements
    
    Returns tailored response with:
    - Role-specific insights
    - Action items
    - Priority items
    - Relevant entities
    """
    if role not in ["engineer", "product_manager", "engineering_manager"]:
        raise HTTPException(status_code=400, detail="Invalid role. Use: engineer, product_manager, engineering_manager")
    
    return await generate_role_task(role, query)


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
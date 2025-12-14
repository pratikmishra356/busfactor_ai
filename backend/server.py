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

# Import Agents
from agents import (
    codehealth_agent,
    employee_agent,
    oncall_agent,
    document_agent,
    PRInput,
    CodeHealthResponse,
    RelatedPR,
    ChecklistItem,
    EmployeeInput,
    EmployeeResponse,
    OnCallInput,
    OnCallResponse,
    DocumentInput,
    DocumentResponse
)

# Import Dynamic Agents
from dynamic_agents import (
    create_agent,
    get_agent_by_name,
    list_all_agents,
    execute_dynamic_agent,
    DynamicAgentCreate,
    DynamicAgent,
    DynamicAgentExecuteInput,
    DynamicAgentResponse
)

# Emergent Google Auth helpers
from auth import (
    SessionExchangeInput,
    UserOut,
    clear_session_cookie,
    create_session,
    exchange_session,
    get_session_token_from_request,
    get_user_from_session,
    set_session_cookie,
    upsert_user,
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


# ============== Code Audit Endpoints ==============

@api_router.get("/code/audit", response_model=CodeAuditResponse)
async def code_audit(
    file_path: Optional[str] = Query(default=None, description="Search by file path (e.g., 'src/api/payments.py')"),
    comment: Optional[str] = Query(default=None, description="Search by comment content"),
    query: Optional[str] = Query(default=None, description="General search query for PRs"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of results to return")
):
    """
    Code Audit API - Search PRs by different criteria:
    
    1. **file_path**: Find PRs that modified a specific file
       - Example: `/api/code/audit?file_path=src/api/payments.py`
    
    2. **comment**: Find PRs with specific review comments  
       - Example: `/api/code/audit?comment=memory leak`
    
    3. **query**: General semantic search across PR descriptions
       - Example: `/api/code/audit?query=payment webhook retry`
    
    Only one parameter should be provided at a time.
    """
    if file_path:
        return search_code_by_file_path(file_path, n_results=limit)
    elif comment:
        return search_code_by_comment(comment, n_results=limit)
    elif query:
        return search_code_by_query(query, n_results=limit)
    else:
        raise HTTPException(
            status_code=400, 
            detail="One of 'file_path', 'comment', or 'query' parameter is required"
        )


# ============== Agent Endpoints ==============

@api_router.post("/agent/codehealth", response_model=CodeHealthResponse)
async def run_codehealth_agent(pr_input: PRInput):
    """
    CodeHealth Agent - Analyzes a PR and generates a review checklist.
    
    **Input**: PR JSON with:
    - pr_number, title, description, author
    - files_changed (list of file paths)
    - labels, jira_ref (optional)
    - comments (can be empty array)
    
    **Process**:
    1. Searches for semantically related PRs
    2. Finds PRs with overlapping file changes
    3. Collects review comments from related PRs
    4. Generates a comprehensive PR scan checklist using LLM
    
    **Output**:
    - Related PRs and file overlap PRs
    - Prioritized checklist items by category
    - Risk level assessment
    - Summary of potential issues
    
    **Example Request**:
    ```json
    {
        "pr_number": 200,
        "title": "feat: add payment retry",
        "description": "Implements retry for failed payments",
        "author": "developer",
        "files_changed": ["src/services/payment.py", "src/queues/retry.py"],
        "labels": ["feature", "payment"],
        "comments": []
    }
    ```
    """
    return await codehealth_agent(pr_input)


@api_router.post("/agent/employee", response_model=EmployeeResponse)
async def run_employee_agent(employee_input: EmployeeInput):
    """
    Employee Agent - Role-based task assistance.
    
    **Input**: 
    - role: "engineer" or "manager"
    - task: Task description/query string
    
    **For Engineer** (task_type detected automatically):
    - **create_pr**: Returns PR draft with title, description, files to modify, implementation steps
      - Triggers: "implement", "create pr", "fix", "build", "jira ticket"
    - **review_pr**: Returns review comments with severity levels
      - Triggers: "review", "check pr", "feedback on"
    - **general**: General engineering guidance
    
    **For Manager** (task_type detected automatically):
    - **send_message**: Returns Slack message draft with channel, recipients, message
      - Triggers: "send message", "notify", "slack", "inform team"
    - **status_update**: Returns status update with key points, blockers, next steps
      - Triggers: "status", "summary", "progress report"
    - **general**: General management guidance
    
    **Example Requests**:
    
    Engineer creating PR:
    ```json
    {"role": "engineer", "task": "implement payment retry mechanism for ENG-500"}
    ```
    
    Manager sending message:
    ```json
    {"role": "manager", "task": "send slack message to team about the payment bug fix"}
    ```
    """
    return await employee_agent(employee_input)


@api_router.post("/agent/oncall", response_model=OnCallResponse)
async def run_oncall_agent(oncall_input: OnCallInput):
    """
    OnCall Agent - Incident response assistance.
    
    **Input**:
    - alert_text: The alert/incident text (e.g., error messages, stack traces, alert details)
    - incident_id: Optional incident ID for tracking
    
    **Process**:
    1. Searches for related entities and summaries based on alert
    2. Finds related PRs that might have caused the issue
    3. Identifies suspect files from recent changes
    4. Generates root cause analysis using LLM
    5. Provides recommended actions and severity assessment
    
    **Output**:
    - alert_summary: Quick summary of findings
    - related_entities: Entities related to the alert
    - related_prs: Recent PRs that might be related
    - suspect_files: Files suspected to have caused the issue (with confidence levels)
    - root_cause_analysis: Detailed LLM-generated analysis
    - recommended_actions: Specific steps to take
    - severity: critical/high/medium/low
    - similar_incidents: Similar past incidents found
    
    **Example Request**:
    ```json
    {
        "alert_text": "PaymentService.process_payment failed with NullPointerException at line 245. Error rate: 15%. Users affected: 1,200",
        "incident_id": "INC-2024-001"
    }
    ```
    """
    return await oncall_agent(oncall_input)


@api_router.post("/agent/document", response_model=DocumentResponse)
async def run_document_agent(document_input: DocumentInput):
    """
    Document Agent - Writes documentation based on organizational context.
    
    **Input**:
    - query: Description of what document to write (e.g., "Write API documentation for payment retry system")
    
    **Process**:
    1. Understands the type of document needed (API doc, guide, runbook, technical doc, overview)
    2. Fetches related context from docs, PRs, Jira, messages, and meetings
    3. Generates a clean, professional document using LLM
    4. Returns polished documentation without reference clutter
    
    **Output**:
    - document_title: Generated title for the document
    - document_content: Complete markdown-formatted documentation
    - document_type: Type of document (api_doc, guide, runbook, technical, overview)
    - word_count: Total words in the document
    - sections_count: Number of major sections
    
    **Document Types Auto-Detected**:
    - **api_doc**: For API/endpoint/integration documentation
    - **guide**: For tutorials, how-to guides, setup instructions
    - **runbook**: For incident response, troubleshooting playbooks
    - **technical**: For architecture, design, implementation details
    - **overview**: For general explanations and feature descriptions
    
    **Example Requests**:
    ```json
    {"query": "Write API documentation for the payment retry system"}
    {"query": "Create a setup guide for new developers"}
    {"query": "Write a runbook for handling database connection failures"}
    {"query": "Document the authentication architecture"}
    ```
    
    **Note**: The output is a clean, publication-ready document without meta-commentary or source references.
    """
    return await document_agent(document_input)


# ============== Dynamic Agent Endpoints ==============

@api_router.post("/agents/create", response_model=DynamicAgent)
async def create_dynamic_agent(agent_input: DynamicAgentCreate):
    """
    Create Dynamic Agent - Build custom agents on the fly.
    
    **Input**:
    - name: Unique agent name (e.g., "payment-specialist", "onboarding-helper")
    - role: Agent's role/purpose (e.g., "Payment Systems Expert", "Onboarding Specialist")
    - prompt: System prompt/instructions for the agent
    
    **Storage**: Agent is stored in SQLite database (unique by name)
    
    **Example Request**:
    ```json
    {
        "name": "payment-specialist",
        "role": "Payment Systems Expert",
        "prompt": "You are an expert in payment systems. Help users understand payment issues, suggest solutions, and reference relevant PRs from the context."
    }
    ```
    
    **Returns**: Created agent with metadata
    
    **Error**: Returns 400 if agent with same name already exists
    """
    try:
        return create_agent(agent_input)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/agents/list", response_model=List[DynamicAgent])
async def list_dynamic_agents():
    """
    List All Dynamic Agents - Get all created agents.
    
    **Returns**: List of all agents with their:
    - name: Agent identifier
    - role: Agent's role/purpose
    - prompt: Agent's system instructions
    - created_at: Timestamp of creation
    
    **Example Response**:
    ```json
    [
        {
            "name": "payment-specialist",
            "role": "Payment Systems Expert",
            "prompt": "You are an expert in payment systems...",
            "created_at": "2024-01-15T10:30:00Z"
        }
    ]
    ```
    """
    return list_all_agents()


@api_router.post("/agents/execute", response_model=DynamicAgentResponse)
async def execute_agent(execute_input: DynamicAgentExecuteInput):
    """
    Execute Dynamic Agent - Run an agent with a user query.
    
    **Input**:
    - agent_name: Name of the agent to execute
    - query: User's query/task for the agent
    
    **Process**:
    1. Fetches agent definition from database
    2. Uses MCP to fetch relevant context:
       - Weekly summaries for high-level context
       - Entity metadata for detailed information
       - PR data for code/technical agents
    3. Calls LLM with:
       - Agent's role and prompt
       - Fetched organizational context
       - User's query
    4. Returns AI-generated response
    
    **Output**:
    - agent_name: Name of the agent executed
    - agent_role: Role of the agent
    - query: User's original query
    - context_fetched: Number of context items retrieved from MCP
    - response: AI-generated response based on context
    - execution_time: Time taken to execute (in seconds)
    
    **Example Request**:
    ```json
    {
        "agent_name": "payment-specialist",
        "query": "How do we handle payment retries in our system?"
    }
    ```
    
    **Example Response**:
    ```json
    {
        "agent_name": "payment-specialist",
        "agent_role": "Payment Systems Expert",
        "query": "How do we handle payment retries in our system?",
        "context_fetched": 12,
        "response": "Based on the context, our payment retry system uses exponential backoff...",
        "execution_time": 2.34
    }
    ```
    
    **Error**: Returns 404 if agent not found
    """
    try:
        return await execute_dynamic_agent(execute_input)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


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
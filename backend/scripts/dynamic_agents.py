"""
Dynamic Agent Builder - Create and execute custom agents on the fly.

This module allows users to create custom agents with specific roles and prompts,
store them in SQLite, and execute them with MCP context fetching.
"""

import os
import sqlite3
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Import MCP API functions
from mcp_api import (
    natural_search,
    search_code_by_query,
    get_entity_metadata,
    SummarizedEntity
)

load_dotenv()

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")

# Database path
SCRIPT_DIR = os.path.dirname(__file__)
DYNAMIC_AGENTS_DB_PATH = os.path.join(SCRIPT_DIR, "..", "dynamic_agents.db")


# ============== Pydantic Models ==============

class DynamicAgentCreate(BaseModel):
    """Input for creating a dynamic agent"""
    name: str  # Unique agent name
    role: str  # Agent's role/purpose
    prompt: str  # System prompt/instructions for the agent


class DynamicAgent(BaseModel):
    """Dynamic agent stored in database"""
    name: str
    role: str
    prompt: str
    created_at: str


class DynamicAgentExecuteInput(BaseModel):
    """Input for executing a dynamic agent"""
    agent_name: str
    query: str  # User's query/task for the agent


class RelatedContext(BaseModel):
    """Context item fetched from MCP"""
    type: str  # "summary", "pr", "entity"
    source: str  # "slack", "github", "jira", "docs", "meetings"
    title: str
    content: str
    relevance: float = 0.0


class DynamicAgentResponse(BaseModel):
    """Response from dynamic agent execution"""
    agent_name: str
    agent_role: str
    query: str
    context_fetched: int
    response: str
    execution_time: float


# ============== Database Functions ==============

def init_dynamic_agents_db():
    """Initialize SQLite database for dynamic agents"""
    conn = sqlite3.connect(DYNAMIC_AGENTS_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dynamic_agents (
            name TEXT PRIMARY KEY,
            role TEXT NOT NULL,
            prompt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()


def create_agent(agent_data: DynamicAgentCreate) -> DynamicAgent:
    """Create a new dynamic agent in the database"""
    init_dynamic_agents_db()
    
    conn = sqlite3.connect(DYNAMIC_AGENTS_DB_PATH)
    cursor = conn.cursor()
    
    created_at = datetime.now(timezone.utc).isoformat()
    
    try:
        cursor.execute('''
            INSERT INTO dynamic_agents (name, role, prompt, created_at)
            VALUES (?, ?, ?, ?)
        ''', (agent_data.name, agent_data.role, agent_data.prompt, created_at))
        
        conn.commit()
        
        return DynamicAgent(
            name=agent_data.name,
            role=agent_data.role,
            prompt=agent_data.prompt,
            created_at=created_at
        )
    except sqlite3.IntegrityError:
        raise ValueError(f"Agent with name '{agent_data.name}' already exists")
    finally:
        conn.close()


def get_agent_by_name(agent_name: str) -> Optional[DynamicAgent]:
    """Get agent by name from database"""
    init_dynamic_agents_db()
    
    conn = sqlite3.connect(DYNAMIC_AGENTS_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT name, role, prompt, created_at
        FROM dynamic_agents
        WHERE name = ?
    ''', (agent_name,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return DynamicAgent(
        name=row[0],
        role=row[1],
        prompt=row[2],
        created_at=row[3]
    )


def list_all_agents() -> List[DynamicAgent]:
    """List all dynamic agents"""
    init_dynamic_agents_db()
    
    conn = sqlite3.connect(DYNAMIC_AGENTS_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT name, role, prompt, created_at
        FROM dynamic_agents
        ORDER BY created_at DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        DynamicAgent(
            name=row[0],
            role=row[1],
            prompt=row[2],
            created_at=row[3]
        )
        for row in rows
    ]


# ============== Agent Execution Functions ==============

async def fetch_context_from_mcp(query: str, agent_role: str) -> List[RelatedContext]:
    """
    Fetch relevant context from MCP based on query and agent role.
    
    Strategy:
    1. Search weekly summaries for high-level context
    2. Search code PRs for technical details (if role involves code/engineering)
    3. Extract entity metadata for detailed context
    """
    context_items: List[RelatedContext] = []
    
    # Step 1: Search weekly summaries
    try:
        search_result = natural_search(query, top_k=3)
        
        for summary in search_result.results:
            context_items.append(RelatedContext(
                type="summary",
                source="mixed",
                title=f"Week {summary.week_key}",
                content=summary.summary_text,
                relevance=1.0 - (summary.distance / 2)  # Convert distance to relevance score
            ))
            
            # Get detailed entity metadata from sub-entities (top 5)
            for entity_id in summary.sub_entity_ids[:5]:
                entity_meta = get_entity_metadata(entity_id)
                if entity_meta:
                    context_items.append(RelatedContext(
                        type="entity",
                        source=entity_meta.get("source", ""),
                        title=entity_meta.get("title", "")[:150],
                        content=entity_meta.get("content", "")[:800],
                        relevance=0.8
                    ))
    except Exception as e:
        print(f"Error fetching summaries: {e}")
    
    # Step 2: Search code PRs if role involves engineering/code
    role_lower = agent_role.lower()
    if any(kw in role_lower for kw in ["engineer", "developer", "code", "technical", "sre", "devops"]):
        try:
            pr_results = search_code_by_query(query, n_results=5)
            
            for pr in pr_results.results[:3]:  # Top 3 PRs
                context_items.append(RelatedContext(
                    type="pr",
                    source="github",
                    title=f"PR #{pr.pr_number}: {pr.title}",
                    content=f"Author: {pr.author}\nFiles: {', '.join(pr.files_changed[:5])}\n\n{pr.matched_content[:500]}",
                    relevance=pr.match_score
                ))
        except Exception as e:
            print(f"Error fetching PRs: {e}")
    
    return context_items


def format_context_for_llm(context_items: List[RelatedContext]) -> str:
    """Format context items into a readable string for LLM"""
    if not context_items:
        return "No relevant context found in the knowledge base."
    
    context_text = "## Relevant Context from Knowledge Base\n\n"
    
    # Group by type
    summaries = [c for c in context_items if c.type == "summary"]
    entities = [c for c in context_items if c.type == "entity"]
    prs = [c for c in context_items if c.type == "pr"]
    
    if summaries:
        context_text += "### Weekly Summaries\n"
        for item in summaries[:2]:  # Top 2 summaries
            context_text += f"**{item.title}** (relevance: {item.relevance:.2f})\n"
            context_text += f"{item.content[:400]}\n\n"
    
    if entities:
        context_text += "### Related Entities\n"
        for item in entities[:8]:  # Top 8 entities
            context_text += f"**[{item.source}] {item.title}**\n"
            context_text += f"{item.content[:300]}\n\n"
    
    if prs:
        context_text += "### Related PRs\n"
        for item in prs:
            context_text += f"**{item.title}** (relevance: {item.relevance:.2f})\n"
            context_text += f"{item.content[:400]}\n\n"
    
    return context_text


async def call_llm_with_context(system_prompt: str, user_query: str, context: str, session_id: str) -> str:
    """Call LLM with agent's prompt, user query, and fetched context"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message=system_prompt
        ).with_model("openai", "gpt-4o-mini")
        
        # Build full user message with context
        full_message = f"""## User Query
{user_query}

{context}

Please respond to the user's query using the provided context and your expertise as defined by your role."""
        
        message = UserMessage(text=full_message)
        response = await chat.send_message(message)
        return response
    except Exception as e:
        return f"Error generating response: {str(e)}"


async def execute_dynamic_agent(execute_input: DynamicAgentExecuteInput) -> DynamicAgentResponse:
    """
    Execute a dynamic agent by:
    1. Fetching agent definition from database
    2. Fetching relevant context from MCP
    3. Calling LLM with agent's prompt + context + user query
    4. Returning the response
    """
    import time
    start_time = time.time()
    
    # Step 1: Fetch agent definition
    agent = get_agent_by_name(execute_input.agent_name)
    if not agent:
        raise ValueError(f"Agent '{execute_input.agent_name}' not found")
    
    # Step 2: Fetch context from MCP
    context_items = await fetch_context_from_mcp(execute_input.query, agent.role)
    
    # Step 3: Format context for LLM
    formatted_context = format_context_for_llm(context_items)
    
    # Step 4: Build system prompt
    system_prompt = f"""You are an AI agent with the following role: {agent.role}

Your specific instructions:
{agent.prompt}

Use the provided organizational context from the knowledge base to inform your response.
Be helpful, accurate, and actionable in your responses."""
    
    # Step 5: Call LLM
    response_text = await call_llm_with_context(
        system_prompt=system_prompt,
        user_query=execute_input.query,
        context=formatted_context,
        session_id=f"dynamic-agent-{execute_input.agent_name}"
    )
    
    execution_time = time.time() - start_time
    
    return DynamicAgentResponse(
        agent_name=agent.name,
        agent_role=agent.role,
        query=execute_input.query,
        context_fetched=len(context_items),
        response=response_text,
        execution_time=execution_time
    )


# ============== Demo ==============

async def demo():
    """Demo the dynamic agent builder"""
    print("=" * 70)
    print("Dynamic Agent Builder Demo")
    print("=" * 70)
    
    # Create a sample agent
    print("\n1. Creating a new agent...")
    agent_input = DynamicAgentCreate(
        name="payment-specialist",
        role="Payment Systems Expert",
        prompt="You are an expert in payment systems and transaction processing. Help users understand payment-related issues, suggest solutions, and provide best practices. Always reference relevant PRs and incidents from the context."
    )
    
    try:
        agent = create_agent(agent_input)
        print(f"✓ Created agent: {agent.name}")
        print(f"  Role: {agent.role}")
    except ValueError as e:
        print(f"  Agent already exists: {e}")
    
    # List all agents
    print("\n2. Listing all agents...")
    agents = list_all_agents()
    print(f"  Found {len(agents)} agent(s):")
    for ag in agents:
        print(f"    - {ag.name} ({ag.role})")
    
    # Execute the agent
    print("\n3. Executing agent...")
    execute_input = DynamicAgentExecuteInput(
        agent_name="payment-specialist",
        query="How do we handle payment retries?"
    )
    
    response = await execute_dynamic_agent(execute_input)
    print(f"✓ Agent executed in {response.execution_time:.2f}s")
    print(f"  Context fetched: {response.context_fetched} items")
    print(f"  Response preview: {response.response[:200]}...")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())

"""
Context Intelligence Platform - Application Layer
Provides high-level use case APIs that leverage the MCP layer for specific organizational needs.

Use Cases:
1. /context - Generate context for a natural language query
2. /incident - Generate RCA/incident report
3. /role/{role}/task - Role-based task generation
"""

import os
import asyncio
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Import MCP API functions
from mcp_api import (
    natural_search,
    search_with_connections,
    get_entity_metadata,
    SearchResponse,
    ConnectionGraph
)

load_dotenv()

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")


# ============== Pydantic Models ==============

class ContextResponse(BaseModel):
    """Response for context query"""
    query: str
    context: str
    sources_used: List[str]
    entity_count: int
    weeks_covered: List[str]


class IncidentReport(BaseModel):
    """RCA/Incident report response"""
    query: str
    report: str
    incident_summary: str
    root_cause: str
    timeline: List[Dict]
    affected_entities: List[Dict]
    recommendations: List[str]
    related_tickets: List[str]
    related_prs: List[str]


class RoleTaskResponse(BaseModel):
    """Role-based task response"""
    query: str
    role: str
    response: str
    action_items: List[str]
    relevant_entities: List[Dict]
    priority_items: List[str]


# ============== Helper Functions ==============

def get_entity_details(entity_ids: List[str], limit: int = 20) -> List[Dict]:
    """Get detailed metadata for a list of entity IDs"""
    details = []
    for entity_id in entity_ids[:limit]:
        metadata = get_entity_metadata(entity_id)
        if metadata:
            details.append(metadata)
    return details


def format_entities_for_prompt(entities: List[Dict]) -> str:
    """Format entity details for LLM prompt"""
    formatted = []
    for e in entities:
        formatted.append(f"[{e.get('source', 'unknown').upper()}] {e.get('title', 'No title')}\n  Preview: {e.get('preview', '')[:200]}")
    return "\n\n".join(formatted)


def format_connections_for_prompt(edges: List[Dict]) -> str:
    """Format connection edges for LLM prompt"""
    formatted = []
    for edge in edges:
        formatted.append(f"  {edge.get('source', '')} --[{edge.get('connection_type', '')}]--> {edge.get('target', '')}")
    return "\n".join(formatted)


async def call_llm(system_message: str, user_message: str, session_id: str = "app-layer") -> str:
    """Call LLM using Emergent integration"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message=system_message
        ).with_model("openai", "gpt-4o-mini")
        
        message = UserMessage(text=user_message)
        response = await chat.send_message(message)
        return response
    except Exception as e:
        return f"Error generating response: {str(e)}"


# ============== Use Case 1: Context Generation ==============

async def generate_context(query: str, top_k: int = 3) -> ContextResponse:
    """
    Generate context for a natural language query.
    
    1. Fetch summarized results using vector search
    2. Get entity details for sub-entities
    3. Use LLM to generate comprehensive context
    """
    # Step 1: Search for relevant summaries
    search_result = natural_search(query, top_k=top_k)
    
    # Step 2: Collect all sub-entity IDs and get their details
    all_entity_ids = []
    weeks_covered = []
    
    for summary in search_result.results:
        all_entity_ids.extend(summary.sub_entity_ids)
        weeks_covered.append(summary.week_key)
    
    # Get unique entity details
    unique_ids = list(dict.fromkeys(all_entity_ids))  # Preserve order, remove duplicates
    entity_details = get_entity_details(unique_ids, limit=25)
    
    # Group entities by source
    by_source = {}
    for e in entity_details:
        source = e.get('source', 'unknown')
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(e)
    
    # Step 3: Generate context using LLM
    system_message = """You are a context intelligence assistant. Your job is to provide comprehensive, 
well-organized context about organizational activities based on data from multiple sources 
(Slack conversations, Jira tickets, GitHub PRs, documentation, and meetings).

Provide clear, actionable context that helps users understand what happened, who was involved, 
and what the outcomes were. Be specific and reference actual entities when relevant."""

    # Build prompt with summaries and entity details
    summaries_text = "\n\n".join([
        f"**Week {s.week_key}**:\n{s.summary_text[:500]}..." 
        for s in search_result.results
    ])
    
    entities_text = format_entities_for_prompt(entity_details[:20])
    
    user_prompt = f"""Query: "{query}"

## Weekly Summaries
{summaries_text}

## Relevant Entities ({len(entity_details)} found)
{entities_text}

Based on the above information, provide a comprehensive context response that:
1. Directly addresses the query
2. Synthesizes information from multiple sources
3. Highlights key events, decisions, and outcomes
4. Mentions specific people, tickets, or PRs when relevant
5. Provides a timeline if applicable

Keep the response focused and well-structured."""

    context_response = await call_llm(system_message, user_prompt, f"context-{query[:20]}")
    
    return ContextResponse(
        query=query,
        context=context_response,
        sources_used=list(by_source.keys()),
        entity_count=len(entity_details),
        weeks_covered=weeks_covered
    )


# ============== Use Case 2: Incident Report / RCA ==============

async def generate_incident_report(query: str) -> IncidentReport:
    """
    Generate RCA (Root Cause Analysis) incident report.
    
    1. Fetch summarized results and entity details
    2. Fetch connections/relations between entities
    3. Use LLM to generate comprehensive RCA
    """
    # Step 1: Get summaries
    search_result = natural_search(query, top_k=2)
    
    # Step 2: Get connection graph
    graph = search_with_connections(query, top_k=2, graph_depth=1)
    
    # Step 3: Get entity details
    all_entity_ids = []
    for summary in search_result.results:
        all_entity_ids.extend(summary.sub_entity_ids)
    
    entity_details = get_entity_details(list(dict.fromkeys(all_entity_ids)), limit=30)
    
    # Categorize entities
    jira_tickets = [e for e in entity_details if e.get('source') == 'jira']
    github_prs = [e for e in entity_details if e.get('source') == 'github']
    slack_threads = [e for e in entity_details if e.get('source') == 'slack']
    docs = [e for e in entity_details if e.get('source') == 'docs']
    meetings = [e for e in entity_details if e.get('source') == 'meetings']
    
    # Format for prompt
    system_message = """You are an incident analysis expert. Your job is to generate comprehensive 
Root Cause Analysis (RCA) reports based on organizational data from multiple sources.

Your reports should follow standard RCA format:
1. Executive Summary
2. Incident Timeline
3. Root Cause Analysis
4. Impact Assessment
5. Resolution Steps Taken
6. Recommendations for Prevention

Be specific, technical where appropriate, and actionable."""

    entities_text = format_entities_for_prompt(entity_details[:25])
    connections_text = format_connections_for_prompt([e.model_dump() for e in graph.edges[:20]])
    
    user_prompt = f"""Incident Query: "{query}"

## Related Jira Tickets ({len(jira_tickets)})
{format_entities_for_prompt(jira_tickets[:5])}

## Related GitHub PRs ({len(github_prs)})
{format_entities_for_prompt(github_prs[:5])}

## Slack Discussions ({len(slack_threads)})
{format_entities_for_prompt(slack_threads[:5])}

## Documentation ({len(docs)})
{format_entities_for_prompt(docs[:3])}

## Meetings ({len(meetings)})
{format_entities_for_prompt(meetings[:3])}

## Entity Connections
{connections_text}

Based on the above information, generate a comprehensive RCA report with:
1. **Executive Summary**: Brief overview of the incident
2. **Timeline**: Sequence of events
3. **Root Cause**: What caused the incident
4. **Impact**: What was affected
5. **Resolution**: How it was fixed
6. **Recommendations**: How to prevent recurrence

Also extract:
- A one-line incident summary
- The primary root cause
- List of 3-5 actionable recommendations"""

    rca_response = await call_llm(system_message, user_prompt, f"incident-{query[:20]}")
    
    # Build timeline from entities
    timeline = []
    for e in entity_details:
        if e.get('timestamp'):
            timeline.append({
                "timestamp": e['timestamp'],
                "source": e['source'],
                "title": e['title'][:60],
                "entity_id": e['entity_id']
            })
    timeline.sort(key=lambda x: x.get('timestamp', ''))
    
    return IncidentReport(
        query=query,
        report=rca_response,
        incident_summary=f"Incident related to: {query}",
        root_cause="See detailed analysis in report",
        timeline=timeline[:10],
        affected_entities=[{"id": e['entity_id'], "source": e['source'], "title": e['title']} for e in entity_details[:10]],
        recommendations=["See detailed recommendations in report"],
        related_tickets=[e['entity_id'] for e in jira_tickets],
        related_prs=[e['entity_id'] for e in github_prs]
    )


# ============== Use Case 3: Role-Based Task Generation ==============

ROLE_PROMPTS = {
    "engineer": {
        "system": """You are an assistant helping software engineers. Focus on:
- Technical details and implementation specifics
- Code changes, PRs, and technical debt
- Debugging and troubleshooting information
- Action items related to coding, testing, and deployment
Be technical and specific. Reference specific PRs, commits, and technical decisions.""",
        "focus": ["github", "jira", "slack"]
    },
    "product_manager": {
        "system": """You are an assistant helping product managers. Focus on:
- Feature progress and roadmap updates
- Customer impact and user experience
- Stakeholder communication points
- Product decisions and trade-offs
- Timeline and milestone tracking
Be business-focused and highlight customer value and strategic implications.""",
        "focus": ["jira", "meetings", "docs"]
    },
    "engineering_manager": {
        "system": """You are an assistant helping engineering managers. Focus on:
- Team capacity and workload distribution
- Incident trends and system reliability
- Process improvements and team efficiency
- Cross-team dependencies and blockers
- Resource allocation and prioritization
Provide a leadership perspective with actionable management insights.""",
        "focus": ["jira", "meetings", "slack", "github"]
    }
}


async def generate_role_task(role: str, query: str) -> RoleTaskResponse:
    """
    Generate role-specific task response.
    
    Different roles get different perspectives:
    - Engineer: Technical details, PRs, debugging
    - Product Manager: Feature progress, customer impact
    - Engineering Manager: Team health, incidents, process
    """
    if role not in ROLE_PROMPTS:
        role = "engineer"  # Default
    
    role_config = ROLE_PROMPTS[role]
    
    # Get data
    search_result = natural_search(query, top_k=3)
    graph = search_with_connections(query, top_k=2, graph_depth=1)
    
    # Get entity details
    all_entity_ids = []
    for summary in search_result.results:
        all_entity_ids.extend(summary.sub_entity_ids)
    
    entity_details = get_entity_details(list(dict.fromkeys(all_entity_ids)), limit=30)
    
    # Filter entities by role's focus areas
    focused_entities = [e for e in entity_details if e.get('source') in role_config['focus']]
    if not focused_entities:
        focused_entities = entity_details[:15]
    
    # Build prompt
    system_message = role_config['system']
    
    entities_text = format_entities_for_prompt(focused_entities[:20])
    
    user_prompt = f"""Query: "{query}"
Role: {role.replace('_', ' ').title()}

## Relevant Information
{entities_text}

## Weekly Context
{search_result.results[0].summary_text[:600] if search_result.results else 'No summary available'}

Based on the above information and your role as a {role.replace('_', ' ')}, provide:

1. **Summary**: What's happening related to this query from your role's perspective
2. **Key Insights**: 3-5 insights relevant to your role
3. **Action Items**: Specific tasks you should take or delegate
4. **Priority Items**: What needs immediate attention
5. **Questions to Ask**: What you should clarify or follow up on

Be specific and actionable for someone in the {role.replace('_', ' ')} role."""

    response = await call_llm(system_message, user_prompt, f"role-{role}-{query[:15]}")
    
    # Extract priority items (simple heuristic - items with P1/critical/urgent)
    priority_items = []
    for e in focused_entities:
        title = e.get('title', '').lower()
        if any(p in title for p in ['p1', 'critical', 'urgent', 'incident', 'outage']):
            priority_items.append(e.get('title', ''))
    
    return RoleTaskResponse(
        query=query,
        role=role,
        response=response,
        action_items=["See detailed action items in response"],
        relevant_entities=[{"id": e['entity_id'], "source": e['source'], "title": e['title'][:60]} for e in focused_entities[:10]],
        priority_items=priority_items[:5] if priority_items else ["No critical items identified"]
    )


# ============== Demo ==============

async def demo():
    """Demo the application layer APIs"""
    print("=" * 70)
    print("Context Intelligence Platform - Application Layer Demo")
    print("=" * 70)
    
    # Use Case 1: Context
    print("\n--- Use Case 1: Context Generation ---")
    context = await generate_context("payment gateway issues")
    print(f"Query: {context.query}")
    print(f"Sources: {context.sources_used}")
    print(f"Entities: {context.entity_count}")
    print(f"Weeks: {context.weeks_covered}")
    print(f"\nContext:\n{context.context[:800]}...")
    
    # Use Case 2: Incident Report
    print("\n\n--- Use Case 2: Incident Report ---")
    incident = await generate_incident_report("payment outage")
    print(f"Query: {incident.query}")
    print(f"Related Tickets: {incident.related_tickets[:5]}")
    print(f"Related PRs: {incident.related_prs[:3]}")
    print(f"\nReport:\n{incident.report[:800]}...")
    
    # Use Case 3: Role-based
    print("\n\n--- Use Case 3: Role-Based (Engineer) ---")
    engineer_task = await generate_role_task("engineer", "database performance")
    print(f"Query: {engineer_task.query}")
    print(f"Role: {engineer_task.role}")
    print(f"Priority Items: {engineer_task.priority_items}")
    print(f"\nResponse:\n{engineer_task.response[:600]}...")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo())

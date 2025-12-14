"""
Context Intelligence Platform - Agents Layer
AI-powered agents that leverage the MCP layer for specific use cases.

Agents:
1. CodeHealth Agent - PR analysis with checklist generation
2. Employee Agent - Role-based intelligence (TODO)
3. OnCall Agent - Incident response assistance (TODO)
4. Document Agent - Documentation intelligence (TODO)
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Import MCP API functions
from mcp_api import (
    search_code_by_query,
    search_code_by_file_path,
    search_code_by_comment,
    natural_search,
    get_entity_metadata,
    get_entity_connections,
    CodeAuditResponse,
    CodeAuditPR
)

load_dotenv()

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")


# ============== Pydantic Models ==============

class PRInput(BaseModel):
    """Input PR for CodeHealth Agent"""
    pr_number: int
    title: str
    description: str
    author: str
    author_github: str = ""
    reviewer: str = ""
    branch: str = ""
    base_branch: str = "main"
    files_changed: List[str] = []
    labels: List[str] = []
    lines_added: int = 0
    lines_removed: int = 0
    jira_ref: str = ""
    comments: List[Dict[str, Any]] = []


class RelatedPR(BaseModel):
    """Related PR found during analysis"""
    pr_number: str
    title: str
    author: str
    match_type: str  # "semantic", "file_overlap"
    match_score: float
    overlapping_files: List[str] = []
    relevant_comments: List[str] = []


class ChecklistItem(BaseModel):
    """Individual checklist item"""
    category: str
    item: str
    priority: str  # "high", "medium", "low"
    source: str = ""  # Which PR comment inspired this


class CodeHealthResponse(BaseModel):
    """Response from CodeHealth Agent"""
    pr_number: int
    pr_title: str
    related_prs: List[RelatedPR]
    file_overlap_prs: List[RelatedPR]
    checklist: List[ChecklistItem]
    summary: str
    risk_level: str  # "low", "medium", "high"
    total_related_comments: int


# ============== Employee Agent Models ==============

class EmployeeInput(BaseModel):
    """Input for Employee Agent"""
    role: str  # "engineer" or "manager"
    task: str  # The task description/query


class PRDraft(BaseModel):
    """Draft PR response for engineer"""
    title: str
    description: str
    branch_name: str
    target_branch: str = "main"
    files_to_modify: List[str] = []
    implementation_steps: List[str] = []
    test_suggestions: List[str] = []
    estimated_complexity: str = ""  # "low", "medium", "high"


class ReviewComment(BaseModel):
    """Review comment for PR review task"""
    file_path: str = ""
    line_suggestion: str = ""
    comment: str
    severity: str = "info"  # "critical", "warning", "info", "praise"


class PRReviewResponse(BaseModel):
    """PR review response for engineer"""
    summary: str
    approval_status: str  # "approve", "request_changes", "comment"
    comments: List[ReviewComment]
    key_concerns: List[str] = []
    positive_aspects: List[str] = []


class SlackMessage(BaseModel):
    """Slack message draft for manager"""
    channel_suggestion: str
    recipients: List[str] = []
    subject: str
    message: str
    urgency: str = "normal"  # "urgent", "normal", "low"
    thread_context: str = ""


class StatusUpdate(BaseModel):
    """Status update for manager"""
    summary: str
    key_points: List[str]
    blockers: List[str] = []
    next_steps: List[str] = []
    stakeholders_to_notify: List[str] = []


class RelatedEntity(BaseModel):
    """Related entity found during task analysis"""
    entity_id: str
    source: str
    title: str
    relevance: str


class EmployeeResponse(BaseModel):
    """Response from Employee Agent"""
    role: str
    task: str
    task_type: str  # "create_pr", "review_pr", "send_message", "status_update", "general"
    related_entities: List[RelatedEntity]
    context_summary: str
    
    # Role-specific outputs (only one will be populated based on task_type)
    pr_draft: Optional[PRDraft] = None
    pr_review: Optional[PRReviewResponse] = None
    slack_message: Optional[SlackMessage] = None
    status_update: Optional[StatusUpdate] = None
    general_response: Optional[str] = None


# ============== Helper Functions ==============

async def call_llm(system_message: str, user_message: str, session_id: str = "agent") -> str:
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


def find_overlapping_files(pr_files: List[str], other_files: List[str]) -> List[str]:
    """Find files that overlap between two PRs"""
    pr_files_set = set(pr_files)
    other_files_set = set(other_files)
    
    # Exact matches
    exact_overlap = pr_files_set & other_files_set
    
    # Directory-level overlap (same directory)
    pr_dirs = set(["/".join(f.split("/")[:-1]) for f in pr_files if "/" in f])
    other_dirs = set(["/".join(f.split("/")[:-1]) for f in other_files if "/" in f])
    
    dir_overlap_files = []
    for other_file in other_files:
        if "/" in other_file:
            other_dir = "/".join(other_file.split("/")[:-1])
            if other_dir in pr_dirs and other_file not in exact_overlap:
                dir_overlap_files.append(other_file)
    
    return list(exact_overlap) + dir_overlap_files[:5]  # Limit directory overlaps


# ============== CodeHealth Agent ==============

async def codehealth_agent(pr_input: PRInput) -> CodeHealthResponse:
    """
    CodeHealth Agent - Analyzes a PR and generates a review checklist.
    
    Steps:
    1. Search for semantically related PRs using title/description
    2. Find PRs with overlapping file changes
    3. Collect comments from related PRs
    4. Generate a PR scan checklist using LLM
    """
    
    related_prs: List[RelatedPR] = []
    file_overlap_prs: List[RelatedPR] = []
    all_relevant_comments: List[str] = []
    
    # Step 1: Search for semantically related PRs
    search_query = f"{pr_input.title} {pr_input.description}"
    semantic_results = search_code_by_query(search_query, n_results=10)
    
    for pr in semantic_results.results:
        # Skip if it's the same PR
        if str(pr.pr_number) == str(pr_input.pr_number):
            continue
        
        related_prs.append(RelatedPR(
            pr_number=pr.pr_number,
            title=pr.title,
            author=pr.author,
            match_type="semantic",
            match_score=pr.match_score,
            overlapping_files=[],
            relevant_comments=[]
        ))
    
    # Step 2: Find PRs with overlapping file changes
    if pr_input.files_changed:
        seen_pr_numbers = set([rp.pr_number for rp in related_prs])
        
        for file_path in pr_input.files_changed[:5]:  # Check first 5 files
            file_results = search_code_by_file_path(file_path, n_results=5)
            
            for pr in file_results.results:
                if str(pr.pr_number) == str(pr_input.pr_number):
                    continue
                
                # Find actual overlapping files
                overlapping = find_overlapping_files(pr_input.files_changed, pr.files_changed)
                
                if overlapping and pr.pr_number not in seen_pr_numbers:
                    seen_pr_numbers.add(pr.pr_number)
                    file_overlap_prs.append(RelatedPR(
                        pr_number=pr.pr_number,
                        title=pr.title,
                        author=pr.author,
                        match_type="file_overlap",
                        match_score=pr.match_score,
                        overlapping_files=overlapping,
                        relevant_comments=[]
                    ))
    
    # Step 3: Collect comments from related PRs
    all_pr_numbers = [rp.pr_number for rp in related_prs + file_overlap_prs]
    
    for pr_number in all_pr_numbers[:10]:  # Limit to top 10 PRs
        # Search comments for this PR
        comment_results = search_code_by_comment(f"PR #{pr_number}", n_results=3)
        
        for result in comment_results.results:
            if result.pr_number == pr_number and result.matched_content:
                all_relevant_comments.append(result.matched_content)
    
    # Also search for comments related to the files being changed
    for file_path in pr_input.files_changed[:3]:
        file_comments = search_code_by_comment(file_path, n_results=3)
        for result in file_comments.results:
            if result.matched_content and result.matched_content not in all_relevant_comments:
                all_relevant_comments.append(result.matched_content)
    
    # Step 4: Generate checklist using LLM
    system_message = """You are a senior code reviewer assistant. Your job is to analyze a PR and generate a comprehensive review checklist based on:
1. The PR's title, description, and files changed
2. Comments and learnings from similar PRs in the codebase
3. Best practices for the type of changes being made

Generate a structured checklist with items categorized by type (Security, Performance, Code Quality, Testing, Documentation).
Each item should have a priority (high, medium, low) and be actionable.

Format your response as a JSON array of checklist items:
[
  {"category": "Security", "item": "Check for SQL injection in query parameters", "priority": "high", "source": "From PR #123 comments"},
  ...
]

Also provide:
- A brief summary of potential risks (1-2 sentences)
- An overall risk level: "low", "medium", or "high"
"""

    # Build context for LLM
    pr_context = f"""
## PR Under Review
- **PR #{pr_input.pr_number}**: {pr_input.title}
- **Author**: {pr_input.author}
- **Description**: {pr_input.description}
- **Files Changed** ({len(pr_input.files_changed)}): {', '.join(pr_input.files_changed[:10])}
- **Lines**: +{pr_input.lines_added} / -{pr_input.lines_removed}
- **Labels**: {', '.join(pr_input.labels) if pr_input.labels else 'None'}
- **Jira**: {pr_input.jira_ref or 'None'}

## Related PRs Found ({len(related_prs)})
"""
    for rp in related_prs[:5]:
        pr_context += f"- PR #{rp.pr_number}: {rp.title} (by {rp.author}, score: {rp.match_score:.2f})\n"
    
    pr_context += f"\n## PRs with Overlapping Files ({len(file_overlap_prs)})\n"
    for rp in file_overlap_prs[:5]:
        pr_context += f"- PR #{rp.pr_number}: {rp.title}\n  Overlapping files: {', '.join(rp.overlapping_files[:3])}\n"
    
    pr_context += f"\n## Comments from Related PRs ({len(all_relevant_comments)} found)\n"
    for i, comment in enumerate(all_relevant_comments[:8]):
        pr_context += f"\n### Comment {i+1}:\n{comment[:500]}...\n"

    user_prompt = f"""{pr_context}

Based on the above context, generate:
1. A JSON array of checklist items (at least 8-12 items covering different categories)
2. A risk summary
3. An overall risk level

Respond in this exact format:
CHECKLIST:
[json array here]

SUMMARY:
[1-2 sentence risk summary]

RISK_LEVEL:
[low/medium/high]
"""

    llm_response = await call_llm(system_message, user_prompt, f"codehealth-{pr_input.pr_number}")
    
    # Parse LLM response
    checklist_items: List[ChecklistItem] = []
    summary = "Unable to generate summary"
    risk_level = "medium"
    
    try:
        import json
        import re
        
        # Extract checklist JSON
        checklist_match = re.search(r'CHECKLIST:\s*(\[[\s\S]*?\])\s*(?:SUMMARY:|$)', llm_response)
        if checklist_match:
            checklist_json = checklist_match.group(1)
            checklist_data = json.loads(checklist_json)
            for item in checklist_data:
                checklist_items.append(ChecklistItem(
                    category=item.get("category", "General"),
                    item=item.get("item", ""),
                    priority=item.get("priority", "medium"),
                    source=item.get("source", "")
                ))
        
        # Extract summary
        summary_match = re.search(r'SUMMARY:\s*(.+?)(?:RISK_LEVEL:|$)', llm_response, re.DOTALL)
        if summary_match:
            summary = summary_match.group(1).strip()
        
        # Extract risk level
        risk_match = re.search(r'RISK_LEVEL:\s*(low|medium|high)', llm_response, re.IGNORECASE)
        if risk_match:
            risk_level = risk_match.group(1).lower()
            
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        # Fallback checklist
        checklist_items = [
            ChecklistItem(category="General", item="Review code changes for correctness", priority="high", source=""),
            ChecklistItem(category="Testing", item="Ensure adequate test coverage", priority="high", source=""),
            ChecklistItem(category="Security", item="Check for security vulnerabilities", priority="medium", source=""),
            ChecklistItem(category="Performance", item="Review for performance implications", priority="medium", source=""),
            ChecklistItem(category="Documentation", item="Update relevant documentation", priority="low", source=""),
        ]
        summary = f"PR #{pr_input.pr_number} modifies {len(pr_input.files_changed)} files. Manual review recommended."
    
    return CodeHealthResponse(
        pr_number=pr_input.pr_number,
        pr_title=pr_input.title,
        related_prs=related_prs[:5],
        file_overlap_prs=file_overlap_prs[:5],
        checklist=checklist_items,
        summary=summary,
        risk_level=risk_level,
        total_related_comments=len(all_relevant_comments)
    )


# ============== Employee Agent ==============

def detect_task_type(role: str, task: str) -> str:
    """Detect the type of task based on role and task description"""
    task_lower = task.lower()
    
    if role == "engineer":
        if any(kw in task_lower for kw in ["create pr", "implement", "build", "develop", "fix", "add feature", "write code", "jira", "ticket"]):
            return "create_pr"
        elif any(kw in task_lower for kw in ["review", "check pr", "look at pr", "feedback on"]):
            return "review_pr"
        else:
            return "general"
    
    elif role == "manager":
        if any(kw in task_lower for kw in ["send message", "notify", "communicate", "slack", "inform", "update team", "tell"]):
            return "send_message"
        elif any(kw in task_lower for kw in ["status", "summary", "report", "update on", "progress"]):
            return "status_update"
        else:
            return "general"
    
    return "general"


async def employee_agent(employee_input: EmployeeInput) -> EmployeeResponse:
    """
    Employee Agent - Role-based task assistance.
    
    For Engineer:
    - create_pr: Generate PR draft with implementation steps
    - review_pr: Generate review comments and feedback
    - general: General engineering guidance
    
    For Manager:
    - send_message: Draft Slack messages for team communication
    - status_update: Generate status updates for stakeholders
    - general: General management guidance
    """
    
    role = employee_input.role.lower()
    task = employee_input.task
    
    if role not in ["engineer", "manager"]:
        role = "engineer"  # Default
    
    # Detect task type
    task_type = detect_task_type(role, task)
    
    # Step 1: Fetch related entities/summaries based on task
    related_entities: List[RelatedEntity] = []
    context_data = []
    
    # Search weekly summaries for context
    search_result = natural_search(task, top_k=3)
    
    for summary in search_result.results:
        context_data.append({
            "type": "weekly_summary",
            "week": summary.week_key,
            "content": summary.summary_text[:500],
            "sources": summary.sources
        })
        
        # Get some entity details from sub-entities
        for entity_id in summary.sub_entity_ids[:5]:
            entity_meta = get_entity_metadata(entity_id)
            if entity_meta:
                related_entities.append(RelatedEntity(
                    entity_id=entity_id,
                    source=entity_meta.get("source", ""),
                    title=entity_meta.get("title", "")[:100],
                    relevance="from_summary"
                ))
    
    # Also search for related PRs if task involves code
    if role == "engineer" or "pr" in task.lower() or "code" in task.lower():
        pr_results = search_code_by_query(task, n_results=5)
        for pr in pr_results.results:
            related_entities.append(RelatedEntity(
                entity_id=f"github_pr_{pr.pr_number}",
                source="github",
                title=pr.title[:100],
                relevance="code_related"
            ))
            context_data.append({
                "type": "related_pr",
                "pr_number": pr.pr_number,
                "title": pr.title,
                "author": pr.author,
                "files": pr.files_changed[:5]
            })
    
    # Build context summary
    context_summary = f"Found {len(related_entities)} related entities and {len(context_data)} context items."
    
    # Step 2: Generate role-specific response using LLM
    response = EmployeeResponse(
        role=role,
        task=task,
        task_type=task_type,
        related_entities=related_entities[:10],
        context_summary=context_summary
    )
    
    if role == "engineer":
        if task_type == "create_pr":
            response.pr_draft = await _generate_pr_draft(task, context_data, related_entities)
        elif task_type == "review_pr":
            response.pr_review = await _generate_pr_review(task, context_data, related_entities)
        else:
            response.general_response = await _generate_engineer_response(task, context_data, related_entities)
    
    elif role == "manager":
        if task_type == "send_message":
            response.slack_message = await _generate_slack_message(task, context_data, related_entities)
        elif task_type == "status_update":
            response.status_update = await _generate_status_update(task, context_data, related_entities)
        else:
            response.general_response = await _generate_manager_response(task, context_data, related_entities)
    
    return response


async def _generate_pr_draft(task: str, context_data: List[Dict], related_entities: List[RelatedEntity]) -> PRDraft:
    """Generate a PR draft for engineer"""
    
    system_message = """You are a senior software engineer assistant. Generate a complete PR draft based on the task.
    
Output a JSON object with:
{
    "title": "PR title following conventional commits (feat:, fix:, etc.)",
    "description": "Detailed PR description with context, changes, and testing notes",
    "branch_name": "feature/descriptive-branch-name",
    "target_branch": "main",
    "files_to_modify": ["list", "of", "files"],
    "implementation_steps": ["Step 1: ...", "Step 2: ..."],
    "test_suggestions": ["Test case 1", "Test case 2"],
    "estimated_complexity": "low|medium|high"
}"""

    context_text = _format_context_for_llm(context_data, related_entities)
    
    prompt = f"""Task: {task}

{context_text}

Generate a comprehensive PR draft for this task. Consider similar PRs in the context when designing the solution."""

    llm_response = await call_llm(system_message, prompt, f"employee-engineer-pr")
    
    try:
        import json
        import re
        json_match = re.search(r'\{[\s\S]*\}', llm_response)
        if json_match:
            data = json.loads(json_match.group())
            return PRDraft(
                title=data.get("title", f"feat: {task[:50]}"),
                description=data.get("description", task),
                branch_name=data.get("branch_name", "feature/new-feature"),
                target_branch=data.get("target_branch", "main"),
                files_to_modify=data.get("files_to_modify", []),
                implementation_steps=data.get("implementation_steps", []),
                test_suggestions=data.get("test_suggestions", []),
                estimated_complexity=data.get("estimated_complexity", "medium")
            )
    except Exception as e:
        print(f"Error parsing PR draft: {e}")
    
    # Fallback
    return PRDraft(
        title=f"feat: {task[:50]}",
        description=task,
        branch_name="feature/new-feature",
        files_to_modify=[],
        implementation_steps=["Analyze requirements", "Implement changes", "Add tests", "Update documentation"],
        test_suggestions=["Unit tests for new functionality", "Integration tests"],
        estimated_complexity="medium"
    )


async def _generate_pr_review(task: str, context_data: List[Dict], related_entities: List[RelatedEntity]) -> PRReviewResponse:
    """Generate PR review comments for engineer"""
    
    system_message = """You are a senior code reviewer. Provide thorough PR review feedback.
    
Output a JSON object with:
{
    "summary": "Overall review summary",
    "approval_status": "approve|request_changes|comment",
    "comments": [
        {"file_path": "path/to/file.py", "line_suggestion": "around line X", "comment": "detailed comment", "severity": "critical|warning|info|praise"}
    ],
    "key_concerns": ["concern 1", "concern 2"],
    "positive_aspects": ["positive 1", "positive 2"]
}"""

    context_text = _format_context_for_llm(context_data, related_entities)
    
    prompt = f"""Review Task: {task}

{context_text}

Provide a thorough code review based on the task and related context from similar PRs."""

    llm_response = await call_llm(system_message, prompt, f"employee-engineer-review")
    
    try:
        import json
        import re
        json_match = re.search(r'\{[\s\S]*\}', llm_response)
        if json_match:
            data = json.loads(json_match.group())
            comments = []
            for c in data.get("comments", []):
                comments.append(ReviewComment(
                    file_path=c.get("file_path", ""),
                    line_suggestion=c.get("line_suggestion", ""),
                    comment=c.get("comment", ""),
                    severity=c.get("severity", "info")
                ))
            return PRReviewResponse(
                summary=data.get("summary", "Review completed"),
                approval_status=data.get("approval_status", "comment"),
                comments=comments,
                key_concerns=data.get("key_concerns", []),
                positive_aspects=data.get("positive_aspects", [])
            )
    except Exception as e:
        print(f"Error parsing PR review: {e}")
    
    return PRReviewResponse(
        summary="Unable to generate detailed review. Manual review recommended.",
        approval_status="comment",
        comments=[],
        key_concerns=["Manual review needed"],
        positive_aspects=[]
    )


async def _generate_slack_message(task: str, context_data: List[Dict], related_entities: List[RelatedEntity]) -> SlackMessage:
    """Generate Slack message draft for manager"""
    
    system_message = """You are a communication assistant for engineering managers. Draft professional Slack messages.
    
Output a JSON object with:
{
    "channel_suggestion": "#appropriate-channel",
    "recipients": ["@person1", "@person2"],
    "subject": "Brief subject/topic",
    "message": "The full message content with proper formatting",
    "urgency": "urgent|normal|low",
    "thread_context": "Any context about threading or follow-ups"
}"""

    context_text = _format_context_for_llm(context_data, related_entities)
    
    # Extract people from related entities
    people_mentioned = set()
    for entity in related_entities:
        if entity.source in ["slack", "jira", "github"]:
            people_mentioned.add(entity.title.split(":")[0] if ":" in entity.title else "")
    
    prompt = f"""Task: {task}

{context_text}

People/entities involved: {', '.join(list(people_mentioned)[:5]) if people_mentioned else 'Not specified'}

Draft an appropriate Slack message for this communication task."""

    llm_response = await call_llm(system_message, prompt, f"employee-manager-slack")
    
    try:
        import json
        import re
        json_match = re.search(r'\{[\s\S]*\}', llm_response)
        if json_match:
            data = json.loads(json_match.group())
            return SlackMessage(
                channel_suggestion=data.get("channel_suggestion", "#general"),
                recipients=data.get("recipients", []),
                subject=data.get("subject", "Update"),
                message=data.get("message", task),
                urgency=data.get("urgency", "normal"),
                thread_context=data.get("thread_context", "")
            )
    except Exception as e:
        print(f"Error parsing Slack message: {e}")
    
    return SlackMessage(
        channel_suggestion="#engineering",
        recipients=[],
        subject="Team Update",
        message=f"Regarding: {task}",
        urgency="normal"
    )


async def _generate_status_update(task: str, context_data: List[Dict], related_entities: List[RelatedEntity]) -> StatusUpdate:
    """Generate status update for manager"""
    
    system_message = """You are an assistant helping engineering managers create status updates.
    
Output a JSON object with:
{
    "summary": "Brief executive summary",
    "key_points": ["point 1", "point 2"],
    "blockers": ["blocker 1"],
    "next_steps": ["step 1", "step 2"],
    "stakeholders_to_notify": ["@stakeholder1"]
}"""

    context_text = _format_context_for_llm(context_data, related_entities)
    
    prompt = f"""Status Update Request: {task}

{context_text}

Generate a comprehensive status update based on the related context."""

    llm_response = await call_llm(system_message, prompt, f"employee-manager-status")
    
    try:
        import json
        import re
        json_match = re.search(r'\{[\s\S]*\}', llm_response)
        if json_match:
            data = json.loads(json_match.group())
            return StatusUpdate(
                summary=data.get("summary", "Status update"),
                key_points=data.get("key_points", []),
                blockers=data.get("blockers", []),
                next_steps=data.get("next_steps", []),
                stakeholders_to_notify=data.get("stakeholders_to_notify", [])
            )
    except Exception as e:
        print(f"Error parsing status update: {e}")
    
    return StatusUpdate(
        summary=f"Status update for: {task}",
        key_points=["Review related context for details"],
        blockers=[],
        next_steps=["Continue monitoring progress"]
    )


async def _generate_engineer_response(task: str, context_data: List[Dict], related_entities: List[RelatedEntity]) -> str:
    """Generate general response for engineer"""
    
    system_message = """You are a senior software engineer assistant. Provide helpful, technical guidance based on the organizational context."""
    
    context_text = _format_context_for_llm(context_data, related_entities)
    prompt = f"""Task/Question: {task}

{context_text}

Provide helpful guidance for this engineering task."""

    return await call_llm(system_message, prompt, f"employee-engineer-general")


async def _generate_manager_response(task: str, context_data: List[Dict], related_entities: List[RelatedEntity]) -> str:
    """Generate general response for manager"""
    
    system_message = """You are an assistant for engineering managers. Provide strategic, people-focused guidance based on the organizational context."""
    
    context_text = _format_context_for_llm(context_data, related_entities)
    prompt = f"""Task/Question: {task}

{context_text}

Provide helpful guidance for this management task."""

    return await call_llm(system_message, prompt, f"employee-manager-general")


# ============== Document Agent ==============

class DocumentInput(BaseModel):
    """Input for Document Agent"""
    query: str  # What document to write


class DocumentResponse(BaseModel):
    """Response from Document Agent"""
    document_title: str
    document_content: str
    document_type: str  # "technical", "overview", "guide", "api_doc", "runbook"
    word_count: int
    sections_count: int


async def document_agent(document_input: DocumentInput) -> DocumentResponse:
    """
    Document Agent - Writes documentation based on organizational context.
    
    Steps:
    1. Understand what document the user wants
    2. Fetch related entities (docs, PRs, Jira, messages) for context
    3. Generate a clean, professional document using LLM
    4. Return polished document without reference clutter
    """
    
    query = document_input.query
    
    # Step 1: Fetch related context from different sources
    related_entities: List[RelatedEntity] = []
    context_items = []
    
    # Search weekly summaries for high-level context
    search_result = natural_search(query, top_k=5)
    
    for summary in search_result.results:
        context_items.append({
            "type": "summary",
            "content": summary.summary_text,
            "sources": summary.sources
        })
        
        # Get entity details from sub-entities
        for entity_id in summary.sub_entity_ids[:10]:
            entity_meta = get_entity_metadata(entity_id)
            if entity_meta:
                source = entity_meta.get("source", "")
                
                # Add to context based on source type
                if source == "docs":
                    context_items.append({
                        "type": "existing_doc",
                        "title": entity_meta.get("title", ""),
                        "content": entity_meta.get("content_preview", "")[:800]
                    })
                elif source == "jira":
                    context_items.append({
                        "type": "jira",
                        "title": entity_meta.get("title", ""),
                        "content": entity_meta.get("content_preview", "")[:500]
                    })
                elif source == "slack" or source == "meetings":
                    context_items.append({
                        "type": "discussion",
                        "content": entity_meta.get("content_preview", "")[:400]
                    })
                
                related_entities.append(RelatedEntity(
                    entity_id=entity_id,
                    source=source,
                    title=entity_meta.get("title", "")[:100],
                    relevance="context"
                ))
    
    # Fetch relevant PRs for technical details
    pr_results = search_code_by_query(query, n_results=8)
    for pr in pr_results.results[:5]:
        if pr.match_score > 0.5:  # Only high-quality matches
            context_items.append({
                "type": "pr",
                "pr_number": pr.pr_number,
                "title": pr.title,
                "description": pr.matched_content[:600],
                "author": pr.author
            })
    
    # Step 2: Detect document type from query
    query_lower = query.lower()
    doc_type = "overview"
    
    if any(kw in query_lower for kw in ["api", "endpoint", "integration", "sdk"]):
        doc_type = "api_doc"
    elif any(kw in query_lower for kw in ["guide", "tutorial", "how to", "setup"]):
        doc_type = "guide"
    elif any(kw in query_lower for kw in ["runbook", "playbook", "incident", "troubleshoot"]):
        doc_type = "runbook"
    elif any(kw in query_lower for kw in ["technical", "architecture", "design", "implementation"]):
        doc_type = "technical"
    
    # Step 3: Generate clean documentation using LLM
    system_message = f"""You are a technical documentation expert. Your task is to write clear, professional documentation.

CRITICAL INSTRUCTIONS:
- Write a COMPLETE, POLISHED document ready for publication
- DO NOT include meta-commentary like "Based on the context..." or "According to PRs..."
- DO NOT list references, sources, or PR numbers in the document
- DO NOT show your research - only the final, clean documentation
- Use proper markdown formatting with clear sections
- Be concise but comprehensive
- Write as if you are the authoritative source, not a summarizer

Document Type: {doc_type}

Style Guidelines:
- {doc_type == 'api_doc' and 'Include endpoints, parameters, request/response examples, authentication'}
- {doc_type == 'guide' and 'Step-by-step instructions, prerequisites, examples, troubleshooting'}
- {doc_type == 'runbook' and 'Problem detection, diagnosis steps, resolution procedures, prevention'}
- {doc_type == 'technical' and 'Architecture overview, components, data flow, design decisions'}
- {doc_type == 'overview' and 'High-level explanation, purpose, key features, usage scenarios'}"""

    # Build context for LLM (internal use only)
    context_text = "## Background Context (For Your Understanding Only)\n\n"
    
    # Group context by type
    existing_docs = [c for c in context_items if c["type"] == "existing_doc"]
    prs = [c for c in context_items if c["type"] == "pr"]
    jiras = [c for c in context_items if c["type"] == "jira"]
    discussions = [c for c in context_items if c["type"] == "discussion"]
    
    if existing_docs:
        context_text += "### Existing Documentation\n"
        for doc in existing_docs[:3]:
            context_text += f"- {doc['title']}: {doc['content'][:300]}\n"
        context_text += "\n"
    
    if prs:
        context_text += "### Recent Implementation Details\n"
        for pr in prs[:4]:
            context_text += f"- PR #{pr['pr_number']}: {pr['title']}\n  {pr['description'][:250]}\n"
        context_text += "\n"
    
    if jiras:
        context_text += "### Related Requirements\n"
        for jira in jiras[:3]:
            context_text += f"- {jira['title']}: {jira['content'][:200]}\n"
        context_text += "\n"
    
    if discussions:
        context_text += "### Team Discussions\n"
        for disc in discussions[:3]:
            context_text += f"- {disc['content'][:200]}\n"
        context_text += "\n"
    
    prompt = f"""Write comprehensive documentation for: {query}

{context_text}

IMPORTANT: 
- Write the FINAL document directly - no preamble, no meta-text
- Start with the document title as # heading
- Do NOT mention sources, PRs, or where information came from
- Write authoritatively as the official documentation
- Be practical and actionable

Write the complete documentation now:"""

    llm_response = await call_llm(system_message, prompt, f"document-{query[:50]}")
    
    # Step 4: Parse and clean the response
    document_content = llm_response.strip()
    
    # Extract title from first heading or generate one
    import re
    title_match = re.search(r'^#\s+(.+)$', document_content, re.MULTILINE)
    if title_match:
        document_title = title_match.group(1).strip()
    else:
        document_title = query
        # Add title if missing
        document_content = f"# {document_title}\n\n{document_content}"
    
    # Count sections and words
    sections = len(re.findall(r'^#{1,3}\s+', document_content, re.MULTILINE))
    word_count = len(document_content.split())
    
    return DocumentResponse(
        document_title=document_title,
        document_content=document_content,
        document_type=doc_type,
        word_count=word_count,
        sections_count=sections
    )


def _format_context_for_llm(context_data: List[Dict], related_entities: List[RelatedEntity]) -> str:
    """Format context data for LLM prompt"""
    context_text = "## Relevant Context\n\n"
    
    for item in context_data[:5]:
        if item["type"] == "weekly_summary":
            context_text += f"**Week {item['week']}** (sources: {', '.join(item['sources'])})\n"
            context_text += f"{item['content'][:300]}...\n\n"
        elif item["type"] == "related_pr":
            context_text += f"**Related PR #{item['pr_number']}**: {item['title']}\n"
            context_text += f"  Author: {item['author']}, Files: {', '.join(item['files'][:3])}\n\n"
    
    if related_entities:
        context_text += "\n## Related Entities\n"
        for entity in related_entities[:8]:
            context_text += f"- [{entity.source}] {entity.title[:60]}\n"


# ============== OnCall Agent ==============

class OnCallInput(BaseModel):
    """Input for OnCall Agent"""
    alert_text: str  # The alert/incident text
    incident_id: str = ""  # Optional incident ID


class SuspectFile(BaseModel):
    """File suspected to have caused the issue"""
    file_path: str
    reason: str
    confidence: str  # "high", "medium", "low"
    related_pr: Optional[str] = None
    pr_title: Optional[str] = None


class OnCallResponse(BaseModel):
    """Response from OnCall Agent"""
    alert_summary: str
    related_entities: List[RelatedEntity]
    related_prs: List[RelatedPR]
    suspect_files: List[SuspectFile]
    root_cause_analysis: str
    recommended_actions: List[str]
    severity: str  # "critical", "high", "medium", "low"
    similar_incidents: List[str]


async def oncall_agent(oncall_input: OnCallInput) -> OnCallResponse:
    """
    OnCall Agent - Incident response assistance.
    
    Steps:
    1. Parse alert text and search for related entities/summaries
    2. Find related PRs that might have caused the issue
    3. Identify suspect files from recent changes
    4. Generate root cause analysis using LLM
    5. Provide recommended actions
    """
    
    alert_text = oncall_input.alert_text
    related_entities: List[RelatedEntity] = []
    related_prs: List[RelatedPR] = []
    suspect_files: List[SuspectFile] = []
    similar_incidents: List[str] = []
    
    # Step 1: Search for related entities and summaries
    search_result = natural_search(alert_text, top_k=5)
    
    for summary in search_result.results:
        # Get entity details from sub-entities
        for entity_id in summary.sub_entity_ids[:10]:
            entity_meta = get_entity_metadata(entity_id)
            if entity_meta:
                related_entities.append(RelatedEntity(
                    entity_id=entity_id,
                    source=entity_meta.get("source", ""),
                    title=entity_meta.get("title", "")[:100],
                    relevance="alert_related"
                ))
                
                # Check if it's a similar incident
                if entity_meta.get("source") == "meetings" and "incident" in entity_meta.get("title", "").lower():
                    similar_incidents.append(f"{entity_meta.get('title', '')}: {entity_meta.get('content_preview', '')[:100]}")
    
    # Step 2: Find related PRs using code audit
    pr_results = search_code_by_query(alert_text, n_results=10)
    
    # Also search for error messages or stack traces if present
    error_keywords = []
    for word in alert_text.lower().split():
        if any(kw in word for kw in ["error", "exception", "failed", "timeout", "null", "undefined"]):
            error_keywords.append(word)
    
    if error_keywords:
        for keyword in error_keywords[:3]:
            comment_results = search_code_by_comment(keyword, n_results=5)
            for pr in comment_results.results:
                if pr.pr_number not in [rp.pr_number for rp in related_prs]:
                    pr_results.results.append(pr)
    
    # Sort PRs by recency (most recent first)
    pr_results.results.sort(key=lambda pr: pr.timestamp, reverse=True)
    
    for pr in pr_results.results[:10]:
        # Extract files from PR - use files_changed if available, otherwise extract from title/content
        pr_files = pr.files_changed[:10] if pr.files_changed else []
        
        # If no files in metadata, try to extract file paths from title or matched content
        if not pr_files:
            import re
            # Look for common file patterns in title and matched content
            text_to_search = f"{pr.title} {pr.matched_content}"
            # Pattern: path/to/file.ext or just filename.ext
            file_patterns = re.findall(r'[\w/\-\.]+\.(?:py|js|jsx|ts|tsx|java|go|rb|yml|yaml|json|xml|sql|sh)', text_to_search)
            pr_files = list(set(file_patterns))[:5]  # Unique files, max 5
        
        related_prs.append(RelatedPR(
            pr_number=pr.pr_number,
            title=pr.title,
            author=pr.author,
            match_type="alert_related",
            match_score=pr.match_score,
            overlapping_files=pr_files,
            relevant_comments=[]
        ))
    
    # Filter PRs to only highly relevant ones - be very aggressive with filtering
    # Only keep PRs with match_score > 0.55 (good relevance threshold)
    filtered_prs = [pr for pr in related_prs if pr.match_score > 0.55]
    filtered_prs = sorted(filtered_prs, key=lambda pr: pr.match_score, reverse=True)[:3]
    
    # If no PRs meet threshold, take just the top 1 if it's above 0.4
    if not filtered_prs and related_prs:
        top_pr = max(related_prs, key=lambda pr: pr.match_score)
        if top_pr.match_score > 0.4:
            filtered_prs = [top_pr]
    
    # Step 3: Identify suspect files from the most relevant PRs
    file_frequency: Dict[str, List[str]] = {}  # file_path -> [pr_numbers]
    file_to_pr_info: Dict[str, tuple] = {}  # file_path -> (pr_number, pr_title, match_score)
    
    # Build suspect files from filtered PRs only
    for pr in filtered_prs:
        for file_path in pr.overlapping_files:
            if file_path not in file_frequency:
                file_frequency[file_path] = []
                file_to_pr_info[file_path] = (pr.pr_number, pr.title, pr.match_score)
            file_frequency[file_path].append(pr.pr_number)
    
    # Add files from the TOP PR (highest match score) even if they appear only once
    if filtered_prs:
        top_pr = filtered_prs[0]
        for file_path in top_pr.overlapping_files[:5]:  # Top 5 files from best PR
            if file_path not in file_frequency:
                file_frequency[file_path] = [top_pr.pr_number]
                file_to_pr_info[file_path] = (top_pr.pr_number, top_pr.title, top_pr.match_score)
    
    # Build suspect files list with proper confidence
    for file_path, pr_numbers in sorted(file_frequency.items(), key=lambda x: len(x[1]), reverse=True):
        pr_num, pr_title, match_score = file_to_pr_info.get(file_path, ("", "", 0))
        
        # Confidence based on both frequency and PR match score
        if len(pr_numbers) >= 3 or match_score > 0.8:
            confidence = "high"
        elif len(pr_numbers) == 2 or match_score > 0.6:
            confidence = "medium"
        else:
            confidence = "low"
        
        reason = f"Modified in PR(s): {', '.join([f'#{pn}' for pn in pr_numbers])}"
        if match_score > 0:
            reason += f" (match score: {match_score:.2f})"
        
        suspect_files.append(SuspectFile(
            file_path=file_path,
            reason=reason,
            confidence=confidence,
            related_pr=pr_num if pr_num else None,
            pr_title=pr_title if pr_title else None
        ))
    
    # Step 4: Generate root cause analysis using LLM
    system_message = """You are an experienced SRE/DevOps engineer analyzing production incidents.

CRITICAL INSTRUCTIONS:
- Be DEFINITIVE and CONFIDENT in your analysis (avoid words like "likely", "might", "possibly", "could be")
- State findings as facts based on the evidence
- Reference specific files and PRs with certainty
- Be direct and actionable
- Do NOT mention severity in the root cause section - it will be handled separately"""

    context_text = f"""## Alert/Incident
{alert_text}

## Highly Relevant PRs (Match Score > 0.6)
"""
    
    # Show all filtered PRs (max 3)
    for pr in filtered_prs:
        context_text += f"\n**PR #{pr.pr_number}**: {pr.title} (Score: {pr.match_score:.2f})\n"
        context_text += f"  - Author: {pr.author}\n"
        context_text += f"  - Key Files: {', '.join(pr.overlapping_files[:4])}\n"
    
    if not filtered_prs:
        context_text += "\nNo PRs found with high confidence match.\n"
    
    context_text += "\n## Suspect Files (Ordered by Confidence)\n"
    if suspect_files:
        for sf in suspect_files[:5]:
            context_text += f"- `{sf.file_path}` [{sf.confidence} confidence] - {sf.reason}\n"
    else:
        context_text += "No specific suspect files identified. Focus on general system health.\n"
    
    if similar_incidents:
        context_text += "\n## Similar Past Incidents\n"
        for incident in similar_incidents[:2]:
            context_text += f"- {incident}\n"
    
    prompt = f"""{context_text}

Provide a definitive incident analysis in this EXACT format:

ROOT CAUSE:
[State the root cause with certainty. Reference specific files/PRs. Be direct - this IS what caused it, not what "might have" caused it.]

IMMEDIATE ACTIONS:
1. [First action - be specific about file/service]
2. [Second action - include exact commands or steps if applicable]
3. [Third action]
4. [Fourth action if needed]

PREVENTION:
[2-3 sentences on how to prevent this. Reference specific improvements to code/infrastructure.]

Do NOT include severity assessment in your response."""

    llm_response = await call_llm(system_message, prompt, f"oncall-{oncall_input.incident_id or 'alert'}")
    
    # Parse LLM response
    root_cause_analysis = llm_response
    recommended_actions = []
    
    try:
        import re
        
        # Extract recommended actions
        actions_match = re.search(r'IMMEDIATE ACTIONS?:(.+?)(?:PREVENTION:|$)', llm_response, re.DOTALL | re.IGNORECASE)
        if actions_match:
            actions_text = actions_match.group(1)
            # Extract bullet points or numbered items
            actions = re.findall(r'(?:[-*•]|\d+\.)\s*(.+)', actions_text)
            recommended_actions = [action.strip() for action in actions if action.strip()][:6]
        
        if not recommended_actions:
            recommended_actions = [
                "Review the suspect files identified above",
                "Check application logs for stack traces",
                "Verify database connection pool settings",
                "Monitor error rates and system metrics"
            ]
            
    except Exception as e:
        print(f"Error parsing oncall response: {e}")
        recommended_actions = [
            "Review the suspect files identified above",
            "Check application logs for detailed error information",
            "Monitor system metrics"
        ]
    
    # Determine severity based on error rate and keywords in alert
    severity = "medium"  # default
    alert_lower = alert_text.lower()
    
    # Critical indicators
    if any(kw in alert_lower for kw in ["critical", "down", "outage", "crash", "cannot connect", "total failure", "100%"]):
        severity = "critical"
    # High severity indicators
    elif any(kw in alert_lower for kw in ["high error rate", "timeout", "degraded", "50%", "60%", "70%", "80%", "90%"]):
        severity = "high"
    # Medium severity indicators  
    elif any(kw in alert_lower for kw in ["error", "exception", "failed", "warning", "15%", "20%", "30%", "40%"]):
        severity = "medium"
    # Low severity
    else:
        severity = "low"
    
    # If no suspect files were found but we have PRs, extract file mentions from alert and LLM response
    if not suspect_files and filtered_prs:
        import re
        # Extract file paths from alert text
        alert_files = re.findall(r'[\w/\-\.]+\.(?:py|js|jsx|ts|tsx|java|go|rb|yml|yaml|json|xml|sql|sh|conf|config)', alert_text)
        
        for file_path in alert_files[:3]:
            suspect_files.append(SuspectFile(
                file_path=file_path,
                reason=f"Mentioned in alert - {filtered_prs[0].title}" if filtered_prs else "Mentioned in alert",
                confidence="medium",
                related_pr=filtered_prs[0].pr_number if filtered_prs else None,
                pr_title=filtered_prs[0].title if filtered_prs else None
            ))
    
    # Generate alert summary with accurate counts
    num_suspect = min(len(suspect_files), 5)  # We'll return max 5
    num_prs = len(filtered_prs)  # Actual PRs we're returning
    
    if num_suspect > 0 and num_prs > 0:
        alert_summary = f"Analysis complete. Identified {num_suspect} suspect file(s) across {num_prs} relevant PR(s)."
    elif num_prs > 0:
        alert_summary = f"Analysis complete. Found {num_prs} relevant PR(s)."
    else:
        alert_summary = f"Analysis complete. Limited historical data available for this alert type."
    
    return OnCallResponse(
        alert_summary=alert_summary,
        related_entities=related_entities[:10],
        related_prs=filtered_prs,  # Return only filtered PRs (max 3)
        suspect_files=suspect_files[:5],  # Top 5 suspect files
        root_cause_analysis=root_cause_analysis,
        recommended_actions=recommended_actions,
        severity=severity,
        similar_incidents=similar_incidents[:2]  # Limit to 2 most relevant
    )
    
    return context_text


# ============== Demo ==============

async def demo():
    """Demo the CodeHealth Agent"""
    print("=" * 70)
    print("Context Intelligence Platform - CodeHealth Agent Demo")
    print("=" * 70)
    
    # Sample PR input
    sample_pr = PRInput(
        pr_number=999,
        title="feat: add payment retry mechanism",
        description="Implements automatic retry for failed payment transactions with exponential backoff",
        author="Test Developer",
        author_github="testdev",
        files_changed=[
            "src/services/payment_service.py",
            "src/queues/retry_queue.py",
            "src/config/payment_config.py",
            "tests/test_payment_retry.py"
        ],
        labels=["feature", "payment"],
        lines_added=250,
        lines_removed=30,
        jira_ref="ENG-500",
        comments=[]
    )
    
    print(f"\nAnalyzing PR #{sample_pr.pr_number}: {sample_pr.title}")
    print("-" * 50)
    
    result = await codehealth_agent(sample_pr)
    
    print(f"\n✓ Risk Level: {result.risk_level.upper()}")
    print(f"✓ Summary: {result.summary}")
    print(f"✓ Related PRs found: {len(result.related_prs)}")
    print(f"✓ File overlap PRs: {len(result.file_overlap_prs)}")
    print(f"✓ Comments analyzed: {result.total_related_comments}")
    
    print("\n--- Checklist ---")
    for item in result.checklist:
        print(f"  [{item.priority.upper()}] [{item.category}] {item.item}")
        if item.source:
            print(f"         Source: {item.source}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo())

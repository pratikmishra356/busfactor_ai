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

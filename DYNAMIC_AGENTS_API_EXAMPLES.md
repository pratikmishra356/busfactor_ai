# Dynamic Agent Builder - API Examples

Complete guide with real examples for testing the Dynamic Agent Builder API.

## Quick Start

All examples use the production API URL. Replace `$API_URL` with your actual URL:

```bash
export API_URL="https://your-domain.com"
```

---

## 1. Create Agents

### Example 1: Code Reviewer Agent
```bash
curl -X POST "$API_URL/api/agents/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "code-reviewer",
    "role": "Senior Code Reviewer",
    "prompt": "You are a senior code reviewer with expertise in security, performance, and best practices. When analyzing code or PRs, provide specific, actionable feedback. Reference relevant past PRs and incidents from the context to support your recommendations."
  }'
```

**Response:**
```json
{
  "name": "code-reviewer",
  "role": "Senior Code Reviewer",
  "prompt": "You are a senior code reviewer...",
  "created_at": "2024-01-15T10:30:00+00:00"
}
```

### Example 2: Payment Specialist Agent
```bash
curl -X POST "$API_URL/api/agents/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "payment-specialist",
    "role": "Payment Systems Expert",
    "prompt": "You are an expert in payment systems and transaction processing. Help users understand payment-related issues, suggest solutions based on past PRs and incidents, and provide best practices for handling payment failures and retries."
  }'
```

### Example 3: Incident Responder Agent
```bash
curl -X POST "$API_URL/api/agents/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "incident-responder",
    "role": "SRE Incident Response Specialist",
    "prompt": "You are an expert SRE focused on incident response. Analyze alerts, identify root causes from past incidents and PRs, suggest immediate actions, and provide prevention strategies."
  }'
```

### Example 4: Onboarding Helper Agent
```bash
curl -X POST "$API_URL/api/agents/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "onboarding-helper",
    "role": "Developer Onboarding Specialist",
    "prompt": "You help new developers get up to speed. Explain system architecture, point to relevant documentation and PRs, and provide setup guidance based on organizational context."
  }'
```

### Example 5: Database Expert Agent
```bash
curl -X POST "$API_URL/api/agents/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "database-expert",
    "role": "Database Performance Specialist",
    "prompt": "You are a database optimization expert. Analyze query performance issues, suggest indexing strategies, and provide migration guidance. Use past incidents and PRs to inform your recommendations."
  }'
```

---

## 2. List All Agents

```bash
curl -X GET "$API_URL/api/agents/list"
```

**Response:**
```json
[
  {
    "name": "code-reviewer",
    "role": "Senior Code Reviewer",
    "prompt": "You are a senior code reviewer...",
    "created_at": "2024-01-15T10:30:00+00:00"
  },
  {
    "name": "payment-specialist",
    "role": "Payment Systems Expert",
    "prompt": "You are an expert in payment systems...",
    "created_at": "2024-01-15T10:31:00+00:00"
  }
]
```

### Pretty Print with jq
```bash
curl -s -X GET "$API_URL/api/agents/list" | jq '.'
```

### Count Agents
```bash
curl -s -X GET "$API_URL/api/agents/list" | jq 'length'
```

### List Agent Names Only
```bash
curl -s -X GET "$API_URL/api/agents/list" | jq -r '.[].name'
```

---

## 3. Execute Agents

### Code Reviewer Examples

**Query 1: General Code Review Guidance**
```bash
curl -X POST "$API_URL/api/agents/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "code-reviewer",
    "query": "What should I look for when reviewing authentication code?"
  }'
```

**Query 2: Error Handling Review**
```bash
curl -X POST "$API_URL/api/agents/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "code-reviewer",
    "query": "What are the best practices for error handling in APIs?"
  }'
```

**Query 3: Security Review**
```bash
curl -X POST "$API_URL/api/agents/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "code-reviewer",
    "query": "Review this SQL query for security vulnerabilities: SELECT * FROM users WHERE email = '\''$email'\''"
  }'
```

### Payment Specialist Examples

**Query 1: Payment Retries**
```bash
curl -X POST "$API_URL/api/agents/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "payment-specialist",
    "query": "How should we handle payment retries?"
  }'
```

**Query 2: Webhook Implementation**
```bash
curl -X POST "$API_URL/api/agents/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "payment-specialist",
    "query": "What should I consider when implementing payment webhooks?"
  }'
```

**Query 3: Idempotency**
```bash
curl -X POST "$API_URL/api/agents/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "payment-specialist",
    "query": "How do we ensure payment idempotency in our system?"
  }'
```

### Incident Responder Examples

**Query 1: API Error Investigation**
```bash
curl -X POST "$API_URL/api/agents/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "incident-responder",
    "query": "API error rate is at 15%. How should I investigate?"
  }'
```

**Query 2: Database Connection Issues**
```bash
curl -X POST "$API_URL/api/agents/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "incident-responder",
    "query": "We are seeing database connection timeouts. What could be causing this?"
  }'
```

**Query 3: Memory Leak Analysis**
```bash
curl -X POST "$API_URL/api/agents/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "incident-responder",
    "query": "Memory usage is growing continuously. How do I debug this?"
  }'
```

### Onboarding Helper Examples

**Query 1: System Architecture**
```bash
curl -X POST "$API_URL/api/agents/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "onboarding-helper",
    "query": "Can you explain our payment service architecture?"
  }'
```

**Query 2: Local Setup**
```bash
curl -X POST "$API_URL/api/agents/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "onboarding-helper",
    "query": "How do I set up the development environment locally?"
  }'
```

**Query 3: Testing Guidelines**
```bash
curl -X POST "$API_URL/api/agents/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "onboarding-helper",
    "query": "What are our testing best practices?"
  }'
```

---

## Response Format

All execute responses follow this format:

```json
{
  "agent_name": "code-reviewer",
  "agent_role": "Senior Code Reviewer",
  "query": "What should I look for when reviewing authentication code?",
  "context_fetched": 21,
  "response": "When reviewing authentication code, there are several critical aspects to consider...",
  "execution_time": 8.5
}
```

### Fields Explained

- **agent_name**: Name of the executed agent
- **agent_role**: Role/purpose of the agent
- **query**: Original user query
- **context_fetched**: Number of context items retrieved from MCP
- **response**: AI-generated response (can be long)
- **execution_time**: Time taken in seconds

---

## Error Handling

### Error 1: Agent Already Exists (400)
```bash
curl -X POST "$API_URL/api/agents/create" \
  -H "Content-Type: application/json" \
  -d '{"name": "code-reviewer", "role": "Test", "prompt": "Test"}'
```

**Response:**
```json
{
  "detail": "Agent with name 'code-reviewer' already exists"
}
```

### Error 2: Agent Not Found (404)
```bash
curl -X POST "$API_URL/api/agents/execute" \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "non-existent", "query": "test"}'
```

**Response:**
```json
{
  "detail": "Agent 'non-existent' not found"
}
```

---

## Advanced Usage

### Parsing Response with Python
```bash
curl -s -X POST "$API_URL/api/agents/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "code-reviewer",
    "query": "Best practices for error handling"
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Agent: {data[\"agent_name\"]}')
print(f'Context: {data[\"context_fetched\"]} items')
print(f'Time: {data[\"execution_time\"]:.2f}s')
print(f'Response:\n{data[\"response\"][:300]}...')
"
```

### Save Response to File
```bash
curl -s -X POST "$API_URL/api/agents/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "code-reviewer",
    "query": "What are the best practices for API design?"
  }' | jq -r '.response' > agent_response.txt
```

### Batch Execute Multiple Queries
```bash
#!/bin/bash

QUERIES=(
  "How do we handle authentication?"
  "What are our deployment practices?"
  "How do we monitor production?"
)

for query in "${QUERIES[@]}"; do
  echo "Query: $query"
  curl -s -X POST "$API_URL/api/agents/execute" \
    -H "Content-Type: application/json" \
    -d "{\"agent_name\": \"onboarding-helper\", \"query\": \"$query\"}" | \
    jq -r '.response' | head -3
  echo "---"
done
```

### Check Agent Execution Time
```bash
curl -s -X POST "$API_URL/api/agents/execute" \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "payment-specialist", "query": "Payment retry strategies"}' | \
  jq -r '"Execution time: \(.execution_time)s | Context: \(.context_fetched) items"'
```

---

## Integration Examples

### JavaScript/TypeScript
```typescript
async function executeAgent(agentName: string, query: string) {
  const response = await fetch(`${API_URL}/api/agents/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_name: agentName, query })
  });
  
  return await response.json();
}

// Usage
const result = await executeAgent('code-reviewer', 'Review my auth code');
console.log(result.response);
```

### Python
```python
import requests

def execute_agent(agent_name: str, query: str):
    response = requests.post(
        f"{API_URL}/api/agents/execute",
        json={"agent_name": agent_name, "query": query}
    )
    return response.json()

# Usage
result = execute_agent('payment-specialist', 'How to handle refunds?')
print(result['response'])
```

### cURL Script
```bash
#!/bin/bash

AGENT_NAME="$1"
QUERY="$2"

if [ -z "$AGENT_NAME" ] || [ -z "$QUERY" ]; then
  echo "Usage: $0 <agent_name> <query>"
  exit 1
fi

curl -s -X POST "$API_URL/api/agents/execute" \
  -H "Content-Type: application/json" \
  -d "{\"agent_name\": \"$AGENT_NAME\", \"query\": \"$QUERY\"}" | \
  jq -r '.response'
```

Save as `ask-agent.sh` and use:
```bash
./ask-agent.sh code-reviewer "What are best practices for caching?"
```

---

## Performance Tips

1. **Specific Queries**: More specific queries = better context = faster responses
   - ✅ "How do we handle payment retries in checkout service?"
   - ❌ "Tell me about payments"

2. **Agent Specialization**: Use specialized agents for better results
   - Use `payment-specialist` for payment questions
   - Use `code-reviewer` for code quality
   - Use `incident-responder` for debugging

3. **Context Awareness**: Agents fetch 12-21 context items typically
   - More context = better answers but slower execution
   - Average execution: 5-10 seconds

4. **Caching**: Consider caching frequently asked questions on your side

---

## Testing Checklist

✅ Create multiple specialized agents  
✅ List all agents successfully  
✅ Execute agents with various queries  
✅ Verify context is fetched from MCP  
✅ Check error handling (duplicate names, non-existent agents)  
✅ Measure execution time  
✅ Verify response quality  

---

## Troubleshooting

### Slow Execution
- Normal: 5-15 seconds
- Check: MCP database size, network latency
- Solution: Use more specific queries

### Poor Response Quality
- Check: Agent prompt is specific enough
- Check: Relevant data exists in MCP
- Solution: Improve agent prompt or add more context to query

### Agent Not Found
- Verify: Agent name is case-sensitive
- List: Use `/api/agents/list` to verify name

---

## Support

For issues or questions:
- Check logs: `/var/log/supervisor/backend.*.log`
- Database: `/app/backend/dynamic_agents.db`
- Documentation: `/app/DYNAMIC_AGENTS_README.md`

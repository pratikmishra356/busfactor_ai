# Dynamic Agent Builder UI - User Guide

## Overview

The Dynamic Agent Builder UI allows you to create, manage, and interact with custom AI agents directly from your browser. Each agent leverages your organization's knowledge base through MCP (Micro-services Context Platform) to provide context-aware responses.

---

## Features

✨ **Create Custom Agents** - Define agents with unique roles and prompts  
💬 **Interactive Chat** - Real-time conversations with your agents  
📊 **Context Display** - See how many context items were fetched (PRs, docs, messages)  
⚡ **Performance Metrics** - View execution time for each response  
🎨 **Beautiful UI** - Modern, gradient-based design with smooth interactions  
📱 **Responsive** - Works on desktop and tablet devices

---

## Getting Started

### Accessing the Agent Builder

1. Navigate to your application URL
2. Click on **"Agent Builder"** in the top navigation (marked with "NEW" badge)
3. You'll see the Dynamic Agent Builder page with:
   - **Left Sidebar**: Your created agents
   - **Main Area**: Chat interface or agent creation form
   - **Top Right**: "Create Agent" button

---

## Creating Your First Agent

### Step 1: Click "Create Agent"

Click the blue **"Create Agent"** button in the top-right corner.

### Step 2: Fill in Agent Details

**Agent Name** (required)
- Unique identifier for your agent
- Use lowercase with hyphens
- Examples: `payment-specialist`, `code-reviewer`, `incident-responder`

**Role** (required)
- Describes what your agent does
- Examples:
  - "Payment Systems Expert"
  - "Senior Code Reviewer"
  - "SRE Incident Response Specialist"

**System Prompt** (required)
- Instructions that define your agent's behavior
- Be specific about:
  - What expertise the agent has
  - How it should respond
  - What organizational context to reference

**Example Prompts:**

```
You are an expert in payment systems and transaction processing. 
Help users understand payment-related issues, suggest solutions 
based on past PRs and incidents, and provide best practices for 
handling payment failures and retries.
```

```
You are a senior code reviewer with expertise in security, 
performance, and best practices. When analyzing code or PRs, 
provide specific, actionable feedback. Reference relevant past 
PRs and incidents from the context to support your recommendations.
```

### Step 3: Create the Agent

Click the **"Create Agent"** button at the bottom of the form.

✅ Success: You'll see a green notification and the agent will appear in your sidebar  
❌ Error: If the name already exists, you'll see a red error message

---

## Interacting with Agents

### Selecting an Agent

1. In the left sidebar, click on any agent card
2. The agent will be highlighted with a gradient background
3. The main chat area will open

### Asking Questions

1. Type your question in the input field at the bottom
2. Click **"Send"** or press Enter
3. You'll see:
   - Your message in a blue bubble on the right
   - "Agent is thinking..." loading message
   - Agent's response in a gray bubble on the left

### Understanding Responses

Each agent response includes:
- **Context Count**: Number of items fetched from knowledge base (e.g., "Context: 18 items")
- **Execution Time**: How long it took to generate the response (e.g., "7.8s")
- **Response Text**: The actual answer from the agent

---

## Example Use Cases

### 1. Payment Systems Expert

**Create Agent:**
- Name: `payment-specialist`
- Role: "Payment Systems Expert"
- Prompt: "Expert in payment systems. Reference past PRs and incidents."

**Example Questions:**
- "How should we handle payment retries?"
- "What are best practices for payment webhooks?"
- "How do we ensure idempotency in payment processing?"

---

### 2. Code Reviewer

**Create Agent:**
- Name: `code-reviewer`
- Role: "Senior Code Reviewer"
- Prompt: "Provide specific, actionable feedback on code quality, security, and performance."

**Example Questions:**
- "What should I look for when reviewing authentication code?"
- "Review this SQL query for security vulnerabilities"
- "What are the best practices for error handling in APIs?"

---

### 3. Incident Responder

**Create Agent:**
- Name: `incident-responder`
- Role: "SRE Incident Response Specialist"
- Prompt: "Analyze alerts, identify root causes, suggest actions based on past incidents."

**Example Questions:**
- "API error rate is at 15%. How should I investigate?"
- "We're seeing database connection timeouts. What could be causing this?"
- "Memory usage is growing continuously. How do I debug this?"

---

### 4. Onboarding Helper

**Create Agent:**
- Name: `onboarding-helper`
- Role: "Developer Onboarding Specialist"
- Prompt: "Help new developers understand the system. Explain architecture and point to relevant docs."

**Example Questions:**
- "How do I set up the development environment locally?"
- "Can you explain our payment service architecture?"
- "What are our testing best practices?"

---

## How Context Works

When you ask a question, the agent automatically:

1. **Searches Knowledge Base**: Finds relevant content based on your query
2. **Fetches Context**:
   - Weekly summaries (high-level organizational context)
   - Entity metadata (detailed info from docs, Jira, messages)
   - PR data (for technical/code-related agents)
3. **Generates Response**: Uses OpenAI GPT with:
   - Agent's role and prompt
   - Fetched organizational context
   - Your specific question

**Context Types Fetched:**
- 📝 Documentation
- 🔧 Pull Requests (PRs)
- 📋 Jira tickets
- 💬 Slack messages
- 🗓️ Meeting notes

---

## Tips for Better Responses

### 1. Be Specific
✅ "How do we handle payment retries in the checkout service?"  
❌ "Tell me about payments"

### 2. Ask Follow-up Questions
Agents maintain context within a conversation, so you can ask follow-ups:
- First: "How do we handle authentication?"
- Then: "What are the common issues with this approach?"

### 3. Reference Specific Systems
✅ "What's the authentication flow for the API service?"  
❌ "How does auth work?"

### 4. Use the Right Agent
- Use `payment-specialist` for payment questions
- Use `code-reviewer` for code quality questions
- Use `incident-responder` for debugging production issues

---

## UI Elements Explained

### Navigation Bar
- **Context Intelligence Logo**: Home
- **Agents Link**: Go to main agents page (CodeHealth, Employee, OnCall, Document)
- **Agent Builder Link**: Current page (marked with "NEW" badge)

### Agent Builder Page

**Header Section:**
- Title: "Dynamic Agent Builder"
- Subtitle: "Build and deploy your agent on top of your knowledge base"
- Create Agent button

**Left Sidebar:**
- "Your Agents (X)": Shows total agent count
- Agent Cards:
  - Robot icon
  - Agent name
  - Agent role
  - Selected state: Gradient background

**Main Area (No Agent Selected):**
- Large robot icon
- "Select an agent to start"
- Helpful prompt text

**Main Area (Agent Selected):**
- **Chat Header** (gradient): Agent name and role
- **Messages Area**: Scrollable conversation history
- **Input Bar**: Type queries and send

**Create Form:**
- Appears at the top when "Create Agent" is clicked
- Two columns: Agent Name and Role
- Full-width System Prompt textarea
- Create Agent button

---

## Keyboard Shortcuts

- **Enter**: Send message (when input is focused)
- **Tab**: Navigate between form fields

---

## Performance

**Typical Response Times:**
- Context Fetching: 1-2 seconds
- LLM Generation: 5-10 seconds
- Total: 5-15 seconds per query

**Context Fetched:**
- Average: 12-21 items per query
- More context = better answers (but slower)

---

## Troubleshooting

### Agent Not Responding
- **Check**: Backend service is running
- **Solution**: Refresh the page

### Slow Responses
- **Normal**: 5-15 seconds
- **If slower**: Check if your query is too broad
- **Solution**: Be more specific in your questions

### Can't Create Agent
- **Error**: "Agent already exists"
- **Solution**: Use a different name

### No Context Fetched
- **Possible Cause**: New system with limited data
- **Note**: Agent will still respond using general knowledge

### Response Quality Issues
- **Check**: Agent prompt is specific enough
- **Check**: Relevant data exists in knowledge base
- **Solution**: Improve agent prompt or add more organizational data

---

## Best Practices

### Creating Agents

1. **Specific Roles**: Define clear, focused purposes
   - ✅ "Payment Systems Expert"
   - ❌ "General Helper"

2. **Detailed Prompts**: Tell the agent HOW to behave
   - ✅ "Provide specific code examples and reference past PRs"
   - ❌ "Be helpful"

3. **Context Usage**: Instruct to use organizational knowledge
   - ✅ "Reference relevant PRs and incidents from the context"
   - ❌ "Just answer the question"

### Using Agents

1. **Match Agent to Task**: Use specialized agents
2. **Iterate on Questions**: Refine based on responses
3. **Leverage Context**: Ask about your organization's specifics
4. **Check Metrics**: Note context count and execution time

---

## Technical Details

**Frontend Stack:**
- React with Hooks
- React Router for navigation
- Axios for API calls
- Lucide React for icons
- Tailwind CSS for styling

**State Management:**
- Local React state (useState)
- No external state library needed

**API Integration:**
- Backend: FastAPI
- Endpoints:
  - POST `/api/agents/create`
  - GET `/api/agents/list`
  - POST `/api/agents/execute`

---

## Screenshots Guide

### 1. Main Page - Agent List
Shows all your created agents in the left sidebar with their names and roles.

### 2. Create Agent Form
Form with fields for Agent Name, Role, and System Prompt.

### 3. Agent Selected - Empty Chat
Selected agent with chat interface ready for questions.

### 4. Active Conversation
Shows user messages (blue) and agent responses (gray) with context metrics.

### 5. Agent Executing
Loading state showing "Agent is thinking..." while processing your query.

---

## Support

For issues or questions:
- Check backend logs: `/var/log/supervisor/backend.*.log`
- Check frontend logs: `/var/log/supervisor/frontend.*.log`
- Database: `/app/backend/dynamic_agents.db`
- API Documentation: `/app/DYNAMIC_AGENTS_README.md`

---

## Future Enhancements

Potential features being considered:
- Agent editing/deletion
- Conversation history persistence
- Response streaming (real-time output)
- Agent templates/presets
- Multi-turn conversation memory
- Agent analytics and usage stats

---

## Security Notes

- All agents use the same Emergent LLM Key
- Agents access the same knowledge base
- No user authentication required (configured separately)
- Rate limiting applies at the API level

---

## Conclusion

The Dynamic Agent Builder UI empowers you to create custom AI agents tailored to your organization's needs. With access to your entire knowledge base through MCP, these agents provide context-aware, intelligent responses that reference your actual PRs, docs, and conversations.

Start building your agents today and unlock the power of organizational intelligence! 🚀

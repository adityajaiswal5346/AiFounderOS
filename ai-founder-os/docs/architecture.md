# Architecture

## System Overview

AI Founder OS is a multi-agent system that automates the daily operational work of an early-stage startup. Three specialist agents (Marketing, Sales, Operations) run under a CEO Agent that plans, arbitrates conflicts, and synthesizes a daily digest.

## Components

### CEO Agent
- **planner.py** — generates a prioritized task list each morning based on company goals and previous outcomes
- **arbitration.py** — resolves conflicts when agents disagree on priority or resource usage
- **digest.py** — synthesizes agent outputs into a founder-readable daily briefing

### Specialist Agents (ReAct-style)
Each agent follows a Reason → Act → Observe loop:
1. Receives tasks from the CEO planner
2. Selects tools from its toolset
3. All tool calls requiring real-world side effects pass through the approval gate
4. Results are written back to shared state and Postgres

| Agent | Core Tools |
|---|---|
| Marketing | Google Trends search, content drafting, Gmail send |
| Sales | Sheets read/write, lead email draft, pipeline update |
| Operations | Notion task creation, doc generation, Slack notify |

### Orchestration
- **graph.py** — LangGraph `StateGraph` wiring the daily execution flow
- **scheduler.py** — cron or Temporal-based daily trigger
- **state_machine.py** — task status transitions: `pending → in_progress → awaiting_approval → done | failed`

### MCP Clients
Thin wrappers around external service APIs. Each client handles auth, retries, and rate limiting. Mocked in tests via `unittest.mock`.

### Memory
- **Short-term** — current run context stored in LangGraph state (in-memory)
- **Long-term** — business profile, past decisions, outcomes stored in Postgres
- **Retrieval** — pgvector RAG over unstructured docs (founder notes, meeting transcripts)

### Guardrails
Approval gate is enforced at the **tool layer**, not via prompt instructions. Any tool call that matches a policy rule (e.g., `send_email`, `post_content`) is intercepted and written to the `approvals` table. Execution resumes only after explicit human approval via the API/UI.

### Observability
Langfuse traces every LLM call, tool call, and agent run. Trace IDs are stored alongside task records for post-hoc debugging.

## Data Model

```
tasks           (id, agent, description, status, created_at, completed_at)
approvals       (id, task_id, tool_name, payload, status, reviewed_at)
memory_long     (id, key, value, embedding, updated_at)
outcomes        (id, task_id, result_summary, success, trace_id)
```

## Decisions & Tradeoffs

| Decision | Rationale |
|---|---|
| LangGraph over custom orchestration | Explicit state, easy to inspect, built-in retries |
| Tool-layer approval gate | Prompts can be jailbroken; tool hooks cannot |
| pgvector over Pinecone | Keeps infra simple (single DB), sufficient for early scale |
| ReAct over plan-then-execute | Better handling of unexpected tool results |
| Stub agents (Finance/CS/RnD) | Scope honesty — these would need separate data integrations |

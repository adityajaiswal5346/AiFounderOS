# Roadmap

## What's Built (v0.1 — Demo Ready)

### Agents
- [x] CEO Agent — planner, arbitration, daily digest
- [x] Marketing Agent — trend search, content draft, ReAct loop
- [x] Sales Agent — lead pipeline, Sheets read/write, ReAct loop
- [x] Operations Agent — Notion tasks, doc generation, ReAct loop

### Infrastructure
- [x] LangGraph orchestration graph
- [x] Approval gate (tool-layer enforcement)
- [x] Short-term and long-term memory
- [x] pgvector RAG retrieval
- [x] MCP clients: Gmail, Sheets, Notion, Slack, Google Trends
- [x] FastAPI backend with digest/approval/memory routes
- [x] Langfuse tracing
- [x] Eval harness with hand-built test cases
- [x] Next.js frontend scaffold (dashboard, approvals, company brain)

---

## Planned (v0.2)

- [ ] Finance Agent — P&L tracking, burn rate alerts, invoice automation
  - Requires: accounting software integration (QuickBooks / Stripe)
- [ ] Customer Success Agent — NPS tracking, churn signals, support ticket triage
  - Requires: CRM + support desk integration (HubSpot / Intercom)
- [ ] R&D Agent — literature search, experiment tracking, code review summaries
  - Requires: GitHub integration, arXiv/Semantic Scholar API

## Stub Agents (Interface Only)

These agents are documented as interface stubs in `backend/agents/stubs/`. They define the expected inputs, outputs, and tool contracts but contain no implementation. This is intentional — building them properly requires integrations that are out of scope for v0.1.

See:
- `backend/agents/stubs/finance_agent.md`
- `backend/agents/stubs/customer_success_agent.md`
- `backend/agents/stubs/rnd_agent.md`

---

## Known Limitations

- MCP clients require real OAuth credentials; demo uses mocked responses
- Eval scoring is rule-based; LLM-as-judge grading is planned
- Frontend is a scaffold — full interactivity in v0.2
- No multi-tenant support yet (single-company design)

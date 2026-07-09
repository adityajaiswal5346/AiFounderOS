# AI Founder OS

An autonomous multi-agent system that runs the operational layer of an early-stage startup — handling marketing, sales, and operations through coordinated AI agents.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        CEO Agent                            │
│         (planner · arbitration · daily digest)              │
└──────────────┬──────────────────────────────────────────────┘
               │ orchestrates via LangGraph
   ┌───────────┼───────────────────┐
   ▼           ▼                   ▼
Marketing   Sales Agent     Operations Agent
 Agent      (leads, CRM)    (tasks, docs)
(content,
 trends)
   │           │                   │
   └───────────┴───────────────────┘
               │ tool calls via MCP clients
   ┌───────────┼───────────────────┐
   ▼           ▼                   ▼
 Gmail      Sheets           Notion / Slack
                              Google Trends
               │
   ┌───────────┴───────────────────┐
   ▼                               ▼
Postgres (tasks, approvals)   pgvector (RAG memory)
```

## What's Built

| Module | Status |
|---|---|
| CEO Agent (planner, arbitration, digest) | ✅ Scaffolded |
| Marketing Agent (ReAct loop, tools) | ✅ Scaffolded |
| Sales Agent | ✅ Scaffolded |
| Operations Agent | ✅ Scaffolded |
| LangGraph orchestration graph | ✅ Scaffolded |
| MCP clients (Gmail, Sheets, Notion, Slack, Trends) | ✅ Scaffolded |
| Memory (short-term, long-term, RAG retrieval) | ✅ Scaffolded |
| Approval guardrails (tool-layer enforcement) | ✅ Scaffolded |
| FastAPI backend | ✅ Scaffolded |
| Eval harness | ✅ Scaffolded |
| Langfuse observability | ✅ Scaffolded |
| Finance Agent | 🔲 Stub only |
| Customer Success Agent | 🔲 Stub only |
| R&D Agent | 🔲 Stub only |

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker + Docker Compose
- API keys for: OpenAI, Langfuse, Gmail OAuth, Google Sheets, Notion, Slack

### Local Development

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd ai-founder-os

# 2. Copy and fill env vars
cp .env.example .env

# 3. Start Postgres
docker-compose up -d

# 4. Install backend deps
cd backend
pip install -e .

# 5. Run the API
uvicorn api.main:app --reload

# 6. Install and run frontend
cd ../frontend
npm install
npm run dev
```

### MCP Auth Setup
```bash
python scripts/setup_mcp_auth.py
```

### Seed Onboarding Memory
```bash
python scripts/seed_onboarding.py
```

### Run Daily Cycle (manual/demo)
```bash
python scripts/run_daily_cycle.py
```

## Honest Scope Notes

- Finance, Customer Success, and R&D agents are **interface stubs only** — see `docs/roadmap.md`
- MCP integrations require real OAuth credentials; mocked in tests
- Approval gate is enforced at the tool layer, not via prompt instructions
- Eval cases (~20–30 per agent) are hand-built; LLM-graded scoring is planned

## Project Structure

```
backend/        Python agents, orchestration, API
frontend/       Next.js dashboard (digest, approvals, memory)
docs/           Architecture, roadmap, demo script
scripts/        Onboarding, daily cycle trigger, OAuth setup
tests/          Unit, integration, e2e
```

# AI Founder OS — Codebase Inspection & Analysis Report

> **Inspection date:** 2026-08-10  
> **Inspected by:** Antigravity (Claude Opus 4.6 Thinking)  
> **No files were created or modified during this inspection.**

---

## 1. PROJECT UNDERSTANDING

**AI Founder OS** is a multi-agent AI system designed to automate the daily operational workload of a solo startup founder. The core idea: instead of spending hours on repetitive tasks (trend research, lead follow-up, content drafting, task management), a team of AI agents handles 80% of the daily grind while keeping the human founder in control of anything consequential.

**The problem it solves:** A solo, early-stage founder must simultaneously manage product, marketing, sales, and operations — all alone. AI Founder OS automates the repeatable portions via:

1. A **CEO Agent** that plans daily work based on a roadmap and recent outcomes
2. **Specialist agents** (Operations, Marketing, Sales) that execute tasks using real external tools
3. A **shared state store** (PostgreSQL) so agents coordinate without talking directly to each other
4. A **human-in-the-loop approval gate** enforced at the code layer (not prompt instructions) to prevent any external-facing action without explicit human sign-off
5. **Observability** (Langfuse) for full inspection of what any agent did and why

**Dual purpose:** (1) A genuine automation tool for a solo founder, and (2) a portfolio-grade demonstration of production agentic AI engineering patterns.

---

## 2. CURRENT ARCHITECTURE

### CEO Agent
- **Location:** [ceo_agent/](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/agents/ceo_agent)
- **Responsibility:** Daily planning only — reads roadmap, outcomes, pending tasks; produces structured `DailyPlan` via forced tool-calling + Pydantic validation; writes new Task rows.
- **Actual status:** [planner.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/agents/ceo_agent/planner.py) is implemented and uses the Anthropic SDK with Claude directly. [schemas.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/agents/ceo_agent/schemas.py) and [prompts.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/agents/ceo_agent/prompts.py) are **empty files** — yet `planner.py` imports `DailyPlan` from `schemas.py` and `PLANNER_SYSTEM_PROMPT`/`build_planning_prompt` from `prompts.py`, meaning the planner **cannot run** as-is.
- **Additional files:** [arbitration.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/agents/ceo_agent/arbitration.py) and [digest.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/agents/ceo_agent/digest.py) exist with full implementations using **LangChain + OpenAI** (not Anthropic), which contradicts the documented architecture. These are Phase 8 components that were supposed to be "not started."

### Operations Agent
- **Location:** [operations_agent/](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/agents/operations_agent)
- **Responsibility:** Execute operations tasks via ReAct loop using Notion MCP tools
- **Actual status:** [agent.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/agents/operations_agent/agent.py) has a hand-rolled ReAct loop (NOT using a shared `react_agent.py`). It uses `@observe` decorator but **never imports it** — the import is missing, making this file **broken**. The loop calls `execute_tool(block.name, block.input)` with only 2 args, but [tools.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/agents/operations_agent/tools.py) defines `execute_tool(db, task_id, tool_name, tool_input)` with 4 args — **signature mismatch**.
- The `__init__.py` exports `run_operations_agent` but agent.py defines `run_operations_task` and `run_all_pending_operations_tasks` — **no `run_operations_agent` exists**.

### Marketing Agent
- **Location:** [marketing_agent/](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/agents/marketing_agent)
- **Responsibility:** Trend research + content drafting via Google Trends and Notion tools
- **Actual status:** Uses **LangChain + LangGraph** (`create_react_agent` from `langgraph.prebuilt`), NOT the documented custom ReAct loop or Anthropic SDK. Imports `memory.long_term.get_company_profile` and `memory.short_term.get_current_context`. Uses `@tool` decorator from LangChain. Tools include `search_trends`, `draft_content`, `send_marketing_email` — email uses `@requires_approval` decorator (the commented-out version from the old approval gate, not `check_and_gate()`).

### Sales Agent
- **Location:** [sales_agent/](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/agents/sales_agent)
- **Responsibility:** Pipeline management via Google Sheets + email outreach via Gmail
- **Actual status:** **Fully written** (not "not started" as docs say). Uses same LangChain/LangGraph pattern as Marketing. Has complete `tools.py` with `read_leads_sheet`, `update_lead_status`, `draft_outreach_email`, `send_outreach_email`. Uses `@requires_approval` decorator. All tools import from implemented Gmail and Sheets clients.

### PostgreSQL / Database Layer
- **Location:** [db/](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/db)
- **Actual schema:** Radically different from documentation:
  - `Task` model has fields: `id`, `run_id`, `agent`, `description`, `status`, `priority`, `requires_approval`, `notes` — **NOT** `agent_name`, `title`, `output`, `updated_at` as documented
  - `Approval` model has: `id`, `task_id`, `tool_name`, `description`, `payload`, `status`, `reviewed_at`, `reviewed_by` — **NOT** `action_type`, `action_payload`, `resolved_at` as documented
  - `Memory` table documented as existing — **does not exist**. Instead there is `MemoryLong` with `id`, `key`, `value`, `embedding` (pgvector Vector(1536)), `updated_at`
  - `Outcome` model has `agent` field and `trace_id` field — not in docs
  - Extra table `TaskRun` exists — not documented at all
  - IDs are `String` type, not `UUID` as documented
  - **pgvector is already integrated** in the schema — docs say Phase 7

### Repository Layer
- **Location:** [db/repository/](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/db/repository)
- **Actual status:** Synchronous (`sqlalchemy.orm.Session`), BUT the database connection layer (`connection.py`) is **fully async** (`AsyncSession`, `asyncpg`). The repository layer imports `Session` from `sqlalchemy.orm` which **won't work** with the async engine.
- `task_repository.py` references `Task.agent_name` — the model field is actually `Task.agent`. References `Task.output` — field doesn't exist.
- `approval_repository.py` has a **syntax error** on line 8: semicolon instead of comma (`task_id=task_id;`). Also calls `db.commit` without parentheses (line 15) — **doesn't actually commit**. References `Approval.action_type` and `Approval.action_payload` — fields don't exist (actual: `tool_name`, `payload`). Functions referenced by approval_gate (`create_approval_request`, `get_approval_for_task`) **don't exist** — actual functions are `create_approval`, `is_action_approved`.
- `memory_repository.py` references `Memory` model — **doesn't exist** (actual: `MemoryLong`). References `Memory.created_at` — field doesn't exist on `MemoryLong`.
- `outcome_repository.py` references `Outcome.created_at` — this field exists.

### MCP Clients
- **Location:** [mcp_clients/](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/mcp_clients)
- [mcp_session.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/mcp_clients/mcp_session.py) — Generic stdio MCP session. This **IS** the documented pattern — working, correct.
- [notion_client.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/mcp_clients/notion_client.py) — **NOT a thin MCP wrapper**. Uses the `notion-client` Python SDK directly (REST API), not MCP at all. No calls to `mcp_session.py`. Exports `create_notion_task` and `get_notion_tasks` — but `operations_agent/tools.py` imports `list_notion_tools` and `call_notion_tool` which **don't exist**.
- [trends_client.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/mcp_clients/trends_client.py) — Uses **direct HTTP calls to SerpAPI**, not MCP. Not a wrapper around `mcp_session.py`.
- [gmail_client.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/mcp_clients/gmail_client.py) — **Fully implemented** using Google API client directly. Not a stub.
- [sheets_client.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/mcp_clients/sheets_client.py) — **Fully implemented** using Google API client. Not a stub.
- [slack_client.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/mcp_clients/slack_client.py) — **Fully implemented** using Slack SDK. Not a stub.

### MCP Tool Layer
- The documented pattern (agents discover tools live via `list_tools()` from real MCP servers, dispatch via `call_tool()`) **does not exist in any agent**. Only `mcp_session.py` has the MCP protocol code. No agent or client actually uses it.

### Approval Gate
- **Location:** [guardrails/](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/guardrails)
- [approval_gate.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/guardrails/approval_gate.py) contains **two competing implementations**:
  1. Lines 1-139: A **fully commented-out** decorator-based `requires_approval` + `ApprovalPendingError` using async DB calls and the old decorator pattern
  2. Lines 144-193: Active code with `ApprovalPending` exception and TWO duplicate definitions of `check_and_gate()` (lines 162-178 and 181-193 — Python will silently use only the second one)
- `check_and_gate()` imports `requires_approval` from `policies.py` — but `policies.py` exports `requires_human_approval`, NOT `requires_approval`. **Import will fail.**
- `check_and_gate()` calls `approval_repository.create_approval_request` and `approval_repository.get_approval_for_task` — **neither function exists** in approval_repository.py.
- Marketing and Sales agents use `@requires_approval` (the old commented-out decorator) — this is imported from `guardrails.approval_gate` where it's **commented out** on lines 101-139, making the import fail.

### Langfuse Observability
- **Location:** [observability/tracing.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/observability/tracing.py)
- Uses `langfuse` SDK v2 (declared as `langfuse==2.27.0` in pyproject.toml, not v4/OTEL-based as documented)
- Provides `@observe` re-export, `trace_agent_run`, `trace_tool_call` decorators, `get_tracer()`, `get_current_trace_id()`, and a `NoOpTracer` fallback
- Has graceful degradation when Langfuse credentials are missing — **contradicts** docs saying no fallback exists
- Operations agent uses `@observe` but **never imports it**

### Orchestration Layer
- **Location:** [orchestration/](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/orchestration)
- **NOT scaffolded/empty** as docs say — contains **full implementations**:
  - [graph.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/orchestration/graph.py): Complete LangGraph `StateGraph` with plan → parallel agents → arbitration → digest pipeline
  - [scheduler.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/orchestration/scheduler.py): Full APScheduler cron configuration (7AM UTC daily)
  - [state_machine.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/orchestration/state_machine.py): Complete task state machine with transitions
- Graph imports `generate_daily_tasks` from CEO agent — function doesn't exist (actual: `generate_daily_plan`)
- Graph imports `run_operations_agent` — function doesn't exist in operations agent

### API Layer
- **Location:** [api/](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/api)
- **NOT scaffolded/empty** as docs say — contains **working implementations**:
  - [main.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/api/main.py): Full FastAPI app with CORS, lifespan, scheduler integration
  - [routes/](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/api/routes): Complete route handlers for digest, approvals, memory, roadmap
  - [schemas.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/api/schemas.py): Full Pydantic schemas
- API routes bypass the repository layer and query models directly via async SQLAlchemy — **violates** the repository-only access pattern

### Memory Layer
- **Location:** [memory/](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/memory)
- **NOT scaffolded/empty** as docs say — contains **full implementations**:
  - [long_term.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/memory/long_term.py): Complete implementation with `get_company_profile()`, `get_recent_outcomes()`, `save_memory()`, `get_memory()`
  - [short_term.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/memory/short_term.py): In-memory dict store for per-run context
  - [retrieval.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/memory/retrieval.py): Full pgvector RAG retrieval with OpenAI embeddings, `index_document()`, `retrieve_context()`

### Component Interactions
The documented flow (CEO plans → agents execute via shared ReAct loop → approval gate at tool layer → MCP tool calls → outcomes recorded) **does not work end-to-end** due to:
- Schema mismatches between models and repository functions
- Missing imports and broken function signatures
- Two incompatible architectures coexisting (Anthropic/custom ReAct vs LangChain/LangGraph)
- MCP clients not actually using MCP protocol
- Broken approval gate references

---

## 3. IMPLEMENTATION STATUS

### Phase 0 — Database ❌ PARTIALLY IMPLEMENTED (contradicts docs: "COMPLETED")
- `models.py` exists with 5 tables (`Task`, `Approval`, `MemoryLong`, `Outcome`, `TaskRun`) but schema is **completely different** from documented schema
- `connection.py` exists but is **async** (asyncpg) while repository layer uses sync `Session` — **incompatible**
- pgvector integration already present in schema (documented as Phase 7)
- `init_db.py` exists, uses async engine correctly

### Phase 1 — Repository Layer ❌ BROKEN (contradicts docs: "COMPLETED")
- All 4 repository files exist but reference **wrong model field names**:
  - `task_repository.py` uses `Task.agent_name` (actual: `Task.agent`), `Task.title` (doesn't exist), `Task.output` (doesn't exist)
  - `approval_repository.py` has a **syntax error** (semicolon), uses `Approval.action_type` (actual: `Approval.tool_name`), `Approval.action_payload` (actual: `Approval.payload`), and `db.commit` missing parentheses
  - `memory_repository.py` references `Memory` model (actual: `MemoryLong`), `Memory.created_at` (doesn't exist on `MemoryLong`)
  - `outcome_repository.py` uses `Outcome.task_id`, `Outcome.created_at` — these exist
- All repository functions use synchronous `Session` but the engine is async — **fundamentally incompatible**
- `test_repository.py` references `SessionLocal` which doesn't exist in `connection.py`

### Phase 2 — CEO Agent ❌ PARTIALLY IMPLEMENTED (contradicts docs: "COMPLETED")
- `planner.py` exists with correct Anthropic SDK usage and `@observe` decorator
- **BUT** imports `DailyPlan` from empty `schemas.py` and `PLANNER_SYSTEM_PROMPT`/`build_planning_prompt` from empty `prompts.py` — **cannot execute**
- `arbitration.py` and `digest.py` exist with full LangChain/OpenAI implementations — these are Phase 8 components, not Phase 2

### Phase 3 — Operations Agent + ReAct + Notion MCP ❌ BROKEN (contradicts docs: "COMPLETED")
- `agent.py` has hand-rolled ReAct loop but **missing `@observe` import** and **wrong `execute_tool` call signature** (2 args vs 4 params)
- `tools.py` imports `list_notion_tools`, `call_notion_tool` from `notion_client.py` — **these functions don't exist** (actual exports: `create_notion_task`, `get_notion_tasks`)
- `notion_client.py` uses direct Notion REST API, **NOT MCP protocol**
- `__init__.py` exports `run_operations_agent` which **doesn't exist** in agent.py

### Phase 4 — Approval Gate ❌ BROKEN (contradicts docs: "COMPLETED")
- `approval_gate.py` has TWO duplicate `check_and_gate()` definitions (Python uses only the second)
- Imports `requires_approval` from `policies.py` — function is named `requires_human_approval` — **import fails**
- References `approval_repository.create_approval_request` and `get_approval_for_task` — **neither exists**
- The old decorator-based `requires_approval` is fully commented out but imported by Marketing/Sales agents
- `policies.py` uses a set-based lookup (`APPROVAL_REQUIRED_TOOLS`) not the documented dict-based map. Default is **NOT fail-closed** for unknown tools — it's fail-open (returns `tool_name in APPROVAL_REQUIRED_TOOLS`, unknown tools return `False`)

### Phase 5 — Langfuse Observability ⚠️ PARTIALLY WORKING
- `tracing.py` exists with working `@observe` re-export, graceful degradation
- `langfuse==2.27.0` in pyproject.toml — v2, not v4 as documented
- Operations agent fails to import `@observe`
- Has `NoOpTracer` fallback — docs say no fallback exists

### Phase 6 — Marketing + Sales Agents ⚠️ CODE EXISTS BUT WRONG ARCHITECTURE
- Both agents are **fully written** — docs say Sales is "not started"
- Both use **LangChain + LangGraph** (`create_react_agent`), NOT the documented custom `shared/react_agent.py`
- `agents/shared/` directory **does not exist** — `react_agent.py` was never created
- Marketing and Sales tools use `@requires_approval` decorator that doesn't exist at runtime
- Gmail, Sheets, Slack clients are **fully implemented** (REST APIs) — docs say they're stubs

### Phase 7 — Memory + pgvector/RAG ⚠️ CODE EXISTS (contradicts docs: "NOT STARTED")
- `memory/long_term.py`, `short_term.py`, `retrieval.py` are **fully implemented**
- pgvector is in the schema (`Vector(1536)` on `MemoryLong`)
- RAG retrieval with OpenAI embeddings is complete
- Onboarding seed script exists (`scripts/seed_onboarding.py`)

### Phase 8 — CEO Synthesis + Daily Digest ⚠️ CODE EXISTS (contradicts docs: "NOT STARTED")
- `ceo_agent/arbitration.py` — Full conflict arbitration using LangChain/OpenAI
- `ceo_agent/digest.py` — Full daily digest synthesis using LangChain/OpenAI
- Both are imported and used by the orchestration graph

### Phase 9 — Evaluations ⚠️ CODE EXISTS (contradicts docs: "NOT STARTED")
- `evals/run_evals.py` — Full evaluation runner with assertion-based scoring
- `evals/test_cases/` — Has JSON test case files for all 3 agents (marketing, sales, operations)
- `evals/results/` — Has `.gitkeep` placeholder

### Phase 10 — Frontend ⚠️ SCAFFOLDED
- Next.js app structure exists with route directories (approvals, company-brain, dashboard, roadmap)
- `components/` has only `.gitkeep`
- `app/page.tsx`, `layout.tsx`, `globals.css` exist
- No actual UI implementation

---

## 4. PHASE 6 ANALYSIS

### What Has Already Been Implemented
1. **Marketing Agent** — Full agent.py, tools.py, prompts.py using LangChain/LangGraph
2. **Sales Agent** — Full agent.py, tools.py, prompts.py using LangChain/LangGraph  
3. **Gmail client** — Fully implemented REST API client (not MCP)
4. **Sheets client** — Fully implemented REST API client (not MCP)
5. **Trends client** — Fully implemented SerpAPI HTTP client (not MCP)

### What Is Partially Implemented
1. **Approval integration** — Marketing/Sales tools reference `@requires_approval` decorator which is commented out in approval_gate.py, so the import chain is broken
2. **Observability** — Marketing agent uses `get_tracer()` but not `@observe`; Sales doesn't use either consistently

### What Is Missing
1. **`agents/shared/react_agent.py`** — The generic ReAct loop documented as the central reuse pattern **does not exist**. Both Marketing/Sales use LangGraph's `create_react_agent` instead.
2. **MCP-based tool integration** — No agent uses `mcp_session.py`. All external clients use direct REST APIs/SDKs.
3. **Repository-based task lifecycle** — Marketing/Sales agents don't use `task_repository` or `outcome_repository`. They receive tasks as dicts and return dicts, with no DB persistence.
4. **Working approval gate integration** — The `check_and_gate()` function can't execute due to import mismatches and missing repository functions.
5. **`@observe` tracing** on Marketing/Sales agent functions
6. **Test scripts** — `scripts/test_marketing_agent.py` referenced in PROJECT_CONTEXT.md doesn't exist in `backend/scripts/`
7. **Operations Agent refactoring** to use shared ReAct loop — never happened

### Which Existing Components Should Be Reused
1. `mcp_session.py` — The correct MCP transport pattern (if MCP is desired)
2. `db/repository/*` — Once field names are fixed to match actual models
3. `guardrails/approval_gate.py::check_and_gate()` — Once import issues are fixed
4. `observability/tracing.py::@observe` — Already works
5. `db/models.py` — Existing schema (the actual one, not documented one)

### Which New Components Are Required
1. **`agents/shared/react_agent.py`** — A generic ReAct loop OR a decision to standardize on LangGraph's `create_react_agent`
2. **Fix approval gate** — Resolve function name mismatches, remove duplicate definitions
3. **Fix repository layer** — Match field names to actual models, resolve sync/async mismatch
4. **Fix CEO agent schemas.py and prompts.py** — Currently empty

### Dependencies
- Google OAuth credentials for Gmail/Sheets (documented blocker)
- SerpAPI key for Trends (has mock fallback)
- Notion API key/database ID
- OpenAI API key (used by LangChain agents, embeddings)
- Anthropic API key (used by CEO planner, Operations agent)
- Langfuse credentials (optional, has fallback)

### Blockers
1. **Architectural decision required:** The codebase has TWO incompatible agent architectures:
   - CEO + Operations: Raw Anthropic SDK + custom ReAct loop
   - Marketing + Sales + Orchestration: LangChain + LangGraph + OpenAI
   - These cannot coexist as documented — a decision must be made
2. **Sync/async mismatch:** Repository layer is sync, connection layer is async — nothing can run
3. **Schema/field name mismatches:** Every repository function references wrong field names
4. **Google OAuth** for Gmail/Sheets

### Tests Required
- Unit tests for fixed repository functions
- Integration test: Marketing agent end-to-end (trend search → draft → Notion save)
- Integration test: Approval gate blocks/allows correctly
- End-to-end: CEO plans → Marketing executes → outcomes recorded
- MCP integration tests (if MCP protocol is adopted)

---

## 5. IMPORTANT FILES FOR PHASE 6

### Agents
| File | Role | Status |
|------|------|--------|
| [shared/react_agent.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/agents/shared/react_agent.py) | Generic ReAct loop | **DOES NOT EXIST** |
| [marketing_agent/agent.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/agents/marketing_agent/agent.py) | Marketing execution | Uses LangChain/LangGraph, not custom loop |
| [marketing_agent/tools.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/agents/marketing_agent/tools.py) | Marketing tools | LangChain `@tool` decorator, broken approval import |
| [marketing_agent/prompts.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/agents/marketing_agent/prompts.py) | Marketing prompts | LangChain `ChatPromptTemplate` |
| [sales_agent/agent.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/agents/sales_agent/agent.py) | Sales execution | Fully implemented, LangChain/LangGraph |
| [sales_agent/tools.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/agents/sales_agent/tools.py) | Sales tools | LangChain `@tool`, broken approval import |
| [sales_agent/prompts.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/agents/sales_agent/prompts.py) | Sales prompts | LangChain `ChatPromptTemplate` |
| [operations_agent/agent.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/agents/operations_agent/agent.py) | Operations execution | Custom Anthropic loop, broken imports |
| [operations_agent/tools.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/agents/operations_agent/tools.py) | Operations tools | Imports non-existent Notion MCP functions |

### Repositories
| File | Role | Status |
|------|------|--------|
| [task_repository.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/db/repository/task_repository.py) | Task CRUD | Wrong field names (`agent_name` → `agent`, `title` doesn't exist) |
| [approval_repository.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/db/repository/approval_repository.py) | Approval CRUD | Syntax error, wrong field names, missing functions |
| [outcome_repository.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/db/repository/outcome_repository.py) | Outcome logging | Mostly correct |
| [memory_repository.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/db/repository/memory_repository.py) | Memory access | References non-existent `Memory` model |

### MCP Clients
| File | Role | Status |
|------|------|--------|
| [mcp_session.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/mcp_clients/mcp_session.py) | Generic MCP transport | Correct implementation, **unused by anything** |
| [notion_client.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/mcp_clients/notion_client.py) | Notion integration | Direct REST API, not MCP |
| [trends_client.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/mcp_clients/trends_client.py) | Google Trends | Direct HTTP/SerpAPI, not MCP |
| [gmail_client.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/mcp_clients/gmail_client.py) | Gmail | Direct Google API, fully implemented |
| [sheets_client.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/mcp_clients/sheets_client.py) | Google Sheets | Direct Google API, fully implemented |
| [slack_client.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/mcp_clients/slack_client.py) | Slack | Direct Slack SDK, fully implemented |

### Guardrails
| File | Role | Status |
|------|------|--------|
| [approval_gate.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/guardrails/approval_gate.py) | Tool-layer enforcement | Duplicate function defs, broken imports |
| [policies.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/guardrails/policies.py) | Policy lookup | Fail-OPEN (not fail-closed as documented) |

### Observability
| File | Role | Status |
|------|------|--------|
| [tracing.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/observability/tracing.py) | Langfuse setup | Working, with graceful degradation |

### Database
| File | Role | Status |
|------|------|--------|
| [models.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/db/models.py) | SQLAlchemy models | 5 tables, schema differs from docs |
| [connection.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/db/connection.py) | DB connection | Async (asyncpg), incompatible with sync repos |

### Orchestration
| File | Role | Status |
|------|------|--------|
| [graph.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/orchestration/graph.py) | LangGraph daily flow | Fully implemented, broken imports |
| [scheduler.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/orchestration/scheduler.py) | APScheduler cron | Fully implemented |
| [state_machine.py](file:///d:/Projects/AiFounderOS/ai-founder-os/backend/orchestration/state_machine.py) | Task transitions | Fully implemented, uses async DB |

---

## 6. DOCUMENTATION VS CODE — DISCREPANCIES

### Discrepancy 1: Database Schema
**DOCUMENT SAYS:** 4 tables (tasks, approvals, memory, outcomes) with UUID primary keys. Task has `agent_name`, `title`, `description`, `status`, `output` (JSON), `created_at`/`updated_at`. Memory model with `key`, `value`, `memory_type`, `created_at`.  
**ACTUAL CODE:** 5 tables (tasks, approvals, memory_long, outcomes, task_runs). Task has String `id`/`run_id`/`agent`/`description`/`status`/`priority`/`requires_approval`/`notes` — no `title`, no `output`, no `agent_name`, no `updated_at`. MemoryLong (not Memory) with `id`/`key`/`value`/`embedding`(Vector)/`updated_at` — no `memory_type`, no `created_at`. Extra `TaskRun` table not documented.  
**IMPACT:** 🔴 Critical — Every repository function uses wrong field names and will crash at runtime. The entire data access layer is non-functional.

### Discrepancy 2: Sync vs Async Database Layer
**DOCUMENT SAYS:** "Database: PostgreSQL, via SQLAlchemy ORM (synchronous — sessionmaker, Session)" and "DB/repository layer remain fully synchronous."  
**ACTUAL CODE:** `connection.py` uses `AsyncSession`, `create_async_engine`, `async_sessionmaker`, `asyncpg`. Repository functions use sync `Session` from `sqlalchemy.orm`. These are fundamentally incompatible.  
**IMPACT:** 🔴 Critical — The repository layer cannot obtain sessions from the async connection layer. No database operations can execute.

### Discrepancy 3: MCP Protocol Usage
**DOCUMENT SAYS:** "Real MCP protocol usage — tool discovery is live (list_tools() called against the actual running MCP server)" and "This was a deliberate correction made mid-project (an earlier version used a direct REST wrapper)."  
**ACTUAL CODE:** `mcp_session.py` implements real MCP stdio transport, but NO client uses it. `notion_client.py` uses the `notion-client` Python SDK directly. `trends_client.py` uses direct HTTP to SerpAPI. Gmail/Sheets/Slack use direct Google/Slack SDKs. The "deliberate correction" described never happened in this codebase.  
**IMPACT:** 🔴 Critical — The documented MCP architecture is aspirational, not actual. Operations agent imports `list_notion_tools`/`call_notion_tool` which don't exist.

### Discrepancy 4: Agent Architecture (LLM/Framework)
**DOCUMENT SAYS:** "LLM: Anthropic Claude, called directly via the anthropic Python SDK — no LangChain wrapping the LLM calls." Generic ReAct loop in `agents/shared/react_agent.py`.  
**ACTUAL CODE:** CEO planner and Operations agent use Anthropic SDK. Marketing, Sales, CEO arbitration/digest, and the entire orchestration layer use **LangChain + LangGraph + OpenAI (GPT-4o)**. `agents/shared/` directory doesn't exist.  
**IMPACT:** 🔴 Critical — Two incompatible stacks coexist. The `pyproject.toml` includes both `anthropic` (implied — not actually listed!) and `langchain`/`langchain-openai`/`langgraph`/`openai`.

### Discrepancy 5: Anthropic SDK Not In Dependencies
**DOCUMENT SAYS:** LLM calls use the Anthropic Python SDK.  
**ACTUAL CODE:** `pyproject.toml` does NOT list `anthropic` as a dependency. Lists `openai`, `langchain-openai`, `langgraph`. `planner.py` imports `from anthropic import Anthropic` — this would fail unless installed manually outside pyproject.toml.  
**IMPACT:** 🟡 Medium — Operations agent and CEO planner can't run without manual installation.

### Discrepancy 6: Shared ReAct Loop
**DOCUMENT SAYS:** "`agents/shared/react_agent.py` — the single generic ReAct execution loop... used by every execution-capable agent"  
**ACTUAL CODE:** The `agents/shared/` directory does not exist. Operations agent has its own hand-rolled loop. Marketing/Sales use `langgraph.prebuilt.create_react_agent`.  
**IMPACT:** 🔴 Critical — The core architectural pattern that all docs describe as the system's reuse backbone doesn't exist.

### Discrepancy 7: Approval Gate Function Names
**DOCUMENT SAYS:** `policies.py` has `APPROVAL_REQUIRED_TOOLS` as a dict map, `requires_approval()` function, fail-closed default. `approval_gate.py` has `check_and_gate()`.  
**ACTUAL CODE:** `policies.py` has `APPROVAL_REQUIRED_TOOLS` as a **set** (not dict), function is named `requires_human_approval` (not `requires_approval`). Default is **fail-open** for unknown tools (returns `False`). `approval_gate.py` imports `requires_approval` from policies — **will fail**. `create_page` is not in the policy set (docs say it's deliberately gated).  
**IMPACT:** 🔴 Critical — Approval gate cannot import correctly, meaning it cannot function. Unknown tools default to allowed (security hole).

### Discrepancy 8: Sales Agent Status
**DOCUMENT SAYS:** "Sales Agent — NOT YET IMPLEMENTED — blocked on Google OAuth setup" (all three docs)  
**ACTUAL CODE:** Sales agent is **fully implemented** with complete agent.py, tools.py, prompts.py, and the Gmail/Sheets clients it depends on are also fully implemented.  
**IMPACT:** 🟡 Medium — Documentation misrepresents the state; no functional harm but misleading for future development planning.

### Discrepancy 9: Orchestration/API/Memory/Evals Status
**DOCUMENT SAYS:** All scaffolded but empty/not implemented.  
**ACTUAL CODE:** All have **substantial implementations**:
- `orchestration/graph.py` — Full LangGraph pipeline  
- `orchestration/scheduler.py` — Full APScheduler setup  
- `orchestration/state_machine.py` — Full task state machine  
- `api/main.py` + `api/routes/*` — Full FastAPI app with 4 route modules  
- `memory/*` — Full long-term, short-term, and RAG retrieval  
- `evals/run_evals.py` — Full eval runner with test case files  
**IMPACT:** 🟡 Medium — These are implemented but likely can't run due to cascading import/schema issues throughout the codebase.

### Discrepancy 10: CEO Agent `__init__.py` Exports
**DOCUMENT SAYS:** CEO agent exports `generate_daily_plan`, `persist_daily_plan`, `run_daily_planning`  
**ACTUAL CODE:** `__init__.py` exports `generate_daily_tasks` (doesn't exist in planner.py), `arbitrate_conflicts`, `synthesize_digest`  
**IMPACT:** 🔴 Critical — Any code importing from `agents.ceo_agent` package will crash.

### Discrepancy 11: Test Scripts
**DOCUMENT SAYS:** Multiple test scripts in `backend/scripts/`: `test_repository.py`, `test_ceo_planning.py`, `test_operations_agent.py`, `test_marketing_agent.py`  
**ACTUAL CODE:** `backend/scripts/` contains only `approve_pending.py` and `init_db.py`. `test_repository.py` exists in `db/repository/` (not scripts), and the other test scripts don't exist. Root `scripts/` has `run_daily_cycle.py`, `seed_onboarding.py`, `setup_mcp_auth.py`.  
**IMPACT:** 🟡 Medium — Missing test infrastructure for manual verification.

### Discrepancy 12: `pyproject.toml` Dependencies vs Documented Stack
**DOCUMENT SAYS:** "No LangChain wrapping." Python `mcp` SDK for MCP. `uv` for dependency management.  
**ACTUAL CODE:** `pyproject.toml` includes `langchain==0.2.1`, `langchain-openai==0.1.8`, `langgraph==0.1.4`, `openai==1.30.1` as **core dependencies**. Also includes `notion-client==2.2.1`, `slack-sdk==3.27.2`, `google-api-python-client`. Does NOT include `anthropic` or `mcp`. Build backend uses `setuptools`, not `uv`.  
**IMPACT:** 🔴 Critical — The actual tech stack is LangChain/OpenAI-centric, not Anthropic-centric as documented.

### Discrepancy 13: Approval Gate `create_page` Policy
**DOCUMENT SAYS:** "`create_page` (Notion) is deliberately marked True even though low-risk, specifically to demonstrate the full block→approve→execute flow"  
**ACTUAL CODE:** `APPROVAL_REQUIRED_TOOLS` set = `{send_email, post_content, update_crm, send_slack_notification, publish_post}`. `create_page` is NOT in the set.  
**IMPACT:** 🟡 Medium — The documented approval demo flow won't work as described.

---

## 7. ARCHITECTURAL RISKS

### 🔴 CRITICAL: Two Incompatible Agent Architectures
The codebase contains two fundamentally different patterns:
1. **Anthropic SDK + custom ReAct loop** (CEO planner, Operations agent)
2. **LangChain + LangGraph + OpenAI** (Marketing, Sales, orchestration, arbitration, digest)

These can't coexist without explicit bridging. A decision must be made before any further development.

### 🔴 CRITICAL: Sync/Async Database Mismatch
`connection.py` is fully async (`AsyncSession`/`asyncpg`). Repository functions use synchronous `Session` from `sqlalchemy.orm`. These are incompatible — no repository function can obtain a session from the connection layer. **Nothing database-related works.**

### 🔴 CRITICAL: Schema vs Repository Field Name Mismatches
Every repository function references fields that don't exist on the actual models. This is a cascading failure — agents → repositories → wrong fields → runtime crash.

### 🔴 CRITICAL: Broken Import Chains
Multiple critical import failures:
- `approval_gate.py` → `policies.requires_approval` (doesn't exist; actual: `requires_human_approval`)
- `approval_gate.py` → `approval_repository.create_approval_request` / `get_approval_for_task` (don't exist)
- `operations_agent/tools.py` → `notion_client.list_notion_tools` / `call_notion_tool` (don't exist)
- `operations_agent/agent.py` → `observe` (never imported)
- `operations_agent/__init__.py` → `run_operations_agent` (doesn't exist)
- `ceo_agent/__init__.py` → `generate_daily_tasks` (doesn't exist)
- `ceo_agent/planner.py` → `schemas.DailyPlan` / `prompts.PLANNER_SYSTEM_PROMPT` (empty files)
- Marketing/Sales agents → `requires_approval` decorator (commented out)

### 🔴 CRITICAL: Approval Gate is Fail-Open
`policies.requires_human_approval()` returns `tool_name in APPROVAL_REQUIRED_TOOLS`. Unknown tools return `False` (not in set = no approval needed). Docs say fail-closed. This is a **security gap** — any new tool added by any agent will bypass approval by default.

### 🟡 HIGH: `approval_gate.py` Duplicate Function Definitions
Two `check_and_gate()` functions defined at lines 162-178 and 181-193. Python silently uses only the second. The first (simpler, always-create-new) is dead code. Combined with the import failures, neither would work anyway.

### 🟡 HIGH: `approval_repository.py` Syntax Error
Line 8: `task_id=task_id;` — semicolon instead of comma. This is a Python syntax error that would prevent the file from being imported at all.

### 🟡 HIGH: No MCP Protocol Usage Despite mcp_session.py
`mcp_session.py` correctly implements MCP stdio transport but nothing uses it. All "MCP clients" use direct REST APIs/SDKs. The `mcp` Python SDK dependency isn't even in `pyproject.toml`.

### 🟡 HIGH: `anthropic` Not In pyproject.toml
The CEO planner and Operations agent import `from anthropic import Anthropic` but the package isn't declared as a dependency. Would fail on clean install.

### 🟡 MEDIUM: LangChain/OpenAI as Undocumented Primary Stack
`pyproject.toml` lists `langchain`, `langchain-openai`, `langgraph`, `openai` as core dependencies. This is never mentioned in any documentation. The `.env.example` lists `OPENAI_API_KEY` as the first entry, not `ANTHROPIC_API_KEY`.

### 🟡 MEDIUM: `approval_repository.py` Missing `db.commit()` Call
Line 15: `db.commit` without parentheses — the method is referenced but never called. Approval records would never be persisted.

### 🟡 MEDIUM: No `tests/` Directory Implementation
Docs mention scaffolded `tests/` directory at the repo root — it doesn't exist. The only test infrastructure is `evals/` and the manual `test_repository.py` in the repository directory.

### 🟡 MEDIUM: `docker-compose.yml` References Non-Existent Dockerfile
The `api` service references `./backend/Dockerfile` — no Dockerfile exists in the backend directory.

---

## 8. CURRENT POSITION

| | |
|---|---|
| **CURRENT PHASE:** | Phase 6 (Marketing + Sales Agents) — IN PROGRESS |
| **LAST COMPLETED PHASE:** | **None are genuinely complete.** Phases 0-5 all have significant issues (wrong schemas, broken imports, incompatible sync/async, missing functions). The closest to "working" is Phase 5 (observability), which has a functional `tracing.py` with graceful degradation. |
| **NEXT TARGET PHASE:** | Phase 6 — but **foundational issues in Phases 0-4 must be fixed first** |
| **PHASE 6 COMPLETION STATUS:** | Code exists for both Marketing and Sales agents, but uses an incompatible architecture (LangChain/LangGraph/OpenAI) from what's documented and what Operations/CEO use (Anthropic SDK). The code cannot run due to cascading import failures, schema mismatches, and sync/async incompatibilities in the layers it depends on. |

### What Should Happen Next

Before any Phase 6 work can proceed, the **foundational layers (Phases 0-4) must be made functional.** The codebase has a split-brain problem: the documentation describes one architecture (Anthropic SDK, custom ReAct loop, MCP protocol, sync repositories), while a substantial portion of the actual code implements a different architecture (LangChain/LangGraph, OpenAI, direct REST APIs, async database).

The first and most critical decision needed from the project owner:

1. **Which architecture to standardize on?** Anthropic SDK + custom ReAct (as documented) vs LangChain/LangGraph + OpenAI (as partially implemented)?
2. **Which database layer to standardize on?** Sync repositories + sync engine (as documented) vs async engine + async everything (as implemented in connection.py)?
3. **Should MCP protocol be used?** Real MCP via `mcp_session.py` (as documented) vs direct SDK/REST (as actually implemented)?

Until these decisions are made, the codebase has no consistent foundation to build on. No amount of Phase 6 work can succeed when the underlying Phases 0-4 can't execute.

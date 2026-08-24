# Founder OS — Project Context

> **Provenance note:** This document was generated/updated from the complete design and build conversation history for this project, not from direct filesystem inspection. Verify against the actual repository before treating any specific implementation claim as ground truth. This is the primary context document intended for AI coding agents (including Antigravity) continuing this project.

> **Document status:** This is a revision of the original `PROJECT_CONTEXT.md`. It preserves the historical implementation record (what was actually built through the original Phase 0–5 build) while documenting a deliberate, intentional architecture revision made in August 2026. See Section 14 for the revision rationale. **Current implementation and target architecture now differ in real, specific ways — this document distinguishes them explicitly throughout. Do not assume the target architecture described here is already built.**

---

## 1. Project Overview

Founder OS is an AI operating/execution system for solo startup founders. It is **not** a task-management app and **not** a generic chatbot — its objective is not simply to generate tasks, but to help a solo founder reduce repetitive execution work (research, content drafting, outreach, internal task tracking) so their limited time goes toward high-value decisions instead.

The long-term product vision is a closed loop:

```
Business Goal → Planning → Agent Execution → Real Business Actions
→ Outcomes → Measurement → Learning → Improved Planning
```

**V1 is intentionally narrow.** It does not attempt to replace an entire marketing, sales, or operations department — it consists of three specialist agents (Marketing, Sales, Operations) coordinated by a CEO Agent, each handling a small number of complete, reliable workflows rather than broad, shallow coverage.

---

## 2. Product Vision

Founder OS should function as a **daily-operating AI team**, not a single assistant — a CEO Agent plans and coordinates; specialist agents execute real work using real external tools; consequential actions are gated behind human approval; outcomes feed back into future planning. Over time, the system is meant to evolve from "executes assigned tasks reliably" toward "learns what works and improves planning accordingly" — but this learning loop is aspirational for V1, not yet built.

---

## 3. V1 Objective

Deliver a small, reliable, trustworthy version of the full vision: CEO Agent planning + three working specialist agents (Marketing, Sales, Operations), each with at least one genuinely useful, real-tool-integrated workflow, protected by a tool-execution-layer approval gate, fully observable via tracing. V1 explicitly avoids expanding into Finance, Customer Success, R&D, or advanced automation (see Section 12, V1 Boundaries).

---

## 4. Target Architecture

**This section describes the TARGET architecture the project is being revised toward. See Section 10 for what is actually implemented today, and Section 11 for the specific, current gaps between the two.**

1. **Agent orchestration:** LangGraph.
2. **Initial LLM provider:** Google Gemini.
3. **Initial primary model:** Gemini 3.5 Flash, subject to actual API/model availability and quota.
4. **Lightweight model:** Gemini 3.1 Flash-Lite may be used for simple/high-frequency operations; optional for V1.
5. **Gemini 3.1 Pro:** Explicitly NOT a required dependency — the Gemini API does not provide a free tier for it, and V1 must not depend on paid-tier-only models.
6. **LLM provider abstraction:** The model/provider layer must remain replaceable. Business logic must not be hard-coded around Gemini-specific behavior unless the API genuinely requires it. The architecture must allow swapping in OpenAI or Anthropic later without rewriting agent logic.
7. **Database:** PostgreSQL.
8. **ORM/database layer:** SQLAlchemy.
9. **Target database execution model:** Async SQLAlchemy (`AsyncSession`) + `asyncpg`. **The current repository is synchronous — this is a known, explicit target-vs-current gap, not something to claim is complete (see Section 11).**
10. **External service integration:** MCP is the standard tool/integration protocol for all external service access.
11. **Agent → external service architecture (target chain):**
    ```
    Agent
      ↓
    LangGraph
      ↓
    Tool interface
      ↓
    Approval Gate (when required)
      ↓
    MCP Client
      ↓
    MCP Server
      ↓
    External Service
    ```
12. External integrations must not be directly embedded inside agent business logic.
13. **Observability:** Langfuse.
14. **Shared state:** PostgreSQL, accessed exclusively through the repository layer.
15. **Human-in-the-loop:** Tool-layer approval gate for consequential external actions — enforced in code, not via prompt instruction.
16. **Security:** Unknown/unapproved tools fail closed (default to requiring approval).

---

## 5. Agent Responsibilities

### CEO Agent
**Purpose:** Planning and coordination — not execution.

V1 responsibilities:
1. Read company roadmap/goals.
2. Read pending tasks.
3. Read recent outcomes.
4. Read relevant company state/memory.
5. Identify priorities.
6. Generate today's task plan.
7. Assign tasks to Marketing, Sales, and Operations.
8. Review agent outcomes.
9. Generate a daily business summary.

The CEO Agent must not directly execute external business tools in V1 — this constraint is unchanged from the original architecture.

### Marketing Agent
**Purpose:** Content and demand generation.

V1 workflow:
```
Research → Content opportunity → Content creation → Approval → Publish/Draft → Outcome
```

V1 responsibilities:
1. Research relevant industry/content trends.
2. Identify content opportunities relevant to the ICP.
3. Determine content angle.
4. Generate content.
5. Create a content draft.
6. Submit external/public actions for approval.
7. Publish approved content if a supported official integration is available.
8. Record the result/outcome.

Potential V1 integrations: search/trend tool; Notion MCP (drafts/context); LinkedIn official API/MCP, if available and authorized. **Scraping or unofficial social-media automation must not be used.** If publishing access is unavailable for a given channel, the agent must fall back to draft/prepare mode rather than attempting an unsupported action.

### Sales Agent
**Purpose:** Lead qualification and revenue-oriented outreach.

V1 workflow:
```
Lead → Qualification → Research → Personalized Outreach → Approval → Send → Pipeline Update → Outcome
```

V1 responsibilities:
1. Read leads from the configured lead source.
2. Qualify leads against the company's ICP.
3. Score leads.
4. Research the relevant company/prospect.
5. Generate personalized outreach.
6. Create an email draft.
7. Submit the email for approval.
8. Send the approved email.
9. Update lead/pipeline status.
10. Record the sales outcome.

Potential V1 integrations: Google Sheets MCP; Gmail MCP; web/search tool. **Automated mass lead scraping is explicitly not a V1 requirement.**

### Operations Agent
**Purpose:** Internal execution and organization.

V1 workflow:
```
Task → Execute → Update → Report
```

V1 responsibilities:
1. Read assigned operational tasks.
2. Search/read relevant Notion information.
3. Create Notion pages.
4. Update Notion pages.
5. Create operational checklists.
6. Update task status.
7. Send approved Slack updates where appropriate.
8. Record outcomes.
9. Generate operational summaries.

Potential V1 integrations: Notion MCP; Slack MCP.

---

## 6. Tool/MCP Architecture

**MCP is a protocol/integration boundary, not an agent.** Agents reason about business tasks; MCP tools perform external actions. Example chain:

```
Sales Agent: "Send this personalized email."
  → Approval Gate
  → Gmail MCP tool
  → Gmail
```

Gmail/Notion/Slack-specific REST/SDK logic must not live directly inside agent business logic — it belongs exclusively in the MCP client/tool layer. Where a suitable official MCP server exists, it should be preferred. Where an official API exists but no suitable MCP server exists, the gap should be documented explicitly rather than silently implemented via scraping or an unofficial workaround.

**Current implementation note:** The original build already established this separation in practice — a generic MCP session/transport helper (`mcp_clients/mcp_session.py`) with thin, per-service config wrappers, using real stdio-transport MCP client/server communication (not REST wrappers) for Notion and Google Trends. This pattern is compatible with and should be preserved under the target architecture — see Section 10.

---

## 7. Database Architecture

- **Target:** PostgreSQL via async SQLAlchemy (`AsyncSession` + `asyncpg`).
- **Current:** PostgreSQL via synchronous SQLAlchemy (`Session`, `sessionmaker`) — this is a real, current-vs-target inconsistency (see Section 11), not yet migrated.
- **Core entities (implemented, unchanged by this revision):** `tasks`, `approvals`, `memory`, `outcomes` — see the original schema documentation preserved in Section 10.
- **Access pattern (unchanged, applies under both current and target models):** All agents and orchestration code must access the database exclusively through the repository layer (`db/repository/`) — never via direct SQL/ORM queries inside agent code. This constraint is independent of sync-vs-async and must be preserved regardless of which execution model is in effect at any given time.

---

## 8. Approval Architecture

Consequential external actions must be protected by the approval layer. Examples: sending an email, publishing public content, external Slack communication where appropriate, destructive operations, and other sensitive external actions.

**Approval must be enforced at the tool-execution layer, not merely through prompts** — this principle is unchanged from the original architecture and remains non-negotiable under the revised target architecture. In the target chain (Section 4, item 11), the Approval Gate sits between the Tool interface and the MCP Client — i.e., still immediately before any real external action, consistent with how it was originally implemented.

**Current implementation note:** This principle is already implemented and tested in the existing codebase (`guardrails/policies.py`, `guardrails/approval_gate.py`) using an exception-based blocking mechanism (`ApprovalPending`) and a fail-closed default for unregistered tools. This existing mechanism satisfies the target architecture's approval principle and should be preserved/reused, not rebuilt, when the agent orchestration layer migrates to LangGraph.

---

## 9. Observability

Langfuse should observe: agent runs, LLM calls, tool calls, MCP calls, failures, latency, relevant metadata, and trace IDs — used to diagnose and improve the system, not merely as a passive log.

**Current implementation note:** Function-level tracing via the `@observe` decorator is already implemented and working (see Section 10), with automatic trace nesting derived from real call structure. This satisfies the observability principle at the level currently built; it does not yet capture per-token/generation-level LLM cost detail, and does not yet have defined behavior for Langfuse unavailability (both are known, pre-existing gaps, not introduced by this revision).

---

## 10. Current Implementation State

**This section describes what has ACTUALLY been built, inspected from the original implementation history. It reflects the architecture as it stood before this revision — it is historical/current fact, not target architecture. Do not assume any of Section 4's target items are implemented unless explicitly stated here.**

- **Orchestration:** No LangGraph usage exists. All agent execution is manually triggered via standalone test scripts (`scripts/test_*.py`); there is no daily scheduler or orchestration graph.
- **LLM provider:** Claude (`claude-sonnet-4-5`), called directly via the `anthropic` Python SDK — no provider abstraction layer exists; no Gemini integration exists.
- **Structured output:** CEO Agent planning uses Anthropic's tool-calling mechanism as a schema-enforcement trick (a "fake tool" whose schema is generated from a Pydantic model, response validated via `model_validate()`).
- **Database:** PostgreSQL via **synchronous** SQLAlchemy (`Session`, `sessionmaker`) — `db/connection.py`, `db/models.py` define `Task`, `Approval`, `Memory`, `Outcome` (UUID primary keys, JSON columns for flexible output/payload/metrics).
- **Repository layer:** `db/repository/{task,approval,memory,outcome}_repository.py` — the sole sanctioned DB access point, fully implemented and working.
- **CEO Agent:** Implemented (`agents/ceo_agent/{schemas,prompts,planner}.py`) — planning only, reads roadmap/outcomes/pending tasks, writes structured daily tasks. Daily synthesis/digest generation is not yet implemented.
- **Operations Agent:** Implemented, using a real MCP client/server integration with Notion (stdio transport, live tool discovery) via `mcp_clients/notion_client.py` and the generic `mcp_clients/mcp_session.py` helper. Uses a ReAct execution loop, since refactored into a shared, reusable implementation (`agents/shared/react_agent.py::run_react_loop()`).
- **Marketing Agent:** Code implemented (`agents/marketing_agent/{prompts,tools,agent}.py`), combining Google Trends and Notion MCP tools; end-to-end test execution status not confirmed as of the last recorded session.
- **Sales Agent:** Not implemented. Gmail/Sheets MCP clients exist as empty stub files (`mcp_clients/gmail_client.py`, `sheets_client.py`), blocked on a Google OAuth setup walkthrough not yet completed.
- **Approval gate:** Implemented and tested (`guardrails/{policies,approval_gate}.py`) — fail-closed default, exception-based blocking (`ApprovalPending`), integrated into Operations (and, via the shared loop, Marketing) agents' `execute_tool()`. Resolution is currently CLI-only (`scripts/approve_pending.py`).
- **Observability:** Implemented — Langfuse Cloud, `@observe` decorator applied to CEO and Operations (and Marketing, via the shared loop) agent functions, with automatic trace nesting. No per-token cost tracking; no defined Langfuse-unavailable fallback.
- **Memory:** Only simple structured key/value facts (e.g., roadmap) in the `Memory` table, insert-only. No unstructured/RAG memory, no pgvector.
- **Frontend/API:** Neither implemented — `frontend/` and `api/` exist only as scaffolded, empty folders per the original project structure. All human interaction is currently via CLI scripts.
- **Evaluation pipeline:** Not implemented — `evals/` scaffolded, empty.

---

## 11. Known Architectural Inconsistencies (Current vs. Target)

These are the specific, current gaps between what's built (Section 10) and the target architecture (Section 4), introduced or clarified by the August 2026 revision. **Do not treat these as resolved — they are open work.**

1. **Orchestration:** Currently manual test-script triggering; target is LangGraph-based orchestration. No migration has occurred.
2. **LLM provider:** Currently hard-wired to direct Anthropic Claude SDK calls with no abstraction layer; target is Gemini as the initial provider, behind a provider-agnostic abstraction layer that would also support Anthropic/OpenAI. This is a genuine rewrite of the LLM-calling layer, not an additive change — CEO Agent's structured-output mechanism (Anthropic tool-calling-as-schema-trick) is provider-specific and will need a Gemini-compatible equivalent designed as part of this migration.
3. **Database execution model:** Currently fully synchronous SQLAlchemy throughout the repository layer and CEO planner; target is async (`AsyncSession` + `asyncpg`). This has NOT been migrated. Any future work must not claim this migration is complete without it actually being done and verified.
4. **Async/sync boundary shift:** Under the original architecture, async was deliberately isolated to the MCP client boundary only (a documented, intentional decision). Under the target architecture (async DB), this boundary decision will need to be explicitly revisited — moving to async DB access likely means async will need to extend further than originally scoped. This should be treated as a deliberate future design decision, not an automatic consequence to implement without discussion.
5. **Tool-execution chain shape:** The target chain explicitly includes LangGraph and a distinct "Tool interface" layer between the agent and the Approval Gate (Section 4, item 11). The current implementation's chain is agent → `tools.py::execute_tool()` → approval gate → MCP client, without a LangGraph layer. Reconciling this shape with LangGraph's own tool-calling/graph-node conventions is unresolved design work, not yet started.

---

## 12. V1 Boundaries

**Explicitly excluded from V1** (per this revision — treat these as out of scope unless a future, separate decision changes this):

- Automated lead discovery/enrichment
- CRM integrations beyond the planned Sheets-as-pipeline approach
- Advanced sales automation
- Autonomous follow-up campaigns
- Advanced marketing analytics
- Autonomous experimentation
- SEO engine
- Paid advertising
- Finance Agent
- Customer Success Agent
- Product/R&D Agent
- Recruiting Agent
- Advanced financial forecasting
- Autonomous financial decisions
- Broader autonomous business optimization

V1 must remain narrow, reliable, and limited to CEO Agent + Marketing + Sales + Operations, each with the specific workflows described in Section 5 — not broader departmental coverage.

---

## 13. Future Direction

The long-term goal is to evolve Founder OS into a business execution system that measurably helps improve business outcomes and eventually contributes to growth/revenue — but this remains a long-term direction, not a V1 commitment. The items in Section 12 represent the expansion path once V1 is proven reliable, not a backlog to be pulled forward incidentally during V1 work.

---

## 14. Important Engineering Constraints

These constraints apply regardless of current-vs-target architecture state, and must be preserved by any future development:

- Approval enforcement must always be at the tool-execution layer, never solely prompt-based — this is unchanged by the LangGraph/Gemini revision.
- The repository layer remains the sole DB access point — this is unchanged regardless of sync-vs-async migration status.
- MCP remains the standard external-integration boundary — no provider-specific REST/SDK logic embedded directly in agent business logic.
- The LLM provider layer must remain swappable — avoid Gemini-specific business logic bleeding into agent reasoning code.
- Unknown/unapproved tools must fail closed (require approval) by default.
- Do not claim an architectural migration (async DB, LangGraph, Gemini) is complete unless it has actually been implemented and verified — Section 11's inconsistencies must be updated/resolved individually as actual work is done, not assumed complete because this document describes the target.
- Do not silently expand V1 scope into any item listed in Section 12.

---

## Architecture Revision — August 2026

The project's architecture was intentionally revised in August 2026 from the original implementation (direct Anthropic Claude SDK calls, no orchestration framework, fully synchronous SQLAlchemy) toward a new target stack:

**LangGraph + Gemini (behind a provider-agnostic model layer) + PostgreSQL + async SQLAlchemy + MCP + Approval Gate + Langfuse.**

This revision is deliberate, not corrective — the original implementation was functionally sound and its core safety/architectural principles (repository-layer-only DB access, tool-execution-layer approval enforcement, MCP as the external-integration boundary, Langfuse observability) are being **carried forward, not discarded**, into the new stack. What's changing is the orchestration framework, the LLM provider (with an explicit new requirement for provider-agnosticism going forward), and the database execution model (sync → async).

This document (`PROJECT_CONTEXT.md`) has been updated accordingly: Sections 1–3 and 5–9 and 12–14 describe the enduring product vision, V1 scope, and non-negotiable architectural principles that survive this revision unchanged. Section 4 describes the new target architecture. Section 10 preserves an accurate record of what was actually built under the original architecture, for continuity and so that working, tested components (the approval gate, the repository layer's data model, the MCP session pattern) are reused rather than rebuilt from scratch during the migration. Section 11 documents the specific, current gaps between the original implementation and this new target, and must be updated as each gap is actually closed — not marked resolved preemptively.

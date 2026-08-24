# Founder OS — Product Requirements Document

> **Provenance note:** This PRD was generated/updated from the complete design and build conversation history for this project, not from direct filesystem inspection. Verify against the actual repository before treating any implementation claim as ground truth.

> **Document status:** This is a revision of the original PRD, updated to reflect the August 2026 architecture and V1 scope revision (see `PROJECT_CONTEXT.md`'s "Architecture Revision — August 2026" section for full rationale). Product vision and core principles are preserved from the original; target architecture, agent workflows, and the phase roadmap have been updated. Sections below distinguish CURRENT IMPLEMENTATION from TARGET/V1 REQUIREMENTS throughout.

---

## 1. Product Overview

Founder OS is an AI operating/execution system for solo founders. Its purpose is to reduce repetitive business execution work and help the founder focus on high-value decisions — it is **not** simply an AI task generator, and V1 does not attempt to replace an entire department.

The long-term product loop:
```
Business Goal → Strategy/Planning → Agent Execution → Real Business Actions
→ Outcomes → Analysis → Improved Planning
```

V1 intentionally implements only a small number of complete, reliable workflows — three specialist agents (Marketing, Sales, Operations) plus a CEO coordination layer — rather than broad departmental coverage.

---

## 2. V1 Product Principle

V1 prioritizes:
- Real execution (genuine tool-mediated actions, not simulated output)
- Real integrations (official APIs/MCP servers, not scraping or unofficial automation)
- Reliable workflows (a small number done well, not many done shallowly)
- Human approval for consequential actions (enforced at the tool-execution layer)
- Measurable outcomes
- Explainability
- Observability

V1 explicitly does **not** attempt to replace an entire department. The goal is three useful specialist workflows plus a CEO coordination layer, built to a genuinely reliable standard.

---

## 3. Target Users

Unchanged from the original PRD: a solo, early-stage startup founder managing product, marketing, sales, finance, and operations without a team, needing day-to-day execution help without losing control over consequential actions. Secondary user: developers/AI coding agents maintaining and extending the system.

---

## 4. Core Product Workflow

The daily lifecycle remains conceptually unchanged from the original PRD (founder/company context → CEO planning → task generation → specialist agent execution → tool usage → approval → outcomes → memory → CEO synthesis → daily digest → evaluation/observability). What has changed is the underlying architecture executing this workflow — see Section 6 (Target Architecture) and Section 7 (Agent Architecture — V1 Requirements) below for the current, revised specifics.

---

## 5. System Architecture — Overview

**High-level target chain for all agent-to-external-service actions:**
```
Agent → LangGraph → Tool interface → Approval Gate → MCP Client → MCP Server → External Service
```

This chain is new/explicit as of this revision. See Section 6 for full target architecture detail and Section 12 (Current Implementation State) for what's actually built today.

---

## 6. Target Architecture

1. **Agent orchestration:** LangGraph.
2. **LLM provider:** Google Gemini (initial provider). Preferred initial model: **Gemini 3.5 Flash**, subject to actual API availability/quota. Optional lightweight model: **Gemini 3.1 Flash-Lite**. **Gemini 3.1 Pro must not be a required V1 dependency** — no free API tier exists for it.
3. **Provider-agnosticism requirement:** The architecture must remain provider-agnostic. Business logic must not be hard-coded around Gemini-specific behavior. The system must support swapping in another provider (e.g., Anthropic, OpenAI) later without rewriting agent logic.
4. **Database:** PostgreSQL, as persistent shared state.
5. **Target database execution model:** SQLAlchemy `AsyncSession` + `asyncpg`. **Existing synchronous code may remain temporarily during migration** — this PRD identifies async as the target, not as already complete (see Section 12/13).
6. **Repository layer:** Remains the sole boundary between agents and database persistence. Agents must not write raw SQL.
7. **External integration protocol:** MCP is the preferred protocol. Where a suitable official MCP server exists, use it. Where none exists, document the gap rather than introducing scraping to satisfy a requirement.
8. **Approval:** Enforced at the tool-execution layer (unchanged core principle from the original PRD).
9. **Observability:** Langfuse — agent traces, LLM calls, tool calls, MCP calls, latency, failures, debugging, and (future) evaluation support.

---

## 7. Agent Architecture — V1 Requirements

### CEO Agent
1. Reads company goals and roadmap.
2. Reads recent outcomes.
3. Reads pending tasks.
4. Reads relevant company context/memory.
5. Identifies priorities.
6. Generates daily tasks.
7. Assigns tasks to Marketing, Sales, and Operations.
8. Reviews completed outcomes.
9. Produces a daily business summary.

The CEO Agent does not directly execute external tools in V1 — unchanged constraint.

### Marketing Agent
**Workflow:** `Research → Content Opportunity → Content Creation → Approval → Publish/Draft → Outcome`

1. Research relevant trends/topics.
2. Identify content opportunities.
3. Determine content angle.
4. Generate content.
5. Create a content draft.
6. Submit public/external actions for approval.
7. Publish approved content when an official supported integration exists.
8. Record outcome.

**Initial integrations:** search/trend tool; Notion MCP; LinkedIn integration only where official API access is available. **If publishing access is unavailable, the system must support draft/prepare mode** rather than failing or attempting an unsupported action. No scraping or unofficial social automation.

### Sales Agent
**Workflow:** `Lead → Qualify → Research → Personalized Outreach → Approval → Send → Pipeline Update → Outcome`

1. Read leads from the configured source.
2. Qualify against ICP.
3. Score leads.
4. Research prospect/company.
5. Generate personalized outreach.
6. Create email draft.
7. Request approval.
8. Send approved email.
9. Update lead/pipeline status.
10. Record sales outcome.

**Initial integrations:** Google Sheets MCP; Gmail MCP; web/search tool. V1 does not require automated mass lead generation or scraping.

### Operations Agent
**Workflow:** `Task → Execute → Update → Report`

1. Read assigned operational tasks.
2. Search/read relevant Notion information.
3. Create Notion pages.
4. Update Notion pages.
5. Create operational checklists.
6. Update task status.
7. Send approved Slack updates where appropriate.
8. Record outcomes.
9. Generate operational summary.

**Initial integrations:** Notion MCP; Slack MCP.

---

## 8. Shared State and Database

**Target:** PostgreSQL via async SQLAlchemy (`AsyncSession` + `asyncpg`), accessed exclusively through the repository layer.
**Current:** PostgreSQL via synchronous SQLAlchemy — this PRD does not claim the async migration is complete (see Section 12/13). The core entities (`tasks`, `approvals`, `memory`, `outcomes`) and the repository-layer-only access pattern are unchanged by this revision and should be preserved/reused, not rebuilt, regardless of sync/async status.

---

## 9. MCP and External Tool Architecture

MCP is the preferred external integration protocol. Target chain (repeated from Section 5/6 for completeness):
```
Agent → LangGraph → Tool interface → Approval Gate → MCP Client → MCP Server → External Service
```

Agents must not contain service-specific API implementation — this belongs exclusively in the MCP client/tool layer, unchanged principle from the original PRD. Where no suitable official MCP server exists, document the limitation rather than introducing scraping merely to satisfy the requirement.

**Current implementation note:** A generic MCP session/transport helper and thin per-service config wrappers already exist for Notion and Google Trends, using real stdio-transport MCP client/server communication. This pattern should be preserved and extended (Gmail, Sheets, Slack, LinkedIn where available) rather than rebuilt when LangGraph is introduced.

---

## 10. Approval and Guardrails

Approval is enforced at the tool-execution layer — unchanged, non-negotiable principle. Actions requiring approval include: sending emails, publishing public content, sensitive external communication, destructive actions, and other consequential external actions. Unknown tools must fail closed.

**Current implementation note:** This is already implemented and tested (exception-based blocking, fail-closed default for unregistered tools) and should be reused/extended into the LangGraph-based execution chain, not rebuilt.

---

## 11. Observability

Langfuse is used for: agent traces, LLM calls, tool calls, MCP calls, latency, failures, debugging, and evaluation support (future). Unchanged principle from the original PRD; current implementation (function-level `@observe` tracing) should be extended to cover new LangGraph nodes and the Gemini provider layer as they're introduced, not replaced with a different observability approach.

---

## 12. Current Implementation State

*(Preserved from the prior PRD revision, reflecting the original build — see also `PROJECT_CONTEXT.md` Section 10 for full detail.)*

- No LangGraph usage exists yet — orchestration is currently manual test-script triggering.
- LLM calls go directly through the Anthropic SDK (Claude) with no provider abstraction layer — no Gemini integration exists yet.
- Database access is fully synchronous SQLAlchemy, not async.
- CEO Agent (planning only), Operations Agent (Notion MCP, ReAct loop), and Marketing Agent (Trends + Notion MCP, code written, end-to-end pass not confirmed) are implemented under the original architecture.
- Sales Agent is not implemented; Gmail/Sheets MCP clients are stubs, blocked on Google OAuth setup.
- The approval gate, repository layer, and Langfuse tracing are implemented and working under the original architecture and are intended to carry forward into the new target architecture with reuse/extension, not a rewrite.

---

## 13. Known Architectural Inconsistencies (Current vs. Target)

Repeated here for completeness (full detail in `PROJECT_CONTEXT.md` Section 11):
1. No LangGraph orchestration exists yet.
2. LLM provider is currently Anthropic-specific with no abstraction layer; target is Gemini behind a provider-agnostic layer.
3. Database is currently synchronous; target is async (`AsyncSession` + `asyncpg`) — not yet migrated.
4. The async/sync boundary decision (previously scoped to only the MCP client layer) will need to be explicitly revisited once async DB access is introduced.
5. The target tool-execution chain now explicitly includes a LangGraph layer and a distinct "Tool interface" layer not present in the current implementation's chain shape.

**Do not claim any of these are resolved unless actually implemented and verified.**

---

## 14. V1 Success Criteria

**CEO:**
- Can generate a plan from real company state.
- Creates specialist tasks.
- Reviews outcomes.
- Produces a daily summary.

**Marketing:**
- Can research.
- Generate content.
- Create a draft.
- Pass through approval.
- Publish when supported, OR reliably fall back to draft mode.
- Record an outcome.

**Sales:**
- Can read leads.
- Qualify and score them.
- Research them.
- Generate personalized outreach.
- Create an approval request.
- Send an approved email.
- Update pipeline state.
- Record outcome.

**Operations:**
- Can execute assigned tasks.
- Interact with Notion.
- Interact with Slack where required.
- Pass consequential actions through approval.
- Record outcomes.

**System-wide:**
- LangGraph orchestration works.
- MCP integration works.
- PostgreSQL shared state works.
- Approval gate works.
- Langfuse tracing works.
- Failures are observable.
- No secrets are hard-coded.

---

## 15. Phase-by-Phase Implementation Plan

### Phase 0 — DB schema + connection — COMPLETED
Unchanged from original build. See `PROJECT_CONTEXT.md` Section 10 for detail.

### Phase 1 — Repository layer — COMPLETED
Unchanged from original build.

### Phase 2 — CEO Agent — COMPLETED
Implemented under the original architecture (direct Anthropic SDK calls, sync DB). **Note:** this phase's LLM-calling mechanism will need revisiting once the Gemini/provider-agnostic migration (Phase 6+ or a dedicated future phase) occurs — not yet scheduled as a distinct phase in this revision.

### Phase 3 — Operations Agent + first MCP integration — COMPLETED
Implemented under the original architecture (Notion MCP via stdio transport, ReAct loop later refactored into a shared/generic implementation).

### Phase 4 — Approval Gate — COMPLETED
Implemented and tested; principle and mechanism carry forward unchanged into the target architecture.

### Phase 5 — Langfuse Observability — COMPLETED
Implemented; carries forward, to be extended as new components (LangGraph nodes, Gemini calls) are added.

### Phase 6 — Growth & Execution Agents — REVISED SCOPE, IN PROGRESS
**Revised objective:** Complete the V1 Marketing and Sales workflows exactly as defined in Section 7, stabilize Operations, and standardize the LangGraph + MCP + Approval architecture across all three specialist agents. **Do not expand this phase beyond the V1 workflows defined in Section 7.**
- Marketing V1 workflow (Research → Content Opportunity → Content Creation → Approval → Publish/Draft → Outcome).
- Sales V1 workflow (Lead → Qualify → Research → Personalized Outreach → Approval → Send → Pipeline Update → Outcome).
- Operations stabilization.
- Standardized LangGraph + MCP + approval architecture applied consistently across all three agents.
- **Status note:** Marketing Agent code exists from the original architecture (direct Anthropic calls, no LangGraph) — this needs to be reconciled with the new target architecture as part of completing this phase, not assumed already compliant.

### Phase 7 — Memory + onboarding + pgvector — NOT STARTED
Unchanged objective from prior PRD revision.

### Phase 8 — CEO synthesis + daily digest — NOT STARTED
Unchanged objective from prior PRD revision.

### Phase 9 — Evaluations — NOT STARTED
Unchanged objective from prior PRD revision.

### Phase 10 — Frontend dashboard — NOT STARTED
Unchanged objective from prior PRD revision.

---

## 16. Functional Requirements

Requirements from the original PRD (FR-001 through FR-018) remain valid where they describe principles unchanged by this revision (repository-layer-only DB access, approval enforcement, live tool discovery, outcome recording, fail-closed defaults). The following requirements are **new or revised** as of this architecture update:

- **FR-019:** Agent orchestration must be implemented via LangGraph; no alternate orchestration framework should be introduced without explicit approval.
- **FR-020:** The LLM-calling layer must be provider-agnostic; Gemini-specific logic must not be hard-coded into agent business logic.
- **FR-021:** Gemini 3.5 Flash is the preferred initial model; Gemini 3.1 Pro must not be treated as a required dependency.
- **FR-022:** Database access must migrate toward async SQLAlchemy (`AsyncSession` + `asyncpg`) as the target execution model; this PRD does not claim this migration is complete.
- **FR-023:** The Marketing Agent must support a draft/prepare fallback mode when official publishing access is unavailable for a given channel.
- **FR-024:** The Sales Agent must qualify and score leads against the company's ICP before generating outreach, not merely draft outreach for all leads indiscriminately.
- **FR-025:** V1 must not implement automated mass lead scraping or unofficial social media automation, regardless of technical feasibility.

---

## 17. Non-Functional Requirements

Unchanged from the original PRD (Reliability, Scalability, Observability, Maintainability, Security, Data integrity, Error handling, Testability, Modularity) — see prior revision for full detail. One addition:

- **Provider replaceability:** The system must be structured so that changing the underlying LLM provider does not require rewriting agent reasoning logic — a new non-functional requirement introduced by this revision.

---

## 18. Architectural Constraints

Unchanged constraints from the original PRD, plus the following, new to this revision:
- Do not introduce a second agent orchestration framework alongside or instead of LangGraph without explicit approval.
- Do not scatter provider-specific (Gemini) logic throughout agent/business logic — keep model construction/configuration centralized.
- Do not claim the async database migration is complete unless it has actually been done and verified.
- Do not expand Phase 6 beyond the V1 workflows explicitly defined in Section 7.

---

## 19. Out of Scope (Future/V2/V3)

Revised and expanded list, explicitly kept as future scope, not V1:
- Automated lead discovery/enrichment
- Enrichment providers
- CRM integrations beyond the planned Sheets-as-pipeline approach
- Autonomous follow-up campaigns
- Advanced marketing analytics
- Experimentation engine
- SEO
- Paid advertising
- Finance Agent
- Customer Success Agent
- Product Agent
- Recruiting Agent
- Advanced forecasting
- Autonomous business optimization

---

## 20. Known Limitations

Carried forward from the original PRD revision (no scheduler, no API layer, no frontend, no memory/RAG, Sales Agent unimplemented, no eval harness, no per-token Langfuse cost tracking, no Alembic migrations in active use, task status as plain strings) — plus, new to this revision:
- No LangGraph implementation exists yet; the current orchestration approach (manual scripts) has not been migrated.
- No Gemini/provider-agnostic LLM layer exists yet; all current LLM calls are Anthropic-specific.
- No async database implementation exists yet.

---

## 21. Definition of Done

Unchanged in substance from the original PRD's Definition of Done, updated to reference the current target stack: full LangGraph orchestration, Gemini behind a provider-agnostic layer (with provider swap demonstrated as a stretch goal), async database access, all V1 success criteria (Section 14) met, plus memory/RAG, CEO synthesis, evaluations, API, and frontend as previously defined.

---

## V1 Scope Boundary

The purpose of V1 is to demonstrate **reliable end-to-end business execution through a small number of real workflows** — CEO planning + Marketing's research-to-draft-or-publish workflow + Sales' lead-to-outreach workflow + Operations' task-to-report workflow — each using real integrations, protected by a genuine approval gate, and fully observable. V1 is explicitly **not** an attempt at broad departmental replacement, and any pressure to expand agent count, integration breadth, or autonomous capability beyond what's defined in Section 7 should be treated as out of scope (Section 19) until V1 is proven reliable end-to-end.

---

*Only PRD.md was updated in the course of producing this document. No source code was modified.*

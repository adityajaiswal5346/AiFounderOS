# AGENTS.md — Development Rules for AI Coding Agents

These are persistent, binding instructions for any AI coding agent (including Antigravity, Claude Code, or others) continuing development on Founder OS. They apply to every task, every phase, every session.

> **Document status:** This is a revision of the original AGENTS.md, updated to reflect the August 2026 architecture decision (LangGraph + Gemini + async database target + MCP + Approval Gate + Langfuse). Rules unchanged by this revision are preserved; new/revised rules are marked accordingly. See `PROJECT_CONTEXT.md`'s "Architecture Revision — August 2026" section for full rationale.

---

## 1. Project Context

Founder OS is an **existing, partially implemented multi-agent AI system** — not a greenfield project. Phases 0–5 are completed under the original architecture (direct Anthropic SDK calls, no orchestration framework, synchronous SQLAlchemy). Phase 6 is in progress under a **revised target architecture** (LangGraph, Gemini, async database target). Before writing any code, understand what already exists and which architecture (original vs. target) a given piece of code currently reflects — do not assume.

---

## 2. Source of Truth Hierarchy

Unchanged:
1. Actual source code and tests
2. Database/schema/migrations
3. `PROJECT_CONTEXT.md`
4. `PRD.md`
5. Phase/implementation documentation (`PROJECT_PROGRESS.md`, etc.)
6. Previous AI conversation context

If documentation conflicts with actual implementation, inspect the code and report the discrepancy — do not blindly follow documentation, and do not assume the target architecture is already implemented merely because it's documented as the target.

---

## 3. Mandatory Repository Inspection

Unchanged — before implementing any phase or feature: read `PROJECT_CONTEXT.md`, `PRD.md`, inspect relevant source files, inspect callers of anything you're about to modify, inspect related database models/repositories, inspect related tests, understand existing interfaces, and determine what's already implemented before writing new code. Do not start coding from the task description alone.

---

## 4. Core Architecture Rules — Agent Orchestration (NEW/REVISED)

**LangGraph is the preferred orchestration framework.** Do not introduce another agent orchestration framework unless explicitly approved.

LangGraph should be responsible for: state, nodes, transitions, conditional routing, retries, interrupts, workflow orchestration, and multi-agent coordination.

**Do not create independent custom ReAct architectures for each agent when a shared LangGraph pattern can be reused.** Note: the existing `agents/shared/react_agent.py::run_react_loop()` was built under the original (pre-LangGraph) architecture as a reusable ReAct loop — when migrating to LangGraph, evaluate whether its logic can be reimplemented as a LangGraph pattern (nodes/edges) rather than assuming it must be discarded outright; inspect first, per Section 3.

---

## 5. LLM Provider (NEW/REVISED)

**The initial LLM provider is Google Gemini.** Preferred initial model: Gemini 3.5 Flash, subject to actual API availability/quota. Optional lightweight model: Gemini 3.1 Flash-Lite. **Do not make Gemini 3.1 Pro a required V1 dependency** (no free API tier).

**The LLM provider must remain replaceable.** Do not spread provider-specific implementation throughout agent/business logic. Keep model construction/configuration centralized. Agents should depend on a model interface/configuration, not hard-coded provider details scattered across the codebase.

**Do not switch providers or introduce additional providers without an explicit architectural decision.** Note: the existing CEO Agent's structured-output mechanism (Anthropic tool-calling used as a schema-enforcement trick) is Anthropic-specific and will need a Gemini-compatible equivalent designed during migration — this is expected, planned work, not an error to silently "fix" by reverting to Anthropic.

---

## 6. Database (REVISED)

PostgreSQL is the shared persistent state. **Target architecture: SQLAlchemy `AsyncSession` + `asyncpg`.**

The repository layer is the ONLY normal interface between agents and database persistence. Agents must not write raw SQL, directly manipulate database tables, or create independent database sessions.

**IMPORTANT:** The existing codebase contains synchronous repositories (confirmed, not merely "may contain" — this is the actual current state). **Do NOT blindly rewrite all database code.** Before changing database interfaces:
1. Inspect callers.
2. Inspect dependency injection.
3. Inspect FastAPI usage (where it exists).
4. Inspect LangGraph nodes (once introduced).
5. Inspect tests.
6. Migrate incrementally.

Preserve working behavior during migration — do not attempt a wholesale sync-to-async rewrite in a single uncoordinated pass.

---

## 7. MCP (REVISED — chain shape updated)

MCP is the standard external integration protocol. Preferred architecture:
```
Agent → LangGraph → tool interface → approval gate → MCP client → MCP server → external service
```

Agents must not contain provider-specific Gmail/Notion/Slack/etc. API implementation — this belongs exclusively in the MCP client/tool layer, unchanged principle. Use MCP where a suitable official MCP server exists; prefer live tool discovery when appropriate. Do not use unofficial scraping to bypass missing API/MCP access.

If an integration cannot be implemented due to permissions/API availability: document the limitation, implement a safe draft/prepare mode if possible, and do not silently introduce unsupported automation.

**Note:** The existing `mcp_clients/mcp_session.py` generic transport helper and its thin per-service config wrappers (Notion, Google Trends) already satisfy the "MCP client → MCP server → external service" portion of this chain under the original architecture. This should be preserved and extended, not rebuilt, as the LangGraph and Tool Interface layers are introduced above it.

---

## 8. Approval Gate (UNCHANGED — reaffirmed as non-negotiable)

Approval must be enforced at the tool-execution layer. **Never rely solely on an LLM prompt to prevent a consequential action.**

Actions requiring approval: send email, publish public content, sensitive external communication, destructive operations, and other consequential external actions — evaluated by the approval policy. Unknown tools must fail closed. Agents must not bypass the approval layer.

**Note:** This is already implemented (`guardrails/policies.py`, `guardrails/approval_gate.py`, exception-based blocking via `ApprovalPending`) and tested under the original architecture. This mechanism should be reused/extended into the LangGraph-based chain, not rebuilt from scratch.

---

## 9. Shared State (CLARIFIED)

Agents communicate indirectly through shared persistent state, not direct calls. Do not create unnecessary direct agent-to-agent calls. Use PostgreSQL, the repository layer, task state, outcome records, memory, and events where implemented.

Example: Sales produces a customer-won outcome; the CEO/Operations layer observes that outcome through shared state rather than Sales directly invoking Operations. This is consistent with, and unchanged from, the original architecture's shared-state-store principle.

---

## 10. Observability (UNCHANGED)

Langfuse is the standard observability layer. Instrument: agent runs, LLM calls, tool calls, MCP calls, important workflow transitions, errors, latency, and relevant metadata. Do not create a second observability platform unless explicitly approved.

**Note:** Existing `@observe` decorator coverage (CEO, Operations, Marketing agent functions) should be extended to cover new LangGraph nodes and Gemini calls as they're introduced — do not replace the tracing mechanism, extend it.

---

## 11. V1 Agent Boundaries (NEW — explicit scope guardrail)

- **CEO:** Planning and coordination only.
- **Marketing:** Research → content → approval → publish/draft → outcome.
- **Sales:** Lead → qualification → research → outreach → approval → send → pipeline → outcome.
- **Operations:** Task → Notion/Slack execution → update → outcome.

**Do not expand V1 into full departmental replacement.** Finance, Customer Success, R&D/Product, and Recruiting agents remain explicitly out of scope (see `PRD.md` Section 19) unless a separate, explicit scoping decision changes this.

---

## 12. Engineering Principle (NEW)

Prefer: small tools, explicit schemas, deterministic business logic, narrow agent responsibilities, reusable LangGraph patterns, repository abstractions, explicit state transitions, approval policies, observable execution.

Avoid: giant agent prompts, giant multi-purpose tools, hidden side effects, direct database access from agents, provider-specific logic scattered across the application, unofficial scraping, unnecessary abstractions, speculative future features.

---

## 13. Existing Codebase (NEW — explicit non-destructive-migration rule)

The repository contains historical implementation choices (direct Anthropic SDK usage, synchronous SQLAlchemy, no LangGraph) that differ from the target architecture. **Do not assume existing code is wrong merely because it differs from the target.**

Before modifying an existing component:
1. Inspect the implementation.
2. Inspect all callers.
3. Inspect tests.
4. Understand its role in the workflow.
5. Identify migration impact.
6. Make the smallest safe change.

**Do not reconstruct the project from scratch.** Preserve working functionality whenever possible — this applies with equal force to the architecture migration itself, not just to individual feature work.

---

## 14. Documentation vs. Implementation (REAFFIRMED)

Always distinguish CURRENT IMPLEMENTATION from TARGET ARCHITECTURE. Never claim a component is implemented merely because it exists in the PRD. Never delete working code simply because documentation is outdated.

If documentation and implementation disagree:
1. Inspect the repository.
2. Report the discrepancy.
3. Propose a migration.
4. Wait for approval before destructive refactoring.

---

## 15. Phase Execution (REAFFIRMED, unchanged process)

The project is implemented phase-by-phase. Do not automatically jump to later phases. Before implementing a phase:
1. Inspect current state.
2. Read `PRD.md`.
3. Read `PROJECT_CONTEXT.md`.
4. Read `AGENTS.md` (this file).
5. Identify dependencies.
6. Create/confirm an implementation plan.
7. Implement only the requested phase.
8. Run tests.
9. Update implementation documentation (`PROJECT_PROGRESS.md`).

Do not implement future-scope features unless explicitly requested.

---

## 16. Current V1 Priority (NEW)

The priority is to finish a reliable, internship-portfolio-ready V1. The project should demonstrate: LangGraph, Gemini, MCP, PostgreSQL, the async database target architecture (even if migration is incremental/in progress), the approval gate, Langfuse, three genuinely useful specialist workflows, real external tool execution, persistent outcomes, and CEO planning/synthesis.

**Depth and reliability are more important than the number of agents or tools.** Do not add agents, integrations, or capabilities beyond V1 scope in pursuit of "more impressive" surface area.

---

## 17. Security (REAFFIRMED, extended)

Never: hard-code API keys, commit secrets, bypass OAuth, bypass approval policies, use scraping to bypass official API restrictions, expose credentials in logs, execute arbitrary unknown tools. Use environment variables/secrets management.

---

## 18. V1 External Integrations (NEW — explicit, do-not-assume-availability rule)

Primary intended integrations:
- **Marketing:** search/trend tooling; Notion MCP; official social publishing integration if available.
- **Sales:** Google Sheets MCP; Gmail MCP; web/search.
- **Operations:** Notion MCP; Slack MCP.

**Do not assume an integration is available merely because it appears in the PRD. Verify the actual MCP server/API availability before implementing against it.**

---

## 19. Async/Sync Consistency (UPDATED from original — no longer a fixed permanent boundary)

The original architecture deliberately isolated async usage to the MCP client boundary only. **This is now explicitly a migration-in-progress area, not a permanent boundary** — the target architecture calls for async database access as well. Do not, however, treat this as license to convert code to async opportunistically or piecemeal without a plan; follow Section 6's incremental migration rule (inspect callers, dependency injection, tests, migrate incrementally, preserve working behavior).

---

## 20. Error Handling (REAFFIRMED, unchanged)

External systems and LLM calls can fail. New functionality must handle expected failure modes explicitly, avoid silently swallowing important exceptions, return meaningful errors, preserve Task/Outcome state consistently, record important failures in observability, and avoid leaving tasks permanently stuck in an invalid state. Do not use broad exception handling without specific justification — the existing `except ApprovalPending` pattern remains the model to follow.

---

## 21. Testing (REAFFIRMED, unchanged)

Every new feature must include appropriate tests (unit, integration, MCP/tool, database, agent behavior, end-to-end as relevant). Testing has so far been manual scripts, not an automated suite — introducing proper automated tests is encouraged, consistent with the eventual Phase 9 eval pipeline. Before declaring a phase/task complete: run relevant existing tests/scripts, run new tests, verify no regressions. Do not claim a feature is complete without actually verifying it runs correctly.

---

## 22. Dependencies (REAFFIRMED, unchanged process, new context)

Before adding a dependency: check for an existing equivalent, check existing versions in `pyproject.toml`, prefer existing libraries, add only when necessary. Note: this revision itself introduces the need for new dependencies (`langgraph`, a Gemini SDK, `asyncpg`, async SQLAlchemy extras) — these are expected additions for this migration, not violations of this rule, but should still be added deliberately and documented, not silently.

Use `uv add <package>` / `uv sync`, consistent with established project tooling.

---

## 23. Code Style (REAFFIRMED, unchanged)

Small, focused functions; clear names; type hints; focused modules; explicit interfaces; reusable abstractions. Avoid massive files, duplicated logic, unnecessary abstractions, dead code, unused imports, magic values. Do not refactor unrelated code while implementing a phase or task.

---

## 24. Documentation (REAFFIRMED, unchanged)

After completing a phase or significant task, update `PROJECT_PROGRESS.md` (which combines the roles of phase-status and implementation-log tracking for this project). Record what was implemented, files created/modified, database changes, API changes, tests added/executed/results, known limitations, architectural decisions, and next-phase dependencies. Update `PROJECT_CONTEXT.md`/`PRD.md` if a phase status materially changes.

---

## 25. Phase Completion Criteria (REAFFIRMED, unchanged)

A phase is not complete merely because code has been written. Complete only when: required functionality is implemented, existing functionality still works, tests added/passing, integration points verified, error handling exists, observability integrated, documentation updated, no unnecessary architectural duplication introduced, known limitations documented.

---

## 26. Stop Conditions (REAFFIRMED, unchanged)

Stop and ask for clarification rather than proceeding on assumption when: requirements conflict with existing architecture, a destructive database migration appears necessary, existing behavior would need to be intentionally broken, authentication/security requirements are unclear, a major architectural change seems required, `PRD.md` and actual code disagree significantly, a required external service/API is unavailable/misconfigured/unspecified, or intended behavior cannot be determined safely. Do not make large architectural decisions silently.

---

## 27. Final Report After Every Implementation (REAFFIRMED, unchanged)

After completing any task or phase: summary of implementation, files created/modified, existing files/functions reused, database changes, API changes, tests added/executed/results, known limitations, architectural decisions and why, suggested next step. Do not automatically implement the suggested next step.

---

## Final Rule

The goal is not to maximize technical complexity. The goal is to build a coherent, reliable AI business-execution system where:

- **LangGraph** controls workflows,
- **Gemini** provides reasoning,
- **MCP** connects the agents to external services,
- **PostgreSQL** stores shared state,
- **Approval Gate** protects consequential actions,
- and **Langfuse** makes execution observable.

Any architectural change that materially affects these boundaries requires explicit approval. When uncertain: inspect first, reason about the existing architecture second, and ask before making any destructive or irreversible decision.

---

*Only `AGENTS.md` was updated in the course of producing this document. No source code was modified.*

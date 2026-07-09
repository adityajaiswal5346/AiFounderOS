# Demo Script

## Setup (before the call)

1. `docker-compose up -d` — Postgres running
2. `python scripts/seed_onboarding.py` — long-term memory seeded with company profile
3. `uvicorn api.main:app --reload` — API up on :8000
4. `npm run dev` (frontend/) — UI up on :3000
5. Open browser to `http://localhost:3000/dashboard`

---

## Walkthrough (~10 minutes)

### 1. Architecture Overview (2 min)
- Show the diagram in `docs/architecture.md`
- Key points: CEO agent coordinates three specialists; all side-effecting tool calls go through the approval gate; everything is traced in Langfuse

### 2. Trigger a Daily Cycle (2 min)
```bash
python scripts/run_daily_cycle.py
```
- Walk through the terminal output: CEO planner → Marketing/Sales/Ops tasks generated
- Show the LangGraph execution graph running in logs

### 3. Dashboard — Daily Digest (2 min)
- Open `http://localhost:3000/dashboard`
- Show the synthesized digest: what each agent did, key decisions, blockers
- Point out the trace ID links (open in Langfuse if credentials available)

### 4. Approval Queue (2 min)
- Open `http://localhost:3000/approvals`
- Show a pending approval: e.g., "Marketing agent wants to send this email"
- Demonstrate approve / reject — show how the agent resumes or aborts
- Explain: this is enforced at the tool layer, not the prompt layer

### 5. Company Brain (1 min)
- Open `http://localhost:3000/company-brain`
- Show long-term memory entries: company goals, past decisions, outcomes
- Mention: this is what gets RAG-retrieved when agents need context

### 6. Honest Scope (1 min)
- Open `docs/roadmap.md`
- Point to stub agents section — Finance, CS, R&D are interfaces only
- "These would need accounting/CRM integrations — out of scope for v0.1, documented here deliberately"

---

## Likely Questions

**Q: How do you prevent agents from doing something harmful?**
A: Approval gate at the tool layer. The `approval_gate.py` intercepts any call matching a policy rule before it executes. Prompts can be manipulated; tool hooks are code.

**Q: How does the CEO agent decide what to prioritize?**
A: `planner.py` receives company goals from long-term memory and yesterday's outcomes, then generates a prioritized task list. `arbitration.py` handles conflicts if two agents claim the same resource.

**Q: What happens if an LLM call fails?**
A: LangGraph handles retries at the node level. Failed tasks are written to the `tasks` table with status `failed` and surfaced in the digest.

**Q: Is this production-ready?**
A: No — it's a v0.1 demo scaffold. Production would need auth, multi-tenancy, secret rotation, and proper monitoring. The architecture is designed to scale to that.

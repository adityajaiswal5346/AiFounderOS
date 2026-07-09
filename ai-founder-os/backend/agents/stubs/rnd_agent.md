# R&D Agent — Interface Stub

> **Status: NOT IMPLEMENTED**  
> This document defines the intended interface and capabilities of the R&D Agent.
> Building this requires GitHub and research API integrations out of scope for v0.1.

## Purpose

Support the technical R&D function:
- Literature search and summarization (new papers, competitor releases)
- Experiment tracking and result summaries
- Code review summaries for non-technical stakeholders
- Technical debt monitoring

## Intended Tools

| Tool | Description | External Dependency |
|---|---|---|
| `search_papers(query, since)` | Search arXiv / Semantic Scholar | arXiv API / S2 API |
| `summarize_paper(url)` | Read and summarize a paper | HTTP + LLM |
| `get_pr_summaries(repo, days)` | Recent PR activity summary | GitHub API |
| `get_open_issues(repo, label)` | Open issues by label | GitHub API |
| `log_experiment(name, results)` | Log experiment outcome | Internal DB / MLflow |

## Expected Inputs (from CEO Planner)

```json
{
  "task": "Summarize the last 3 days of relevant AI agent papers and any new competitor releases",
  "priority": 3,
  "requires_approval": false,
  "success_criterion": "Research brief produced with top 3 relevant papers and competitor update"
}
```

## Expected Outputs

```json
{
  "agent": "rnd",
  "run_id": "...",
  "output": "3 relevant papers found. Top pick: 'AgentBench v2' — new benchmark for tool-use agents (key result: GPT-4o scores 68% on task completion). Competitor: LangChain released v0.3 with streaming improvements. 2 open P0 GitHub issues flagged.",
  "research_brief": "..."
}
```

## Approval Policy

- All read operations: no approval required
- Posting code review summaries to Slack: requires approval
- Merging PRs (future): requires approval + CI green

## Why This Is Deferred

Requires GitHub OAuth (read access to repo), which involves a separate auth flow from other
integrations. The research summarization component works standalone but the value is
much higher when combined with the GitHub integration to connect papers to current work.
Planned for v0.2 alongside a technical metrics dashboard.

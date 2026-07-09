# Customer Success Agent — Interface Stub

> **Status: NOT IMPLEMENTED**  
> This document defines the intended interface and capabilities of the Customer Success Agent.
> Building this requires CRM + support desk integrations out of scope for v0.1.

## Purpose

Monitor customer health and proactively prevent churn:
- Track NPS and support ticket sentiment
- Identify at-risk accounts from usage signals
- Draft proactive check-in emails
- Escalate critical issues to founder

## Intended Tools

| Tool | Description | External Dependency |
|---|---|---|
| `get_nps_scores(period)` | NPS survey results | Delighted / Typeform |
| `get_at_risk_accounts()` | Accounts with low engagement | HubSpot / Mixpanel |
| `list_open_tickets(priority)` | Support tickets by priority | Intercom / Zendesk |
| `draft_checkin_email(account)` | Personalized check-in email | Internal + Gmail |
| `update_crm_health_score(account_id, score)` | Update CRM health field | HubSpot |

## Expected Inputs (from CEO Planner)

```json
{
  "task": "Identify any accounts at churn risk and draft proactive outreach",
  "priority": 2,
  "requires_approval": true,
  "success_criterion": "At-risk accounts identified, outreach drafted and queued for approval"
}
```

## Expected Outputs

```json
{
  "agent": "customer_success",
  "run_id": "...",
  "output": "3 at-risk accounts identified. Outreach drafted for Acme Corp (NPS: 4) and TechCo (no login in 14 days). 1 critical support ticket escalated.",
  "pending_approvals": [
    {"tool": "send_email", "to": "ceo@acmecorp.com", "preview": "..."}
  ]
}
```

## Approval Policy

- Reading CRM and support data: no approval required
- Sending emails to customers: requires approval
- Updating CRM fields: no approval required (internal state only)

## Why This Is Deferred

Requires integration with HubSpot or similar CRM plus a support desk tool (Intercom/Zendesk).
Usage signal analysis also requires access to product analytics (Mixpanel/Amplitude).
The multi-system data join to produce accurate churn signals is non-trivial at v0.1 scale.

# Finance Agent — Interface Stub

> **Status: NOT IMPLEMENTED**  
> This document defines the intended interface and capabilities of the Finance Agent.
> Building this properly requires accounting software integration out of scope for v0.1.

## Purpose

Automate financial monitoring and reporting for an early-stage startup:
- Track burn rate and runway
- Flag unusual expenses
- Draft investor update financial sections
- Automate invoice follow-ups

## Intended Tools

| Tool | Description | External Dependency |
|---|---|---|
| `get_bank_balance()` | Current account balance | Plaid / Mercury API |
| `get_burn_rate(period)` | Monthly burn calculation | QuickBooks / Xero |
| `list_outstanding_invoices()` | Unpaid customer invoices | Stripe / QuickBooks |
| `send_invoice_reminder(invoice_id)` | Email reminder to customer | Gmail + Stripe |
| `generate_financial_summary()` | P&L summary for given period | QuickBooks / Xero |

## Expected Inputs (from CEO Planner)

```json
{
  "task": "Review this month's burn rate and flag any budget overruns",
  "priority": 1,
  "requires_approval": false,
  "success_criterion": "Burn rate report generated with variance analysis"
}
```

## Expected Outputs

```json
{
  "agent": "finance",
  "run_id": "...",
  "output": "Monthly burn: $24,500 (18% over budget). Top variance: AWS costs +$2,100. 2 unpaid invoices totaling $8,000 outstanding.",
  "alerts": [
    {"type": "budget_overrun", "category": "infrastructure", "amount": 2100}
  ]
}
```

## Approval Policy

- Reading financial data: no approval required
- Sending invoice reminders: requires approval
- Any payment actions: requires approval + 2FA

## Why This Is Deferred

Requires OAuth integration with at least one of: QuickBooks, Xero, Mercury, or Plaid.
Each has a different auth flow, data model, and rate limit. The abstraction layer to support
multiple providers is non-trivial. Planned for v0.2 with QuickBooks as the initial target.

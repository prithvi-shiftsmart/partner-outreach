# Concierge Tools

Available tools the concierge can invoke during conversations. Each tool is a structured API call with defined inputs, outputs, and access controls.

## Status Key

| Status | Meaning |
|--------|---------|
| `placeholder` | Spec defined, not yet implemented |
| `draft` | Implementation in progress, not production-ready |
| `active` | Deployed and available for use |

## Available Tools

| Tool | Status | Owner | Description |
|------|--------|-------|-------------|
| [retrieve_partner_info](retrieve_partner_info.md) | placeholder | EPD (Eton) | Pull partner profile, funnel status, preferences, and account state |
| [retrieve_quality_shifts](retrieve_quality_shifts.md) | placeholder | EPD (Eton) | Query available shifts ranked by quality score for a given partner |
| [make_shift_assignment](make_shift_assignment.md) | placeholder | EPD (Eton) | Book a specific shift on behalf of a partner |

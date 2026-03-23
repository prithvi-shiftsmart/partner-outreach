# Query Cache Rules

## Cache Location
`stages/01_identify/output/{campaign_id}_{YYYY-MM-DD}.json`

## Freshness
A cached result is FRESH if:
1. The filename date matches today (America/New_York), AND
2. The file was written less than 4 hours ago

## TTL by Campaign
| Campaign | Max Age | Rationale |
|----------|---------|-----------|
| activation_large | 4 hours | Partner pool changes slowly |
| activation_medium | 4 hours | Same |
| activation_small | 4 hours | Same |
| incomplete_orientation | 4 hours | Module progress updates infrequently |
| referral_low_dl | 2 hours | DL target comparison is more dynamic |
| custom_* | 1 hour | Ad-hoc queries expire faster |

## Session Reuse
Within a Claude Code session, ALWAYS use cached results for follow-up questions — even if TTL has elapsed. Only re-query if PK explicitly says "refresh" or "re-run."

## Daily Budget
- Hard limit: **15 BQ queries per calendar day**
- Enforced by `run_query.py` — checks `bq_usage` table before executing
- If budget hit: return stale cache if available, otherwise notify PK
- Cache hits don't count against the budget

## Ad-Hoc Query Policy
1. Check `query_registry.json` patterns first — use existing campaign if it matches
2. If truly novel: run it, cache it, log it, offer to save to registry
3. Ad-hoc queries cache for 1 hour

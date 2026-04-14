# Stage 01: Identify Partners

## Purpose
Find partners who need outreach by running BQ queries for each active campaign.

## Inputs
- Layer 3: `../../_config/campaigns.json` (which campaigns to run)
- Layer 3: `../../_config/markets.json` (market scope)
- Layer 3: `../../_config/timing_rules.md` (cooldown checks)
- Layer 3: `queries/*.sql` (the actual queries)

## Pre-Run Check
Before running queries, check SQLite for cooldowns:
```sql
SELECT partner_id, COUNT(*) as msg_count
FROM message_log
WHERE logged_at > datetime('now', '-48 hours')
GROUP BY partner_id
```
Exclude these partners from results.

## Process
1. Read `campaigns.json` — only run campaigns where `active: true`
2. For each active campaign, run: `python3 scripts/run_query.py --campaign <id>`
   - The script checks cache first (no BQ hit if results are fresh)
   - Returns path to JSON results file
3. Load results from the returned paths
4. Deduplicate across campaigns (priority: incomplete_orientation > activation > referral)
5. Remove partners in cooldown
6. Results are already cached in `output/` by run_query.py

## Cache Note
If results were cached from an earlier run today, `run_query.py` returns the cached
file without hitting BQ. No special handling needed — just use the returned path.
To force a fresh query: `python3 scripts/run_query.py --campaign <id> --force-refresh`

## Output
One JSON file per campaign in `output/`:
```json
[
  {
    "partner_id": "abc-123",
    "first_name": "Jane",
    "last_name": "Doe",
    "phone_number": "5551234567",
    "email": "jane@example.com",
    "company_name": "Circle K - Premium",
    "market": "Morgantown_WV",
    "distance_miles": 4.2,
    "msa": "Morgantown, WV",
    "campaign_context": {}
  }
]
```

## After Completion
Tell the operator: "Found X partners across Y campaigns. Ready to draft messages?"
Then proceed to Stage 02.

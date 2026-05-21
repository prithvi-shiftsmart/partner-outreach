# Tool: retrieve_partner_info

**Status:** placeholder
**Owner:** EPD (Eton)

## Purpose

Pull the partner's profile, funnel status, preferences, and account state so the concierge can personalize responses and make informed decisions about next steps.

## When to Use

- On any inbound message where partner context would change the response (e.g., partner says "I already did orientation" — verify before trusting)
- Before surfacing shifts (need location, preferences, eligibility)
- When partner reports account issues (need account state, ban status)

## Input

```json
{
  "partner_id": "uuid",
  "fields": ["profile", "funnel_status", "preferences", "account_state"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| partner_id | string (UUID) | yes | Partner's unique ID |
| fields | string[] | no | Subset of fields to return (default: all) |

## Output

```json
{
  "partner_id": "uuid",
  "first_name": "string",
  "last_name": "string",
  "phone": "string",
  "zone_description": "string",
  "closest_store_miles": 3.2,
  "funnel_status": {
    "dl_date": "2026-05-01",
    "oa_date": "2026-05-02",
    "remote_modules_complete_date": "2026-05-02",
    "op_date": "2026-05-03",
    "s1a_date": null,
    "s1c_date": null,
    "failed_op": false
  },
  "preferences": {
    "preferred_distance_miles": 10,
    "preferred_shift_types": [],
    "preferred_times": []
  },
  "account_state": {
    "status": "active",
    "banned": false,
    "suspension_history": []
  }
}
```

## Access Control

- Read-only — concierge cannot modify partner data through this tool
- Available at all funnel stages

## Notes

- This replaces the current approach of joining `int_master_partner_throughput` at query time
- Funnel status is authoritative — use it to verify partner claims ("I already did orientation")
- `closest_store_miles` drives shift relevance scoring

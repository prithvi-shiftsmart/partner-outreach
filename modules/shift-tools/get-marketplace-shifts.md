# Tool: retrieve_quality_shifts

**Status:** placeholder
**Owner:** EPD (Eton)

## Purpose

Query available shifts for a partner, ranked by quality score. Returns the best shifts based on proximity, pay, bonus eligibility, and historical fill rates.

## When to Use

- Post-OP: surface top 3 shifts to prime S1A
- Partner asks "what shifts are available" or "show me shifts"
- Re-query when partner states a preference (distance, pay, time)
- Nudge cadence: refresh top 3 shifts for each follow-up nudge

## Input

```json
{
  "partner_id": "uuid",
  "limit": 3,
  "offset": 0,
  "filters": {
    "max_distance_miles": 15,
    "min_pay_hourly": null,
    "time_of_day": null,
    "shift_date_range": {
      "start": "2026-05-14",
      "end": "2026-05-21"
    }
  },
  "sort_by": "quality_score"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| partner_id | string (UUID) | yes | Partner's unique ID (used for location + eligibility) |
| limit | int | no | Number of shifts to return (default: 3) |
| offset | int | no | Pagination offset for "show me more" (default: 0) |
| filters.max_distance_miles | float | no | Max distance from partner (default: partner's preferred radius) |
| filters.min_pay_hourly | float | no | Minimum hourly pay filter |
| filters.time_of_day | string | no | "morning" / "afternoon" / "evening" |
| filters.shift_date_range | object | no | Date window (default: next 7 days) |
| sort_by | string | no | "quality_score" (default) / "distance" / "pay" / "date" |

## Output

```json
{
  "shifts": [
    {
      "shift_id": "uuid",
      "role": "Food Prep",
      "sub_type": "Breakfast",
      "brand": "Circle K",
      "store_address": "123 Main St, Houston TX 77002",
      "store_number": "CK-4701625",
      "date": "2026-05-15",
      "start_time": "06:00",
      "end_time": "10:00",
      "pay_hourly": 16.50,
      "bonus_amount": 5.00,
      "bonus_eligible": true,
      "distance_miles": 3.2,
      "quality_score": 0.87
    }
  ],
  "total_available": 12,
  "partner_zone": "Houston_TX_1"
}
```

## Quality Score

Composite score (0-1) based on:
- Proximity to partner (closer = higher)
- Pay rate relative to zone average
- Historical fill rate (lower fill = higher priority — we need coverage)
- Bonus eligibility
- Time-of-day match to partner preferences (if known)

## Access Control

- Read-only — does not modify shift state
- Available at `op_completed` and later funnel stages

## Notes

- Returns shifts the partner is eligible for (orientation complete, BGC cleared or in-progress)
- Shifts with active bonus pay are flagged for display in the shift card
- `total_available` helps the concierge say "I found 12 shifts near you — here are the top 3"

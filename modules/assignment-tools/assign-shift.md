# Tool: make_shift_assignment

**Status:** placeholder
**Owner:** EPD (Eton)

## Purpose

Book a specific shift on behalf of a partner. This is the write action that converts a shift surfacing interaction into an S1A (first shift assigned).

## When to Use

- Partner replies "1", "2", or "3" to a shift card
- Partner says "book that one" or "sign me up for the first one"
- Concierge confirms booking after partner selects a shift

## Input

```json
{
  "partner_id": "uuid",
  "shift_id": "uuid",
  "confirmation_required": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| partner_id | string (UUID) | yes | Partner being assigned |
| shift_id | string (UUID) | yes | Shift to book (from `retrieve_quality_shifts` output) |
| confirmation_required | bool | no | If true, return shift details for partner confirmation before booking (default: true) |

## Output (confirmation mode)

```json
{
  "status": "pending_confirmation",
  "shift": {
    "shift_id": "uuid",
    "role": "Food Prep",
    "brand": "Circle K",
    "store_address": "123 Main St, Houston TX 77002",
    "date": "2026-05-15",
    "start_time": "06:00",
    "end_time": "10:00",
    "pay_hourly": 16.50,
    "bonus_amount": 5.00
  },
  "confirmation_message": "Book Food Prep at Circle K (123 Main St) on Thu 5/15 6:00-10:00 AM for $16.50/hr + $5 bonus? Reply YES to confirm."
}
```

## Output (confirmed)

```json
{
  "status": "booked",
  "shift_id": "uuid",
  "assignment_id": "uuid",
  "partner_id": "uuid",
  "confirmation_message": "You're booked! Food Prep at Circle K (123 Main St) on Thu 5/15, 6:00-10:00 AM. You'll get a reminder the day before."
}
```

## Error States

| Error | Meaning | Concierge Action |
|-------|---------|-----------------|
| `shift_filled` | Shift was taken between surfacing and booking | Apologize, offer next-best shift via `retrieve_quality_shifts` |
| `partner_ineligible` | Partner doesn't meet requirements (BGC pending, etc.) | Explain what's needed before they can book |
| `shift_conflict` | Partner already has a shift at that time | Show the conflict, offer alternative times |
| `rate_limit` | Too many assignment attempts | Wait and retry |

## Access Control

- **Write action** — modifies shift state and partner schedule
- Available at `op_completed` and later funnel stages
- Requires partner eligibility check (orientation complete, not banned)

## Notes

- Default is confirmation mode — concierge should always confirm before booking
- Race condition: shift may fill between retrieval and assignment. Handle gracefully with re-query.
- Successful assignment triggers state transition to `s1a` and starts the pre-shift check-in flow

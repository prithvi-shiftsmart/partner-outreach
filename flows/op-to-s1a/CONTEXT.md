# OP -> S1A Flow

This flow handles shift booking for partners who have just completed orientation (OP status).

## When this flow fires
- Partner reaches OP status (orientation complete, BGC submitted) in a market with the OP->S1A flag enabled
- Trigger type: `canned_s1a_intro`
- Funnel stage: `op_to_s1a`

## What this flow does
1. Surfaces the 3 best shifts near the partner (by quality score)
2. Handles preference-based filtering (distance, pay, time)
3. Books the partner's first shift via assign_to_shift
4. Schedules a pre-shift check-in (triggers the S1A->S1C flow)

## Conversation lifecycle
- Opens with `funnel_stage = op_to_s1a`
- Closes when partner books a shift (S1A achieved) -> new S1A->S1C conversation opens
- Also closes on: STOP/opt-out, 14 days inactivity (no response to any of the 5 nudges), partner not at OP status

## Available tools
- `get_partner_profile` (shared) -- ground truth for funnel stage
- `search_shifts` (shared) -- shift surfacing and preference filtering
- `assign_to_shift` (shared) -- booking
- `schedule_reminder` (flow-specific) -- queue pre-shift check-in

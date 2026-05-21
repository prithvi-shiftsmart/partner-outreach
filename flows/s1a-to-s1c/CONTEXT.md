# S1A -> S1C Flow

This flow handles shift completion for partners who have a booked shift (S1A status).

## When this flow fires
- Scheduled message 24-26 hours before the booked shift
- Trigger type: `pre_shift_checkin`
- Funnel stage: `s1a_to_s1c`
- New conversation opens with its own conversation_id

## What this flow does
1. Sends pre-shift check-in with logistics (what to bring, where to park)
2. Handles cancellation requests (cancel_shift -> recovery shifts)
3. Answers logistics questions
4. Detects system cancellations (shift removed by store)

## Conversation lifecycle
- Opens with `funnel_stage = s1a_to_s1c`
- Closes when: shift completes (S1C), partner opts out, 24h inactivity after cancel recovery
- Partner sees one continuous SMS thread -- conversation boundary is invisible

## Available tools
- `get_partner_profile` (shared) -- verify partner is at S1A
- `search_shifts` (shared) -- for cancellation recovery
- `assign_to_shift` (shared) -- for re-booking after cancellation
- `check_shift_status` (flow-specific) -- verify shift before check-in
- `cancel_shift` (flow-specific) -- cancel on partner's behalf

# schedule_reminder

Queues a future message to be sent at a specific time. This triggers the S1A->S1C flow.

## When to call
- Immediately after a successful assign_to_shift call
- Schedule for 24-26 hours before the shift start time

## Important behaviors
- This is what connects the OP->S1A flow to the S1A->S1C flow
- The scheduled message opens a new conversation with funnel_stage = s1a_to_s1c
- Only one reminder per booked shift -- don't double-schedule

## Dependencies
- Requires a prior successful assign_to_shift call

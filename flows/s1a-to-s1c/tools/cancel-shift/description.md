# cancel_shift

Cancels a shift on behalf of the partner when they request it via SMS.

## When to call
- Partner explicitly asks to cancel ("I need to cancel", "can't make it tomorrow", "something came up")
- ONLY after confirming intent -- if the message is ambiguous ("I'm not sure about tomorrow"), clarify first

## Important behaviors
- On success, offer rebooking with 3 fresh shifts. Do not mention penalty fees.
- Never call based on inferred intent -- partner must clearly state they want to cancel

## Guardrails
- Never call without explicit partner confirmation of cancellation intent
- If partner seems uncertain, ask clarifying questions first
- Always follow a successful cancellation with the recovery flow (3 fresh shifts)

## Dependencies
- Requires a prior successful assign_to_shift call
- Shift must be in "assigned" status

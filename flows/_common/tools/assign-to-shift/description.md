# assign_to_shift

Books a specific shift on behalf of the partner. This is the booking action -- only call after explicit partner confirmation.

## When to call
- Partner replies with 1, 2, or 3 (numeric selection)
- Partner uses natural language that unambiguously identifies a shift ("the first one", "the one with the bonus", "Wednesday")
- During re-booking after cancellation (same flow)

## Important behaviors
- NEVER call without explicit partner selection -- no auto-assignment
- If `success: false` with error `SHIFT_FULL`: shift was taken -> re-query with same preference, show 3 fresh options
- If `success: true`: confirm booking with shift details + trust copy + schedule reminder
- Partner must be at OP or S1A status -- check via get_partner_profile first

## Race condition handling
- Assignment can fail if another partner claimed the last slot between display and booking
- On failure: acknowledge honestly ("that one just got picked up"), re-query, present fresh options
- If re-query also returns empty: "all matches have been taken, I'll check back tomorrow"

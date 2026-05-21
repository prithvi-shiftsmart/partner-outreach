# check_shift_status

Checks whether a partner's booked shift is still active, was cancelled, or has been completed.

## When to call
- Before sending the pre-shift check-in (24-26h before shift): confirm shift is still assigned
- When processing a cancellation reply from the partner
- After shift end time: to confirm S1C conversion (completed) vs no-show

## Important behaviors
- If status is "cancelled_by_partner": trigger cancellation recovery flow (re-surface 3 shifts)
- If status is "cancelled_by_system": different messaging -- shift was removed, not partner's fault
- If status is "completed": S1C achieved -- no further action needed
- If status is "no_show": separate handling (out of scope for this milestone)

## Dependencies
- Requires a prior successful assign_to_shift call for this partner + shift

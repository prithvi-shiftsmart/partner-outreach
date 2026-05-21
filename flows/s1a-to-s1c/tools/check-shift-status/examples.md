# check_shift_status -- Examples

## Shift still assigned
Input: partner_id: "p_abc123", shift_id: "s_001"
Output:
{ "shift_id": "s_001", "status": "assigned", "shift_start": "2026-05-13T09:30:00", "shift_end": "2026-05-13T11:15:00", "cancellation_reason": null, "cancelled_at": null }

## Cancelled by system
Input: partner_id: "p_abc123", shift_id: "s_001"
Output:
{ "shift_id": "s_001", "status": "cancelled_by_system", "shift_start": "2026-05-13T09:30:00", "shift_end": "2026-05-13T11:15:00", "cancellation_reason": "Shift removed by store manager", "cancelled_at": "2026-05-12T08:00:00" }

## Completed
Input: partner_id: "p_abc123", shift_id: "s_001"
Output:
{ "shift_id": "s_001", "status": "completed", "shift_start": "2026-05-13T09:30:00", "shift_end": "2026-05-13T11:15:00", "cancellation_reason": null, "cancelled_at": null }

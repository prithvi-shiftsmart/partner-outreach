# assign_to_shift -- Examples

## Successful assignment
Input: partner_id: "p_abc123", shift_id: "s_001"
Output:
{ "success": true, "assignment_id": "a_001", "shift_id": "s_001", "partner_id": "p_abc123", "confirmed_at": "2026-05-12T14:30:00Z", "error": null, "message": null }

## Shift already full (race condition)
Input: partner_id: "p_abc123", shift_id: "s_001"
Output:
{ "success": false, "assignment_id": null, "shift_id": "s_001", "partner_id": "p_abc123", "confirmed_at": null, "error": "SHIFT_FULL", "message": "No remaining slots for shift s_001" }

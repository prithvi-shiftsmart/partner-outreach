# cancel_shift -- Examples

## Standard cancellation
Input: partner_id: "p_abc123", shift_id: "s_001", reason: "Something came up"
Output:
{ "success": true, "cancellation_id": "cx_789", "penalty_applied": false, "penalty_amount": null }

## Late cancellation (penalty)
Input: partner_id: "p_abc123", shift_id: "s_001", reason: "Can't make it"
Output:
{ "success": true, "cancellation_id": "cx_790", "penalty_applied": true, "penalty_amount": 15.00 }

## Already cancelled
Input: partner_id: "p_abc123", shift_id: "s_001"
Output:
{ "success": false, "cancellation_id": null, "penalty_applied": false, "penalty_amount": null }

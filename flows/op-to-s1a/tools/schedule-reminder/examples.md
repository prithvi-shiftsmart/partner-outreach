# schedule_reminder -- Examples

## Standard check-in scheduling
Input:
  partner_id: "p_abc123"
  shift_id: "s_001"
  send_at: "2026-05-12T09:30:00Z"
  message_type: "pre_shift_checkin"

Output:
{ "success": true, "reminder_id": "rem_001", "scheduled_for": "2026-05-12T09:30:00Z", "message_type": "pre_shift_checkin" }

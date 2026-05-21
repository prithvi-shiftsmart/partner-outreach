# get_partner_profile -- Examples

## Standard OP partner
Input: partner_id: "p_abc123"
Output:
{
  "partner_id": "p_abc123",
  "first_name": "Marcus",
  "last_name": "Johnson",
  "phone": "+15125551234",
  "funnel_cohort": { "current_stage": "op", "last_transition_at": "2026-05-12T10:00:00Z" },
  "location": { "lat": 27.8006, "lng": -97.3964, "city": "Corpus Christi", "state": "TX" },
  "preferences": null
}

## Partner already at S1A
Input: partner_id: "p_def456"
Output:
{
  "partner_id": "p_def456",
  "first_name": "Sarah",
  "last_name": "Williams",
  "phone": "+15125555678",
  "funnel_cohort": { "current_stage": "s1a", "last_transition_at": "2026-05-11T14:30:00Z" },
  "location": { "lat": 27.8006, "lng": -97.3964, "city": "Corpus Christi", "state": "TX" },
  "preferences": { "preferred_distance_mi": 5.0, "preferred_time_window": "morning", "preferred_pay_min": 18.00 }
}

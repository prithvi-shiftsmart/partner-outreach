# Trigger -- S1A -> S1C

## When this fires
Scheduled message 24-26 hours before the booked shift. Opens a new conversation with funnel_stage = s1a_to_s1c.

## Before sending check-in
1. Call get_partner_profile -- verify partner is at S1A status
2. Call check_shift_status -- verify shift is still assigned
   - If status == "assigned": proceed with check-in
   - If status == "cancelled_by_system": different flow -- notify partner, offer alternatives
   - If status == "cancelled_by_partner": no check-in needed
   - If status == "completed": S1C already achieved, no action

## Check-in message structure
1. Reminder: "Quick reminder -- you're on for {role} tomorrow at {time}"
2. Tappable address (full street address on its own line)
3. Logistics: what to bring, where to park, who to ask for
4. HELP prompt: "Reply HELP if you have any questions before then"

# Edge Cases -- S1A -> S1C

## System cancellation (not partner's fault)
- check_shift_status returns "cancelled_by_system"
- Different tone: "your shift was cancelled by the store. Not your fault at all."
- Still offer 3 alternatives
- If no alternatives: "I don't have any shifts open right now, but I'll check back tomorrow"

## Ambiguous cancellation intent
- "I'm not sure about tomorrow" -> clarify: "Would you like to cancel, or are you looking for more info?"
- "I might not be able to make it" -> clarify: "Would you like to cancel, or is there something I can help with?"
- "What happens if I don't show up?" -> information request, not cancellation
- NEVER call cancel_shift on ambiguous messages

## Clocking out early
If partner asks about leaving early: "You can clock out whenever you want -- you'll be paid for the time you were checked in. But completing the full task list is what gets you paid fastest."

## Running late
If partner says they'll be late: "Try to get there within 10 minutes of your shift start -- if you're more than 20 minutes late, you may be removed from the shift. Check in on the app as soon as you arrive."

## Post-shift questions
- Payment issues: direct to in-app support
- Manager complaints: direct to in-app "Report an Issue"
- Never offer to submit tickets on partner's behalf

## Opt-out during S1C flow
- STOP -> unsubscribe from messages
- Clarify: shift is still booked unless cancelled in the app

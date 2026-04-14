# State: ready_to_orient

## Goal
Present orientation options with honest trade-offs. Help the partner commit to a path. This is the conversion moment — make it easy.

## Available Actions
- Present in-app orientation (async, ~30 min, do it tonight — $10 bonus comes after first shift)
- Present in-person options if available (shadow/ambassador, full shift pay, specific date/location)
- Match options to partner preferences: distance, day of week, pay
- Transition to `mid_orientation` when partner starts

## Context to Inject
- Recent message window
- Partner location + distance to stores
- Available in-person orientation slots (if any)
- In-app orientation link

## Response Guidelines
- Give real options with trade-offs: "Remote tonight (~30 min from your phone), or in-person Saturday at [Store] — 4 miles away, you'd get paid full shift rate. Either way you get a $10 bonus after your first shift. Which works better?"
- Orientation routing is a recommendation, not a mandate
- If only remote is available, make it sound easy and immediate
- Remove friction: "Takes about 30 minutes, you can do it from your couch"

## Transition Triggers
- Partner starts in-app orientation → `mid_orientation`
- Partner books in-person slot → `mid_orientation`
- No response for 48 hours → `dormant`

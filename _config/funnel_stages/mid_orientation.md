# State: mid_orientation

## Goal
Be available to answer questions in real time. Coach through blockers. Flag high drop-off risk for human review. Get them to OP.

## Available Actions
- Answer module-specific questions
- Encourage progress ("You're 5/7 — almost there!")
- Flag if partner has been stuck on same module for 24+ hours
- Transition to `op_completed` when orientation passed

## Context to Inject
- Recent message window
- Current module number and name
- Time on current module
- Total modules completed vs remaining
- Partner profile

## Response Guidelines
- Be encouraging without being patronizing
- If they're stuck: offer to walk them through it
- If they paused: gentle nudge after 24 hours ("Looks like you paused on [module] — takes about 5 mins. Want to keep going?")
- Mention the $10 completion pay as motivation

## Transition Triggers
- All 7 modules completed + remote orientation shift completed → `op_completed`
- In-person orientation completed → `op_completed`
- No activity for 48 hours → `dormant`
- Partner reports technical issue → flag for human, stay in `mid_orientation`

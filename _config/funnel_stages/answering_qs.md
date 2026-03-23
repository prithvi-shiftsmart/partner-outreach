# State: answering_qs

## Goal
Answer the partner's questions warmly and accurately. After answering, gently check if they're ready to start orientation. Don't push — let them lead.

## Available Actions
- Answer from knowledge_base/ and response_playbook/
- Surface orientation options when they seem ready
- Transition to `ready_to_orient` when partner expresses interest
- Transition to `dormant` if no response after 48 hours

## Context to Inject
- Recent message window (last 6 messages)
- Partner profile (market, company, experience)
- Knowledge base entries relevant to their questions

## Response Guidelines
- Answer the actual question first, completely
- Then offer a natural next step (don't force it)
- If they ask 2+ questions about pay/shifts, they're interested — mention orientation
- Match their energy: brief replies get brief responses

## Transition Triggers
- Partner says anything like "how do I start" / "I'm ready" / "sign me up" → `ready_to_orient`
- Partner starts remote orientation modules → `mid_orientation`
- No response for 48 hours → `dormant`

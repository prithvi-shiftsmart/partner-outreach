# Stage 03: Review and Log

## Purpose
Operator reviews draft messages, approves/edits, and everything gets logged to SQLite. Also handles reply ingestion.

## Inputs
- Layer 4: `../02_draft/output/draft_messages.json`
- Layer 3: `../../_config/response_playbook/` (for reply handling)
- Layer 3: `../../_config/knowledge_base/` (for answering partner questions)

## Outbound Message Flow

1. Present drafts to operator grouped by campaign
2. Operator can:
   - **Approve all**: all drafts marked as approved
   - **Edit specific messages**: modify the message text for individual partners
   - **Skip a campaign**: mark all messages in that campaign as skipped
   - **Skip specific partners**: mark individual messages as skipped
3. For approved messages:
   - Log each to SQLite via `python3 scripts/log_message.py`
   - Output formatted for copy-paste into Zendesk
4. Write approved messages to `output/approved_messages.md` — formatted nicely for PK to send

## Output: approved_messages.md
```markdown
## Approved Messages — 2026-03-24

### activation_small (4 messages)

**Jane Doe** | Morgantown_WV | Circle K | 5551234567
> Hi Jane! I'm your Shiftsmart guide...

**John Smith** | Boone_NC | Dollar General | 5559876543
> Hi John! I'm your Shiftsmart guide...
```

## Reply Logging Flow

When operator says "I got replies" and pastes text from Zendesk:

1. Parse the reply text to identify partner and content
2. Match to original outbound message in SQLite (by partner_id or phone)
3. Classify intent:
   - orientation_question, pay_question, bonus_question, shift_question
   - app_issue, opt_out, confirmation, escalation, other
4. Load relevant playbook entry from `_config/response_playbook/`
5. Draft a response using playbook + partner context
6. Present draft response to operator for approval
7. On approval: log reply + response to SQLite via `python3 scripts/log_reply.py`
8. Output response for operator to send in Zendesk

## Escalation
If intent is "escalation" or confidence is low: flag for manual handling. Don't draft an automated response.

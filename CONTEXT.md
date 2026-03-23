# Task Router

Read the operator's request and route to the appropriate workflow.

## Morning Outreach Run
Operator says something like "run the morning check" or "what's new today"
1. Read `stages/01_identify/CONTEXT.md` — run BQ queries for each active campaign
2. Read `stages/02_draft/CONTEXT.md` — draft messages from templates
3. Read `stages/03_review_and_log/CONTEXT.md` — present for review, log approved messages
4. Output approved messages formatted for PK to copy into Zendesk

## Check / Log Replies
Operator says "I got replies" or pastes reply text
1. Read `stages/03_review_and_log/CONTEXT.md` — reply handling section
2. Load `_config/response_playbook/` for relevant intents
3. Classify intent, draft response, present for approval
4. Log reply chain to SQLite

## Campaign Performance
Operator says "how's it going" or "show me the dashboard"
1. Run `python3 scripts/show_dashboard.py`
2. Optionally cross-reference with BQ for funnel movement

## Export for Ted
Operator says "export for Ted" or "generate audit"
1. Run `python3 scripts/export_audit.py`
2. Output location: `tracking/exports/`

## Custom Query
Operator describes a problem like "show me partners in X market who..."
1. Write a BQ query based on the description
2. Run it, show results
3. If operator wants to message them, go to Stage 02 (draft)
4. If the query is reusable, offer to save it to `stages/01_identify/queries/`

## Setup / First Run
If `tracking/outreach.db` doesn't exist:
1. Run `python3 scripts/init_db.py`
2. Confirm tables created

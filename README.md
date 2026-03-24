# Partner Outreach Platform

SMS-based partner concierge + ops intelligence tool for Shiftsmart priority markets. Built on the [ICM framework](https://arxiv.org/abs/2603.16021) — folder structure as agent architecture.

## What This Does

Two workstreams sharing a common data layer:

**Partner Concierge** — Proactively reaches out to every new download in a priority market via SMS. Coaches them from first contact through orientation passed (OP). Answers questions, surfaces orientation options, handles objections. Reference experience: Delta/United text booking agent.

**Ops Intelligence Tool** — Operator describes a problem ("show me partners in Boone who downloaded but haven't oriented"), Claude Code writes the query, drafts messages, operator reviews and approves. Tracks everything. Learns what works.

## Architecture

```
partner-outreach/
│
├── CLAUDE.md                  ← workspace identity (Layer 0)
├── CONTEXT.md                 ← task router (Layer 1)
│
├── _config/                   ← THE FACTORY — edit these to change behavior
│   ├── state_machine.json        6 conversation states + transition rules
│   ├── campaigns.json            5 campaigns mapped to BQ queries
│   ├── guardrails.md             what the concierge won't do
│   ├── keyword_prefilter.json    regex filters before LLM (zero cost)
│   ├── timing_rules.md           cooldowns, rate limits, LLM budget
│   ├── tone_and_voice.md         concierge personality
│   ├── personalization_rules.md  experience mapping, dedup
│   ├── query_cache_rules.md      BQ cache TTLs + daily budget
│   ├── query_registry.json       campaign → query mapping
│   ├── funnel_stages/            per-state prompt configs
│   ├── message_templates/        outbound message variants
│   ├── response_playbook/        approved answers by intent
│   └── knowledge_base/           source of truth docs
│
├── stages/
│   ├── 01_identify/           ← find partners via BQ queries
│   │   ├── CONTEXT.md            stage contract
│   │   └── queries/              5 SQL files (priority market campaigns)
│   ├── 02_draft/              ← draft messages from templates
│   └── 03_review_and_log/     ← operator review + SQLite logging
│
├── scripts/
│   ├── init_db.py                create SQLite schema
│   ├── run_query.py              BQ runner with cache + budget
│   ├── log_message.py            log outbound messages
│   ├── log_reply.py              log replies + responses
│   ├── show_dashboard.py         campaign metrics
│   └── export_audit.py           CSV + markdown for review
│
└── tracking/
    └── outreach.db            ← SQLite (7 tables, indexed)
```

## Conversation States

```
new_download → answering_qs → ready_to_orient → mid_orientation → op_completed
      │              │               │                 │                │
      └──────────────┴───────────────┴─────────────────┴────────────────┘
                              Any state → dormant (48hr no response)
                              dormant → answering_qs (partner re-engages)
```

## How to Use

```bash
cd ~/partner-outreach && claude
```

**Morning run**: "Run the morning outreach check"
- Queries BQ for partners needing outreach (cached, budget-enforced)
- Drafts personalized messages from templates
- Operator reviews, edits, approves
- Logs to SQLite, outputs messages for send

**Reply handling**: "I got replies" + paste from messaging tool
- Classifies intent, drafts response from playbook
- Operator reviews, approves
- Logs full reply chain

**Dashboard**: "How's this week going?"
- Message counts, reply rates, intent breakdown by campaign/market

**Custom query**: "Show me partners in Austin who passed orientation but haven't taken a shift"
- Claude Code writes BQ query, runs it, shows results
- Reusable queries saved to registry

## Setup

```bash
python3 scripts/init_db.py    # creates tracking/outreach.db
```

Requires:
- Python 3.9+
- `bq` CLI configured for `shiftsmart-api` project
- `google-cloud-bigquery` package

## Guardrails

- Every message reviewed by human before send
- Keyword pre-filter catches prompt injection, abuse, opt-outs at zero LLM cost
- Max 2 unreturned messages per partner, then stop
- Max 3 messages per partner per 7-day window
- 200 LLM calls/day global budget
- 15 BQ queries/day budget
- Full topic restrictions: no legal advice, no competitor talk, no personal info, no bonus promises

## Tracking

SQLite with 7 tables designed for 1:1 migration to MongoDB + BigQuery:

| Table | Purpose |
|-------|---------|
| `message_log` | Every outbound message |
| `reply_chain` | Threaded replies + responses |
| `partner_conversations` | State machine tracking per partner |
| `outcome_events` | Funnel events attributed to messages |
| `partner_context` | Partner profile snapshots |
| `ab_tests` | Test definitions + results |
| `bq_usage` | Query cost tracking + budget enforcement |

## Phasing

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Concierge: DL → OP | MVP built, pending SMS transport |
| 2 | Concierge: OP → S1C | Pending shift assignment API |
| 3 | Ops intelligence tool | Config ready, parallel track |
| 4 | Learning loop + dashboard | After Phase 1-2 prove out |

## Production Migration

- **SMS**: Telnyx via Pub/Sub (per tech lead design)
- **DB**: SQLite → MongoDB (`partner_conversations`) + BigQuery (analytics)
- **Orchestration**: Claude Code PoC → production NestJS service
- **ICM configs** (`_config/`) become the spec for production prompts and state machine

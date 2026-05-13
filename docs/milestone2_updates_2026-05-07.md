# Milestone 2: OP > S1C — Updates (2026-05-07)

Paste each section below into the corresponding section of the existing doc. Each block is labeled with where it goes. Sections marked **[NEW SECTION]** should be added in the position noted.

---

## >> PASTE INTO: "Key Docs" section (replace existing)

**Key Docs**

| Doc | Location |
|-----|----------|
| Technical design doc — shift matching + assignment API | (Eton — in progress) |
| Concierge prompts / system prompt files | `partner-outreach/flows/op_to_s1a/prompts/` and `flows/s1a_to_s1c/prompts/` |
| Tool schemas (shared) | `partner-outreach/flows/_common/tools/` — get_partner_profile, search_shifts, assign_to_shift |
| Tool schemas (OP→S1A) | `partner-outreach/flows/op_to_s1a/tools/` — schedule_reminder |
| Tool schemas (S1A→S1C) | `partner-outreach/flows/s1a_to_s1c/tools/` — check_shift_status, cancel_shift |
| Message templates | `partner-outreach/flows/op_to_s1a/templates/` and `flows/s1a_to_s1c/templates/` |
| Folder architecture doc | Obsidian: `24 - OP to S1C Folder Architecture.md` |
| Test case Excel (expected responses) | `~/Downloads/OP_to_S1C_Test_Cases.xlsx` |
| Test case Excel (live LLM responses) | `~/Downloads/OP_to_S1C_Test_Cases_Live.xlsx` |

---

## >> PASTE INTO: "Knowledge Base" section (replace existing)

**Knowledge Base**

Topics the concierge needs to answer in the OP→S1C flow. All KB files are built and live in `_config/knowledge_base/`.

| Topic | KB File | Status |
|-------|---------|--------|
| First-shift expectations — extra time on first shift (+30/+15 min), learning mindset, what "done well" looks like | `first_shift_expectations.md` | Done |
| Shift selection mechanics — can I change my mind, what if I miss it, what does "booked" mean | (handled in flow prompts — `preference_flow.md`, `edge_cases.md`) | Done |
| Pay timing — when partner gets paid, direct deposit cadence | `getting_paid.md` (updated: same-day release + 1–2 biz day Stripe framing) | Done |
| Cancellations and reschedules — policy, how to cancel via SMS or app, penalty window, reliability impact | `cancellation_policy.md` | Done |
| Day-of logistics — what to bring, what to wear, where to park, who to ask for | `day_of_logistics.md` | Done |
| Post-shift questions — payment status, reporting issues, safety concerns, concierge can't submit tickets | `post_shift_faq.md` | Done |

Keyword mapping in `draft_service.py` updated with 20 new entries so the prompt assembler loads the right KB files when partners ask about these topics.

---

## >> PASTE INTO: "Guardrails" section (replace existing)

**Guardrails**

- Concierge only assigns from the shift set returned by the matching tool — no fabricated shifts.
- No pay promises beyond what is in the returned shift record.
- Assignment only fires for partners at OP status — funnel state checked via `get_partner_profile` before any booking call.
- Partner must explicitly confirm via numeric reply or unambiguous selection — no inferred bookings.
- Pre-shift check-in is informational only — does not re-confirm the booking.
- Cancellation recovery gets one attempt only — no repeated re-surfacing loops.
- `cancel_shift` requires explicit partner confirmation — no inferred cancellations from ambiguous messages (e.g., "I'm not sure about tomorrow" triggers clarification, not cancellation).
- If a cancellation penalty applies, the agent informs the partner.
- STOP / opt-out = immediate unsubscribe, no re-engagement offer.
- Wrong number = silent end, add to do-not-text list.
- Profanity = treat as opt-out.
- Never offer to submit support tickets — direct partner to do it themselves in the app.
- Never say "gig" — always "shift."
- Never say companies "use" Shiftsmart — say "partner with."

---

## >> PASTE INTO: "Concierge Testing" section (replace existing)

**Concierge Testing**

Test infrastructure built and executed. 107 test cases across 25 categories, all run live through Claude (Haiku) with 0 errors.

**Test case breakdown:**

| Flow | Cases | Coverage |
|------|-------|----------|
| OP→S1A | 53 | Happy path booking (1/2/3), preference branches (distance/pay/time/compound/more), reply variants (natural language, ambiguous, invalid), race conditions, KB questions mid-flow, opt-out & compliance, inactivity/nudge sequences, edge cases (wrong status, prompt injection, non-English, wrong number, booking for someone else) |
| S1A→S1C | 37 | Pre-shift check-in, cancellation & recovery (with/without penalty, empathetic acknowledgment), ambiguous cancellation intent guardrails, cancellation limits, system cancellation, edge cases (HELP keyword, post-shift complaints, opt-out during S1C, leaving early, running late) |
| Regression | 17 | Stage identification (DL/mid-orientation/S1A should not fire), shift card formatting (bonus display), no fabricated data, tone & voice (no emoji, no "gig", "partner with" not "use"), opt-out compliance (STOP during S1C = unsubscribe but shift stays booked), conversation boundaries (funnel_stage metadata) |

**KB QA test cases (25):**

| Category | Cases | What it validates |
|----------|-------|-------------------|
| First shift expectations | 5 | +30/+15 extensions, learning mindset, what success looks like, nervous partner in both flows |
| Day-of logistics | 7 | What to bring, parking, manager on duty, arrival time, geofence check-in, can't find manager, dress code |
| Cancellation policy | 5 | Policy questions before/after booking, no-shows, app vs SMS cancel paths, reliability score |
| Post-shift FAQ | 5 | Same-day payment framing, Stripe delay, reporting issues, safety concerns, ticket submission guardrail |
| Pay timing consistency | 3 | "Same day" framing (not "few hours"), orientation $10, pre-shift pay question |

**Results:**
- 107 total test cases
- 104 ran through LLM (3 skipped — metadata verification only)
- 0 errors
- Avg latency: 22s per test (Haiku)
- Live results: `~/Downloads/OP_to_S1C_Test_Cases_Live.xlsx` (expected vs actual side-by-side)

---

## >> PASTE INTO: "Next steps" section (replace existing)

**Next steps**

| Action | Owner | Status |
|--------|-------|--------|
| Define shift-matching tool contract — input filters and output shape | Eton | In Progress |
| Build assignment API for concierge-driven booking | Eton | In Progress |
| Draft system prompt additions for the OP→S1C flow | Prithvi | Done — `flows/op_to_s1a/prompts/` (6 files) + `flows/s1a_to_s1c/prompts/` (5 files) |
| Draft preference-flow copy and 3-shift message template | Prithvi | Done — `flows/op_to_s1a/templates/` (6 templates) + `flows/s1a_to_s1c/templates/` (4 templates) |
| Build knowledge-base entries for first-shift questions | Prithvi | Done — 4 new KB files + 1 updated (`getting_paid.md`) + 20 keyword mappings |
| Define BQ schema additions for OP→S1C reporting | Prithvi + Ted | Not Started |
| Build test scenarios and run baseline concierge evaluation | Prithvi | Done — 107 test cases, 0 errors, live results in Excel |
| Scope scheduled message / check-in functionality | Prithvi + Eton | Not Started |
| Validate tool schemas with Eton | PK + Eton | Not Started — Monday meeting |
| Port prompts to monorepo via concierge-prompt-update workflow | Prithvi | Not Started — blocked on tool schema validation |

---

## >> [NEW SECTION] — paste after "Workflow" section, before "Key Docs"

**S1A → S1C Flow (Shift Completion)**

The S1C leg runs as a separate flow with its own `conversation_id` and `funnel_stage = s1a_to_s1c`. This enables independent reporting — we can measure show-up rate separately from booking rate.

| Step | What happens |
|------|-------------|
| Trigger | Scheduled message fires 24–26h before booked shift. New conversation opens with `funnel_stage = s1a_to_s1c`. |
| Pre-shift check-in | Logistics (what to bring, where to park), tappable address. Implicit cancellation window. |
| Cancellation | Partner requests cancel via SMS → concierge calls `cancel_shift` tool → acknowledges, re-surfaces 3 shifts with same preference. One recovery attempt only. |
| Re-booking | Partner picks from recovery shifts → same assignment flow as OP→S1A. |
| Second cancel | No more re-surfacing. Direct partner to the app. Close out. |
| Completion | Partner shows up → shift event fires → S1C achieved. No additional message needed. |

**Tools specific to S1A→S1C:**

| Tool | Purpose |
|------|---------|
| `check_shift_status` | Verify shift is still `assigned` before sending check-in. Detect system cancellations. |
| `cancel_shift` | Cancel a shift on the partner's behalf when they request it via SMS. Must confirm intent before calling. |

---

## >> [NEW SECTION] — paste after "Architecture decisions" section

**Tool Definitions**

Shared tools (used by both flows):

| Tool | Owner | Status | Description |
|------|-------|--------|-------------|
| `get_partner_profile` | Eton | Active | Retrieve partner tier, location, preferences, and authoritative funnel stage |
| `search_shifts` | Eton | Active | Query available shifts filtered by partner location, preferences, and quality score |
| `assign_to_shift` | Eton | Draft | Book a specific shift on behalf of the partner |

OP→S1A flow-specific:

| Tool | Owner | Status | Description |
|------|-------|--------|-------------|
| `schedule_reminder` | Eton | Draft | Queue a future message (pre-shift check-in) — triggers the S1A→S1C flow |

S1A→S1C flow-specific:

| Tool | Owner | Status | Description |
|------|-------|--------|-------------|
| `check_shift_status` | Eton | Draft | Check current status of an assigned shift (active, cancelled, completed) |
| `cancel_shift` | Eton | Draft | Cancel a shift on behalf of the partner — agent-driven cancellation via SMS |

Full schemas, descriptions, and examples are in `partner-outreach/flows/`. See `24 - OP to S1C Folder Architecture.md` for the complete directory structure.

---

## >> [NEW SECTION] — paste after "Rules of Engagement" section, before "Knowledge Base"

**S1A → S1C Sample Messages**

*Pre-shift check-in (24–26h before shift):*

> Quick reminder — you're on for Food Prep — Lunch tomorrow at 9:30 AM at Circle K, 4501 S Padre Island Dr, Corpus Christi, TX.
>
> What to bring: phone with Shiftsmart app (fully charged), shirt with no logos, comfortable closed-toe shoes. Show up 10 minutes early and ask for the manager on duty.
>
> Reply HELP if you have any questions before then.

*Cancellation recovery:*

> No worries — I cancelled that shift for you. Want me to find some other options? Here are 3 more in the same range:
>
> 1. Stocking — Morning · $20.50
> Thu 5/8 · 6:00–10:00 AM · 7.8 mi
> Circle K, 2810 Ayers St, Corpus Christi, TX
>
> 2. Food Prep — Lunch · $22.75
> Fri 5/9 · 9:30–11:15 AM · 6.2 mi
> Circle K, 4501 S Padre Island Dr, Corpus Christi, TX
>
> 3. Cashier — Afternoon · $19.00
> Sat 5/10 · 1:00–5:00 PM · 9.1 mi
> Circle K, 1810 SPID, Corpus Christi, TX
>
> Reply 1, 2, or 3 to book — or let me know if now's not a good time.

*Re-booking after cancellation:*

> You're booked — Food Prep — Lunch on Fri 5/9, 9:30–11:15 AM at Circle K, 4501 S Padre Island Dr, Corpus Christi, TX.
>
> Same deal — extra 30 minutes on your first shift so you can settle in. I'll send a reminder the day before.

*Ambiguous cancellation intent (guardrail):*

> No problem — would you like to cancel the shift, or are you just looking for more info about what to expect? I'm happy to help either way.

*System cancellation (not partner's fault):*

> Hey Marcus — heads up, your Food Prep — Lunch shift tomorrow was cancelled by the store. Not your fault at all. Let me find you some other options:
>
> [3 fresh shifts]
>
> Reply 1, 2, or 3 to book — or let me know if now's not a good time.

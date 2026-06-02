# Partner Concierge — Overview & DG Expansion Index

## Part 1: High-Level Summary

### What It Is

An automated SMS concierge that guides new Shiftsmart partners from app download through orientation completion (DL→OP) and into their first shift (OP→S1C). Currently live for **Circle K Premium** partners, powered by Gemini 2.5 Flash in production.

### How It Works

1. **Partner downloads the app** → concierge sends a welcome SMS within the messaging window (8 AM–9 PM local time)
2. **Partner replies** → LLM classifies the intent, loads the relevant knowledge base and playbook, generates a response
3. **Concierge guides through orientation** → 4-step in-app orientation (~45 min, $10 payout on BGC completion)
4. **Post-OP** → surfaces top 3 shifts ranked by quality score, handles booking, manages pre-shift check-in

### Architecture

```
Inbound SMS
    ↓
Keyword Prefilter (regex, zero-cost)
    → opt-out, profanity, wrong number, Spanish → deterministic response
    → simple positive reply (yes/ok/help) → deterministic orientation directions
    ↓ (no match)
LLM Pipeline
    → System prompt (HARD RULES + canonical intents)
    → + Tone & voice
    → + Funnel stage prompt (based on partner's current state)
    → + Knowledge base (keyword-matched from last 6 messages)
    → + Response playbook (based on classified intent)
    → + Conversation history (last 12 messages)
    ↓
Structured JSON response
    → { confidence, intent, response, suggestedAction }
```

### Behavioral Controls

| Layer | What It Does |
|-------|-------------|
| **HARD RULES (1-10)** | Absolute behavioral constraints that override everything else — stop-replying on acks, opt-out exact-match, never-say list, no phone numbers, no repeats |
| **Canonical Intents (18)** | Pattern-matched intents with verbatim reply templates — orientation nav, payments, login, shift emergencies, referrals, etc. |
| **Knowledge Base (12 files)** | Factual reference material loaded by keyword match — orientation process, payments, food prep, pay rates, etc. |
| **Response Playbooks (12 files)** | Conversation strategy per intent category — how to handle app issues, payment questions, trust concerns, etc. |
| **Funnel Stages (5 files)** | State-specific goals and available actions — new_download, ready_to_orient, mid_orientation, op_completed, dormant |

### Current Scale (L7D, May 7-13)

- ~460 responsive conversations/week
- 31% OP rate among responders
- 15% S1A rate
- 93 first-message STOPs (message rejection, not experience rejection)
- 43 replay fixtures, all green on Haiku

---

## Part 2: CKP-Specific Content Index

Everything below is Circle K Premium-specific and would need DG equivalents to expand the concierge to Dollar General.

### Tier 1: Must-Have for DG Launch (blocks concierge from running)

| # | File | What's CKP-Specific | What DG Needs |
|---|------|---------------------|---------------|
| 1 | `_config/knowledge_base/orientation_process.md` | 4-step orientation flow: Learning Modules → Certification Call → Profile Photo → BGC. Module content is CKP food prep (Unox oven, Menu Pilot, label printing). | DG orientation steps — what are the modules? How many steps? Same cert call flow? Same BGC? |
| 2 | `_config/knowledge_base/in_app_orientation_walkthrough.md` | Step-by-step walkthrough of all 4 CKP orientation modules with tap sequences, quiz answers, and screenshots. Covers Unox oven operation, Upshop scanning, Menu Pilot label printing. | DG module walkthrough — what does DG's orientation actually teach? What are the quiz topics? |
| 3 | `_config/knowledge_base/food_prep_guide.md` | Full on-shift reference for CKP food prep: Unox oven settings (Sandwiches vs Circle K), cooking batches, tornado box packaging, chicken sandwich assembly, label printing, cooler locations. | DG on-shift guide — what do DG shifts involve? Stocking/merchandising specifics, store layout, equipment, task flow. |
| 4 | `_config/response_playbook/food_prep_shift.md` | On-shift Q&A playbook for food prep: oven troubleshooting, finding items, Menu Pilot/Upshop usage, manager escalation. Scoped to CKP only. | DG shift playbook — what questions will DG partners ask on-shift? Stocking procedures, planogram questions, backroom access? |
| 5 | `_config/knowledge_base/pay_rates.md` | CKP food prep: ~$15-17/hr, 2-4 hour shifts, $10 orientation bonus. | DG rates: ~$15-18/hr listed but needs confirmation. Same $10 orientation bonus? Same shift lengths? |
| 6 | `_config/message_templates/welcome_dl.md` | Welcome message references "In-app orientation for Circle K" and CKP-specific framing. | DG welcome message — what's the hook? Same $10 incentive? Different value prop? |
| 7 | `_config/funnel_stages/op_completed.md` | Post-OP shift surfacing assumes food prep roles, CKP store addresses, CKP-specific bonus structures. | DG post-OP: what shift types? What does the shift card look like for a stocking shift vs food prep? |

### Tier 2: Should Adapt (currently CKP-flavored but mostly generic)

| # | File | What's CKP-Specific | What to Change for DG |
|---|------|---------------------|----------------------|
| 8 | `_config/response_playbook/orientation_logistics.md` | References "the Circle K orientation" and CKP-specific nav (In-app orientation card). | Replace company name. Confirm DG uses the same in-app orientation card UX. |
| 9 | `_config/response_playbook/shift_info.md` | "Circle K Premium" section describes food prep shifts. Explicit rule: "Don't describe shifts for companies other than Circle K." | Add DG section. Remove the CKP-only scoping rule. |
| 10 | `_config/response_playbook/trust_and_identity.md` | "Shiftsmart partners with companies like Circle K to staff shifts at their stores." | Add DG to the legitimacy pitch. |
| 11 | `_config/message_templates/dormant_reengagement.md` | "If you're still interested in starting with Circle K..." | DG variant. |
| 12 | `_config/personalization_rules.md` | Routes food service experience → CKP. Routes warehouse/logistics → PepsiCo or DG. | Update routing logic for DG-specific experience signals. |
| 13 | `_config/tone_and_voice.md` | "Say 'our orientation' — it's the company's orientation (e.g. the Circle K orientation)" | Add DG example. |
| 14 | `_config/knowledge_base/first_shift_expectations.md` | General first-shift guide but includes CKP-specific items (gloves, hairnet). | DG first-shift expectations — dress code, what to bring, who to find on arrival. |
| 15 | `_config/knowledge_base/day_of_logistics.md` | General day-of guide but CKP-flavored (food prep arrival flow). | DG day-of: where to park, who to ask for, stocking vs prep flow. |

### Tier 3: Generic (no changes needed for DG)

These files are company-agnostic and work as-is:

| File | Why It's Generic |
|------|-----------------|
| `server/services/draft_service.py` (HARD RULES) | Behavioral rules apply to all companies |
| `_config/response_playbook/app_issues.md` | Login, quit/reopen, banned accounts — same for all |
| `_config/response_playbook/payment_issues.md` | Stripe, bank accounts, ITIN — same for all |
| `_config/response_playbook/referral_program.md` | Already says "any partner's shifts count (Circle K, PepsiCo, Dollar General)" |
| `_config/response_playbook/account_and_reliability.md` | Address changes, profile updates — same for all |
| `_config/knowledge_base/payments.md` | Full Stripe/payment KB — company-agnostic |
| `_config/knowledge_base/platform_policies.md` | Already covers multi-company ("CK orientation does NOT qualify you for DG shifts") |
| `_config/knowledge_base/cancellation_policy.md` | Same cancellation rules for all |
| `_config/knowledge_base/post_shift_faq.md` | Generic post-shift guidance |
| `_config/knowledge_base/shift_mechanics.md` | Clock in/out, extensions — same for all |
| `_config/auto_responses.json` | Keyword prefilter — same for all |
| `_config/keyword_prefilter.json` | Opt-out, profanity, prompt injection — same for all |
| `tests/fixtures/concierge_replay.yaml` | Test infrastructure — add DG fixtures alongside CKP |

### Questions for DG Planning

1. **Orientation structure** — Does DG use the same 4-step in-app flow? Same certification call? Same BGC provider (Checkr)?
2. **Shift types** — What are DG shifts? Stocking, merchandising, resets, planogram compliance? Multiple sub-types?
3. **On-shift tools** — Does DG have an equivalent to Menu Pilot / Upshop? Any store-specific tech partners need to learn?
4. **Pay structure** — Same ~$15-18/hr range? Same $10 orientation bonus? Any DG-specific bonus programs?
5. **Store layout** — Where do DG partners report? Who's their on-site contact? Any equipment they need to learn?
6. **Dress code** — DG-specific requirements (no hairnet needed for stocking, but what about branded apparel)?
7. **Volume estimate** — How many DG DLs/week do we expect to run through the concierge?

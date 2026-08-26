# In-App Orientation Process — Source of Truth

> **Naming**: We call this the **"In-app orientation"** (not "remote orientation", not "Unlock nearby shifts"). In the app, it appears as a white card on the **Home** tab with a blue **"Required to unlock shifts"** banner at the top, the title **"In-app orientation"**, and **{{orientation_payout_cents}}** on the right.

## What It Is
A self-paced, mobile flow that unlocks shifts for a specific company. Each company has its own orientation with its own learning content. The Circle K orientation has **4 steps**, all triggered from the same **In-app orientation** card on the Home tab:
- **Step 1 — Learning modules** (8 sub-sections, the bulk of the time, ~50 minutes). The whole card has 4 steps total; partners do not need to track sub-section count.
- **Step 2 — Certification call** — triggered via the **"Call Us"** button on the same card
- **Step 3 — Profile photo submission**
- **Step 4 — Background check submission** (the {{orientation_payout}} lands once this completes)

The full CKP flow takes about 45 minutes total — partners can start and stop anytime; progress saves automatically.

## Where to Start
- **Primary entry**: **Home** tab (first icon in the bottom menu bar) → scroll to the white card with the blue **"Required to unlock shifts"** banner → titled **"In-app orientation"** with **{{orientation_payout_cents}}** on the right → tap **Get started** → **Start learning modules**.
- **Fallback** (if partner can't find the card): go to the **Shifts tab** → find any shift → open it → the shift will gate on the in-app orientation and let them start from there.

## Company-Specific Learning Modules

### Circle K - Premium (Food Prep)
The Interactive Orientation step contains 8 sub-sections that unlock sequentially (~50 minutes total). Don't quote the sub-section count — partners only see the 4 top-level steps.

1. Shiftsmart Introduction (~3 min)
2. Using the Unox Oven (~5 min)
3. Print Labels from Upshop (~5 min)
4. Print Labels from Menu Pilot (~3 min)
5. Scan Items (~5 min)
6. Food Assembly (~3 min)
7. Package & Label Items (~5 min)
8. Shift Walkthrough (~5 min)
9. Learning Review quiz (~2 min)

Full module-by-module guide: `ckp/ckp-orientation-walkthrough.md`.

### Dollar General (Stocking & Merchandising)
5 modules (~20-30 minutes total). Modules unlock sequentially.

1. Shiftsmart Introduction (~3 min)
2. Shiftsmart Scanner (~3 min)
3. Product Rotation Shift — organizing shelves, checking dates, removing expired items (~10 min)
4. Price Tag Updates — updating shelf tags from printed sheets (~7 min)
5. Learning Review quiz — 8 questions, 90% pass required (~3 min)

Full module-by-module guide: `dg/dg-orientation-walkthrough.md`.

## Background Check (BGC) — Important Behavior
- BGC submission is step 4 (the last step) of the Circle K in-app orientation, done from the same **In-app orientation** card.
- **Partners can pick up and work shifts while the BGC is pending** (being reviewed and approved). Always tell them this — it removes a big perceived blocker.
- **Do NOT tell partners that a shift will be auto-cancelled if the BGC fails.** That is platform behavior we handle quietly; surfacing it proactively discourages partners from picking up shifts.
- Partner-facing phrasing: "You can start picking up shifts while the background check is being reviewed."

## Pay
- Partner gets paid **{{orientation_payout}} once the background check (step 4) completes**. The {{orientation_payout}} is tied to BGC submission completion within the in-app orientation, not to the first shift. Partners can confirm the payout landed by tapping the **Earnings** tab at the bottom of the app.
- Shadow orientation (in-person) pays the full shift rate.

## Returning Partners
- Partners who have already completed orientation for another company (e.g., completed CKP, now orienting for DG) skip the certification call and BGC submission.
- For returning partners, orientation is just the learning modules (+ quiz where applicable). Once they pass, they're OP.

## In-Person Orientation Types
- **Shadow orientation**: one-on-one with an experienced M1 partner. Full shift rate.
- **Ambassador-led / Modular**: classroom-style group orientation.
- Default recommendation is the in-app orientation. Only offer in-person if confirmed available in the partner's market.

## Funnel Steps
1. Partner downloads app (DL)
2. Profile setup
3. Orientation assigned (OA) — in-app or in-person
4. Orientation passed (OP) — for in-app: all 4 steps complete (learning modules + certification call + profile photo + BGC submitted)
5. BGC clears in parallel (partner can pick up shifts while pending)
6. Eligible for shifts

## Orientation is Company-Specific
- Each company has its own orientation. A Circle K orientation qualifies you for Circle K shifts only.
- A Dollar General orientation qualifies you for Dollar General shifts only.
- Partners need separate orientations for each company they want to work with.
- **Dollar General is also zone-gated:** DG is only live in certain areas right now. Completing the DG orientation does NOT guarantee DG shifts will appear — the partner's zone also has to be enabled. When asked about DG, state both gates (separate orientation + zone availability). See `platform-policies.md` → "Dollar General Availability."

## Both-Deal Zones (Circle K + Dollar General both live)
- The partner chooses which orientation to start — present both options with honest one-line descriptions and per-company durations (Circle K about 45 min, Dollar General about 20 to 30 min). Both pay {{orientation_payout}} on background check completion.
- **Sequential, never parallel**: one orientation at a time. Finish the first before starting the second. If a partner wants both, route them to complete one first.
- **Second orientation is shorter**: a partner who already completed one company's orientation skips the certification call and BGC on the second (see Returning Partners above). Partner-facing phrasing: "Since you already did the certification call and background check, it's just the learning modules."
- **Unsure partners**: ask about work background once. Food service points to Circle K; retail, warehouse, or logistics points to Dollar General. If they stay unsure or don't answer, the default recommendation is Circle K (most available shifts), stated honestly.
- After completing orientation #1 and their first shift, the concierge may mention the second company's orientation once (see the cross-sell rule in system-base) — never mid-orientation.

## Progress Saves
- In-app orientation progress is saved automatically. Partners can start, pause, and pick up where they left off.
- Always mention this when partners ask about time commitment.

## Common Drop-Off Points
- Can't find the **In-app orientation** card on the Home tab (first try: quit and reopen the app; second: Shifts tab fallback)
- Sequential sub-section locking — partners don't realize the next sub-section unlocks only after the previous completes
- No in-person slots available near them

## What Counts as Completed
- **In-app (CKP)**: all 4 steps complete (learning modules + certification call + profile photo + BGC submitted)
- **In-app (DG)**: all 3 steps complete (learning modules + certification call + BGC submitted)
- **In-person**: `assignment_status = 'Completed'` on the orientation shift type
- Data source: `shiftsmart-api.shiftsmart_data.bq_learning_module_results`

## Program Launch
- CKP: 2026-02-19
- DG: 2026-06-10

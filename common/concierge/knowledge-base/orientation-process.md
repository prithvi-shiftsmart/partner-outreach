# In-App Orientation Process — Source of Truth

> **Naming**: We call this the **"In-app orientation"** (not "remote orientation", not "Unlock nearby shifts"). In the app, it appears as a white card on the **Home** tab with a blue **"Required to unlock shifts"** banner at the top, the title **"In-app orientation"**, and **$10.00** on the right.

## What It Is
A self-paced, mobile flow that unlocks shifts for a specific company (Circle K - Premium today). The orientation has **4 steps**, all triggered from the same **In-app orientation** card on the Home tab:
- **Step 1 — Learning modules** (8 sub-sections, the bulk of the time, ~50 minutes). The whole card has 4 steps total; partners do not need to track sub-section count.
- **Step 2 — Certification call** — triggered via the **"Call Us"** button on the same card
- **Step 3 — Profile photo submission**
- **Step 4 — Background check submission** (the $10 lands once this completes)

The full flow takes about 45 minutes total — partners can start and stop anytime; progress saves automatically.

## Where to Start
- **Primary entry**: **Home** tab (first icon in the bottom menu bar) → scroll to the white card with the blue **"Required to unlock shifts"** banner → titled **"In-app orientation"** with **$10.00** on the right → tap **Get started** → **Start learning modules**.
- **Fallback** (if partner can't find the card): go to the **Shifts tab** → find a Circle K Food Prep shift → open it → the shift will gate on the in-app orientation and let them start from there.

## The 4 Steps (Circle K - Premium Food Prep)
The Interactive Orientation step contains 8 sub-sections that unlock sequentially — partners must finish the previous one before the next opens. Don't quote the sub-section count to partners; they only see the 4 top-level steps.

1. Shiftsmart Introduction (~3 min)
2. Using the Unox Oven (~5 min)
3. Print Labels from Upshop (~5 min)
4. Print Labels from Menu Pilot (~3 min)
5. Scan Items (~5 min)
6. Food Assembly (~3 min)
7. Package & Label Items (~5 min)
8. Shift Walkthrough (~5 min)
9. Learning Review quiz (~2 min)

Full module-by-module guide: `in_app_orientation_walkthrough.md`.

## Background Check (BGC) — Important Behavior
- BGC submission is step 4 (the last step) of the in-app orientation, done from the same **In-app orientation** card.
- **Partners can pick up and work shifts while the BGC is pending** (being reviewed and approved). Always tell them this — it removes a big perceived blocker.
- **Do NOT tell partners that a shift will be auto-cancelled if the BGC fails.** That is platform behavior we handle quietly; surfacing it proactively discourages partners from picking up shifts.
- Partner-facing phrasing: "You can start picking up shifts while the background check is being reviewed."

## Pay
- Partner gets paid **$10 once the background check (step 4) completes**. The $10 is tied to BGC submission completion within the in-app orientation, not to the first shift. Partners can confirm the payout landed by tapping the **Earnings** tab at the bottom of the app.
- Shadow orientation (in-person) pays the full shift rate.

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

## Progress Saves
- In-app orientation progress is saved automatically. Partners can start, pause, and pick up where they left off.
- Always mention this when partners ask about time commitment.

## Common Drop-Off Points
- Can't find the **In-app orientation** card on the Home tab (first try: quit and reopen the app; second: Shifts tab fallback)
- Sequential sub-section locking — partners don't realize the next sub-section unlocks only after the previous completes
- No in-person slots available near them

## What Counts as Completed
- **In-app**: all 4 steps complete (learning modules + certification call + profile photo + BGC submitted)
- **In-person**: `assignment_status = 'Completed'` on the orientation shift type
- Data source: `shiftsmart-api.shiftsmart_data.bq_learning_module_results`

## Program Launch
- 2026-02-19

# In-App Orientation Process — Source of Truth

> **Naming**: We call this the "In-App Orientation" (not "remote orientation"). The in-app UI surfaces it under the "Earn $10 today, unlock shifts" section on the Home tab, via the "Unlock nearby shifts" card.

## What It Is
A self-paced, mobile flow that unlocks shifts for a specific company (Circle K - Premium today). It has four parts, all triggered from the same card on the Home tab:
- **9 learning modules** — ~30 minutes total, done on the partner's phone
- **Certification call** — triggered via the "Call Us" button on the same card
- **Profile photo submission**
- **Background check submission**

Certification call + profile photo + BGC submission take ~5 minutes combined.

## Where to Start
- **Primary entry**: Home tab → look for the "Earn $10 today, unlock shifts" section → tap **"Start earning"** on the "Unlock nearby shifts" card.
- **Fallback** (if partner can't find the card): go to the **Shifts tab** → find a Circle K Food Prep shift → open it → the shift will gate on the in-app orientation and let them start from there.

## The 9 Modules (Circle K - Premium Food Prep)
Modules unlock sequentially — partners must finish the previous module before the next opens.

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
- BGC submission is the last step of the in-app orientation, done from the same "Unlock nearby shifts" card.
- **Partners can pick up and work shifts while the BGC is pending** (being reviewed and approved). Always tell them this — it removes a big perceived blocker.
- **Do NOT tell partners that a shift will be auto-cancelled if the BGC fails.** That is platform behavior we handle quietly; surfacing it proactively discourages partners from picking up shifts.
- Partner-facing phrasing: "You can start picking up shifts while the background check is being reviewed."

## Pay
- Partner gets paid **$10 after finishing all the steps of the In-App Orientation** (all 9 modules + cert call + profile photo + BGC submission). The $10 is tied to orientation completion, not to the first shift.
- Shadow orientation (in-person) pays the full shift rate.

## In-Person Orientation Types
- **Shadow orientation**: one-on-one with an experienced M1 partner. Full shift rate.
- **Ambassador-led / Modular**: classroom-style group orientation.
- Default recommendation is the in-app orientation. Only offer in-person if confirmed available in the partner's market.

## Funnel Steps
1. Partner downloads app (DL)
2. Profile setup
3. Orientation assigned (OA) — in-app or in-person
4. Orientation passed (OP) — for in-app: all 9 modules + cert call + profile photo + BGC submitted
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
- Can't find the "Unlock nearby shifts" card on the Home tab (use the Shifts tab fallback)
- Sequential module locking — partners don't realize the next module unlocks only after the previous completes
- No in-person slots available near them

## What Counts as Completed
- **In-app**: all 9 modules status = 'completed' AND cert call + profile photo + BGC submitted
- **In-person**: `assignment_status = 'Completed'` on the orientation shift type
- Data source: `shiftsmart-api.shiftsmart_data.bq_learning_module_results`

## Program Launch
- 2026-02-19

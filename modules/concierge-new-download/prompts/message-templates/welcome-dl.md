# Welcome Download Template

## Campaign: activation (large/medium/small)
## Variables: {first_name}, {company}, {market}, {distance_miles}

Two A/B variants for first contact with a new download. Variant A is the **production DL intro currently in use** — short, names the orientation as the first step, anchors on the $10 payout, surfaces the HELP keyword CTA. Variant B is the pay-first alternative with a deep-link. Keyword behavior: see `_config/response_playbook/keyword_replies.md`.

## Variant A — Production DL Intro (currently in use)

Hi {first_name}! Welcome to Shiftsmart. I'm your personal concierge here to help you get started! Your first step is to complete your orientation in the app and you get paid {{orientation_payout}} when you finish it! Reply HELP if you have any questions

> **Note (2026-08):** The payout-timing token experiment (`{{orientation_payout_timing_verb}}` / `{{orientation_payout_timing_trigger}}` resolved from `firstShiftCompletedPayoutEnabled`) was reverted in production — Variant A is back to the plain finish-framing copy above with `{{orientation_payout}}` as the only token.

## Variant B — Pay-First + Reply HELP CTA

Hi {first_name}, welcome to Shiftsmart. You can earn {{orientation_payout}} with our In-app orientation for Circle K, which unlocks shifts in your area. 4 steps, about 45 min on your phone.

Reply **HELP** and I'll walk you through it, or tap here to start: shiftsmart://explore

Reply STOP to unsubscribe

## Variant C — Both-Deal Zone (CKP + DG)

Hi {first_name}! Welcome to Shiftsmart. I'm your personal concierge here to help you get started! Complete your orientation in the app and get paid {{orientation_payout}} when you finish. Reply HELP if you have any questions

### Variant C payout resolution

- **No timing treatment** — Variant C keeps the finish-framing copy above; the "a … bonus" wrapper was dropped in production along with the timing-token revert (2026-08).
- **Amount source**: the `{{orientation_payout}}` amount must come from the orientation card the app **renders first** in the partner's list of available remote orientations, mirroring the worker-app home ranking:
  - LD flag `WORKER_APP_API_REMOTE_ORIENTATION_RANKING` **off**: Dollar General card first when present.
  - Flag **on**: not-started cards ranked by launch window (in-window first) → advanced pickup rate (ascending, missing last) → shift-volume category (descending).
  - The winning card's company:role → closest remote-orientation-enabled site → `payoutAmount` (default $10 on any miss).

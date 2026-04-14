# Stage 02: Draft Messages

## Purpose
Generate personalized messages for each partner identified in Stage 01.

## Inputs
- Layer 4: `../01_identify/output/` (partner lists from BQ queries)
- Layer 3: `../../_config/message_templates/` (message templates)
- Layer 3: `../../_config/campaigns.json` (campaign-to-template mapping)
- Layer 3: `../../_config/personalization_rules.md` (personalization logic)
- Layer 3: `../../_config/tone_and_voice.md` (tone guide)

## Process
1. For each partner in each campaign's output:
   a. Look up the campaign's template from `campaigns.json`
   b. Load the template from `message_templates/`
   c. Fill variable slots: {first_name}, {company}, {market}, {distance_miles}, etc.
   d. Apply personalization rules (company display name mapping, experience-based recommendations)
   e. Apply tone guidelines
2. If A/B test is active: randomly assign variant A or B, note assignment
3. Flag any partners who appear in multiple campaigns (dedup — keep highest priority)

## Output
Write `output/draft_messages.json`:
```json
[
  {
    "draft_id": "msg_20260324_001",
    "partner_id": "abc-123",
    "partner_name": "Jane Doe",
    "phone": "5551234567",
    "campaign": "activation_small",
    "template": "welcome_dl",
    "variant": "A",
    "market": "Morgantown_WV",
    "company": "Circle K - Premium",
    "message": "Hi Jane! I'm your Shiftsmart guide...",
    "flagged": false,
    "flag_reason": null
  }
]
```

## After Completion
Present drafts to operator in a scannable format:
- Group by campaign
- Show partner name, market, message preview
- Highlight any flagged messages
- Ask: "Approve all, edit specific ones, or skip a campaign?"

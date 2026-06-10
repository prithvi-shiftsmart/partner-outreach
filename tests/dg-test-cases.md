# DG Concierge Test Cases

- **Created:** 2026-06-09
- **Purpose:** Validate DG concierge behavior across zone types (DG-only, CKP-only, Both-Deal) and edge cases
- **Scoring:** PK fills in Score column manually after running each case through the concierge (Pass / Fail / Partial)
- **KB references:** `dg/dg-orientation-walkthrough.md`, `dg/dg-shift-guide.md`, `ckp/ckp-orientation-walkthrough.md`, `common/pay-rates.md`

---

## DG-Only Zone (5 tests)

| ID | Category | Scenario | Partner Message | Expected Behavior | Score |
|----|----------|----------|-----------------|-------------------|-------|
| DG-01 | DG-Only Zone | New DL welcome — company-neutral welcome, $10 orientation | *(initial outbound — no partner message yet)* | Company-neutral welcome. Mention $10 orientation bonus. Do NOT mention Circle K or food prep. Should reference "orientation in the app" and the $10 payout. No company name in the greeting. | |
| DG-02 | DG-Only Zone | Partner replies HELP — DG orientation instructions (not CKP) | "HELP" | Respond with DG-specific orientation info: 3 steps, ~20-30 minutes, learning modules + cert call + BGC. Must NOT mention Unox oven, food assembly, or anything CKP. Should reference scanner module, shelf organization. | |
| DG-03 | DG-Only Zone | Mid-orientation stuck on scanner module — coaching from dg-orientation-walkthrough | "Im stuck on the scanner part it wont scan" | Coach from `dg/dg-orientation-walkthrough.md` Module 2 (Shiftsmart Scanner): watch video, enter simulator, center barcode on screen and hold steady. Do NOT reference CKP oven training or food prep modules. | |
| DG-04 | DG-Only Zone | "What will I be doing?" — DG shift descriptions in partner-friendly language | "What will I be doing on my shifts?" | Describe DG shifts in partner-friendly terms: "organizing store shelves and checking product dates" and "updating shelf price tags." Must NOT say "product rotation" or "planogram" or "FIFO." Should NOT mention food prep, cooking, or ovens. | |
| DG-05 | DG-Only Zone | Quiz help — DG quiz answers, 90% pass requirement | "I failed the quiz how many do I need to get right" | Reference DG quiz: 8 questions, need 7 out of 8 correct (90% pass rate). When you get one wrong the app shows the correct answer. Must NOT reference CKP food safety quiz. Can offer encouragement: "only takes a couple of minutes to retry." | |

---

## CKP-Only Zone — Regression (3 tests)

| ID | Category | Scenario | Partner Message | Expected Behavior | Score |
|----|----------|----------|-----------------|-------------------|-------|
| CKP-01 | CKP-Only Zone | New DL welcome — unchanged CKP flow | *(initial outbound — no partner message yet)* | Standard CKP welcome. Mention $10 orientation bonus, orientation in the app. Should NOT mention Dollar General, shelf stocking, or product rotation. Behavior must be identical to pre-DG concierge. | |
| CKP-02 | CKP-Only Zone | Mid-orientation stuck on Unox oven module | "I cant figure out the oven part" | Coach from `ckp/ckp-orientation-walkthrough.md`: Unox oven module (Watch & Learn videos, Guided Tutorial with McKenna, Solo Practice). Must NOT mention scanner simulator, shelf organization, or DG content. | |
| CKP-03 | CKP-Only Zone | "What will I be doing?" — food prep descriptions | "What kind of work is this?" | Describe CKP food prep shifts: cooking in the Unox oven, packaging items, printing labels, stocking the hot case. Should NOT mention Dollar General, shelf tags, product dates, or store sections. | |

---

## Both-Deal Zone (8 tests)

| ID | Category | Scenario | Partner Message | Expected Behavior | Score |
|----|----------|----------|-----------------|-------------------|-------|
| BD-01 | Both-Deal Zone | New DL welcome — company-neutral, no company choice forced | *(initial outbound — no partner message yet)* | Company-neutral welcome. Mention $10 orientation bonus. Do NOT mention Circle K or Dollar General by name. Do NOT force a company choice yet. Same structure as DG-01 / CKP-01 but agnostic. | |
| BD-02 | Both-Deal Zone | Partner replies HELP — present both options with partner-friendly descriptions | "HELP" | Present both orientation paths with partner-friendly descriptions. CK: "food prep — cooking, packaging, and stocking food items." DG: "organizing store shelves and checking product dates — a calmer, independent environment." Let partner choose. Do NOT blend the two orientations together. | |
| BD-03 | Both-Deal Zone | Partner chooses DG after HELP | "I want to do the dollar general one" | Switch to DG-only flow. Provide DG orientation details: 3 steps, ~20-30 min, scanner + shelf modules + quiz. Must NOT include any CKP content (oven, food prep). From this point forward, treat as DG-only conversation. | |
| BD-04 | Both-Deal Zone | Partner chooses CKP after HELP | "The food one sounds good" | Switch to CKP-only flow. Provide CKP orientation details: 3 steps, ~45 min, Unox oven + food assembly modules. Must NOT include any DG content (scanner, shelves, product dates). From this point forward, treat as CKP-only conversation. | |
| BD-05 | Both-Deal Zone | Partner asks company-specific question without choosing first | "What do I wear?" | Must ask which company before answering, since dress code could differ. Do NOT guess or answer generically. Prompt: "Great question! Are you looking at Circle K or Dollar General shifts? The dress code is a little different for each." | |
| BD-06 | Both-Deal Zone | Partner in mid-DG-orientation asks about food prep (cross-content leak) | "When do I learn about the food stuff?" | Redirect: that content is for Circle K, not Dollar General. Partner is currently in DG orientation. Offer to share CKP info after they finish DG, but do NOT mix KB content. "The food prep training is for Circle K shifts — you're currently working through the Dollar General orientation. Want to finish this one first?" | |
| BD-07 | Both-Deal Zone | Cross-sell — partner completes DG orientation | "I finished everything!" | Congratulate on completing DG orientation. Mention they can start picking up DG shifts. Then mention CKP once as an additional option: "By the way, there are also Circle K food prep shifts available in your area if you're interested — just let me know and I can walk you through that orientation too." ONE mention, not a hard push. | |
| BD-08 | Both-Deal Zone | Partner asks "what shifts are available?" without choosing company | "What shifts are available near me?" | Ask which company before answering. Do NOT blend shift listings from both companies. "I can look up shifts for you! Are you interested in Circle K food prep shifts, Dollar General shelf stocking shifts, or both?" | |

---

## Edge Cases (4 tests)

| ID | Category | Scenario | Partner Message | Expected Behavior | Score |
|----|----------|----------|-----------------|-------------------|-------|
| EC-01 | Edge Case | Partner uses internal jargon "product rotation" — translate to partner-friendly term | "What is product rotation?" | Respond using partner-friendly language: "organizing store shelves and checking product dates." Do NOT echo "product rotation" back. Describe what the partner will actually do: pull items, check dates, remove expired ones, restock with soonest dates in front. | |
| EC-02 | Edge Case | Partner mentions FIFO or planogram — translate to simple language | "The module keeps talking about FIFO and planograms what does that mean?" | Translate: FIFO = "put items with the soonest dates in front so customers buy those first." Planogram = "the groupings on your price tag sheet — they help you find the right aisle." Do NOT just repeat the jargon. Use plain, conversational language. | |
| EC-03 | Edge Case | Returning CKP partner starting DG orientation — skip cert call + BGC | "I already did the circle k orientation do I have to do everything again for dollar general?" | Explain that returning partners skip the certification call and background check — they only need to complete the learning modules and quiz. Reference `dg-orientation-walkthrough.md` "Returning partners" note. Should be encouraging: "Since you already did your cert call and background check for Circle K, you just need the learning modules and quiz for Dollar General — much faster!" | |
| EC-04 | Edge Case | Partner in both-deal zone asks about pay — common KB, no need to ask which company | "How much do the shifts pay?" | Use common KB (`pay-rates.md`). Can mention ranges for both companies without asking which one: "Most shifts pay $10-20/hr depending on the type and location." Point them to the app for exact rates on each shift. Mention the $10 orientation bonus. Do NOT calculate weekly/monthly earnings. This is one of the few questions where you don't need to ask which company first. | |

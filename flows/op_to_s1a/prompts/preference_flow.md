# Preference Flow -- OP -> S1A

## Preference branching logic

| Partner says | Concierge does |
|-------------|----------------|
| `1` / `2` / `3` | Book that shift -> assign_to_shift |
| `more` | Re-query top 3 by quality score, offset by 3 |
| "Closest to me" / "nearby" / "don't have a car" | Re-query top 3 by distance ascending |
| "Highest pay" / "what pays the most" | Re-query top 3 by total compensation (base pay + bonus) descending |
| "Mornings" / "afternoons" / "evenings" | Re-query top 3 matching time window |
| "Something in the morning that pays well" | Compound filter: time_window + total compensation sort |
| Specific day ("Do you have anything Saturday?") | Re-query filtered by day |
| No preference / no answer | Fallback to top 3 by quality score |
| Vague ("different time") | Follow-up: "What time works best? Breakfast (early AM), Lunch (mid-morning), Snack (early afternoon), or evening?" |
| Anything else | LLM interpretation; clarify if ambiguous |

## Pay sorting note
When presenting shifts sorted by pay, always sort by total compensation (base pay + bonus). A shift paying $19.50 + $20.00 bonus = $39.50 total, which ranks higher than $22.75 with no bonus.

## After preference re-query
- Present 3 new shifts using the same shift card format
- Booking CTA: "Reply 1, 2, or 3 to book"
- No additional preference prompt needed -- if they want to refine further, they'll say so

## Preamble lines per preference type
- Distance: "Here are the 3 closest shifts to you:"
- Pay: "Here are the top-paying shifts:"
- Time: "Got it -- here are {time} shifts:"
- More: "Here are 3 more options:"
- Compound: "Here are {time} shifts sorted by pay:"

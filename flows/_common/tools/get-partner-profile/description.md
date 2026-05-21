# get_partner_profile

Retrieves the partner's full profile including their authoritative funnel stage.

## When to call
- At the START of every conversation (ground truth rule)
- Before any assignment or booking action
- When verifying partner eligibility

## Important behaviors
- `funnel_cohort.current_stage` is the single source of truth for where the partner is in the funnel
- OP->S1A flow should only proceed if `current_stage == "op"`
- S1A->S1C flow should only proceed if `current_stage == "s1a"`
- If stage doesn't match the expected flow, do not proceed -- inform the partner of their actual status

-- ============================================================================
-- Bonus Partner Lookup
-- ============================================================================
-- PURPOSE: Pull all partners sent a specific payment bonus with contact info.
--          Swap the bonus ID in the WHERE clause to look up any campaign.
-- ============================================================================

SELECT
  d.partner_id,
  a.first_name,
  a.last_name,
  a.phone_number,
  a.email,
  d.bonus_name,
  d.company_name,
  d.is_opted_in,
  d.bonus_amount,
  d.shifts_requirement,
  d.shifts_picked_up,
  d.shifts_complete,
  d.valid_start_date,
  d.valid_end_date,
  d.total_paid
FROM `shiftsmart-api.growth.dim_dxgy_bonuses` d
LEFT JOIN (
  SELECT user_id, reporting_company, first_name, last_name, phone_number, email
  FROM `shiftsmart-api.bi.fct_partner_assessment_status`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY user_id, reporting_company ORDER BY last_active_at DESC) = 1
) a
  ON d.partner_id = a.user_id
  AND d.company_name = a.reporting_company
WHERE d.payment_bonus_id IN ({{BONUS_IDS}})
  AND d.is_opted_in IS NOT TRUE
ORDER BY d.shifts_complete DESC

-- ============================================================================
-- Dormant Partner Viewing Nudge — Low Forward PUR Zones
-- ============================================================================
-- PURPOSE: Identify OP/S1C partners who are sent shifts but not viewing them,
--          in CKP zones with low forward pickup rate. Daily Braze campaign.
-- SCOPE:   Circle K - Premium only. Partners in partner_cohort sent-not-seen
--          cohorts, active in L14D. Sliding scale on churn lookback by PUR tier.
--          Forward PUR = SUM(filled)/SUM(shifts) for next 7 days in supply model.
--          Export script enforces cooldown against past sends.
-- DATE:    2026-05-06
-- GRAIN:   One row per partner
-- TABLES:  growth.supply_model_daily_position,
--          growth.int_master_partner_throughput,
--          shiftsmart_data.bq_usercompanies_deduped
-- ============================================================================


-- ─── Forward PUR: of N7D shifts, what % are currently assigned ───
WITH low_pickup_zones AS (
  SELECT
    zone_description,
    company_name,
    SAFE_DIVIDE(SUM(filled), SUM(shifts)) AS forward_pickup_rate,
    CASE
      WHEN SAFE_DIVIDE(SUM(filled), SUM(shifts)) < 0.45 THEN 60
      ELSE 30
    END AS max_days_lookback
  FROM `growth.supply_model_daily_position`
  WHERE date BETWEEN CURRENT_DATE('America/New_York')
                 AND DATE_ADD(CURRENT_DATE('America/New_York'), INTERVAL 6 DAY)
    AND position = 'All'
    AND company_name = 'Circle K - Premium'
    AND shifts > 0
  GROUP BY zone_description, company_name
  HAVING SAFE_DIVIDE(SUM(filled), SUM(shifts)) < 0.60
),

-- ─── Active employee filter ───
active_employees AS (
  SELECT DISTINCT CAST(user AS STRING) AS partner_id
  FROM `shiftsmart_data.bq_usercompanies_deduped`
  WHERE status = 'employee'
    AND company_name = 'Circle K - Premium'
),

-- ─── Dormant partners: sent shifts but not viewing (sliding lookback) ───
dormant_partners AS (
  SELECT
    p.partner_id,
    p.first_name,
    p.last_name,
    p.phone_number,
    p.email,
    p.company_name,
    p.zone_description,
    p.op_date,
    p.s1c_date,
    p.partner_cohort,
    p.work_shifts_sent_next_7d,
    p.work_shifts_seen_next_7d,
    p.last_active_at,
    DATETIME_DIFF(
      CURRENT_DATETIME('America/New_York'),
      p.last_active_at,
      DAY
    ) AS days_since_last_active,
    lpz.forward_pickup_rate,
    lpz.max_days_lookback,
    CASE
      WHEN MOD(ABS(FARM_FINGERPRINT(p.partner_id)), 10) = 0 THEN 'control'
      ELSE 'treatment'
    END AS assignment_group
  FROM `growth.int_master_partner_throughput` p
  INNER JOIN low_pickup_zones lpz
    ON p.zone_description = lpz.zone_description
   AND p.company_name = lpz.company_name
  INNER JOIN active_employees ae
    ON p.partner_id = ae.partner_id
  WHERE p.partner_cohort IN (
      '06_s1c_not_assigned_sent_not_seen',
      '10_bgc_passed_sent_not_seen'
    )
    AND DATETIME_DIFF(CURRENT_DATETIME('America/New_York'), p.last_active_at, DAY) <= LEAST(lpz.max_days_lookback, 14)
    AND p.partner_added_to_company IS TRUE
    AND (p.currently_suspended IS NULL OR p.currently_suspended = FALSE)
    AND (p.currently_deactivated IS NULL OR p.currently_deactivated = FALSE)
    AND (p.is_fraud_partner IS NULL OR p.is_fraud_partner = FALSE)
    AND p.phone_number IS NOT NULL
)

SELECT *
FROM dormant_partners
ORDER BY assignment_group ASC, forward_pickup_rate ASC, work_shifts_sent_next_7d DESC

-- ============================================================================
-- Partner Churn Re-engagement — Low Forward PUR Zones
-- ============================================================================
-- PURPOSE: Identify churning S1C+ partners in CKP zones with low forward
--          pickup rate for daily Braze re-engagement campaign.
-- SCOPE:   Circle K - Premium only. S1C+ partners worked in L60D but not L30D.
--          Sliding scale: worse forward PUR = wider lookback window.
--            <45% PUR → up to 60 days since last shift
--            45-60%   → up to 45 days
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
      ELSE 45
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

-- ─── Churning S1C+ partners in low-PUR zones (sliding lookback) ───
churning_partners AS (
  SELECT
    p.partner_id,
    p.first_name,
    p.last_name,
    p.phone_number,
    p.email,
    p.company_name,
    p.zone_description,
    p.s1c_date,
    p.last_active_at,
    p.days_since_last_shift_worked,
    p.churn_status,
    p.churn_probability,
    p.partner_cohort,
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
  WHERE p.s1c_date IS NOT NULL
    AND p.days_since_last_shift_worked > 30
    AND p.days_since_last_shift_worked <= lpz.max_days_lookback
    AND p.partner_added_to_company IS TRUE
    AND (p.currently_suspended IS NULL OR p.currently_suspended = FALSE)
    AND (p.currently_deactivated IS NULL OR p.currently_deactivated = FALSE)
    AND (p.is_fraud_partner IS NULL OR p.is_fraud_partner = FALSE)
    AND p.phone_number IS NOT NULL
)

SELECT *
FROM churning_partners
ORDER BY assignment_group ASC, forward_pickup_rate ASC, churn_probability DESC

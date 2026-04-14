-- ============================================================================
-- Referral Campaign — Recent OPs in Low DL Priority Markets
-- ============================================================================
-- PURPOSE: Identify partners who recently completed orientation in priority
--          markets where DL volume is below the rolling L7D target.
--          Include referral bonus amounts available in their market.
-- OUTPUT:  One row per partner with contact info, market, and bonus details.
-- ============================================================================

-- ┌───────────────────────────────────────────────────┐
-- │ ADJUSTABLE PARAMETERS                              │
-- │                                                     │
-- │  Recent OP window:  14 days  (recent_ops CTE)       │
-- │  Low DL definition: dl_l7d < rolling_l7d_dl_target  │
-- └───────────────────────────────────────────────────┘


-- ─────────────────────────────────────────────────────────────────────────────
-- 1. REFERENCE LOOKUPS
-- ─────────────────────────────────────────────────────────────────────────────

WITH hex_lookup AS (
  SELECT
    hex AS store_cluster,
    stg_hex_city_description AS city_name
  FROM `growth.int_hex_description`
),


-- ─────────────────────────────────────────────────────────────────────────────
-- 2. PRIORITY MARKETS + DL TARGET
-- ─────────────────────────────────────────────────────────────────────────────

priority_markets AS (
  SELECT
    sm.company_name,
    h.stg_hex_city_description AS city_name,
    SUM(IFNULL(sm.rolling_l7d_dl_target, 0)) AS rolling_l7d_dl_target
  FROM `growth.supply_model_daily_position` sm
  JOIN `growth.int_hex_description` h ON sm.store_cluster = h.hex
  WHERE
    sm.date = CURRENT_DATE('America/New_York')
    AND sm.position = 'All'
    AND sm.sm_priority_market_flag = 1
    AND sm.company_name IN ('Circle K - Premium', 'PepsiCo Beverages', 'PepsiCo Foods')
  GROUP BY 1, 2
),


-- ─────────────────────────────────────────────────────────────────────────────
-- 3. ACTUAL DL VOLUME (L7D)
-- ─────────────────────────────────────────────────────────────────────────────

dl_actual_l7d AS (
  SELECT
    dl.company_name,
    h.city_name,
    COUNT(DISTINCT dl.partner_id) AS dl_l7d
  FROM `growth.int_master_partner_throughput` dl
  JOIN hex_lookup h ON h.store_cluster = dl.closest_store_cluster
  WHERE
    dl.created_date >= DATE_TRUNC(CURRENT_DATE('America/New_York'), WEEK(MONDAY)) - INTERVAL 7 DAY
    AND dl.created_date < DATE_TRUNC(CURRENT_DATE('America/New_York'), WEEK(MONDAY))
    AND dl.partner_onboarded
    AND dl.closest_project_store_proximity_miles <= 30
    AND dl.company_name IN ('Circle K - Premium', 'PepsiCo Beverages', 'PepsiCo Foods')
  GROUP BY 1, 2
),


-- ─────────────────────────────────────────────────────────────────────────────
-- 4. LOW DL MARKETS (actual < target)
-- ─────────────────────────────────────────────────────────────────────────────

low_dl_markets AS (
  SELECT
    pm.company_name,
    pm.city_name,
    pm.rolling_l7d_dl_target,
    IFNULL(da.dl_l7d, 0) AS dl_l7d
  FROM priority_markets pm
  LEFT JOIN dl_actual_l7d da
    ON pm.company_name = da.company_name
    AND pm.city_name = da.city_name
  WHERE IFNULL(da.dl_l7d, 0) < pm.rolling_l7d_dl_target
),


-- ─────────────────────────────────────────────────────────────────────────────
-- 5. RECENT OPs IN LOW DL MARKETS
-- ─────────────────────────────────────────────────────────────────────────────

recent_ops AS (
  SELECT DISTINCT
    a.partner_id,
    a.company_name,
    a.shift_date AS op_date,
    CASE
      WHEN a.location.store_cluster IS NULL THEN p.closest_store_cluster
      ELSE a.location.store_cluster
    END AS store_cluster
  FROM `bi.fct_shift_assignments` a
  LEFT JOIN `growth.int_master_partner_throughput` p
    ON a.partner_id = p.partner_id
    AND a.company_name = p.company_name
  WHERE
    a.company_name IN ('Circle K - Premium', 'PepsiCo Beverages', 'PepsiCo Foods')
    AND a.shift_date >= CURRENT_DATE('America/New_York') - 14  -- ← RECENT OP WINDOW
    AND a.shift.type = 'orientation'
    AND a.assignment_status = 'Completed'
    AND a.partner_id IS NOT NULL
),

recent_ops_with_city AS (
  SELECT
    ro.partner_id,
    ro.company_name,
    ro.op_date,
    ro.store_cluster,
    h.city_name
  FROM recent_ops ro
  JOIN hex_lookup h ON h.store_cluster = ro.store_cluster
  -- Only keep partners in low DL markets
  INNER JOIN low_dl_markets ldm
    ON ro.company_name = ldm.company_name
    AND h.city_name = ldm.city_name
),


-- ─────────────────────────────────────────────────────────────────────────────
-- 6. PARTNER CONTACT INFO
-- ─────────────────────────────────────────────────────────────────────────────

partner_details AS (
  SELECT DISTINCT
    mpt.partner_id,
    mpt.company_name,
    mpt.first_name,
    mpt.last_name,
    mpt.email,
    mpt.phone_number,
    mpt.msa
  FROM `growth.int_master_partner_throughput` mpt
  WHERE
    mpt.company_name IN ('Circle K - Premium', 'PepsiCo Beverages', 'PepsiCo Foods')
),


-- ─────────────────────────────────────────────────────────────────────────────
-- 7. REFERRAL BONUS AMOUNTS (per city)
-- ─────────────────────────────────────────────────────────────────────────────

referral_offers AS (
  SELECT DISTINCT
    h3Geohash,
    referrerAmount,
    refereeAmount,
    shiftCountRequirement
  FROM `shiftsmart-api.shiftsmart_data.ssm_referralcampaigns`,
  UNNEST(h3Geohashes) AS h3Geohash
  WHERE isActive = TRUE
),

referral_by_city AS (
  SELECT
    h.city_name,
    MAX(r.referrerAmount) AS referrer_bonus,
    MAX(r.refereeAmount) AS referee_bonus,
    MAX(r.shiftCountRequirement) AS shifts_required
  FROM referral_offers r
  JOIN hex_lookup h ON h.store_cluster = r.h3Geohash
  GROUP BY 1
)


-- ─────────────────────────────────────────────────────────────────────────────
-- 8. FINAL OUTPUT
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
  ro.partner_id,
  pd.first_name,
  pd.last_name,
  pd.email,
  pd.phone_number,
  ro.company_name,
  ro.city_name,
  ro.op_date,
  pd.msa,

  -- Market DL context
  ldm.rolling_l7d_dl_target,
  ldm.dl_l7d,

  -- Referral bonus available in their market
  IFNULL(rb.referrer_bonus, 0) AS referrer_bonus,
  IFNULL(rb.referee_bonus, 0) AS referee_bonus,
  IFNULL(rb.shifts_required, 0) AS shifts_required

FROM recent_ops_with_city ro

JOIN partner_details pd
  ON ro.partner_id = pd.partner_id
  AND ro.company_name = pd.company_name

JOIN low_dl_markets ldm
  ON ro.company_name = ldm.company_name
  AND ro.city_name = ldm.city_name

LEFT JOIN referral_by_city rb
  ON ro.city_name = rb.city_name

ORDER BY ro.company_name, ro.city_name, ro.op_date DESC

-- ============================================================================
-- Priority Market Partner Activation — LARGE MARKETS (>300 weekly shifts)
-- ============================================================================
-- RADIUS:   10 miles
-- ACTIVITY: Last active within 14 days
-- SCOPE:    Company+city combinations with >300 shifts in supply model
-- EXCLUDE:  San Antonio_TX (CKP), Westminster_CO (CKP)
-- INCLUDE:  Austin_TX, Houston_TX (PepsiCo Foods — forced regardless of shift count)
-- ============================================================================

-- ┌──────────────────────────────────────────────┐
-- │ ADJUSTABLE PARAMETERS (edit these as needed)  │
-- │                                                │
-- │  Shift threshold:  > 300  (market_shifts CTE)  │
-- │  Radius:           10 mi  (16093.4 m)          │
-- │  Activity window:  14 days                     │
-- │  Exclusions:       San Antonio_TX, Westminster │
-- │  Force-includes:   Austin_TX, Houston_TX (Pep) │
-- └──────────────────────────────────────────────┘

-- Step 1: Dynamically identify priority markets from supply model flag.
WITH priority_zones AS (
  SELECT DISTINCT
    sm.store_cluster,
    sm.zone_description,
    sm.company_name
  FROM `growth.supply_model_daily_position` sm
  WHERE
    sm.date = DATE_TRUNC(CURRENT_DATE('America/New_York'), WEEK(MONDAY))
    AND sm.position = 'All'
    AND sm.sm_priority_market_flag = 1
    AND sm.company_name LIKE ANY ('%Pepsi%', '%Circle%Pre%')
),

-- Step 2: Calculate shifts per company+city — filter to LARGE markets (>300).
-- Excludes San Antonio (CKP) and Westminster (CKP).
-- Force-includes Austin and Houston (Pepsi) regardless of shift count.
market_shifts AS (
  SELECT
    sm.company_name,
    h.stg_hex_city_description AS city_name,
    SUM(IFNULL(sm.shifts, 0)) AS total_shifts
  FROM `growth.supply_model_daily_position` sm
  JOIN `growth.int_hex_description` h ON sm.store_cluster = h.hex
  WHERE
    sm.date = CURRENT_DATE('America/New_York')
    AND sm.position = 'All'
    AND sm.company_name LIKE ANY ('%Pepsi%', '%Circle%Pre%')
    AND sm.sm_priority_market_flag = 1
    -- ← EXCLUSIONS: remove these CKP markets
    AND NOT (sm.company_name = 'Circle K - Premium' AND h.stg_hex_city_description IN ('San Antonio_TX', 'Westminster_CO'))
  GROUP BY 1, 2
  HAVING SUM(IFNULL(sm.shifts, 0)) > 300  -- ← SHIFT THRESHOLD

  UNION ALL

  -- ← FORCE-INCLUDES: Pepsi markets added regardless of shift count
  SELECT
    sm.company_name,
    h.stg_hex_city_description AS city_name,
    SUM(IFNULL(sm.shifts, 0)) AS total_shifts
  FROM `growth.supply_model_daily_position` sm
  JOIN `growth.int_hex_description` h ON sm.store_cluster = h.hex
  WHERE
    sm.date = CURRENT_DATE('America/New_York')
    AND sm.position = 'All'
    AND sm.company_name LIKE '%Pepsi%'
    AND sm.sm_priority_market_flag = 1
    AND h.stg_hex_city_description IN ('Austin_TX', 'Houston_TX')
  GROUP BY 1, 2
  HAVING SUM(IFNULL(sm.shifts, 0)) <= 300  -- only add if not already captured above
),

-- Step 3: Get store locations for stores in large priority markets.
priority_stores AS (
  SELECT DISTINCT
    s.location.external_id AS store_num,
    pz.zone_description AS zone,
    s.location.store_cluster,
    s.location.lat AS store_lat,
    s.location.lng AS store_lng,
    s.company_name
  FROM `bi.fct_shift_assignments` s
  INNER JOIN priority_zones pz
    ON s.location.store_cluster = pz.store_cluster
    AND s.company_name = pz.company_name
  INNER JOIN `growth.int_hex_description` h
    ON s.location.store_cluster = h.hex
  INNER JOIN market_shifts ms
    ON s.company_name = ms.company_name
    AND h.stg_hex_city_description = ms.city_name
  WHERE
    s.shift_date >= CURRENT_DATE("America/New_York") - 7
),

-- Step 4: Get eligible partners — active within 14 days, un-oriented.
eligible_partners AS (
  SELECT DISTINCT
    partner_id,
    first_name,
    last_name,
    email,
    phone_number,
    partner_lat,
    partner_lng,
    company_name,
    last_active_at,
    msa
  FROM `growth.int_master_partner_throughput` mpt
  WHERE
    partner_added_to_company IS TRUE
    AND last_active_at >= DATETIME_SUB(CURRENT_DATETIME("America/New_York"), INTERVAL 14 DAY)  -- ← ACTIVITY WINDOW
    AND op_date IS NULL
    AND company_name IN ('Circle K - Premium', 'PepsiCo Beverages', 'PepsiCo Foods')
    AND partner_lat IS NOT NULL
    AND partner_lng IS NOT NULL
    AND NOT EXISTS (
      SELECT 1
      FROM `bi.fct_shift_assignments` sa
      WHERE sa.partner_id = mpt.partner_id
        AND sa.company_name = mpt.company_name
        AND sa.shift_date >= CURRENT_DATE("America/New_York") - 90
        AND sa.shift.type = 'orientation'
        AND sa.assignment_status != 'Canceled'
    )
),

-- Step 5: Calculate distance — 10 mile radius.
partner_store_distance AS (
  SELECT
    p.partner_id,
    p.first_name,
    p.last_name,
    p.email,
    p.phone_number,
    p.company_name,
    p.last_active_at,
    p.msa,
    s.store_num,
    s.zone,
    s.store_cluster,
    ST_DISTANCE(
      ST_GEOGPOINT(p.partner_lng, p.partner_lat),
      ST_GEOGPOINT(s.store_lng, s.store_lat)
    ) AS distance_meters,
    ROW_NUMBER() OVER (
      PARTITION BY p.partner_id, p.company_name
      ORDER BY ST_DISTANCE(
        ST_GEOGPOINT(p.partner_lng, p.partner_lat),
        ST_GEOGPOINT(s.store_lng, s.store_lat)
      )
    ) AS rn
  FROM eligible_partners p
  INNER JOIN priority_stores s
    ON p.company_name = s.company_name
  WHERE
    ST_DISTANCE(
      ST_GEOGPOINT(p.partner_lng, p.partner_lat),
      ST_GEOGPOINT(s.store_lng, s.store_lat)
    ) <= 16093.4  -- ← RADIUS (10 mi)
)

SELECT
  partner_id,
  first_name,
  last_name,
  email,
  phone_number,
  company_name,
  zone,
  store_num,
  ROUND(distance_meters / 1609.34, 1) AS distance_miles,
  last_active_at,
  msa
FROM partner_store_distance
WHERE rn = 1
ORDER BY company_name, zone, distance_miles

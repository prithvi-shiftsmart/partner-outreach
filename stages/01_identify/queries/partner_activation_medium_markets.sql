-- ============================================================================
-- Priority Market Partner Activation — MEDIUM MARKETS (Specific Scope)
-- ============================================================================
-- RADIUS:   15 miles
-- ACTIVITY: Last active within 14 days
-- SCOPE:    All Pepsi priority markets + 5 specific Circle K cities
-- ============================================================================

-- ┌──────────────────────────────────────────────┐
-- │ ADJUSTABLE PARAMETERS (edit these as needed)  │
-- │                                                │
-- │  Radius:           15 mi  (24140.2 m)          │
-- │  Activity window:  7 days                      │
-- └──────────────────────────────────────────────┘

-- Step 1: Define target markets — all Pepsi priority + specific CK cities.
WITH target_markets AS (
  -- All Pepsi priority markets
  SELECT DISTINCT
    sm.company_name,
    h.stg_hex_city_description AS city_name,
    sm.store_cluster
  FROM `growth.supply_model_daily_position` sm
  JOIN `growth.int_hex_description` h ON sm.store_cluster = h.hex
  WHERE
    sm.date = CURRENT_DATE('America/New_York')
    AND sm.position = 'All'
    AND sm.sm_priority_market_flag = 1
    AND sm.company_name LIKE '%Pepsi%'

  UNION DISTINCT

  -- Specific Circle K cities
  SELECT DISTINCT
    sm.company_name,
    h.stg_hex_city_description AS city_name,
    sm.store_cluster
  FROM `growth.supply_model_daily_position` sm
  JOIN `growth.int_hex_description` h ON sm.store_cluster = h.hex
  WHERE
    sm.date = CURRENT_DATE('America/New_York')
    AND sm.position = 'All'
    AND sm.sm_priority_market_flag = 1
    AND sm.company_name LIKE '%Circle%Pre%'
    AND h.stg_hex_city_description IN (
      'Morgantown_WV',
      'Terre Haute_IN',
      'Belville_NC',
      'Calallen_TX',
      'Jacksonville_NC'
    )
),

-- Step 2: Get store locations for stores in target markets.
priority_stores AS (
  SELECT DISTINCT
    s.location.external_id AS store_num,
    tm.city_name AS zone,
    s.location.store_cluster,
    s.location.lat AS store_lat,
    s.location.lng AS store_lng,
    s.company_name
  FROM `bi.fct_shift_assignments` s
  INNER JOIN target_markets tm
    ON s.location.store_cluster = tm.store_cluster
    AND s.company_name = tm.company_name
  WHERE
    s.shift_date >= CURRENT_DATE("America/New_York") - 7
),

-- Step 3: Get eligible partners — active within 7 days, no orientation (past or scheduled).
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
    AND last_active_at >= DATETIME_SUB(CURRENT_DATETIME("America/New_York"), INTERVAL 7 DAY)  -- ← ACTIVITY WINDOW
    AND op_date IS NULL                          -- never completed an orientation
    AND company_name IN ('Circle K - Premium', 'PepsiCo Beverages', 'PepsiCo Foods')
    AND partner_lat IS NOT NULL
    AND partner_lng IS NOT NULL
    AND NOT EXISTS (                             -- no past or future orientation on the books
      SELECT 1
      FROM `bi.fct_shift_assignments` sa
      WHERE sa.partner_id = mpt.partner_id
        AND sa.company_name = mpt.company_name
        AND sa.shift_date BETWEEN DATE_SUB(CURRENT_DATE("America/New_York"), INTERVAL 1 YEAR) AND DATE_ADD(CURRENT_DATE("America/New_York"), INTERVAL 90 DAY)
        AND sa.shift.type = 'orientation'
        AND sa.assignment_status != 'Canceled'
    )
),

-- Step 4: Calculate distance — 15 mile radius.
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
    ) <= 24140.2  -- ← RADIUS (15 mi)
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

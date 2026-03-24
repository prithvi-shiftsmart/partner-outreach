-- ============================================================================
-- Priority Market Partner Activation — VARIABLE RADIUS TEST VERSION
-- ============================================================================
-- RADIUS:   Per-market (set individually in target_markets CTE)
-- ACTIVITY: Last active within 14 days OR downloaded in last 30 days
-- SCOPE:    13 hardcoded small markets
-- OUTPUT:   Flag for active DxGy — filter to get both views
-- ============================================================================

-- ┌──────────────────────────────────────────────────────────┐
-- │ To adjust a market's radius, edit the radius_miles       │
-- │ value next to the city name in Step 1 below.             │
-- └──────────────────────────────────────────────────────────┘

-- Step 1: Target markets with per-market radius.
WITH target_markets AS (
  SELECT city, radius_miles, radius_miles * 1609.34 AS radius_meters
  FROM UNNEST([
    STRUCT('Hollywood_FL'       AS city, 20 AS radius_miles),
    STRUCT('Elizabethtown_KY'   AS city, 20 AS radius_miles),
    STRUCT('George West_TX'     AS city, 20 AS radius_miles),
    STRUCT('Boone_NC'           AS city, 20 AS radius_miles),
    STRUCT('Odessa_TX'          AS city, 20 AS radius_miles),
    STRUCT('Rockport_AR'        AS city, 20 AS radius_miles),
    STRUCT('Dayton_TN'          AS city, 20 AS radius_miles),
    STRUCT('Dunlap_TN'          AS city, 20 AS radius_miles),
    STRUCT('Vernon_FL'          AS city, 20 AS radius_miles),
    STRUCT('Pilot Mountain_NC'  AS city, 20 AS radius_miles),
    STRUCT('Clifton_CO'         AS city, 20 AS radius_miles),
    STRUCT('Mount Vernon_IL'    AS city, 20 AS radius_miles),
    STRUCT('Niceville_FL'       AS city, 20 AS radius_miles)
  ])
),

-- Step 2: Get store locations in target markets (carry radius through).
priority_stores AS (
  SELECT DISTINCT
    s.location.external_id AS store_num,
    h.stg_hex_city_description AS zone,
    s.location.store_cluster,
    s.location.lat AS store_lat,
    s.location.lng AS store_lng,
    s.company_name,
    tm.radius_miles,
    tm.radius_meters
  FROM `bi.fct_shift_assignments` s
  INNER JOIN `growth.int_hex_description` h
    ON s.location.store_cluster = h.hex
  INNER JOIN target_markets tm
    ON h.stg_hex_city_description = tm.city
  WHERE
    s.shift_date >= CURRENT_DATE("America/New_York") - 7
    AND s.company_name IN ('Circle K - Premium', 'PepsiCo Beverages', 'PepsiCo Foods')
),

-- Step 3: Get eligible partners — active within 14 days OR DL'd in last 30 days.
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
    created_date,
    msa
  FROM `growth.int_master_partner_throughput` mpt
  WHERE
    partner_added_to_company IS TRUE
    AND (
      last_active_at >= DATETIME_SUB(CURRENT_DATETIME("America/New_York"), INTERVAL 14 DAY)
      OR created_date >= DATE_SUB(CURRENT_DATE("America/New_York"), INTERVAL 30 DAY)
    )
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

-- Step 4: Partners with an active DxGy offer + opt-in status.
active_dxgy AS (
  SELECT DISTINCT
    company_name,
    partner_id,
    is_opted_in
  FROM `growth.dim_dxgy_bonuses`
  WHERE valid_start_date <= CURRENT_DATE()
    AND valid_end_date >= CURRENT_DATE()
),

-- Step 5: Calculate distance — filtered by per-market radius.
partner_store_distance AS (
  SELECT
    p.partner_id,
    p.first_name,
    p.last_name,
    p.email,
    p.phone_number,
    p.company_name,
    p.last_active_at,
    p.created_date,
    p.msa,
    s.store_num,
    s.zone,
    s.store_cluster,
    s.radius_miles AS market_radius_miles,
    d.partner_id IS NOT NULL AS has_active_dxgy,
    IFNULL(d.is_opted_in, FALSE) AS dxgy_opted_in,
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
  LEFT JOIN active_dxgy d
    ON p.partner_id = d.partner_id
    AND p.company_name = d.company_name
  WHERE
    ST_DISTANCE(
      ST_GEOGPOINT(p.partner_lng, p.partner_lat),
      ST_GEOGPOINT(s.store_lng, s.store_lat)
    ) <= s.radius_meters  -- ← PER-MARKET RADIUS
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
  market_radius_miles,
  ROUND(distance_meters / 1609.34, 1) AS distance_miles,
  last_active_at,
  created_date,
  msa,
  has_active_dxgy,
  dxgy_opted_in
FROM partner_store_distance
WHERE rn = 1
ORDER BY company_name, zone, distance_miles

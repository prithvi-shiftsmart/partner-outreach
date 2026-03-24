-- =============================================================================
-- INCOMPLETE ASYNC ORIENTATION — PRIORITY MARKET PARTNERS
-- =============================================================================
-- PURPOSE: Find partners in priority markets who started the async orientation
--          but did not finish it. These are re-engagement candidates.
--
-- LOGIC:
--   1. Identify current priority market zones (supply model flag, this week's Monday)
--   2. Pull all async orientation attempts, count completed modules per partner
--   3. Match partners to priority markets via their most recent CKP shift location
--   4. Check if partner completed the remote orientation (shift_id IS NOT NULL)
--   5. Filter to: started (2+ modules), not finished (<7 modules), no remote OP
--
-- OUTPUT: One row per partner — name, phone, market, module progress, remote OP status
-- =============================================================================

-- STEP 1: Anchor to current week's Monday for supply model snapshot
WITH week_bounds AS (
  SELECT DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY)) AS curr_mon
),

-- STEP 2: Get all store_clusters flagged as priority markets this week
-- Covers Pepsi and Circle K Premium accounts
priority_zones AS (
  SELECT DISTINCT store_cluster, hex_city_description
  FROM `growth.supply_model_daily_position`
  CROSS JOIN week_bounds wb
  WHERE company_name LIKE ANY ('%Pepsi%', '%Circle%Pre%')
    AND position = 'All'                -- aggregate position view
    AND sm_priority_market_flag = 1     -- priority market flag from supply model
    AND date = wb.curr_mon              -- snapshot as of this Monday
),

-- STEP 3: Parse async orientation progress from learning module JSON
-- completed_modules = 1 if all 7 modules done, 0 otherwise
-- num_of_completed_modules = raw count of finished modules (0-7)
-- remote_orientation = 1 if partner has a completed remote auto-creation shift (shift_id IS NOT NULL)
learning_modules AS (
  SELECT
    m.user_id AS partner_id,
    CASE
      WHEN (
        SELECT COUNTIF(JSON_VALUE(progress_modules[key], '$.status') = 'completed')
        FROM UNNEST(JSON_KEYS(progress_modules)) AS key
      ) >= 7 THEN 1
      ELSE 0
    END AS completed_modules,
    (
      SELECT COUNTIF(JSON_VALUE(progress_modules[key], '$.status') = 'completed')
      FROM UNNEST(JSON_KEYS(progress_modules)) AS key
    ) AS num_of_completed_modules,
    MAX(CASE WHEN a.shift_id IS NOT NULL THEN 1 ELSE 0 END) AS remote_orientation,
    DATE(TIMESTAMP(m.created_at), "America/New_York") AS mod_create_date,
    progress_current_module_id AS last_mod_completed
  FROM `shiftsmart-api.shiftsmart_data.bq_learning_module_results` m
  LEFT JOIN `bi.fct_shift_assignments` a
    ON a.partner_id = m.user_id
    AND a.shift_date >= '2026-02-19'
    AND a.assignment_status = 'Completed'
    AND a.shift.is_remote IS TRUE           -- remote orientation shift
    AND a.shift.source = 'auto-creation'    -- auto-created (not manual)
  GROUP BY ALL
  HAVING mod_create_date >= '2026-02-19'  -- program launch date
),

-- STEP 4: Link partners to priority markets via their most recent CKP shift
-- INNER JOIN to priority_zones ensures only priority market partners survive
-- QUALIFY keeps one row per partner (most recent shift location wins)
partner_market AS (
  SELECT
    f.partner_id,
    pz.hex_city_description AS city_name
  FROM `bi.fct_shift_assignments` f
  INNER JOIN priority_zones pz
    ON f.location.store_cluster = pz.store_cluster
  WHERE f.company_name = 'Circle K - Premium'
    AND f.shift_date >= CURRENT_DATE - 90  -- look back 90 days for shift history
  QUALIFY ROW_NUMBER() OVER (PARTITION BY f.partner_id ORDER BY f.shift_date DESC) = 1
)

-- STEP 6: Final output — join modules to market, add partner contact info
-- INNER JOIN partner_market: only partners in priority markets
-- WHERE: started (>= 2 modules), not completed (< 7), no remote orientation
SELECT
  lm.partner_id,
  s.first_name,
  s.last_name,
  s.phone_number,
  pm.city_name,
  lm.num_of_completed_modules,
  lm.last_mod_completed,
  lm.remote_orientation,
  lm.mod_create_date
FROM learning_modules lm
INNER JOIN partner_market pm
  ON pm.partner_id = lm.partner_id
LEFT JOIN `shiftsmart-api.shiftsmart_data.bq_userstats_deduped` s
  ON s.uuid = lm.partner_id
WHERE lm.completed_modules = 0           -- did NOT finish all 7 modules
  AND lm.num_of_completed_modules >= 2   -- but completed at least 2
  AND lm.remote_orientation = 0          -- has NOT completed the remote orientation
ORDER BY lm.mod_create_date DESC, lm.num_of_completed_modules DESC

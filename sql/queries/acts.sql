-- Defines a five-column table, each row is a run.
-- The first columns it the run ID, the rest of columns are Boolean.
-- Mind: Acts get generated with Seed, so known even if *not* reached!
-- Params (see export.py): :collection, :charac, ASC_PLACEHOLDER -> :asc0, :asc1, ...

WITH runs_id_acts AS (
SELECT runs.id,
    (CASE WHEN runs_acts.act = 'ACT.OVERGROWTH' THEN 1 ELSE 0 END) AS overgrowth,
    (CASE WHEN runs_acts.act = 'ACT.UNDERDOCKS' THEN 1 ELSE 0 END) AS underdocks,
    (CASE WHEN runs_acts.act = 'ACT.HIVE' THEN 1 ELSE 0 END) AS hive,
    (CASE WHEN runs_acts.act = 'ACT.GLORY' THEN 1 ELSE 0 END) as glory
  FROM runs
  JOIN runs_acts on runs.id = runs_acts.run_id
  WHERE runs.collection = :collection
  AND (:charac IS NULL OR runs.charac = :charac)
  AND runs.ascension IN (ASC_PLACEHOLDER)

),

-- Use the run IDs in runs_overgrowth to list the log ("node", "seen", etc.)
-- up to floor 17 of the runs that saw ACT.OVERGROWTH
overgrowth_nodes AS (
  SELECT 'overgrowth' AS act, runs_nodes.*,
    (CASE WHEN runs_nodes.current_hp = 0 THEN 1 ELSE 0 END ) AS death
  FROM runs_id_acts
  JOIN runs_nodes on runs_nodes.run_id = runs_id_acts.id
  WHERE runs_nodes.floor BETWEEN 0 AND 16 
   AND runs_id_acts.overgrowth = 1
),
underdocks_nodes AS (
  SELECT 'underdocks' AS act, runs_nodes.*, 
    (CASE WHEN runs_nodes.current_hp = 0 THEN 1 ELSE 0 END ) AS death
  FROM runs_id_acts
  JOIN runs_nodes on runs_nodes.run_id = runs_id_acts.id
  WHERE runs_nodes.floor BETWEEN 0 AND 16 
   AND runs_id_acts.underdocks = 1
),
hive_nodes AS (
  SELECT 'hive' AS act, runs_nodes.*, 
    (CASE WHEN runs_nodes.current_hp = 0 THEN 1 ELSE 0 END ) AS death
  FROM runs_id_acts
  JOIN runs_nodes on runs_nodes.run_id = runs_id_acts.id
  WHERE runs_nodes.floor BETWEEN 17 AND 32
   AND runs_id_acts.hive = 1
), 
glory_nodes AS (
  SELECT 'glory' AS act, runs_nodes.*, 
    (CASE WHEN runs_nodes.current_hp = 0 THEN 1 ELSE 0 END ) AS death
  FROM runs_id_acts
  JOIN runs_nodes on runs_nodes.run_id = runs_id_acts.id
  WHERE runs_nodes.floor BETWEEN 33 AND 48 
   AND runs_id_acts.glory = 1
),

-- Joint them all up to compute metrics per Act, but running down same column
all_nodes AS (
  SELECT * FROM overgrowth_nodes
  UNION ALL 
  SELECT * FROM underdocks_nodes
  UNION ALL 
  SELECT * FROM hive_nodes
  UNION ALL
  SELECT * FROM glory_nodes
)

-- Each row is an (alternate) Act, final row are  full runs.
-- Each column is a relevant metric. 
SELECT
  act, 
  1 - SUM(death) * 1.0 / COUNT (DISTINCT run_id)
  AS survive_rate,
  SUM (CASE WHEN node = "monster" THEN 1 ELSE 0 END)
  * 1.0 / COUNT (DISTINCT run_id)
  AS avg_hallways,
  SUM (CASE WHEN node = "elite" THEN 1 ELSE 0 END)
  * 1.0 / COUNT (DISTINCT run_id)
  AS avg_elites,
  SUM (CASE WHEN node = "rest_site" THEN 1 ELSE 0 END)
  * 1.0 / COUNT (DISTINCT run_id)
  AS avg_rest_site, 
  SUM (CASE WHEN node = "unknown" THEN 1 ELSE 0 END)
  * 1.0 / COUNT (DISTINCT run_id)
  AS avg_unknown
FROM all_nodes 
GROUP BY act
ORDER BY CASE act
  WHEN 'overgrowth' THEN 1
  WHEN 'underdocks' THEN 2
  WHEN 'hive'       THEN 3
  WHEN 'glory'      THEN 4
END;


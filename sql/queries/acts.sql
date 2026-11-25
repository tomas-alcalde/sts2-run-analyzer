-- Survival rate and average number of each node type, per act.
-- Floors are matched to acts through "tier" (the act's position in the run),
-- which ingest derives from each act's real length, so no floor range is
-- hardcoded here (see FLOOR-RANGE FIX in run.py).
-- Mind: Acts get generated with Seed, so known even if *not* reached!
-- "survived" is NULL for those, so they are left out.
-- Params (see queries.py): :collection, :charac, ASC_PLACEHOLDER -> :asc0, :asc1, ..., PATCH_PLACEHOLDER -> :patch0, :patch1, ...

WITH acts_reached AS (
  SELECT runs_acts.run_id, runs_acts.tier, runs_acts.act, runs_acts.survived
  FROM runs
  JOIN runs_acts ON runs.id = runs_acts.run_id
  WHERE runs.id IN (SELECT run_id FROM run_folders WHERE collection = :collection)
  AND (:charac IS NULL OR runs.charac = :charac)
  AND runs.ascension IN (ASC_PLACEHOLDER)
  AND runs.patch IN (PATCH_PLACEHOLDER)
  AND runs_acts.survived IS NOT NULL
),

-- One row per run and act, counting the nodes of each type in that act.
act_nodes AS (
  SELECT acts_reached.act, acts_reached.tier, acts_reached.survived,
    SUM(CASE WHEN runs_nodes.node = 'monster' THEN 1 ELSE 0 END) AS hallways,
    SUM(CASE WHEN runs_nodes.node = 'elite' THEN 1 ELSE 0 END) AS elites,
    SUM(CASE WHEN runs_nodes.node = 'rest_site' THEN 1 ELSE 0 END) AS rest_sites,
    SUM(CASE WHEN runs_nodes.node = 'unknown' THEN 1 ELSE 0 END) AS unknowns
  FROM acts_reached
  JOIN runs_nodes
    ON runs_nodes.run_id = acts_reached.run_id
    AND runs_nodes.tier = acts_reached.tier
  GROUP BY acts_reached.run_id, acts_reached.tier
)

-- Each row is an (alternate) Act, each column a relevant metric.
SELECT
  act,
  AVG(survived) AS survive_rate,
  AVG(hallways) AS avg_hallways,
  AVG(elites) AS avg_elites,
  AVG(rest_sites) AS avg_rest_site,
  AVG(unknowns) AS avg_unknown
FROM act_nodes
GROUP BY act
ORDER BY MIN(tier), act;

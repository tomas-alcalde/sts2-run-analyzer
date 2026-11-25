-- One row per run: whether it was won, and the last floor it reached. Gives the
-- win rate expected from how far a run got (src/analysis/card_picks.py).
-- Params (see queries.py): :collection, :charac, ASC_PLACEHOLDER -> :asc0, :asc1, ..., PATCH_PLACEHOLDER -> :patch0, :patch1, ...
SELECT
  runs.id AS run_id,
  runs.charac,
  runs.win,
  MAX(runs_nodes.floor) AS last_floor
FROM runs
JOIN runs_nodes ON runs.id = runs_nodes.run_id
WHERE runs.id IN (SELECT run_id FROM run_folders WHERE collection = :collection)
AND (:charac IS NULL OR runs.charac = :charac)
AND runs.ascension IN (ASC_PLACEHOLDER)
AND runs.patch IN (PATCH_PLACEHOLDER)
GROUP BY runs.id;

-- Times taken and wins of every ancient relic taken at least once.
-- Feeds src/analysis/ancient_relics.py.
-- Mind: "taken" is stored as text ('1' or '0'), hence the CAST. HAVING spells
-- out the SUM because there, "taken" would mean the column, not the alias.
-- Params (see queries.py): :collection, :charac, ASC_PLACEHOLDER -> :asc0, :asc1, ..., PATCH_PLACEHOLDER -> :patch0, :patch1, ...
SELECT
  runs_ancient_relics.choices AS relic,
  runs_ancient_relics.ancient,
  SUM(CAST(runs_ancient_relics.taken AS INTEGER)) AS taken,
  SUM(CAST(runs_ancient_relics.taken AS INTEGER) * runs.win) AS wins
FROM runs
JOIN runs_ancient_relics ON runs.id = runs_ancient_relics.run_id
WHERE runs.id IN (SELECT run_id FROM run_folders WHERE collection = :collection)
AND (:charac IS NULL OR runs.charac = :charac)
AND runs.ascension IN (ASC_PLACEHOLDER)
AND runs.patch IN (PATCH_PLACEHOLDER)
GROUP BY runs_ancient_relics.choices, runs_ancient_relics.ancient
HAVING SUM(CAST(runs_ancient_relics.taken AS INTEGER)) > 0;

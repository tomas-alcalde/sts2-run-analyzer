-- Params (see queries.py): :collection, :charac, ASC_PLACEHOLDER -> :asc0, :asc1, ..., PATCH_PLACEHOLDER -> :patch0, :patch1, ...
WITH joint AS (
  SELECT runs.win, runs_ancient_relics.ancient,
    runs_ancient_relics.choices, runs_ancient_relics.taken
  FROM runs
  JOIN runs_ancient_relics on runs.id = runs_ancient_relics.run_id
  WHERE runs.id IN (SELECT run_id FROM run_folders WHERE collection = :collection)
  AND (:charac IS NULL OR runs.charac = :charac)
  AND runs.ascension IN (ASC_PLACEHOLDER)
  AND runs.patch IN (PATCH_PLACEHOLDER)
)
SELECT choices, ancient, 
  AVG(CASE WHEN taken = 1 THEN win END) as win_rate,
  AVG(taken) AS pick_rate,
  SUM(taken) AS times_taken, 
  COUNT(choices) AS times_seen 
FROM joint
GROUP BY choices
ORDER BY ancient ASC, 
  win_rate DESC,
  pick_rate DESC, 
  times_seen DESC;



 

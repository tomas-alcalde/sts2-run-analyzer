-- Compute appearances and win rate of each boss, per act
-- Params (see queries.py): :collection, :charac, ASC_PLACEHOLDER -> :asc0, :asc1, ..., PATCH_PLACEHOLDER -> :patch0, :patch1, ...
WITH joint AS (
  SELECT runs_bosses.act, runs_bosses.boss, runs.win
  FROM runs
  JOIN runs_bosses ON runs.id = runs_bosses.run_id
  WHERE runs.id IN (SELECT run_id FROM run_folders WHERE collection = :collection)
  AND (:charac IS NULL OR runs.charac = :charac)
  AND runs.ascension IN (ASC_PLACEHOLDER)
  AND runs.patch IN (PATCH_PLACEHOLDER)
)
SELECT act, boss, AVG(win) AS win_rate, COUNT(boss) AS appearances
FROM joint
WHERE boss IS NOT NULL
GROUP BY act, boss
ORDER BY act, win_rate DESC, appearances DESC;

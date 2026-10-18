-- Compute appearances and win rate of each boss, per act
-- Params (see export.py): :collection, :charac
WITH joint AS (
  SELECT runs_bosses.act, runs_bosses.boss, runs.win
  FROM runs
  JOIN runs_bosses ON runs.id = runs_bosses.run_id
  WHERE runs.collection = :collection
  AND (:charac IS NULL OR runs.charac = :charac)
)
SELECT act, boss, AVG(win) AS win_rate, COUNT(boss) AS appearances
FROM joint
WHERE boss IS NOT NULL
GROUP BY act, boss
ORDER BY act, win_rate DESC, appearances DESC;

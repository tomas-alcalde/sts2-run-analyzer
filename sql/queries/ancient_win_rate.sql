-- Compute appearences and win rate of Ancients
-- Params (see export.py): :collection, :charac, ASC_PLACEHOLDER -> :asc0, :asc1, ...
WITH joint AS (
  SELECT runs_acts.ancient, runs.win
  FROM runs
  JOIN runs_acts on runs.id = runs_acts.run_id
  WHERE runs.collection = :collection
  AND (:charac IS NULL OR runs.charac = :charac)
  AND runs.ascension IN (ASC_PLACEHOLDER)
)
SELECT ancient, AVG(win) AS win_rate, COUNT(ancient) AS appearences
FROM joint
WHERE ancient IS NOT NULL
GROUP BY ancient 
ORDER BY win_rate DESC, appearences DESC;


-- Overall number of runs and win rate
-- Params (see export.py): :collection, :charac, ASC_PLACEHOLDER -> :asc0, :asc1, ...
SELECT COUNT(*) AS runs, AVG(win) AS win_rate
FROM runs
WHERE collection = :collection
AND (:charac IS NULL OR charac = :charac)
AND ascension IN (ASC_PLACEHOLDER);

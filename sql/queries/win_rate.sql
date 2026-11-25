-- Overall number of runs and win rate
-- Params (see queries.py): :collection, :charac, ASC_PLACEHOLDER -> :asc0, :asc1, ..., PATCH_PLACEHOLDER -> :patch0, :patch1, ...
SELECT COUNT(*) AS runs, AVG(win) AS win_rate
FROM runs
WHERE id IN (SELECT run_id FROM run_folders WHERE collection = :collection)
AND (:charac IS NULL OR charac = :charac)
AND ascension IN (ASC_PLACEHOLDER)
AND patch IN (PATCH_PLACEHOLDER);

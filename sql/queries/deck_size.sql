-- Params (see queries.py): :collection, :charac, ASC_PLACEHOLDER -> :asc0, :asc1, ..., PATCH_PLACEHOLDER -> :patch0, :patch1, ...
SELECT AVG(deck_size) AS deck_size
FROM runs
WHERE id IN (SELECT run_id FROM run_folders WHERE collection = :collection)
AND (:charac IS NULL OR charac = :charac)
AND ascension IN (ASC_PLACEHOLDER)
AND patch IN (PATCH_PLACEHOLDER);

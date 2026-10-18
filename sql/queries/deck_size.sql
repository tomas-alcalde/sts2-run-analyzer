-- Params (see export.py): :collection, :charac
SELECT AVG(deck_size) AS deck_size
FROM runs
WHERE collection = :collection
AND (:charac IS NULL OR charac = :charac);

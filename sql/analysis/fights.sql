-- One row per fight. Feeds hp_per_fight_type.py and hp_per_turn.py in src/analysis/.
-- "fight" is the fight type: hallway fights (including "?" rooms that turned
-- into a fight, which are all *_WEAK or *_NORMAL encounters) are "normal".
-- Params (see queries.py): :collection, :charac, ASC_PLACEHOLDER -> :asc0, :asc1, ..., PATCH_PLACEHOLDER -> :patch0, :patch1, ...
SELECT
  runs_nodes.run_id,
  runs.charac,
  runs.ascension,
  runs_nodes.tier,
  runs_acts.act,
  runs_nodes.floor,
  CASE runs_nodes.node
    WHEN 'boss' THEN 'boss'
    WHEN 'elite' THEN 'elite'
    ELSE 'normal'
  END AS fight,
  runs_nodes.seen AS encounter,
  runs_nodes.turns_taken AS turns,
  runs_nodes.damage_taken AS damage
FROM runs
JOIN runs_nodes ON runs.id = runs_nodes.run_id
JOIN runs_acts
  ON runs_acts.run_id = runs_nodes.run_id
  AND runs_acts.tier = runs_nodes.tier
WHERE runs.id IN (SELECT run_id FROM run_folders WHERE collection = :collection)
AND (:charac IS NULL OR runs.charac = :charac)
AND runs.ascension IN (ASC_PLACEHOLDER)
AND runs.patch IN (PATCH_PLACEHOLDER)
AND runs_nodes.seen LIKE 'ENCOUNTER.%';

-- One row per card offered in a three-card reward after a fight, and whether it
-- was taken: the input of card_picks.py in src/analysis/.
-- Rewards with another number of cards (relic effects, two rewards on one
-- floor) and cards offered by events, ancients or shops are left out.
-- Mind: "taken" is stored as text ('1' or '0'), hence the CAST.
-- Params (see queries.py): :collection, :charac, ASC_PLACEHOLDER -> :asc0, :asc1, ..., PATCH_PLACEHOLDER -> :patch0, :patch1, ...
WITH rewards AS (
  SELECT runs_card_choices.run_id, runs_card_choices.floor
  FROM runs
  JOIN runs_card_choices ON runs.id = runs_card_choices.run_id
  JOIN runs_nodes
    ON runs_nodes.run_id = runs_card_choices.run_id
    AND runs_nodes.floor = runs_card_choices.floor
  WHERE runs.id IN (SELECT run_id FROM run_folders WHERE collection = :collection)
  AND (:charac IS NULL OR runs.charac = :charac)
  AND runs.ascension IN (ASC_PLACEHOLDER)
  AND runs.patch IN (PATCH_PLACEHOLDER)
  AND runs_nodes.seen LIKE 'ENCOUNTER.%'
  GROUP BY runs_card_choices.run_id, runs_card_choices.floor
  HAVING COUNT(*) = 3
)
SELECT
  runs.charac,
  runs.start_time,
  runs.win,
  rewards.run_id,
  rewards.floor,
  runs_card_choices.choices AS card,
  CAST(runs_card_choices.taken AS INTEGER) AS taken
FROM rewards
JOIN runs_card_choices
  ON runs_card_choices.run_id = rewards.run_id
  AND runs_card_choices.floor = rewards.floor
JOIN runs ON runs.id = rewards.run_id;

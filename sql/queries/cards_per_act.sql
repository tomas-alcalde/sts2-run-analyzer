-- Params (see export.py): :collection, :charac
SELECT
  runs_acts.act,
  choices,
  COUNT(choices) AS times_seen,
  AVG(taken) AS times_taken,
  AVG(CASE WHEN taken = 1 THEN runs_acts.survived END) AS act_win_rate,
  AVG(CASE WHEN taken = 1 THEN runs.win END) AS win_rate
FROM runs_card_choices
JOIN runs ON runs.id = runs_card_choices.run_id
JOIN runs_acts
  ON runs_acts.run_id = runs_card_choices.run_id
  AND runs_acts.tier = runs_card_choices.tier
WHERE runs.collection = :collection
AND (:charac IS NULL OR runs.charac = :charac)
GROUP BY runs_acts.act, choices;

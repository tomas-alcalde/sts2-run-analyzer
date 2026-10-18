-- Create a table called "runs" where each *row* is a run. 
-- The primary key (unique identifier) is the filename. 
-- A table is only created if it does not exist already. 
-- With INSERT or IGNORE, can add rows/runs (even if injecting from directory 
  -- that overlaps with what exists already, just keeps rows with the same id). 
-- For adding more *columns*/metrics, will need to use ALTER TABLE later, or 
-- delete the .db file and redefine the table from there!

CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY ON CONFLICT IGNORE,  -- self.id, unique identifier.
  collection TEXT,
  charac TEXT NOT NULL, -- ensures it cannot be assigned *empty* value 
  ascension INTEGER, 
  win INTEGER, 
  killed_encounter TEXT, 
  killed_event TEXT, 
  deck_size INTEGER,
  relic_count INTEGER, 
  max_pot INTEGER, 
  time INTEGER, 
  patch TEXT, 
  seed TEXT, 
  start_time INTEGER 
);

-- Create table with the deck of each run. Each row 
-- corresponds to a card, where first column is always the run id 
-- (so after one deck completed it changes), the second column is the card
-- name, and so on.
CREATE TABLE IF NOT EXISTS runs_decks (
  run_id TEXT NOT NULL,
  card TEXT NOT NULL, 
  floor_added INTEGER, 
  FOREIGN KEY (run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS runs_relics (
  run_id TEXT NOT NULL,
  relic TEXT NOT NULL, 
  floor_added INTEGER, 
  FOREIGN KEY (run_id) REFERENCES runs(id)
);

-- Three rows per run (some None). "tier" is the act's position in the run
-- (1, 2, 3), independent of which named act ("act") occupied that slot.
CREATE TABLE IF NOT EXISTS runs_acts(
  run_id TEXT NOT NULL,
  tier INTEGER,
  act TEXT,
  ancient TEXT,
  survived INTEGER,
  FOREIGN KEY (run_id) REFERENCES runs(id)
);

-- One row per boss fought. Normally three rows per run (one per act), but
-- Ascension 10 adds a second boss to the last act, so "act" can repeat.
CREATE TABLE IF NOT EXISTS runs_bosses(
  run_id TEXT NOT NULL,
  act TEXT,
  boss TEXT,
  FOREIGN KEY (run_id) REFERENCES runs(id)
);

-- Nine rows per run (some None), "ancient" just repeats in threes (to reference later)
CREATE TABLE IF NOT EXISTS runs_ancient_relics(
  run_id TEXT NOT NULL,
  choices TEXT,
  ancient TEXT, 
  taken TEXT, 
  FOREIGN KEY (run_id) REFERENCES runs(id)
);

-- Each row is a floor of a run, runs are concataneted. Columns are 
-- the run id, the node clicked on, and what was in that node.
CREATE TABLE IF NOT EXISTS runs_nodes(
  run_id TEXT NOT NULL,
  floor INTEGER, 
  node TEXT,
  seen TEXT,
  turns_taken INTEGER, 
  current_gold INTEGER, 
  current_hp INTEGER, 
  damage_taken INTEGER, 
  gold_gained INTEGER, 
  gold_lost INTEGER, 
  gold_spent INTEGER, 
  gold_stolen INTEGER, 
  hp_healed INTEGER, 
  max_hp INTEGER, 
  max_hp_gained INTEGER, 
  max_hp_lost INTEGER, 
  FOREIGN KEY (run_id) REFERENCES runs(id)
);

-- "tier" (act position: 1, 2, 3) is derived per-run from each act's actual
-- floor count (see run.py's FLOOR-RANGE FIX), not a hardcoded floor cutoff,
-- so it stays correct when an act's real length varies (e.g. Golden Compass).
CREATE TABLE IF NOT EXISTS runs_card_choices(
  run_id TEXT NOT NULL,
  floor INTEGER,
  tier INTEGER,
  choices TEXT,
  taken TEXT,
  FOREIGN KEY (run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS run_potions_choices(
  run_id TEXT NOT NULL,
  floor INTEGER,
  choices TEXT, 
  taken TEXT, 
  FOREIGN KEY (run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS run_potions_used(
  run_id TEXT NOT NULL, 
  floor INTEGER, 
  potion_used TEXT, 
  FOREIGN KEY (run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS run_rest_choices(
  run_id TEXT NOT NULL, 
  floor INTEGER, 
  rest_site_done TEXT, 
  FOREIGN KEY (run_id) REFERENCES runs(id)
);





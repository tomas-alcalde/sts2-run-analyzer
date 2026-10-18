from pathlib import Path
import sqlite3
from run import Run


def id_list(id, df):
    id_rep = [id] * df.shape[0]
    df.insert(0, "run_id", id_rep)  # "run_id" must match the schema.sql
    return df


def ingest_file(filepath, schema_path="sql/schema.sql", db_path="data/runs.db"):
    con = sqlite3.connect(db_path)
    con.executescript(Path(schema_path).read_text())

    run = Run(filepath)

    # Skip if already ingested into runs.db_path
    exists = con.execute("SELECT 1 FROM runs WHERE id = ?", (run.id,)).fetchone()
    if exists:
        con.close()
        return

    # Skip if multilpayer run
    if run.player_num != 1:
        con.close()
        return

    summary = run.run_summary_df.copy()
    nodes = id_list(run.id, run.run_nodes_df.copy())
    deck = id_list(run.id, run.run_deck_df.copy())
    relics = id_list(run.id, run.run_relics_df.copy())
    acts = id_list(run.id, run.run_acts_df.copy())
    bosses = id_list(run.id, run.run_bosses_df.copy())
    ancients_relics = id_list(run.id, run.run_ancients_relics_df.copy())
    card_choices = id_list(run.id, run.run_card_choices_df.copy())
    potions_choices = id_list(run.id, run.run_potions_choices_df.copy())
    potions_used = id_list(run.id, run.run_potions_used_df.copy())
    rest_choices = id_list(run.id, run.run_rest_choices_df.copy())

    summary.to_sql("runs", con, if_exists="append", index=False)
    nodes.to_sql("runs_nodes", con, if_exists="append", index=False)
    deck.to_sql("runs_decks", con, if_exists="append", index=False)
    relics.to_sql("runs_relics", con, if_exists="append", index=False)
    acts.to_sql("runs_acts", con, if_exists="append", index=False)
    bosses.to_sql("runs_bosses", con, if_exists="append", index=False)
    ancients_relics.to_sql("runs_ancient_relics", con, if_exists="append", index=False)
    card_choices.to_sql("runs_card_choices", con, if_exists="append", index=False)
    potions_choices.to_sql("run_potions_choices", con, if_exists="append", index=False)
    potions_used.to_sql("run_potions_used", con, if_exists="append", index=False)
    rest_choices.to_sql("run_rest_choices", con, if_exists="append", index=False)

    con.close()


def ingest_directory(path, schema_path="sql/schema.sql", db_path="data/runs.db"):
    directory = Path(path)
    for filepath in sorted(directory.iterdir()):
        ingest_file(filepath, schema_path, db_path)


if __name__ == "__main__":
    import sys

    path = sys.argv[1]
    ingest_directory(path)

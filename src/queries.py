from pathlib import Path
import re
import sqlite3
import pandas as pd


def run_queries(path, charac, ascensions=range(11), db_path="data/runs.db", folder="sql/queries", names=None, patches=None):
    """Run the .sql files in `folder` (all, or only `names`) with the given filters, keyed by file name.

    `patches` lists the game versions to keep; None keeps every version in the folder.
    """
    ascensions = list(ascensions)
    patches = patches_in(db_path, path) if patches is None else list(patches)

    con = sqlite3.connect(db_path)

    asc_placeholders = ", ".join(f":asc{i}" for i in range(len(ascensions)))
    patch_placeholders = ", ".join(f":patch{i}" for i in range(len(patches)))
    params = {"collection": path, "charac": charac}
    params.update({f"asc{i}": asc for i, asc in enumerate(ascensions)})
    params.update({f"patch{i}": patch for i, patch in enumerate(patches)})

    results = {}
    for query_file in sorted(Path(folder).glob("*.sql")):
        if names is not None and query_file.stem not in names:
            continue
        query = query_file.read_text()
        query = query.replace("ASC_PLACEHOLDER", asc_placeholders).replace("PATCH_PLACEHOLDER", patch_placeholders)
        results[query_file.stem] = pd.read_sql(query, con, params=params)

    con.close()
    return results


def distinct_values(db_path, column):
    con = sqlite3.connect(db_path)
    rows = con.execute(f"SELECT DISTINCT {column} FROM runs ORDER BY {column}").fetchall()
    con.close()
    return [row[0] for row in rows]


def folders(db_path):
    con = sqlite3.connect(db_path)
    rows = con.execute("SELECT collection FROM folder_counts ORDER BY collection").fetchall()
    con.close()
    return [row[0] for row in rows]


def patches_in(db_path, collection):
    """Game versions of a folder's runs, oldest first.

    Sorted by number, because as text "v0.99.1" would come after "v0.110.1".
    """
    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT DISTINCT patch FROM runs JOIN run_folders ON runs.id = run_folders.run_id WHERE collection = ?",
        (collection,),
    ).fetchall()
    con.close()
    return sorted((row[0] for row in rows), key=lambda patch: [int(n) for n in re.findall(r"\d+", patch)])


def outdated_tables(db_path="data/runs.db", schema_path="sql/schema.sql"):
    """Tables whose columns in db_path differ from schema_path.

    CREATE TABLE IF NOT EXISTS never changes a table that already exists, so
    after a schema change runs.db has to be deleted and ingested again.
    """
    expected = sqlite3.connect(":memory:")
    expected.executescript(Path(schema_path).read_text())
    current = sqlite3.connect(db_path)

    def columns(con, table):
        return [row[1] for row in con.execute(f"PRAGMA table_info({table})")]

    tables = [row[0] for row in expected.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
    outdated = [table for table in tables if columns(current, table) != columns(expected, table)]

    expected.close()
    current.close()
    return outdated

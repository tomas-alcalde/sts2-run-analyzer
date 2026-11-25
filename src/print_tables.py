"""Prints every summary table of sql/queries/ for one character (just for debugging, for now)."""
from queries import run_queries


def print_tables(path, charac, ascensions=range(11), db_path="data/runs.db"):
    charac = "CHARACTER." + charac.upper()
    print(charac)

    for name, df in run_queries(path, charac, ascensions, db_path).items():
        print(name)
        print(df)

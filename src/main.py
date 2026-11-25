from pathlib import Path
from ingest import ingest_directory
from print_tables import print_tables
from queries import outdated_tables
import subprocess
import sys


# TODOs are in TODO.md

# Folders of .run files to ingest, e.g. add "data/my_runs". A run in several of them counts in each
paths = ["data/sample"]
db_path = "data/runs.db"

characs = ["ironclad", "silent", "regent", "necrobinder", "defect", "fool"]
asc = range(11)

if Path(db_path).exists() and outdated_tables(db_path):
    sys.exit(f"{db_path} was built with an older sql/schema.sql. Delete it and run this script again.")

for path in paths:
    if not ingest_directory(path, schema_path="sql/schema.sql", db_path=db_path):   # Default asc is "10"
        continue
    for charac in characs:
        print_tables(path, charac, asc, db_path)

subprocess.run([sys.executable, "-m", "streamlit", "run", "src/app.py"])

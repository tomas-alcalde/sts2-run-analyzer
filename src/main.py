from ingest import ingest_directory
from export import export_directory
import subprocess
import sys

# TODO: Deck size is removed from the dashboard for now. sql/queries/deck_size.sql
# ignores the ascension filter, so add ASC_PLACEHOLDER to it before showing it again.

path = "data/old_saves"

characs = ["ironclad", "silent", "regent", "necrobinder", "defect"]
asc = range(11)

ingest_directory(path, schema_path="sql/schema.sql", db_path="data/runs.db")   # Default asc is "10"
for charac in characs:
    export_directory(path, charac, asc)

subprocess.run([sys.executable, "-m", "streamlit", "run", "src/export.py"])

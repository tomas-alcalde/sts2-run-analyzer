"""Streamlit dashboard. Start it with: streamlit run src/app.py"""
from functools import partial
from pathlib import Path

import pandas as pd
import streamlit as st

from dashboard import acts, ancient_relics, cards, fights, history, overview, relics, runs
from dashboard.common import Filters, pretty
from queries import distinct_values, folders, outdated_tables, patches_in

# (render function, title, URL path). The first one is the home page.
PAGES = [
    (overview.render, overview.TITLE, "overview"),
    (history.render, history.TITLE, "history"),
    (runs.render, runs.TITLE, "runs"),
    (acts.render, acts.TITLE, "acts"),
    (ancient_relics.render, ancient_relics.TITLE, "ancient-relics"),
    (cards.render, cards.TITLE, "cards"),
    (relics.render, relics.TITLE, "relics"),
    (fights.render, fights.TITLE, "fights"),
]

DEFAULT_ASCENSION = 10

# Streamlit has no setting for the size of tab titles: this sits between st.subheader and st.header
TAB_TITLES = """<style>
[data-testid="stTabs"] [role="tablist"] { gap: 2.5rem; }
[data-testid="stTabs"] [data-testid="stTab"] { height: auto; }
[data-testid="stTabs"] [data-testid="stTab"] p { font-size: 2rem; font-weight: 600; }
</style>"""


def sidebar_filters(db_path):
    with st.sidebar:
        collection = st.selectbox("Runs", folders(db_path))
        charac = st.selectbox("Character", ["All"] + distinct_values(db_path, "charac"), format_func=pretty)
        if charac == "All":
            charac = None
        all_asc = distinct_values(db_path, "ascension")
        default_asc = [DEFAULT_ASCENSION] if DEFAULT_ASCENSION in all_asc else all_asc
        ascensions = st.multiselect("Ascension", all_asc, default=default_asc)
        # Oldest first, so the default keeps every run of the folder
        patches = patches_in(db_path, collection)
        patch = st.selectbox("Patch", patches)
        patch_mode = st.radio("Patch range", ["Onwards", "Exact"], horizontal=True)
        start = patches.index(patch) if patches else 0
        selected = patches[start:start + 1] if patch_mode == "Exact" else patches[start:]

        filters = Filters(collection, charac, tuple(ascensions), tuple(selected), db_path)
        # Multiplayer runs never reach the database (see ingest.py), so this count excludes them
        summary = filters.run_queries(names=["win_rate"])["win_rate"]
        run_count, win_rate = summary["runs"].iloc[0], summary["win_rate"].iloc[0]
        st.markdown(f"**Runs analysed:** {run_count}")
        st.markdown(f"**Win rate:** {'-' if pd.isna(win_rate) else f'{win_rate:.1%}'}")
    return filters


def dashboard(db_path="data/runs.db"):
    st.set_page_config(page_title="STS2 run stats", layout="wide")

    if not Path(db_path).exists():
        st.error(f"No database found at {db_path}. Run src/main.py first to build it.")
        st.stop()

    outdated = outdated_tables(db_path)
    if outdated:
        st.error(
            f"{db_path} was built with an older sql/schema.sql (changed tables: {', '.join(outdated)}). "
            "Delete it and run src/main.py again."
        )
        st.stop()

    st.html(TAB_TITLES)

    # The filters live here, outside the pages, so they stay put when switching pages
    filters = sidebar_filters(db_path)
    pages = [st.Page(partial(render, filters), title=title, url_path=url_path) for render, title, url_path in PAGES]
    st.navigation(pages).run()


if __name__ == "__main__":
    dashboard()

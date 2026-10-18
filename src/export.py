from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st


VIEWS = {
    "Win rate by boss": ("boss_win_rate", "boss", "win_rate", "act"),
    "Survival rate by act": ("acts", "act", "survive_rate", None),
    "Win rate by ancient": ("ancient_win_rate", "ancient", "win_rate", None),
    "Win rate by ancient relic": ("ancient_relic_win_rate", "choices", "win_rate", "ancient"),
    "Card win rate by act": ("cards_per_act", "choices", "win_rate", "act"),
}


def run_queries(path, charac, ascensions=range(11), db_path="data/runs.db"):
    con = sqlite3.connect(db_path)

    ascensions = list(ascensions)
    asc_placeholders = ", ".join(f":asc{i}" for i in range(len(ascensions)))
    params = {"collection": path, "charac": charac}
    params.update({f"asc{i}": asc for i, asc in enumerate(ascensions)})

    results = {}
    for query_file in sorted(Path("sql/queries").glob("*.sql")):
        query = query_file.read_text().replace("ASC_PLACEHOLDER", asc_placeholders)
        results[query_file.stem] = pd.read_sql(query, con, params=params)

    con.close()
    return results


def export_directory(path, charac, ascensions=range(11), db_path="data/runs.db"):
    charac = "CHARACTER." + charac.upper()
    print(charac)

    for name, df in run_queries(path, charac, ascensions, db_path).items():
        print(name)
        print(df)


def pretty(value):
    if not isinstance(value, str):
        return value
    return value.split(".")[-1].replace("_", " ").title()


def clean(df):
    df = df.copy()
    for col in df.select_dtypes("object"):
        df[col] = df[col].map(pretty)
    return df


def distinct_values(db_path, column):
    con = sqlite3.connect(db_path)
    rows = con.execute(f"SELECT DISTINCT {column} FROM runs ORDER BY {column}").fetchall()
    con.close()
    return [row[0] for row in rows]


def dashboard(db_path="data/runs.db"):
    st.set_page_config(page_title="STS2 run stats", layout="wide")
    st.title("Slay the Spire 2 run stats")

    if not Path(db_path).exists():
        st.error(f"No database found at {db_path}. Run src/main.py first to build it.")
        st.stop()

    with st.sidebar:
        collection = st.selectbox("Runs", distinct_values(db_path, "collection"))
        charac = st.selectbox("Character", ["All"] + distinct_values(db_path, "charac"), format_func=pretty)
        if charac == "All":
            charac = None
        all_asc = distinct_values(db_path, "ascension")
        ascensions = st.multiselect("Ascension", all_asc, default=all_asc)

    results = {
        name: clean(df)
        for name, df in run_queries(collection, charac, ascensions, db_path).items()
    }

    runs, win_rate = results["win_rate"].iloc[0]
    col_runs, col_win = st.columns(2)
    col_runs.metric("Runs", int(runs))
    col_win.metric("Win rate", "-" if pd.isna(win_rate) else f"{win_rate:.1%}")

    view = st.selectbox("Statistic", list(VIEWS))
    query, x, y, filter_col = VIEWS[view]
    df = results[query]

    if df.empty:
        st.info("No runs match these filters.")
        return

    color = None
    if filter_col:
        choice = st.selectbox(filter_col.title(), ["All"] + sorted(df[filter_col].dropna().unique()))
        if choice == "All":
            color = filter_col
        else:
            df = df[df[filter_col] == choice]

    st.bar_chart(df, x=x, y=y, color=color)
    st.dataframe(df, hide_index=True, width="stretch")


if __name__ == "__main__":
    dashboard()

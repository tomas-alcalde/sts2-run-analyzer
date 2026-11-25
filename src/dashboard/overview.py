import pandas as pd
import streamlit as st

from dashboard.common import clean, method

TITLE = "Overview"
VIEWS = {
    "Win rate by boss": ("boss_win_rate", "boss", "win_rate", "act"),
    "Survival rate by act": ("acts", "act", "survive_rate", None),
    "Win rate by ancient": ("ancient_win_rate", "ancient", "win_rate", None),
    "Win rate by ancient relic": ("ancient_relic_win_rate", "choices", "win_rate", "ancient"),
    "Card win rate by act": ("cards_per_act", "choices", "win_rate", "act"),
}


def render(filters):
    st.title("Slay the Spire 2 run stats")

    results = {name: clean(df) for name, df in filters.run_queries().items()}

    runs, win_rate = results["win_rate"].iloc[0]
    deck_size = results["deck_size"].iloc[0, 0]
    col_runs, col_win, col_deck = st.columns(3)
    col_runs.metric("Runs", int(runs))
    col_win.metric("Win rate", "-" if pd.isna(win_rate) else f"{win_rate:.1%}")
    col_deck.metric("Average final deck size", "-" if pd.isna(deck_size) else f"{deck_size:.1f}")

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
    method(TITLE)

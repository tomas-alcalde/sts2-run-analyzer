from dataclasses import dataclass
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from analysis import FIGHT_TYPES
from queries import run_queries

FIGHT_LABELS = {fight: fight.title() for fight in FIGHT_TYPES}

# How every metric and test works, one "## " section per page or tab
METHODS = Path("docs/methods.md")

# Chart colors per theme: the first three categorical slots of the reference
# dataviz palette (the most that stay colorblind-safe in a scatter). Fight
# types use them in this order on every page. Streamlit can report the wrong
# theme on a session's first load, so either set must read on both backgrounds,
# and labels and reference lines use a gray that is the same in both.
LIGHT = {
    "categorical": ["#2a78d6", "#eb6834", "#1baf7a"],
    "accent": "#2a78d6",
    "neutral": "#898781",
}
DARK = {
    "categorical": ["#3987e5", "#d95926", "#199e70"],
    "accent": "#3987e5",
    "neutral": "#898781",
}


@dataclass(frozen=True)
class Filters:
    """The sidebar selection, shared by every page."""

    collection: str
    charac: str | None
    ascensions: tuple
    patches: tuple
    db_path: str

    def run_queries(self, folder="sql/queries", names=None):
        return run_queries(self.collection, self.charac, self.ascensions, self.db_path, folder, names, self.patches)


def pretty(value):
    if not isinstance(value, str):
        return value
    return value.split(".")[-1].replace("_", " ").title()


def clean(df):
    df = df.copy()
    for col in df.select_dtypes(["object", "string"]):
        df[col] = df[col].map(pretty)
    return df


def format_p(p):
    if pd.isna(p):
        return "-"
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def palette():
    """Chart colors for the current Streamlit theme (light until it is known)."""
    return DARK if st.context.theme.type == "dark" else LIGHT


def fight_scale(colors):
    return alt.Scale(domain=list(FIGHT_LABELS.values()), range=colors["categorical"])


def method(section):
    """Show the section of docs/methods.md with this heading in a collapsed expander."""
    text = METHODS.read_text() if METHODS.exists() else ""
    for block in text.split("\n## ")[1:]:
        heading, _, body = block.partition("\n")
        if heading.strip() == section:
            with st.expander("Method"):
                st.markdown(body)
            return

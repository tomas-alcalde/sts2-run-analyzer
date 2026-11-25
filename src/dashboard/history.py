import streamlit as st

TITLE = "History"


def render(filters):
    st.title(TITLE)
    st.write(
        "Planned: every past run, newest first, with its details, its path through Acts, Bosses and Ancients, "
        "and what killed it. Plus an in-depth view of any single run, with its deck and full metrics."
    )

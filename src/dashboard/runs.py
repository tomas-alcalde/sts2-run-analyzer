import streamlit as st

TITLE = "Runs"


def render(filters):
    st.title(TITLE)
    st.write("Planned: the same metrics as the Acts page, for whole runs, plus total time.")

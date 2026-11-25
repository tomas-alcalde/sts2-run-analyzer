import streamlit as st

TITLE = "Acts"


def render(filters):
    st.title(TITLE)
    st.write(
        "Planned: win rate per Act, with Elites, Hallways, Unknowns, Rest Sites (Smiths and Rests), "
        "cards added and removed, deck size and its rarity and type mix, relics, and deaths by fight type."
    )

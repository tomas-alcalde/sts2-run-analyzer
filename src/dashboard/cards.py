import altair as alt
import pandas as pd
import streamlit as st

from analysis import MIN_RUNS
from analysis.card_picks import MIN_CARDS, SKIP, card_elo, elo_vs_win_rate, win_probability
from dashboard.common import format_p, method, palette, pretty

TITLE = "Cards"
CARD_RATINGS = "Card Ratings"
WR_VS_ELO = "WR vs. ELO"
VERDICTS = ["Overpicked", "Underpicked", "In line"]


@st.cache_data(show_spinner=False)
def rate(rewards, runs):
    ratings, history = card_elo(rewards)
    tested, summary = elo_vs_win_rate(rewards, runs, ratings)
    return ratings, history, tested, summary


def verdict_color(colors):
    return alt.Color(
        "side:N",
        scale=alt.Scale(domain=VERDICTS, range=[colors["categorical"][1], colors["categorical"][0], colors["neutral"]]),
        legend=alt.Legend(title=None, orient="top"),
    )


def strength(verdict, p_value):
    """Opacity of a card's dot: solid when confirmed, slightly faded when
    "possibly", and fading with the p-value when only "leaning"."""
    if verdict in VERDICTS[:2]:
        return 1.0
    if verdict.startswith("Possibly"):
        return 0.8
    if verdict.startswith("Leaning"):
        # 0.5 just above p = 0.05, down to 0.15 at p = 1
        return 0.15 if pd.isna(p_value) else 0.5 - 0.35 * (p_value - 0.05) / 0.95
    return 0.85


def with_sides(tested):
    """The direction of each card's results (the colour), and how strong the evidence is (the opacity)."""
    return tested.assign(
        name=tested["card"].map(pretty),
        side=tested["verdict"].str.removeprefix("Possibly ").str.removeprefix("Leaning ").str.capitalize(),
        strength=[strength(verdict, p) for verdict, p in zip(tested["verdict"], tested["p_value"])],
    )


def skip_layers(skip_rating, x, colors):
    skip = pd.DataFrame({"rating": [skip_rating]})
    return [
        alt.Chart(skip).mark_rule(color=colors["neutral"]).encode(x=x),
        alt.Chart(skip).mark_text(align="left", dx=4, color=colors["neutral"]).encode(x=x, y=alt.value(8), text=alt.value("Skip")),
    ]


def highlight_layers(tested, card, x, y, colors):
    selected = tested[tested["card"] == card]
    if selected.empty:
        return []
    return [
        alt.Chart(selected).mark_point(size=500, strokeWidth=2, color=colors["neutral"]).encode(x=x, y=y),
        alt.Chart(selected).mark_text(align="left", dx=16, color=colors["neutral"]).encode(x=x, y=y, text="name:N"),
    ]


def zero_layers(field, y, colors):
    """The horizontal line at 0 on the `field` axis, and the corners where the flagged cards sit."""
    zero = alt.Chart(pd.DataFrame({field: [0.0]})).mark_rule(color=colors["neutral"]).encode(y=y)
    corner = alt.Chart(pd.DataFrame({"label": ["Underpicked zone", "Overpicked zone"]}))
    return [
        zero,
        corner.transform_filter("datum.label == 'Underpicked zone'")
        .mark_text(align="left", baseline="top", dx=6, dy=6, color=colors["neutral"])
        .encode(x=alt.value(0), y=alt.value(0), text="label:N"),
        corner.transform_filter("datum.label == 'Overpicked zone'")
        .mark_text(align="right", baseline="bottom", dx=-6, dy=-6, color=colors["neutral"])
        .encode(x=alt.value("width"), y=alt.value("height"), text="label:N"),
    ]


def result_tiles(tested, summary, tested_help):
    flagged = tested["verdict"].isin(VERDICTS[:2]).sum()
    possible = tested["verdict"].str.startswith("Possibly").sum()
    tiles = [
        ("Spearman ρ", f"{summary['rho']:+.2f}", "Rank correlation between rating and the vertical axis"),
        ("One-sided p", format_p(summary["p_value"]), "Chance of a correlation at least this positive if the two were unrelated"),
        ("Cards tested", len(tested), tested_help),
        ("Flagged", flagged, "Over- or underpicked with p < 0.05 after the Holm adjustment for testing many cards"),
        (
            "Possibly",
            possible,
            f"p < 0.05 only before the adjustment: with {len(tested)} cards tested, "
            f"chance alone gives about {0.05 * len(tested):.1f} of these",
        ),
    ]
    for column, (label, value, help) in zip(st.columns(len(tiles)), tiles):
        column.metric(label, value, help=help)


def history_chart(history, card, colors):
    # The floor, added as seconds, keeps the rewards of one run in order
    history = history.assign(date=pd.to_datetime(history["start_time"] + history["floor"], unit="s"))
    names = [pretty(card)] if card == SKIP else [pretty(card), pretty(SKIP)]
    x = alt.X("date:T", title="Run date")
    y = alt.Y("rating:Q", title="Rating", scale=alt.Scale(zero=False))
    color = alt.Color(
        "name:N",
        scale=alt.Scale(domain=names, range=[colors["accent"], colors["neutral"]][: len(names)]),
        legend=alt.Legend(title=None, orient="top"),
    )
    shown = history[history["card"] == card].assign(
        name=pretty(card), picked=lambda d: d["picked"].map({True: "Yes", False: "No"})
    )
    tooltip = [
        alt.Tooltip("date:T", title="Run date", format="%d %b %Y"),
        alt.Tooltip("floor:Q", title="Floor"),
        alt.Tooltip("rating:Q", title="Rating", format=".0f"),
        alt.Tooltip("picked:N", title="Picked"),
    ]

    # Steps: a rating only changes at a reward, and holds until the next one
    layers = []
    if card != SKIP:
        skip = history[history["card"] == SKIP].assign(name=pretty(SKIP))
        layers.append(alt.Chart(skip).mark_line(strokeWidth=2, interpolate="step-after").encode(x=x, y=y, color=color))
    layers.append(alt.Chart(shown).mark_line(strokeWidth=2, interpolate="step-after").encode(x=x, y=y, color=color))
    if card != SKIP:
        layers.append(alt.Chart(shown).mark_circle(size=50, opacity=1).encode(x=x, y=y, color=color))

    # Hovering anywhere shows the nearest reward
    nearest = alt.selection_point(nearest=True, on="pointerover", fields=["date"], empty=False)
    layers.append(alt.Chart(shown).mark_point(opacity=0).encode(x=x, y=y, tooltip=tooltip).add_params(nearest))
    layers.append(
        alt.Chart(shown)
        .mark_circle(size=90, color=colors["accent"])
        .encode(x=x, y=y, opacity=alt.condition(nearest, alt.value(1), alt.value(0)))
    )
    return alt.layer(*layers).properties(height=320)


def win_rate_chart(tested, skip_rating, card, colors):
    tested = with_sides(tested)
    x = alt.X("rating:Q", title="ELO rating", scale=alt.Scale(zero=False), axis=alt.Axis(tickCount=10))
    y = alt.Y("above_expected:Q", title="Win rate above expected", axis=alt.Axis(format="+%"))
    tooltip = [
        alt.Tooltip("name:N", title="Card"),
        alt.Tooltip("rating:Q", title="Rating", format=".0f"),
        alt.Tooltip("runs:Q", title="Runs that picked it"),
        alt.Tooltip("win_rate:Q", title="Win rate", format=".0%"),
        alt.Tooltip("expected:Q", title="Expected from floors", format=".0%"),
        alt.Tooltip("p_value:Q", title="p-value", format=".3f"),
        alt.Tooltip("verdict:N", title="Verdict"),
    ]
    points = alt.Chart(tested).mark_circle().encode(
        x=x,
        y=y,
        color=verdict_color(colors),
        opacity=alt.Opacity("strength:Q", scale=None, legend=None),
        size=alt.Size("runs:Q", scale=alt.Scale(range=[40, 400]), legend=None),
        tooltip=tooltip,
    )
    layers = skip_layers(skip_rating, x, colors) + zero_layers("above_expected", y, colors) + [points]
    layers += highlight_layers(tested, card, x, y, colors)
    return alt.layer(*layers).properties(height=420)


def ratings_view(ratings, history, card, charac, colors):
    by_card = ratings.set_index("card")
    row, skip_rating = by_card.loc[card], by_card.loc[SKIP, "rating"]
    rating_col, rank_col, offered_col, picked_col = st.columns(4)
    rating_col.metric("Rating", f"{row['rating']:.0f}")
    rank_col.metric("Rank", f"{int(row['rank'])} of {len(ratings)}")
    offered_col.metric("Rewards it was in", int(row["offered"]))
    picked_col.metric("Picked", f"{int(row['picked'])} ({row['picked'] / row['offered']:.0%})")
    if card != SKIP:
        st.caption(
            f"{row['rating'] - skip_rating:+.0f} points from Skip: the ratings expect you to take it over "
            f"skipping {win_probability(row['rating'], skip_rating):.0%} of the time."
        )

    st.subheader(f"{pretty(card)}: rating over time")
    st.altair_chart(history_chart(history, card, colors), width="stretch")

    st.subheader(f"All {pretty(charac)} ratings")
    st.dataframe(
        pd.DataFrame(
            {
                "Rank": ratings["rank"],
                "Card": ratings["card"].map(pretty),
                "Rating": ratings["rating"],
                "Offered": ratings["offered"],
                "Picked": ratings["picked"],
                "Pick rate": ratings["picked"] / ratings["offered"] * 100,
            }
        ),
        hide_index=True,
        width="stretch",
        column_config={
            "Rating": st.column_config.NumberColumn(format="%.0f"),
            "Pick rate": st.column_config.NumberColumn(format="%.0f%%"),
        },
    )
    method(CARD_RATINGS)


def win_rate_view(tested, summary, skip_rating, card, colors):
    if summary is None:
        st.info(f"Not enough cards to test: it needs {MIN_CARDS} cards picked in {MIN_RUNS} runs or more.")
        method(WR_VS_ELO)
        return

    st.caption(
        "Win rate of the runs that picked each card, minus the win rate expected from the floors it was "
        "picked on. Dot size: runs. Colour: orange when rated above Skip but the results came out worse, "
        "blue when rated below Skip but they came out better; the more solid, the stronger the evidence."
    )
    result_tiles(tested, summary, f"Cards picked in {MIN_RUNS} runs or more")
    st.altair_chart(win_rate_chart(tested, skip_rating, card, colors), width="stretch")

    def percent(help):
        return st.column_config.NumberColumn(format="%.0f%%", help=help)

    st.dataframe(
        pd.DataFrame(
            {
                "Card": tested["card"].map(pretty),
                "Verdict": tested["verdict"],
                "Rating": tested["rating"],
                "Runs": tested["runs"],
                "Wins": tested["wins"],
                "Win rate": tested["win_rate"] * 100,
                "Expected": tested["expected"] * 100,
                "p-value": tested["p_value"].map(format_p),
                "Adjusted p": tested["p_adjusted"].map(format_p),
            }
        ),
        hide_index=True,
        width="stretch",
        column_config={
            "Rating": st.column_config.NumberColumn(format="%.0f"),
            "Runs": st.column_config.NumberColumn(help="Runs that picked the card"),
            "Win rate": percent("Share of those runs that were won"),
            "Expected": percent("Win rate expected from the floors the card was picked on"),
            "p-value": st.column_config.TextColumn(help="Exact binomial test of the wins against the expected win rate"),
            "Adjusted p": st.column_config.TextColumn(help="Holm adjusted, for testing many cards"),
            "Verdict": st.column_config.TextColumn(width="medium"),
        },
    )
    method(WR_VS_ELO)


def render(filters):
    st.title(TITLE)

    charac = filters.charac
    if charac is None:
        st.warning(
            "### All Characters are selected\n\n"
            ":small[Choose a single Character unless you want to compare Skip and Colorless cards across them.]\n\n"
            ":small[Planned: Comparing across character, especially the value of Skip and Colorless cards.]"
        )
        return

    st.caption(
        "Ratings from your three-card fight rewards: the picked option beats the other three, Skip included. "
        "Each character is rated separately, and all the sidebar filters apply."
    )

    data = filters.run_queries("sql/analysis", ["card_rewards", "run_lengths"])
    rewards, runs = data["card_rewards"], data["run_lengths"]
    if rewards.empty:
        st.info("No three-card rewards match these filters.")
        return

    ratings, history, tested, summary = rate(rewards, runs)
    cards = sorted(ratings.loc[ratings["card"] != SKIP, "card"], key=pretty)
    card = st.columns(2)[0].selectbox("Card", [SKIP] + cards, format_func=pretty)
    skip_rating = ratings.set_index("card").loc[SKIP, "rating"]
    colors = palette()

    # Tabs only run when open
    ratings_tab, win_rate_tab = st.tabs([CARD_RATINGS, WR_VS_ELO], on_change="rerun", key="card_picks_tab")
    if ratings_tab.open:
        with ratings_tab:
            ratings_view(ratings, history, card, charac, colors)
    if win_rate_tab.open:
        with win_rate_tab:
            win_rate_view(tested, summary, skip_rating, card, colors)

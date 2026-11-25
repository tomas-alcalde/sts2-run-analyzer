import altair as alt
import pandas as pd
import streamlit as st

from analysis.ancient_relics import relic_win_rates
from dashboard.common import method, palette, pretty

TITLE = "Ancient Relics"
CREDIBLE = 0.95

RAW, BAYES = "Raw win rate", "Bayesian estimate"


@st.cache_data(show_spinner=False)
def estimate(relics):
    return relic_win_rates(relics, credible=CREDIBLE)


def estimate_chart(shown, colors):
    shown = shown.assign(name=shown["relic"].map(pretty))
    order = shown.sort_values("posterior", ascending=False)["name"].tolist()
    # Raw rows first, so the Bayesian dot is drawn on top where they overlap
    long = pd.concat([shown.assign(estimate=RAW, value=shown["raw"]), shown.assign(estimate=BAYES, value=shown["posterior"])])

    y = alt.Y("name:N", sort=order, title=None)
    x_title, x_scale, x_axis = "Win rate", alt.Scale(domain=[0, 1]), alt.Axis(format="%", tickCount=10)
    tooltip = [
        alt.Tooltip("name:N", title="Relic"),
        alt.Tooltip("raw:Q", title=RAW, format=".0%"),
        alt.Tooltip("posterior:Q", title=BAYES, format=".1%"),
        alt.Tooltip("low:Q", title=f"{CREDIBLE:.0%} interval from", format=".1%"),
        alt.Tooltip("high:Q", title=f"{CREDIBLE:.0%} interval to", format=".1%"),
        alt.Tooltip("p_above:Q", title="P(above average)", format=".0%"),
        alt.Tooltip("p_best:Q", title="P(best)", format=".0%"),
        alt.Tooltip("taken:Q", title="Taken"),
        alt.Tooltip("wins:Q", title="Wins"),
    ]

    baseline = alt.Chart(shown).mark_rule(color=colors["neutral"]).encode(
        x=alt.X("mean(baseline):Q", title=x_title, scale=x_scale, axis=x_axis)
    )
    interval = alt.Chart(shown).mark_rule(strokeWidth=2, color=colors["accent"]).encode(
        y=y, x=alt.X("low:Q", title=x_title, scale=x_scale, axis=x_axis), x2="high:Q", tooltip=tooltip
    )
    points = alt.Chart(long).mark_circle(size=110, opacity=1).encode(
        y=y,
        x=alt.X("value:Q", title=x_title, scale=x_scale, axis=x_axis),
        color=alt.Color(
            "estimate:N",
            scale=alt.Scale(domain=[RAW, BAYES], range=[colors["neutral"], colors["accent"]]),
            legend=alt.Legend(title=None, orient="top"),
        ),
        tooltip=tooltip,
    )
    return (baseline + interval + points).properties(height=alt.Step(26))


def render(filters):
    st.title(TITLE)
    st.caption(
        "Win rate of the runs that took each relic, as a probability distribution: how likely each relic "
        "is to beat its ancient's average, and to be the best of its relics."
    )

    relics = filters.run_queries("sql/analysis", ["ancient_relics"])["ancient_relics"]
    if relics.empty:
        st.info("No ancient relics match these filters.")
        return

    estimates = estimate(relics)
    colors = palette()

    by_picks = estimates.groupby("ancient")["taken"].sum().sort_values(ascending=False).index
    ancient = st.selectbox("Ancient (sorted by relics taken)", by_picks, format_func=pretty)
    shown = estimates[estimates["ancient"] == ancient]

    st.subheader(f"{pretty(ancient)}: raw vs Bayesian win rate")
    st.caption(
        f"Grey line: win rate of the runs that took one of {pretty(ancient)}'s relics "
        f"({shown['baseline'].iloc[0]:.0%}). Bars: {CREDIBLE:.0%} credible interval of the Bayesian estimate."
    )
    st.altair_chart(estimate_chart(shown, colors), width="stretch")

    table = pd.DataFrame(
        {
            "Relic": shown["relic"].map(pretty),
            "Taken": shown["taken"],
            "Wins": shown["wins"],
            RAW: shown["raw"] * 100,
            BAYES: shown["posterior"] * 100,
            f"{CREDIBLE:.0%} interval": [f"{low:.0%} to {high:.0%}" for low, high in zip(shown["low"], shown["high"])],
            "P(above average)": shown["p_above"] * 100,
            "P(best)": shown["p_best"] * 100,
        }
    ).sort_values(BAYES, ascending=False)
    percent = st.column_config.NumberColumn(format="%.1f%%")
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={
            RAW: st.column_config.NumberColumn(format="%.0f%%"),
            BAYES: percent,
            "P(above average)": st.column_config.NumberColumn(
                format="%.0f%%", help="Probability that the relic's true win rate beats the grey line"
            ),
            "P(best)": st.column_config.NumberColumn(
                format="%.0f%%", help=f"Probability that the relic has the highest true win rate of {pretty(ancient)}'s relics"
            ),
        },
    )
    method(TITLE)

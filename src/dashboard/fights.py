import altair as alt
import pandas as pd
import streamlit as st

from analysis import MIN_RUNS
from analysis.hp_per_fight_type import compare_fight_types, damage_per_run
from analysis.hp_per_turn import hp_per_turn
from dashboard.common import FIGHT_LABELS, fight_scale, format_p, method, palette, pretty

TITLE = "Fights"
PER_FIGHT_TYPE = "HP lost per Fight type"
PER_TURN = "HP lost per turn"
ALL = "All"

TERM_PREFIXES = {"encounter": "Fight: "}
TERM_LABELS = {"intercept": "Intercept", "turns": "Turns", "ascension": "Ascension (per level)"}


def distribution_chart(fights, colors):
    per_run = damage_per_run(fights).reset_index().melt(id_vars="run_id", value_name="damage").dropna()
    per_run["fight"] = per_run["fight"].map(FIGHT_LABELS)
    return (
        alt.Chart(per_run)
        .mark_boxplot(size=24, rule={"color": colors["neutral"]})
        .encode(
            x=alt.X("fight:N", sort=list(FIGHT_LABELS.values()), title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("damage:Q", title="Average HP lost per fight, per run"),
            color=alt.Color("fight:N", scale=fight_scale(colors), legend=None),
        )
        .properties(height=320)
    )


def difference_chart(results, colors):
    results = results.assign(label=results["mean_diff"].map("{:+.1f} HP".format))
    tooltip = [
        alt.Tooltip("comparison:N", title="Comparison"),
        alt.Tooltip("mean_diff:Q", title="Mean difference (HP)", format="+.1f"),
        alt.Tooltip("ci_low:Q", title="95% CI from", format=".1f"),
        alt.Tooltip("ci_high:Q", title="95% CI to", format=".1f"),
        alt.Tooltip("runs:Q", title="Runs"),
    ]
    x_title = "Extra HP lost per fight"
    base = alt.Chart(results).encode(y=alt.Y("comparison:N", sort=None, title=None), tooltip=tooltip)

    zero = alt.Chart(results).mark_rule(color=colors["neutral"]).encode(x=alt.datum(0))
    interval = base.mark_rule(strokeWidth=2, color=colors["accent"]).encode(
        x=alt.X("ci_low:Q", title=x_title, scale=alt.Scale(zero=True)),
        x2="ci_high:Q",
    )
    point = base.mark_circle(size=90, opacity=1, color=colors["accent"]).encode(x=alt.X("mean_diff:Q", title=x_title))
    label = base.mark_text(dy=-16, color=colors["neutral"]).encode(
        x=alt.X("mean_diff:Q", title=x_title), text="label:N"
    )
    return (zero + interval + point + label).properties(height=320)


def term_label(term):
    if term in TERM_LABELS:
        return TERM_LABELS[term]
    control, value = term.split("_", 1)
    return TERM_PREFIXES[control] + pretty(value)


def fit_line(fights, slope, points):
    """The fitted slope, drawn through the average turns and HP lost (where a
    least squares fit always passes), over the plotted turns."""
    turns = points["turns"].agg(["min", "max"]).to_numpy(float)
    return pd.DataFrame({"turns": turns, "damage": fights["damage"].mean() + slope * (turns - fights["turns"].mean())})


def scatter_chart(fights, summary, coefs, points, color):
    # More coefficients than the intercept and the turns: something was held fixed
    y_title = "Average HP lost per fight, adjusted" if len(coefs) > 2 else "Average HP lost per fight"
    x = alt.X("turns:Q", title="Turns taken", axis=alt.Axis(tickMinStep=1, format="d"))
    y = alt.Y("damage:Q", title=y_title)

    line_layer = alt.Chart(fit_line(fights, summary["estimate"], points)).mark_line(strokeWidth=2, color=color).encode(x=x, y=y)
    point_layer = alt.Chart(points).mark_circle(opacity=1, color=color).encode(
        x=x,
        y=y,
        size=alt.Size("fights:Q", scale=alt.Scale(range=[30, 300]), legend=None),
        tooltip=[
            alt.Tooltip("turns:Q", title="Turns"),
            alt.Tooltip("damage:Q", title="Average HP lost", format=".1f"),
            alt.Tooltip("fights:Q", title="Fights"),
        ],
    )
    return (line_layer + point_layer).properties(height=320)


def fight_type_view(fights, colors):
    st.caption("Each run's average HP lost per fight, compared between fight types within the same run.")

    results = compare_fight_types(fights)
    results["comparison"] = results["harder"].map(FIGHT_LABELS) + " vs " + results["easier"].map(FIGHT_LABELS)
    tested = results.dropna(subset=["t_p"])

    left, right = st.columns(2)
    with left:
        st.subheader(PER_FIGHT_TYPE)
        st.caption("One value per run: its average HP lost per fight of that type.")
        st.altair_chart(distribution_chart(fights, colors), width="stretch")
    with right:
        st.subheader("Paired difference, with 95% CI")
        st.caption("Mean of the runs' differences between the two types.")
        if tested.empty:
            st.info(f"Not enough runs to test: each pair needs {MIN_RUNS} runs that had both fight types.")
        else:
            st.altair_chart(difference_chart(tested, colors), width="stretch")

    table = pd.DataFrame(
        {
            "Comparison": results["comparison"],
            "Runs": results["runs"],
            "Mean difference (HP)": results["mean_diff"].round(1),
            "95% CI": [
                "-" if pd.isna(low) else f"{low:.1f} to {high:.1f}"
                for low, high in zip(results["ci_low"], results["ci_high"])
            ],
            "t-test p (Holm)": results["t_p_holm"].map(format_p),
            "Wilcoxon p (Holm)": results["wilcoxon_p_holm"].map(format_p),
            "Significant at 5%": results["t_p_holm"].map(lambda p: "-" if pd.isna(p) else "Yes" if p < 0.05 else "No"),
        }
    )
    st.dataframe(table, hide_index=True, width="stretch")
    method(PER_FIGHT_TYPE)


def select_fights(fights, fight):
    """The Act dropdown, then the Fight dropdown listing that Act's named fights.
    Returns the fights selected."""
    acts = fights.groupby("act", as_index=False)["tier"].min().sort_values(["tier", "act"])["act"].tolist()
    act_col, fight_col = st.columns(2)
    act = act_col.selectbox("Act", [ALL] + acts, format_func=pretty, key=f"turn_act_{fight}")
    if act == ALL:
        fight_col.selectbox("Fight", [ALL], disabled=True, help="Choose an Act first", key=f"turn_fight_{fight}")
        return fights

    fights = fights[fights["act"] == act]
    named = sorted(fights["encounter"].unique(), key=pretty)
    # One widget per Act, so a Fight of another Act is never left selected
    encounter = fight_col.selectbox("Fight", [ALL] + named, format_func=pretty, key=f"turn_fight_{fight}_{act}")
    return fights if encounter == ALL else fights[fights["encounter"] == encounter]


def interval(low, high):
    return "-" if pd.isna(low) else f"{low:.2f} to {high:.2f}"


def coefficient_table(coefs):
    return pd.DataFrame(
        {
            "Term": coefs.index.map(term_label),
            "Estimate": coefs["estimate"].round(2),
            "Std. error": coefs["se"].map(lambda se: "-" if pd.isna(se) else f"{se:.2f}"),
            "95% CI": [interval(low, high) for low, high in zip(coefs["ci_low"], coefs["ci_high"])],
            "p-value": coefs["p_value"].map(format_p),
        }
    )


def fight_type_section(fights, fight, color):
    st.subheader(FIGHT_LABELS[fight])
    selected = select_fights(fights[fights["fight"] == fight], fight)

    summary, coefs, points = hp_per_turn(selected)
    if coefs is None:
        st.info(
            f"Not enough data for this selection: it needs {MIN_RUNS} runs or more, with fights of different lengths "
            f"(runs: {int(summary['runs'])}, fights: {int(summary['fights'])})."
        )
        return

    st.altair_chart(scatter_chart(selected, summary, coefs, points, color), width="stretch")
    table = pd.DataFrame(
        {
            "HP per turn": [round(summary["estimate"], 2)],
            "95% CI": [interval(summary["ci_low"], summary["ci_high"])],
            "p-value": [format_p(summary["p_value"])],
            "R² (whole model)": [round(summary["r2"], 3)],
            "Fights": [int(summary["fights"])],
            "Runs": [int(summary["runs"])],
        }
    )
    st.dataframe(table, hide_index=True, width="stretch")

    with st.expander("All coefficients"):
        if coefs.index.str.startswith("encounter_").any():
            st.caption("Each named Fight is compared with the most common one of the selection.")
        st.dataframe(coefficient_table(coefs), hide_index=True, width="stretch")


def turn_view(fights, charac, colors):
    if charac is None:
        st.warning(
            "### All Characters are selected\n\n"
            ":small[Choose a single Character unless you want to compare HP costs across them.]\n\n"
            ":small[Planned: Checking how HP costs differ across Characters.]"
        )
        return

    st.caption(
        "HP lost per fight against turns taken, by least squares, within each fight type. Dots: average over the "
        "fights with that many turns, adjusted as explained in Method; the larger, the more fights. Line: the fitted slope."
    )
    for fight, color in zip(FIGHT_LABELS, colors["categorical"]):
        fight_type_section(fights, fight, color)
    method(PER_TURN)


def render(filters):
    st.title(TITLE)

    fights = filters.run_queries("sql/analysis", ["fights"])["fights"]
    if fights.empty:
        st.info("No fights match these filters.")
        return

    colors = palette()

    # Tabs only run when open, so each analysis is computed only when asked for
    fight_type_tab, turn_tab = st.tabs([PER_FIGHT_TYPE, PER_TURN], on_change="rerun", key="fights_tab")
    if fight_type_tab.open:
        with fight_type_tab:
            fight_type_view(fights, colors)
    if turn_tab.open:
        with turn_tab:
            turn_view(fights, filters.charac, colors)

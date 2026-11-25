"""Card picks: an ELO rating of each card, from the three-card rewards you picked from.

Every three-card reward after a fight is a match between four options: the
three cards and Skip. The option you picked beats each of the other three, and
each of those wins moves both ratings by up to K points: more after an upset
(the lower-rated option picked), less when the pick was expected. Ratings start
at 1500 and are updated in the order the runs were played, so they follow how
your picks change over time. Each character is rated separately.
"""
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy import stats

from analysis import MIN_RUNS, holm

START = 1500
K = 16
SKIP = "SKIP"

# With fewer cards to compare than this, the win rate tests are skipped.
MIN_CARDS = 5


def win_probability(rating, opponent):
    """Chance that an option rated `rating` is picked over one rated `opponent`."""
    return 1 / (1 + 10 ** ((opponent - rating) / 400))


def card_elo(rewards):
    """Rate every card, and Skip, from one character's rewards, oldest first.

    Returns the final ratings (one row per option, best first) and the rating
    history (one row per option per reward it was part of).
    """
    ratings = defaultdict(lambda: START)
    history = []
    for (start_time, run_id, floor), reward in rewards.groupby(["start_time", "run_id", "floor"]):
        options = reward["card"].tolist() + [SKIP]
        picked = reward.loc[reward["taken"] == 1, "card"]
        winner = picked.iloc[0] if len(picked) else SKIP

        # Every win is scored with the ratings from before this reward
        before = {option: ratings[option] for option in options}
        for loser in options:
            if loser != winner:
                change = K * (1 - win_probability(before[winner], before[loser]))
                ratings[winner] += change
                ratings[loser] -= change

        history += [
            {"card": option, "start_time": start_time, "floor": floor, "rating": ratings[option], "picked": option == winner}
            for option in options
        ]

    history = pd.DataFrame(history)
    table = history.groupby("card").agg(offered=("picked", "size"), picked=("picked", "sum"))
    table["rating"] = pd.Series(ratings)
    table = table.sort_values("rating", ascending=False).reset_index()
    table.insert(0, "rank", range(1, len(table) + 1))
    return table, history


def floor_baseline(runs):
    """Win rate of the runs that got past each floor.

    A card picked on floor f was picked by a run that survived floor f, and the
    longer a run lasts, the more often it is won, whatever it picked. This is
    the win rate to expect from that alone.
    """
    floors = np.arange(runs["last_floor"].max() + 1)
    survived = runs["last_floor"].to_numpy()[:, None] > floors
    won = survived & runs["win"].to_numpy(bool)[:, None]
    rate = np.divide(won.sum(axis=0), survived.sum(axis=0), out=np.full(len(floors), np.nan), where=survived.any(axis=0))
    return pd.Series(rate, index=floors).fillna(runs["win"].mean())


def verdicts(rating, skip_rating, better, p_value, p_adjusted):
    """Flag the cards whose results go against the side of Skip you rate them on.

    Overpicked: rated above Skip (you'd rather take it), but its runs did no
    better than the comparison. Underpicked: rated below Skip, but they did
    better. Confirmed when the Holm-adjusted p-value is below 0.05, "possibly"
    when only the unadjusted one is, and "leaning" otherwise. In line when the
    results agree with the side of Skip.
    """
    against = pd.Series(
        np.select([(rating > skip_rating) & ~better, (rating < skip_rating) & better], ["overpicked", "underpicked"], ""),
        index=rating.index,
    )
    verdict = pd.Series("In line", index=rating.index)
    verdict[against != ""] = "Leaning " + against
    verdict[(against != "") & (p_value < 0.05)] = "Possibly " + against
    verdict[(against != "") & (p_adjusted < 0.05)] = against.str.capitalize()
    return verdict


def elo_vs_win_rate(rewards, runs, ratings):
    """Do higher-rated cards have higher win rates? And which cards break the rule?

    A card's win rate is the share of the runs that picked it that were won.
    Minus the win rate expected from the floors it was picked on, it becomes
    the card's "win rate above expected". Only cards picked in MIN_RUNS runs
    or more are tested.
      - The claim: one-sided Spearman rank correlation between rating and win
        rate above expected. Cards share runs, so its p-value is approximate.
      - Single cards: an exact binomial test of the card's wins against the
        win rate expected from its floors, with Holm-adjusted p-values for
        testing many cards, and flags as in `verdicts`.

    Returns the tested cards, and the correlation (None if too few cards).
    """
    baseline = floor_baseline(runs)
    picks = rewards[rewards["taken"] == 1].sort_values("floor").drop_duplicates(["run_id", "card"])
    picks = picks.assign(expected=picks["floor"].map(baseline))
    cards = picks.groupby("card").agg(runs=("run_id", "size"), wins=("win", "sum"), expected=("expected", "mean"))
    cards = cards.join(ratings.set_index("card")["rating"])
    cards["win_rate"] = cards["wins"] / cards["runs"]
    cards["above_expected"] = cards["win_rate"] - cards["expected"]

    tested = cards[cards["runs"] >= MIN_RUNS].copy()
    if len(tested) < MIN_CARDS or tested["above_expected"].nunique() < 2:
        return tested.reset_index(), None

    correlation = stats.spearmanr(tested["rating"], tested["above_expected"], alternative="greater")
    tested["p_value"] = [
        stats.binomtest(int(wins), int(runs), expected).pvalue
        for wins, runs, expected in zip(tested["wins"], tested["runs"], tested["expected"])
    ]
    tested["p_adjusted"] = holm(tested["p_value"])
    skip_rating = ratings.set_index("card").loc[SKIP, "rating"]
    tested["verdict"] = verdicts(
        tested["rating"], skip_rating, tested["above_expected"] > 0, tested["p_value"], tested["p_adjusted"]
    )

    summary = {"rho": correlation.statistic, "p_value": correlation.pvalue}
    return tested.sort_values("p_value").reset_index(), summary

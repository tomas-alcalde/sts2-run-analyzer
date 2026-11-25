"""Ancient relic win rates, as Bayesian probabilities.

Each relic's true win rate gets a uniform prior (every win rate equally
plausible, worth one win and one loss), so after k wins in n runs it is
Beta(k + 1, n - k + 1). Those distributions answer the questions behind a
pick directly: how likely is a relic to beat its ancient's average, and how
likely is it to be the best of its ancient's relics?
"""
import numpy as np
from scipy import stats

DRAWS = 20_000


def ancient_baseline(relics):
    """Win rate of each relic's ancient, with one win and one loss added (the
    same uniform prior), so it is never exactly 0 or 1."""
    totals = relics.groupby("ancient")[["wins", "taken"]].transform("sum")
    return (totals["wins"] + 1) / (totals["taken"] + 2)


def relic_win_rates(relics, credible=0.95, seed=0):
    """Posterior win rates of the relics in `relics` (relic, ancient, taken, wins).

    Returns the relics with their raw and posterior mean win rates, a credible
    interval, the probability that the relic beats its ancient's win rate, and
    the probability that it is the best of its ancient's relics.
    """
    relics = relics.reset_index(drop=True)
    relics["baseline"] = ancient_baseline(relics)
    wins, taken = relics["wins"].to_numpy(float), relics["taken"].to_numpy(float)
    posterior = stats.beta(wins + 1, taken - wins + 1)

    tail = (1 - credible) / 2
    relics["raw"] = wins / taken
    relics["posterior"] = posterior.mean()
    relics["low"], relics["high"] = posterior.ppf(tail), posterior.ppf(1 - tail)
    relics["p_above"] = posterior.sf(relics["baseline"].to_numpy())

    # Draw every relic's win rate, and count how often each is its ancient's highest
    draws = posterior.rvs(size=(DRAWS, len(relics)), random_state=np.random.default_rng(seed))
    relics["p_best"] = 0.0
    for rows in relics.groupby("ancient").indices.values():
        best = draws[:, rows].argmax(axis=1)
        relics.loc[rows, "p_best"] = np.bincount(best, minlength=len(rows)) / DRAWS
    return relics

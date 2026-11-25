"""HP lost per fight type: do you lose more HP in some fight types than in others?"""
import pandas as pd
from scipy import stats

from analysis import MIN_RUNS, holm

# Each pair is (harder, easier), and differences are harder minus easier.
PAIRS = [("elite", "normal"), ("boss", "normal"), ("boss", "elite")]


def damage_per_run(fights):
    """Average HP lost per fight: one row per run, one column per fight type."""
    return fights.pivot_table(index="run_id", columns="fight", values="damage", aggfunc="mean")


def compare_fight_types(fights, confidence=0.95):
    """Test every pair of fight types for a difference in HP lost.

    Each run is compared with itself: its average HP lost per fight of one type
    minus its average for the other, over the runs that had both. Pairing
    cancels out what differs between runs (deck, character, ascension), and
    keeps the observations independent, which fights inside one run are not.

    Two two-sided tests per pair:
      - paired t-test: is the mean difference zero? Also gives a confidence
        interval for it.
      - Wilcoxon signed-rank test: the same question without assuming the
        differences are roughly normal, so a few disastrous fights can't
        drive the result.
    Both sets of p-values are Holm-adjusted for the three comparisons.
    """
    damage = damage_per_run(fights)

    rows = []
    for harder, easier in PAIRS:
        paired = damage.reindex(columns=[harder, easier]).dropna()
        diff = paired[harder] - paired[easier]
        row = {"harder": harder, "easier": easier, "runs": len(diff), "mean_diff": diff.mean()}
        if len(diff) >= MIN_RUNS and (diff != 0).any():
            ttest = stats.ttest_rel(paired[harder], paired[easier])
            ci = ttest.confidence_interval(confidence)
            row.update(
                ci_low=ci.low,
                ci_high=ci.high,
                t_p=ttest.pvalue,
                wilcoxon_p=stats.wilcoxon(diff).pvalue,
            )
        rows.append(row)

    columns = ["harder", "easier", "runs", "mean_diff", "ci_low", "ci_high", "t_p", "wilcoxon_p"]
    results = pd.DataFrame(rows, columns=columns)
    results["t_p_holm"] = holm(results["t_p"])
    results["wilcoxon_p_holm"] = holm(results["wilcoxon_p"])
    return results

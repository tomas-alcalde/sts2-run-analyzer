"""Statistical analyses of the fights, ancient relics and card picks in runs.db.

Each module takes the DataFrames from sql/analysis/ and returns plain
DataFrames, so it works the same from the dashboard, the terminal or a notebook.
"""
import numpy as np

FIGHT_TYPES = ["normal", "elite", "boss"]

# With fewer runs than this, a test or a fit is skipped and its results left empty.
MIN_RUNS = 5


def holm(pvalues):
    """Holm-Bonferroni adjusted p-values (NaN where a test was skipped).

    Running several tests raises the chance that at least one is a false
    positive. Holm's method keeps that chance at the chosen level: the i-th
    smallest of m p-values is multiplied by m - i (i from 0), and the adjusted
    values are made non-decreasing.
    """
    pvalues = np.asarray(pvalues, dtype=float)
    adjusted = np.full(pvalues.shape, np.nan)
    tested = np.flatnonzero(~np.isnan(pvalues))
    order = tested[np.argsort(pvalues[tested])]
    scaled = (len(order) - np.arange(len(order))) * pvalues[order]
    adjusted[order] = np.minimum(1, np.maximum.accumulate(scaled))
    return adjusted

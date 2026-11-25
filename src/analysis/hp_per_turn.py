"""HP lost per turn: how much HP does each extra turn of a fight cost?

Fitted on one selection of fights: a fight type, optionally narrowed to an act
and then to a single named fight. The model is written up in docs/methods.md.
"""
import numpy as np
import pandas as pd
from scipy import stats

from analysis import MIN_RUNS

# Held fixed next to turns, whatever the selection. One that doesn't vary in the
# selection is left out: "encounter" once a single named fight is selected,
# "ascension" with a single ascension. A named fight belongs to one act, so
# holding it fixed also holds the act fixed.
CONTROLS = ["encounter", "ascension"]


def design_matrix(fights, controls=CONTROLS):
    """Intercept and turns, then the controls (one 0/1 column per category).

    Each category is compared with the most common one (the most played named
    fight). Controls that don't vary in `fights` are left out.
    """
    columns = [pd.Series(1.0, index=fights.index, name="intercept"), fights["turns"].astype(float)]
    for control in controls:
        values = fights[control]
        if values.nunique() < 2:
            continue
        if control == "ascension":
            columns.append(values.astype(float))
        else:
            baseline = f"{control}_{values.mode()[0]}"
            columns.append(pd.get_dummies(values, prefix=control, dtype=float).drop(columns=baseline))
    return pd.concat(columns, axis=1)


def ols(y, X, groups, confidence=0.95):
    """Least squares fit, with standard errors clustered by `groups`.

    Fights from one run share a deck and a character, so they are not
    independent, and the usual standard errors would come out too small. The
    cluster-robust "sandwich" estimator only assumes that runs are independent.
    It uses the same small-sample correction and G - 1 degrees of freedom
    (G = number of runs) as Stata and statsmodels.
    """
    X_values, y_values = X.to_numpy(float), y.to_numpy(float)
    n, k = X_values.shape

    bread = np.linalg.pinv(X_values.T @ X_values)
    beta = bread @ X_values.T @ y_values
    resid = y_values - X_values @ beta

    # One score per run: the sum of x_i * residual_i over the run's fights
    scores = pd.DataFrame(X_values * resid[:, None]).groupby(np.asarray(groups)).sum().to_numpy()
    g = len(scores)
    meat = scores.T @ scores
    cov = g / (g - 1) * (n - 1) / (n - k) * bread @ meat @ bread
    # A named fight from a single run is fitted exactly (its residuals add up to
    # 0), so nothing estimates the variance of its coefficient: left undefined
    variances = np.diag(cov)
    se = np.sqrt(np.where(variances > 1e-12, variances, np.nan))

    t_crit = stats.t.ppf((1 + confidence) / 2, df=g - 1)
    coefs = pd.DataFrame(
        {
            "estimate": beta,
            "se": se,
            "ci_low": beta - t_crit * se,
            "ci_high": beta + t_crit * se,
            "p_value": 2 * stats.t.sf(np.abs(beta / se), df=g - 1),
        },
        index=X.columns,
    )
    r2 = 1 - resid @ resid / np.sum((y_values - y_values.mean()) ** 2)
    return coefs, r2


def fittable(fights, X):
    """Whether the slope can be estimated: enough runs, more fights than
    coefficients, some variation in HP lost, and no column of X determined by
    the others (e.g. every named fight lasting a single number of turns)."""
    return (
        fights["run_id"].nunique() >= MIN_RUNS
        and len(fights) > X.shape[1]
        and fights["damage"].nunique() > 1
        and np.linalg.matrix_rank(X.to_numpy(float)) == X.shape[1]
    )


def adjusted_points(fights, coefs, X):
    """Average HP lost per number of turns, with the controls' effect removed.

    Each fight keeps its residual but sits on the fitted line for its turns, so
    the line through the overall averages is exactly what these points follow.
    """
    turns, damage = fights["turns"].astype(float), fights["damage"].astype(float)
    residuals = damage - X.to_numpy(float) @ coefs["estimate"].to_numpy()
    adjusted = damage.mean() + coefs.loc["turns", "estimate"] * (turns - turns.mean()) + residuals
    return adjusted.groupby(fights["turns"]).agg(damage="mean", fights="size").reset_index()


def hp_per_turn(fights):
    """Regress HP lost on turns taken over one selection of fights.

    Returns a summary (the number of fights and runs, and when fitted the R²
    and the turns coefficient: HP lost per extra turn with the controls held
    fixed), the full coefficient table, and the adjusted points to plot. The
    last two are None if the selection can't be fitted.
    """
    summary = {"fights": len(fights), "runs": fights["run_id"].nunique()}
    X = design_matrix(fights)
    if not fittable(fights, X):
        return pd.Series(summary), None, None

    coefs, summary["r2"] = ols(fights["damage"], X, fights["run_id"])
    summary.update(coefs.loc["turns"])
    return pd.Series(summary), coefs, adjusted_points(fights, coefs, X)

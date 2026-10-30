"""Walk-forward significance: day-clustered bootstrap CIs, McNemar and Diebold-Mariano.

Issue days are the resampling unit because the 48 leads of one issue, and the
issues of one day, share weather and are strongly correlated.
"""

import numpy as np
import pandas as pd
from scipy import stats

from ml.features import BERLIN

COLUMNS = {"od": ("y_od", "p_od25", "rule_od25", "od_at_issue"),
           "r18": ("y_r18", "p_18_usable", "rule_18_usable", "persistence_18")}
NAMES = ("model", "rule", "persistence")


def _float(value):
    return None if value is None or not np.isfinite(value) else float(value)


def _ci(values):
    values = values[np.isfinite(values)]
    return [_float(np.percentile(values, 2.5)), _float(np.percentile(values, 97.5))] if len(values) else [None, None]


def mcnemar_p(right_a, right_b):
    """Exact binomial on discordant pairs below 25, else chi-square with continuity correction."""
    b = int(np.sum(right_a & ~right_b))
    c = int(np.sum(~right_a & right_b))
    if b + c == 0:
        return 1.0
    if b + c < 25:
        return float(min(1.0, stats.binomtest(b, b + c, 0.5).pvalue))
    return float(stats.chi2.sf((abs(b - c) - 1) ** 2 / (b + c), 1))


def diebold_mariano_p(loss_a, loss_b, days):
    """Two-sided DM on daily mean loss differences, Newey-West variance with lag 1."""
    d = pd.Series(loss_a - loss_b).groupby(days).mean().sort_index().to_numpy()
    n = len(d)
    if n < 3:
        return None
    centred = d - d.mean()
    variance = (centred @ centred + 2 * 0.5 * (centred[1:] @ centred[:-1])) / n
    if variance <= 0:
        return 1.0 if np.allclose(d, 0) else 0.0
    return float(2 * stats.norm.sf(abs(d.mean() / np.sqrt(variance / n))))


def compare(frame, target="od", leads=(1, 6, 24, 48), n_boot=1000, seed=42):
    ycol, pcol, rcol, bcol = COLUMNS[target]
    rng = np.random.default_rng(seed)
    result = []
    for lead in leads:
        rows = frame.loc[frame.lead_h.eq(lead)].dropna(subset=[ycol, pcol, rcol, bcol])
        y = rows[ycol].to_numpy(float)
        probs = {name: rows[col].to_numpy(float) for name, col in zip(NAMES, (pcol, rcol, bcol))}
        right = {name: (p >= 0.5) == (y >= 0.5) for name, p in probs.items()}
        loss = {name: (p - y) ** 2 for name, p in probs.items()}
        days = pd.to_datetime(rows.issue_time, utc=True).dt.tz_convert(BERLIN).dt.date.to_numpy()
        record = {"lead_h": lead, "n": len(rows), "n_days": int(len(set(days)))}
        if not len(rows):
            result.append(record)
            continue
        # Per-day sums let each bootstrap draw recompute pooled means cheaply.
        codes, unique = pd.factorize(days)
        count = np.bincount(codes)
        sums = {f"{name}_{kind}": np.bincount(codes, weights=values[name].astype(float))
                for name in NAMES for kind, values in (("acc", right), ("brier", loss))}
        draws = rng.integers(0, len(unique), size=(n_boot, len(unique)))
        weights = np.stack([np.bincount(draw, minlength=len(unique)) for draw in draws])
        total = weights @ count
        boot = {key: (weights @ value) / total for key, value in sums.items()}
        for name in NAMES:
            record[f"{name}_acc"] = _float(right[name].mean())
            record[f"{name}_acc_ci"] = _ci(boot[f"{name}_acc"])
            record[f"{name}_brier"] = _float(loss[name].mean())
            record[f"{name}_brier_ci"] = _ci(boot[f"{name}_brier"])
        for base in ("rule", "persistence"):
            record[f"acc_diff_vs_{base}"] = _float(right["model"].mean() - right[base].mean())
            record[f"acc_diff_vs_{base}_ci"] = _ci(boot["model_acc"] - boot[f"{base}_acc"])
            record[f"mcnemar_p_vs_{base}"] = mcnemar_p(right["model"], right[base])
            record[f"dm_p_vs_{base}"] = diebold_mariano_p(loss["model"], loss[base], days)
        changed = rows.changed_within_lead.to_numpy(bool)
        record["change_n"] = int(changed.sum())
        for name in NAMES:
            record[f"{name}_change_acc"] = _float(right[name][changed].mean()) if changed.any() else None
        result.append(record)
    return result

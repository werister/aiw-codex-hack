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
    daily = pd.DataFrame({"loss_difference": loss_a - loss_b, "day": days}).groupby("day").mean().sort_index()
    d = daily.loss_difference.to_numpy()
    n = len(d)
    if n < 3:
        return None
    centred = d - d.mean()
    day_ordinals = np.asarray([day.toordinal() for day in daily.index])
    consecutive = np.diff(day_ordinals) == 1
    lag1 = np.sum(centred[:-1][consecutive] * centred[1:][consecutive])
    variance = (centred @ centred + 2 * 0.5 * lag1) / n
    if variance <= 0:
        return 1.0 if np.allclose(d, 0) else 0.0
    return float(2 * stats.norm.sf(abs(d.mean() / np.sqrt(variance / n))))


def _calendar_blocks(days, length):
    """Return indices for moving blocks that never cross a missing calendar day."""
    unique_days = sorted(set(days))
    ordinals = np.asarray([day.toordinal() for day in unique_days])
    return [tuple(range(start, start + length))
            for start in range(max(0, len(unique_days) - length + 1))
            if np.all(np.diff(ordinals[start:start + length]) == 1)]


def _bootstrap_weights(days, n_boot, rng, block_days=1):
    codes, unique = pd.factorize(days, sort=True)
    n_days = len(unique)
    if n_days == 0:
        return np.zeros(0, dtype=np.int64), codes, None
    counts = np.bincount(codes, minlength=n_days)
    if block_days == 1:
        draws = rng.integers(0, n_days, size=(n_boot, n_days))
        weights = np.stack([np.bincount(draw, minlength=n_days) for draw in draws])
    else:
        blocks = _calendar_blocks(days, block_days)
        if not blocks:
            return counts, codes, None
        covered_days = set().union(*(set(block) for block in blocks))
        if len(covered_days) != n_days:
            return counts, codes, None
        weights = np.zeros((n_boot, n_days), dtype=np.int32)
        blocks_needed = int(np.ceil(n_days / block_days))
        for draw in range(n_boot):
            selected = []
            for block in rng.integers(0, len(blocks), size=blocks_needed):
                selected.extend(blocks[block])
            weights[draw] = np.bincount(selected[:n_days], minlength=n_days)
    return counts, codes, weights


def _bootstrap_scores(right, loss, days, n_boot, rng, block_days=1):
    counts, codes, weights = _bootstrap_weights(days, n_boot, rng, block_days)
    if weights is None:
        return None
    sums = {f"{name}_{metric}": np.bincount(
                codes, weights=values[name].astype(float), minlength=len(counts))
            for name in right for metric, values in (("acc", right), ("brier", loss))}
    totals = weights @ counts
    return {key: (weights @ values) / totals for key, values in sums.items()}


def compare(frame, target="od", leads=(1, 6, 24, 48), n_boot=1000, seed=42):
    if n_boot < 1:
        raise ValueError("n_boot must be positive")
    ycol, pcol, rcol, bcol = COLUMNS[target]
    ensemble_column = {"od": "rule_od25_ens", "r18": "rule_18_ens"}[target]
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
        boot = _bootstrap_scores(right, loss, days, n_boot, rng)
        block_boots = {block_days: _bootstrap_scores(right, loss, days, n_boot, rng, block_days)
                       for block_days in (3, 7)}
        for name in NAMES:
            record[f"{name}_acc"] = _float(right[name].mean())
            record[f"{name}_acc_ci"] = _ci(boot[f"{name}_acc"])
            record[f"{name}_brier"] = _float(loss[name].mean())
            record[f"{name}_brier_ci"] = _ci(boot[f"{name}_brier"])
            for block_days, block_boot in block_boots.items():
                record[f"{name}_acc_ci_{block_days}d"] = (
                    _ci(block_boot[f"{name}_acc"]) if block_boot is not None else None)
                record[f"{name}_brier_ci_{block_days}d"] = (
                    _ci(block_boot[f"{name}_brier"]) if block_boot is not None else None)
        for base in ("rule", "persistence"):
            record[f"acc_diff_vs_{base}"] = _float(right["model"].mean() - right[base].mean())
            record[f"acc_diff_vs_{base}_ci"] = _ci(boot["model_acc"] - boot[f"{base}_acc"])
            for block_days, block_boot in block_boots.items():
                record[f"acc_diff_vs_{base}_ci_{block_days}d"] = (
                    _ci(block_boot["model_acc"] - block_boot[f"{base}_acc"])
                    if block_boot is not None else None)
            record[f"mcnemar_p_vs_{base}"] = mcnemar_p(right["model"], right[base])
            record[f"dm_p_vs_{base}"] = diebold_mariano_p(loss["model"], loss[base], days)
        record["inference_notes"] = {
            "accuracy_ci": "paired bootstrap resampling issue-days; 3d and 7d intervals resample contiguous calendar blocks",
            "row_mcnemar": "nominal row-level p-value; within-day dependence is not modeled",
            "diebold_mariano": "daily mean loss differences with Newey-West lag 1",
            "multiple_comparisons": "not adjusted across leads and baselines",
        }
        changed = rows.changed_within_lead.to_numpy(bool)
        record["change_n"] = int(changed.sum())
        for name in NAMES:
            record[f"{name}_change_acc"] = _float(right[name][changed].mean()) if changed.any() else None

        if ensemble_column in rows:
            ensemble_rows = rows.dropna(subset=[ensemble_column])
            record["rule_ensemble_n"] = len(ensemble_rows)
            record["rule_ensemble_coverage"] = len(ensemble_rows) / len(rows)
            if ensemble_rows.empty:
                for key in (
                    "model_acc_on_rule_ensemble_cohort", "rule_ensemble_acc",
                    "model_brier_on_rule_ensemble_cohort", "rule_ensemble_brier",
                    "acc_diff_model_vs_rule_ensemble", "brier_diff_model_vs_rule_ensemble",
                    "mcnemar_p_vs_rule_ensemble", "dm_p_vs_rule_ensemble",
                ):
                    record[key] = None
                for key in (
                    "acc_diff_model_vs_rule_ensemble_ci",
                    "brier_diff_model_vs_rule_ensemble_ci",
                ):
                    record[key] = [None, None]
                for block_days in (3, 7):
                    record[f"acc_diff_model_vs_rule_ensemble_ci_{block_days}d"] = None
                    record[f"brier_diff_model_vs_rule_ensemble_ci_{block_days}d"] = None
                record["rule_ensemble_change_n"] = 0
                for name in ("model", "rule_ensemble"):
                    record[f"{name}_change_acc_on_rule_ensemble_cohort"] = None
                record["rule_ensemble_inference_notes"] = record["inference_notes"] | {
                    "cohort": "model and ensemble-rule metrics use only rows with a labelled target and non-null ensemble rule",
                    "status": "no rows have a non-null ensemble rule",
                }
                result.append(record)
                continue
            y_extra = ensemble_rows[ycol].to_numpy(float)
            p_model = ensemble_rows[pcol].to_numpy(float)
            p_ensemble = ensemble_rows[ensemble_column].to_numpy(float)
            extra_right = {"model": (p_model >= 0.5) == (y_extra >= 0.5),
                           "rule_ensemble": (p_ensemble >= 0.5) == (y_extra >= 0.5)}
            extra_loss = {name: (probability - y_extra) ** 2
                          for name, probability in (("model", p_model),
                                                    ("rule_ensemble", p_ensemble))}
            ensemble_days = pd.to_datetime(ensemble_rows.issue_time, utc=True).dt.tz_convert(BERLIN).dt.date.to_numpy()
            extra_boot = _bootstrap_scores(extra_right, extra_loss, ensemble_days, n_boot, rng)
            extra_blocks = {block_days: _bootstrap_scores(extra_right, extra_loss, ensemble_days,
                                                           n_boot, rng, block_days)
                            for block_days in (3, 7)}
            record["model_acc_on_rule_ensemble_cohort"] = _float(extra_right["model"].mean())
            record["rule_ensemble_acc"] = _float(extra_right["rule_ensemble"].mean())
            record["model_brier_on_rule_ensemble_cohort"] = _float(extra_loss["model"].mean())
            record["rule_ensemble_brier"] = _float(extra_loss["rule_ensemble"].mean())
            record["acc_diff_model_vs_rule_ensemble"] = _float(
                extra_right["model"].mean() - extra_right["rule_ensemble"].mean())
            record["brier_diff_model_vs_rule_ensemble"] = _float(
                extra_loss["model"].mean() - extra_loss["rule_ensemble"].mean())
            record["acc_diff_model_vs_rule_ensemble_ci"] = _ci(
                extra_boot["model_acc"] - extra_boot["rule_ensemble_acc"])
            record["brier_diff_model_vs_rule_ensemble_ci"] = _ci(
                extra_boot["model_brier"] - extra_boot["rule_ensemble_brier"])
            for block_days, block_boot in extra_blocks.items():
                record[f"acc_diff_model_vs_rule_ensemble_ci_{block_days}d"] = (
                    _ci(block_boot["model_acc"] - block_boot["rule_ensemble_acc"])
                    if block_boot is not None else None)
                record[f"brier_diff_model_vs_rule_ensemble_ci_{block_days}d"] = (
                    _ci(block_boot["model_brier"] - block_boot["rule_ensemble_brier"])
                    if block_boot is not None else None)
            record["mcnemar_p_vs_rule_ensemble"] = mcnemar_p(
                extra_right["model"], extra_right["rule_ensemble"])
            record["dm_p_vs_rule_ensemble"] = diebold_mariano_p(
                extra_loss["model"], extra_loss["rule_ensemble"], ensemble_days)
            ensemble_changed = ensemble_rows.changed_within_lead.to_numpy(bool)
            record["rule_ensemble_change_n"] = int(ensemble_changed.sum())
            for name in ("model", "rule_ensemble"):
                record[f"{name}_change_acc_on_rule_ensemble_cohort"] = (
                    _float(extra_right[name][ensemble_changed].mean()) if ensemble_changed.any() else None)
            record["rule_ensemble_inference_notes"] = record["inference_notes"] | {
                "cohort": "model and ensemble-rule metrics use only rows with a labelled target and non-null ensemble rule"}
        elif ensemble_column in frame:
            record["rule_ensemble_n"] = 0
        result.append(record)
    return result

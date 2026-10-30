"""Walk-forward scores. Runway 18 targets are inferred from METAR wind rules."""

import numpy as np
import pandas as pd

LEADS = (1, 6, 24, 48)


def skill(frame, target):
    ycol, pcol, rcol, bcol = (("y_od", "p_od25", "rule_od25", "od_at_issue") if target == "od"
                            else ("y_r18", "p_18_usable", "rule_18_usable", "persistence_18"))
    result = []
    for lead in LEADS:
        rows = frame.loc[frame.lead_h.eq(lead)].dropna(subset=[ycol, pcol, rcol, bcol])
        record = {"lead_h": lead, "n": len(rows)}
        for name, col in (("model", pcol), ("rule", rcol), ("persistence", bcol)):
            y, p = rows[ycol].to_numpy(float), rows[col].to_numpy(float)
            record[name + "_acc"] = float(np.mean((p >= 0.5) == y)) if len(y) else None
            record[name + "_brier"] = float(np.mean((p - y) ** 2)) if len(y) else None
            changed = rows.changed_within_lead.to_numpy(bool)
            record[name + "_change_acc"] = float(np.mean((p[changed] >= 0.5) == y[changed])) if changed.any() else None
        record["change_n"] = int(rows.changed_within_lead.sum())
        result.append(record)
    return result


def reliability(frame, target, confidence=False):
    if target in ("combined", "certainty"):
        rows = frame.dropna(subset=["y_od", "y_r18", "p_od25", "p_18_usable"])
        od, r18 = rows.p_od25.to_numpy(float), rows.p_18_usable.to_numpy(float)
        p = np.minimum(np.maximum(od, 1 - od), np.maximum(r18, 1 - r18))
        if target == "certainty":
            p = 2 * p - 1
        y = (((od >= 0.5) == rows.y_od) & ((r18 >= 0.5) == rows.y_r18)).to_numpy(float)
        return probability_bins(p, y)
    ycol, pcol = ("y_od", "p_od25") if target == "od" else ("y_r18", "p_18_usable")
    rows = frame.dropna(subset=[ycol, pcol])
    p, y = rows[pcol].to_numpy(float), rows[ycol].to_numpy(float)
    if confidence:
        y = ((p >= 0.5) == y).astype(float)
        p = np.maximum(p, 1 - p)
    return probability_bins(p, y)


def probability_bins(p, y):
    records = []
    for index in range(10):
        low, high = index / 10, (index + 1) / 10
        selected = (p >= low) & ((p < high) if high < 0.999 else (p <= 1))
        records.append({"lower": round(float(low), 1), "upper": round(float(high), 1),
                        "n": int(selected.sum()), "mean_predicted": float(p[selected].mean()) if selected.any() else None,
                        "observed_frequency": float(y[selected].mean()) if selected.any() else None})
    return records


def next_change_timing(frame, truth):
    """Score first next changes, counting missed changes as misses.

    Only complete 48-hour OOS trajectories with complete half-hour truth count.
    False alarms on windows without a change are reported separately.
    """
    truth = truth.sort_values("time")
    total = hit1 = hit3 = no_change = false_alarm = excluded = predicted_count = 0
    errors = []
    for issue, rows in frame.groupby("issue_time", sort=False):
        rows = rows.sort_values("lead_h")
        actual = truth.loc[(truth.time > issue) & (truth.time <= issue + pd.Timedelta(hours=48))]
        if len(rows) != 48 or len(actual) != 96 or actual.od.isna().any():
            excluded += 1
            continue
        initial = "25" if rows.od_at_issue.iloc[0] else "07"
        # Include initial direction so an immediate switch counts.
        changes = actual.loc[actual.od.ne(actual.od.shift(fill_value=initial))]
        prediction = np.where(rows.p_od25 >= 0.5, "25", "07")
        pred_changes = rows.loc[prediction != np.concatenate(([initial], prediction[:-1]))]
        predicted = pred_changes.time.iloc[0] if len(pred_changes) else None
        predicted_count += int(predicted is not None)
        if changes.empty:
            no_change += 1
            false_alarm += int(predicted is not None)
            continue
        total += 1
        if predicted is not None:
            error = abs((predicted - changes.time.iloc[0]).total_seconds()) / 3600
            errors.append(error)
            hit1 += error <= 1
            hit3 += error <= 3
    return {"n_actual_change_windows": total, "within_1h": hit1 / total if total else None,
            "within_3h": hit3 / total if total else None, "n_no_change_windows": no_change,
            "false_alarm_rate": false_alarm / no_change if no_change else None,
            "n_predicted_changes": predicted_count, "excluded_incomplete_windows": excluded,
            "mean_absolute_error_h_when_predicted": float(np.mean(errors)) if errors else None,
            "truth": "DFLD half-hour bins, local-clock conversion as documented by data lane"}


def period(values):
    return {"start": values.min().isoformat(), "end": values.max().isoformat()}

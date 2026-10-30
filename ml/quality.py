"""Walk-forward scores. Runway 18 targets are inferred from METAR wind rules."""

import numpy as np
import pandas as pd

from ml.features import components
from ml.rules import RULES

LEADS = (1, 6, 24, 48)


def suspect_od_runs(truth, obs, min_hours=3):
    """Flag recorded OD runs that break the official landing limit for several hours.

    A 10 kt landing tailwind forces an immediate change, so a run with three or more
    such METAR hours points to a stuck feed rather than a flown direction. In
    2024-2026 this flags only 8-12 Oct 2026, when DWD 01420 also shows westerlies.
    """
    truth = truth.sort_values("time")
    wind = pd.merge_asof(truth[["time"]], obs[["time", "wind_kt", "wind_dir_deg"]], on="time",
                         tolerance=pd.Timedelta(hours=1))
    heading = np.where(truth.od.eq("25"), RULES["runway_heading_deg"]["25"], RULES["runway_heading_deg"]["07"])
    tail = components(wind.wind_kt.to_numpy(float), wind.wind_dir_deg.to_numpy(float), heading)
    over = pd.Series(tail >= RULES["landing_tailwind_change_now_kt"], index=truth.index)
    run = truth.od.ne(truth.od.shift()).cumsum()
    return over.groupby(run).transform("sum") >= min_hours


def skill(frame, target):
    ycol, pcol, rcol, bcol = (("y_od", "p_od25", "rule_od25", "od_at_issue") if target == "od"
                            else ("y_r18", "p_18_usable", "rule_18_usable", "persistence_18"))
    result = []
    for lead in LEADS:
        rows = frame.loc[frame.lead_h.eq(lead)].dropna(subset=[ycol, pcol, rcol, bcol])
        record = {"lead_h": lead, "n": len(rows)}
        raw_col = "p_od25_raw" if target == "od" and "p_od25_raw" in rows else pcol
        for name, col in (("model", pcol), ("raw_model", raw_col), ("blend", pcol), ("rule", rcol), ("persistence", bcol)):
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


def r18_events(frame, horizons=(1, 6, 24)):
    """Issue-level runway 18 closure detection within the next H hours.

    An issue counts as an actual event when any labelled target hour within H is
    inferred closed, and as predicted when the forecast calls any hour closed.
    Model calls use p_18_usable < 0.5; rules, corrected rules and persistence use
    their 0/1 states.
    """
    result = []
    rows = frame.dropna(subset=["y_r18"])
    for horizon in horizons:
        window = rows.loc[rows.lead_h <= horizon]
        actual = window.y_r18.eq(0).groupby(window.issue_time).any()
        record = {"horizon_h": horizon, "n_issues": int(len(actual)), "n_actual": int(actual.sum())}
        baselines = [("model", window.p_18_usable < 0.5), ("rule", window.rule_18_usable.eq(0)),
                     ("persistence", window.persistence_18.eq(0))]
        if "rule_18_ens" in window:
            # The official rule on the METAR-scaled ensemble wind: it can close 18, unlike raw 10 m wind.
            baselines.append(("rule_corrected", window.rule_18_ens.eq(0)))
        for name, closed in baselines:
            predicted = closed.groupby(window.issue_time).any().reindex(actual.index, fill_value=False)
            hits, misses = int((actual & predicted).sum()), int((actual & ~predicted).sum())
            false_alarms = int((~actual & predicted).sum())
            record[name] = {"hits": hits, "misses": misses, "false_alarms": false_alarms,
                            "recall": hits / (hits + misses) if hits + misses else None,
                            "precision": hits / (hits + false_alarms) if hits + false_alarms else None,
                            "false_alarm_rate": false_alarms / int((~actual).sum()) if (~actual).any() else None}
        y, p = window.y_r18.to_numpy(float), window.p_18_usable.to_numpy(float)
        record["model_brier"] = float(np.mean((p - y) ** 2)) if len(y) else None
        result.append(record)
    return result

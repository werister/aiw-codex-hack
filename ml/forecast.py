"""48-hour EDDF forecast. Runway 18 weather usability is inferred from wind."""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import math
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests

from ml import live
from ml.features import (MULTIMODELS, PUBLICATION_LAG_H,
                         observations_available_at, select_nwp, tailwind_since_issue)
from ml.quality import suspect_od_runs
from ml.rules import RULES, crosswind, od_state_machine, r18_usable, tailwind

BERLIN = ZoneInfo("Europe/Berlin")


def utc_text(value):
    return pd.Timestamp(value).tz_convert("UTC").strftime("%Y-%m-%dT%H:%MZ")


def local_text(value):
    return pd.Timestamp(value).tz_convert(BERLIN).strftime("%Y-%m-%dT%H:%M")


def issue_time(day=None, *, now=None):
    now = pd.Timestamp(now if now is not None else datetime.now(tz=BERLIN)).tz_convert("UTC")
    if day is None:
        return now.floor("h"), "live", now
    issue = pd.Timestamp(datetime.combine(day, datetime.min.time(), tzinfo=BERLIN)).tz_convert("UTC")
    if issue > now.floor("h"):
        return now.floor("h"), "live", now
    return issue, "hindcast" if day < now.tz_convert(BERLIN).date() else "live", now


def wind_rows(frame):
    return [(row.time, None if pd.isna(row.wind_dir_deg) else float(row.wind_dir_deg),
             float(row.wind_kt), float(row.gust_kt)) for row in frame.itertuples()]


def current_direction(obs, history, cutoff):
    known = history.loc[history.available_at <= cutoff] if len(history) else history
    if len(known) and cutoff - known.available_at.iloc[-1] <= pd.Timedelta(hours=2):
        return known.od.iloc[-1], "recorded DFLD OD; completed hourly bins, reporting delay unknown"
    return od_state_machine(wind_rows(obs))[-1], "current OD inferred from IEM METAR + rules"


def selected_wind(issue, nwp):
    return select_nwp(issue, nwp)[["time", "lead_h", "wind_dir_deg", "wind_kt", "gust_kt"]]


def logistic(value):
    return 1 / (1 + math.exp(-max(-30, min(30, value))))


def fallback_predict(issue, obs, nwp, current_od):
    """Temporary until fitted probabilities are available from predict_48h."""
    frame = selected_wind(issue, nwp)
    rows = wind_rows(frame)
    available_obs = observations_available_at(obs, issue)
    timer = tailwind_since_issue(issue, available_obs, current_od, obs.attrs.get("od_history"))
    frame["rule_od"] = od_state_machine(rows, initial_od=current_od, tailwind_since=timer)
    frame["rule_18_usable"] = [r18_usable(s, d, g) for _, d, s, g in rows]
    for runway in ("25", "18"):
        frame[f"tailwind_{runway}_kt"] = [tailwind(s, d, RULES["runway_heading_deg"][runway])
                                         if d is not None else 0.0 for _, d, s, _ in rows]
    # HACK: 3kt probability scale for a runnable baseline; these probabilities are uncalibrated.
    frame["p_od25"] = [logistic((1 if od == "25" else -1) * max(abs(tw), 0.03) / 3)
                         for od, tw in zip(frame.rule_od, frame.tailwind_25_kt)]
    margins = [min(RULES["departure_tailwind_limit_kt"] - tailwind(s, d, RULES["runway_heading_deg"]["18"]),
                   RULES["crosswind_limit_kt_incl_gusts"] - crosswind(max(s, g), d, RULES["runway_heading_deg"]["18"]))
               if d is not None else 0 for _, d, s, g in rows]
    frame["p_18_usable"] = [logistic(margin / 3) for margin in margins]
    return frame


def predict(issue, obs, nwp, current_od):
    def unavailable(error):
        print(f"WARNING: TRAINED MODEL UNAVAILABLE: {error}. Using rules-fallback; "
              "probabilities are uncalibrated.", file=sys.stderr)
        return fallback_predict(issue, obs, nwp, current_od), "rules-fallback"

    try:
        module = importlib.import_module("ml.predict")
    except ModuleNotFoundError as error:
        if error.name != "ml.predict":
            raise
        return unavailable(error)
    try:
        frame = module.predict_48h(issue, obs, nwp, current_od)
    except FileNotFoundError as error:
        return unavailable(error)
    except ValueError as error:
        missing_fit = str(error).startswith("No model trained before this issue time")
        future = (str(error) == "No METAR within two hours before issue"
                  and issue > pd.Timestamp.now(tz="UTC").floor("h"))
        if not (missing_fit or future):
            raise
        return unavailable(error)
    version = frame.attrs.get("model_version", "trained-forecast")
    return frame, version


def next_change(hours, current_od):
    for index, hour in enumerate(hours):
        if hour["od"] == current_od:
            continue
        new_od = hour["od"]
        probability = lambda row: row["p_od25"] if new_od == "25" else 1 - row["p_od25"]
        left = right = index
        while left > 0 and 0.35 <= probability(hours[left - 1]) <= 0.65:
            left -= 1
        while right + 1 < len(hours) and 0.35 <= probability(hours[right + 1]) <= 0.65:
            right += 1
        return {"time": hour["time"], "local": hour["local"], "from": current_od,
                "to": new_od, "p": probability(hour),
                "window_local": [hours[left]["local"], hours[right]["local"]]}
    return None


def closures(hours):
    result = []
    index = 0
    while index < len(hours):
        if hours[index]["p_18_usable"] >= 0.5:
            index += 1
            continue
        start = index
        while index < len(hours) and hours[index]["p_18_usable"] < 0.5:
            index += 1
        end = pd.Timestamp(hours[index - 1]["time"]) + pd.Timedelta(hours=1)
        result.append({"start": hours[start]["time"], "end": utc_text(end),
                       "local_start": hours[start]["local"], "local_end": local_text(end),
                       "min_p_usable": min(row["p_18_usable"] for row in hours[start:index])})
    return result


def format_hours(frame, issue):
    frame = frame.sort_values("time").reset_index(drop=True)
    if len(frame) != 48 or list(pd.to_datetime(frame.time, utc=True)) != list(live.target_hours(issue)):
        raise ValueError("Predictor must return exactly 48 consecutive target hours")
    hours = []
    for index, row in enumerate(frame.to_dict("records"), 1):
        p_od, p_18 = float(row["p_od25"]), float(row["p_18_usable"])
        if not (0 <= p_od <= 1 and 0 <= p_18 <= 1):
            raise ValueError("Predictor returned an invalid probability")
        hour = {"time": utc_text(row["time"]), "local": local_text(row["time"]), "lead_h": index,
                "wind_dir_deg": None if pd.isna(row["wind_dir_deg"]) or row["wind_kt"] == 0 else float(row["wind_dir_deg"]),
                "wind_kt": float(row["wind_kt"]), "gust_kt": float(row["gust_kt"]),
                "tailwind_25_kt": float(row["tailwind_25_kt"]), "tailwind_18_kt": float(row["tailwind_18_kt"]),
                "rule_od": row["rule_od"], "rule_18_usable": bool(row["rule_18_usable"]),
                "p_od25": p_od, "od": "25" if p_od >= 0.5 else "07", "p_18_usable": p_18,
                "certainty": round(100 * min(abs(2 * p_od - 1), abs(2 * p_18 - 1)))}
        if "p_od25_raw" in row:
            hour["inputs"] = hour_inputs(row)
        hours.append(hour)
    return hours


def number(value):
    return None if value is None or pd.isna(value) else float(value)


def hour_inputs(row):
    """Per-hour evidence; missing inputs stay null."""
    return {"nwp_offset_days": int(row["nwp_offset_days"]), "wind_kt_metar_scaled": float(row["wind_kt_metar_scaled"]),
            **{name: number(row[name]) for name in ("ens_tailwind_25_mean", "ens_tailwind_25_std",
                                                     "ens_tailwind_18_mean", "ens_dir_spread", "ens_votes_25")},
            "rule_od25_ens": int(row["rule_od25_ens"]), "dp_ns_hpa": number(row["dp_ns"]),
            "dp_ew_hpa": number(row["dp_ew"]), "blend_key": str(row["blend_key"]),
            "blend_weight": float(row["blend_weight"]), "p_od25_raw": float(row["p_od25_raw"]),
            "p_18_usable_raw": number(row.get("p_18_usable_raw")),
            "r18_blend_weight": number(row.get("r18_blend_weight"))}


def input_sources(nwp, obs, known, issue):
    """Which inputs were present and when each became available (no later than issue)."""
    def latest(column):
        values = pd.to_datetime(nwp[column], utc=True).dropna() if column in nwp else pd.Series(dtype="datetime64[ns, UTC]")
        if column in ("issued_at", "retrieved_at"):
            values = values.loc[values <= issue]
        return utc_text(values.max()) if len(values) else None

    def present(prefix):
        return any(column.startswith(prefix) and nwp[column].notna().any() for column in nwp)

    base = latest("available_at")
    sources = [{"name": "Open-Meteo best_match", "available_at": base}]
    for stamp in ("issued_at", "retrieved_at"):
        value = latest(stamp)
        if value:
            sources[0][stamp] = value
    for model in MULTIMODELS:
        sources.append({"name": f"Open-Meteo {model}", "available_at": latest(f"{model}__available_at") or base,
                        "missing": not present(f"{model}__wind_speed_10m")})
    sources.append({"name": "Open-Meteo pressure boxes N/S/W/E", "available_at": latest("pressure__available_at") or base,
                    "missing": not present("pressure_n")})
    sources.append({"name": "IEM EDDF METAR", "available_at": utc_text(obs.loc[obs.time <= issue].time.max())})
    if len(known):
        sources.append({"name": "DFLD recorded OD", "available_at": utc_text(known.available_at.max())})
    return sources


def evidence(frame, hours, issue, obs, known, nwp, current_od, provenance):
    import hashlib

    attrs = frame.attrs
    now = obs.loc[obs.time <= issue].sort_values("time").iloc[-1]
    issue_inputs = {"metar_time": utc_text(now.time), "metar_wind_dir_deg": number(now.wind_dir_deg),
                    "metar_wind_kt": float(now.wind_kt), "metar_gust_kt": float(now.gust_kt),
                    "od_at_issue": current_od, "od_source": provenance,
                    "hours_since_change": number(attrs.get("hours_since_change"))}
    artifact = {"version": attrs["model_version"], "file": attrs["model_file"], "sha256": attrs["model_sha256"],
                "trained_through": pd.Timestamp(attrs["trained_through"]).isoformat()}
    payload = json.dumps([utc_text(issue), artifact["sha256"], issue_inputs, [hour.get("inputs") for hour in hours]],
                         sort_keys=True, default=str)
    return {"run_id": hashlib.sha256(payload.encode()).hexdigest()[:12], "model_artifact": artifact,
            "feature_set": "base+ensemble+synoptic", "rules_version": RULES["version"],
            "publication_lag_h": PUBLICATION_LAG_H, "issue_inputs": issue_inputs,
            "sources": input_sources(nwp, obs, known, issue)}


def observed_overlay(issue, history):
    """Keep each recorded OD; unavailable independent runway 18 labels stay null."""
    selected = history.loc[history.time.isin(live.target_hours(issue))]
    if selected.empty:
        return []
    path = live.DATA / "eddf_metar.parquet"
    if path.exists():
        weather = live.normalize_metar(pd.read_parquet(path))
    else:
        weather = pd.DataFrame({
            "time": pd.Series(dtype="datetime64[ns, UTC]"),
            "wind_kt": pd.Series(dtype=float),
            "wind_dir_deg": pd.Series(dtype=float),
            "gust_kt": pd.Series(dtype=float),
        })
    output = []
    for row in selected.itertuples():
        reports = weather.loc[weather.time <= row.time]
        usable = None
        if not reports.empty and row.time - reports.time.iloc[-1] <= pd.Timedelta(hours=1):
            latest = reports.iloc[-1]
            usable = r18_usable(latest.wind_kt, latest.wind_dir_deg, latest.gust_kt)
        output.append({"time": utc_text(row.time), "od": row.od,
                       "r18_usable": None if usable is None else bool(usable)})
    return output


def briefing_settings():
    values = {}
    for path in (live.ROOT / "web/.env.local", live.ROOT / ".env.local"):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            name, separator, value = line.strip().removeprefix("export ").partition("=")
            name = name.strip()
            if separator and name in ("OPENAI_API_KEY", "OPENAI_MODEL"):
                value = value.strip()
                if value.startswith(("'", '"')):
                    end = value.find(value[0], 1)
                    if end < 0:
                        continue
                    value = value[1:end]
                else:
                    value = value.split(" #", 1)[0].strip()
                values.setdefault(name, value)
    return tuple(os.environ.get(name, values.get(name, "")).strip()
                 for name in ("OPENAI_API_KEY", "OPENAI_MODEL"))


def tower_briefing(result):
    """Optional narration; failures never affect the computed forecast."""
    try:
        key, model = briefing_settings()
        if not key or not model:
            return None
        from openai import AsyncOpenAI

        certainties = [hour["certainty"] for hour in result["hours"]]
        summary = {"current_od": result["current_od"], "next_change": result["next_change"],
                   "runway": "18", "closures_18": result["closures_18"],
                   "certainty_percent_range": [min(certainties), max(certainties)]}
        prompt = json.dumps(summary, separators=(",", ":"), allow_nan=False)

        async def request():
            async with asyncio.timeout(8):
                async with AsyncOpenAI(api_key=key, timeout=8.0, max_retries=0) as client:
                    return await client.responses.create(
                        model=model, store=False, input=prompt,
                        instructions="Brief tower staff in at most 2 sentences of plain English. "
                        "Use only the given values. Never invent numbers, times, probabilities or facts; "
                        "do not convert or calculate new numbers or spell out new quantities. "
                        "Summarize current OD, the next change and its window/probability if present, "
                        "runway 18 inferred weather closures, and certainty. Preserve uncertainty. "
                        "Do not give operational clearance or instructions. Return only the briefing.")

        response = asyncio.run(request())
        text = response.output_text.strip()
        numbers = lambda value: set(re.findall(r"\d+(?:\.\d+)?", value))
        if (not text or key in text or not numbers(text).issubset(numbers(prompt))
                or len(re.split(r"(?<=[.!?])\s+", text)) > 2):
            return None
        return text
    except Exception:
        return None


def build_forecast(day=None, *, now=None, include_observed=True, include_briefing=True):
    issue, mode, now = issue_time(day, now=now)
    cutoff = min(issue, now.floor("h"))
    obs = live.metar_until(cutoff)
    history = live.recorded_history()
    current_od, provenance = current_direction(obs, history, cutoff)
    nwp, source = live.archived_weather(issue) if mode == "hindcast" else live.live_weather(issue, now)
    if (obs.time > issue).any() or (pd.to_datetime(nwp.available_at, utc=True) > issue).any():
        raise ValueError("Input availability exceeds issue time")
    # Supply only completed, known hourly states to the predictor's optional history.
    known = history.loc[history.available_at <= cutoff, ["time", "od", "available_at"]]
    if len(known):
        # Parquet observations may be nanosecond-resolution while CSV history is
        # microsecond-resolution; merge_asof requires matching datetime dtypes.
        merge_left = obs.sort_values("time").copy()
        merge_right = known.rename(columns={"time": "od_time"}).copy()
        merge_left["time"] = merge_left["time"].astype("datetime64[ns, UTC]")
        merge_right["available_at"] = merge_right["available_at"].astype("datetime64[ns, UTC]")
        obs = pd.merge_asof(merge_left, merge_right,
                            left_on="time", right_on="available_at", direction="backward")
    obs.attrs["od_history"] = known.copy()
    frame, version = predict(issue, obs, nwp, current_od)
    hours = format_hours(frame, issue)
    note = None
    if day is not None and day > issue.tz_convert(BERLIN).date():
        requested_hours = [hour for hour in hours
                           if pd.Timestamp(hour["time"]).tz_convert(BERLIN).date() == day]
        if not requested_hours:
            raise ValueError("Requested day does not intersect the current 48-hour forecast horizon")
        note = (f"Requested {day}; it falls within the current 48-hour forecast issued at "
                f"{local_text(issue)}. Showing the full 48-hour horizon.")
    result = {"issued_at": utc_text(issue), "issued_local": local_text(issue), "mode": mode,
              "current_od": current_od, "nwp": source + "; " + provenance + "; runway 18 usability inferred",
              "model_version": version, "rules_version": RULES["version"], "hours": hours,
              "next_change": next_change(hours, current_od), "closures_18": closures(hours)}
    if note:
        result["note"] = note
    if mode == "hindcast" and include_observed:
        result["observed"] = observed_overlay(issue, history)
    if "model_sha256" in frame.attrs:
        result["evidence"] = evidence(frame, hours, issue, obs, known, nwp, current_od, provenance)
    result["briefing"] = tower_briefing(result) if include_briefing else None
    return result


def score_forecasts(start, end):
    """Score midnight local issues on matched DFLD hours, without future inputs.

    Runs with repeated 10 kt rule disagreements are a sensitivity flag from
    ml.quality.suspect_od_runs, not evidence that the recorded feed failed.
    Scores are reported with all recorded labels and with flagged hours excluded.
    """
    if start > end:
        raise ValueError("--from must be on or before --to")
    today = datetime.now(tz=BERLIN).date()
    if end >= today:
        raise ValueError("Scoring requires past issue days")
    history = live.recorded_history()
    suspect = suspect_od_runs(history, live.normalize_metar(pd.read_parquet(live.DATA / "eddf_metar.parquet")))
    truth = history.set_index("time").od
    suspect_times = set(history.loc[suspect, "time"])
    labels_all = ("1", "1-6", "7-24", "25-48")
    totals = {scope: {label: {"model": 0, "rules": 0, "persistence": 0, "n": 0} for label in labels_all}
              for scope in ("clean", "all")}
    days = excluded = 0
    for day in pd.date_range(start, end, freq="D"):
        result = build_forecast(day.date(), include_observed=False, include_briefing=False)
        if "fallback" in result["model_version"]:
            raise ValueError(f"Cannot score {day.date()}: trained model unavailable")
        matched = 0
        issue = pd.Timestamp(result["issued_at"])
        known = history.loc[history.available_at <= issue]
        stuck_input = len(known) and known.time.iloc[-1] in suspect_times
        for hour in result["hours"]:
            time = pd.Timestamp(hour["time"])
            observed = truth.get(time)
            if observed not in ("25", "07"):
                continue
            label = "1-6" if hour["lead_h"] <= 6 else "7-24" if hour["lead_h"] <= 24 else "25-48"
            labels = ("1", label) if hour["lead_h"] == 1 else (label,)
            stuck = stuck_input or time in suspect_times
            scopes = ("all",) if stuck else ("clean", "all")
            excluded += stuck
            for scope in scopes:
                for key in labels:
                    bucket = totals[scope][key]
                    bucket["model"] += int(hour["od"] == observed)
                    bucket["rules"] += int(hour["rule_od"] == observed)
                    bucket["persistence"] += int(result["current_od"] == observed)
                    bucket["n"] += 1
            matched += 1
        if not matched:
            raise ValueError(f"No recorded DFLD hours for issue day {day.date()}")
        days += 1

    def rows(scope):
        output = []
        for lead, counts in totals[scope].items():
            if not counts["n"]:
                raise ValueError(f"No recorded DFLD hours for leads {lead}")
            output.append({"lead": lead, **{name: counts[name] / counts["n"]
                                           for name in ("model", "rules", "persistence")}, "n": counts["n"]})
        return output

    clean, everything = rows("clean"), rows("all")
    return {"days": days, "rows": everything[1:], "lead_1": everything[0], "stuck_feed_hours": excluded,
            "rows_stuck_feed_excluded": clean[1:], "lead_1_stuck_feed_excluded": clean[0]}


def print_score(result):
    print(f"Hourly OD hit rate against recorded DFLD | {result['days']} daily issues at 00:00 Europe/Berlin")
    print("Leads | model | rules | persistence | matched hours")
    for row in result["rows"]:
        print(f"{row['lead']:>5} | {row['model']:6.1%} | {row['rules']:6.1%} | "
              f"{row['persistence']:11.1%} | {row['n']}")
    first = result["lead_1"]
    print(f"Lead 1 only | model {first['model']:.1%} | rules {first['rules']:.1%} | "
          f"persistence {first['persistence']:.1%} | {first['n']} matched hours")
    print("The 1-6 band combines six leads; compare backtest lead 1 with 'Lead 1 only'.")
    if result["stuck_feed_hours"]:
        print(f"Sensitivity excluding {result['stuck_feed_hours']} matched hours flagged for repeated "
              "10 kt landing-limit disagreement (not evidence of feed failure):")
        for row in result["rows_stuck_feed_excluded"] + [result["lead_1_stuck_feed_excluded"]]:
            print(f"{row['lead']:>5} | {row['model']:6.1%} | {row['rules']:6.1%} | "
                  f"{row['persistence']:11.1%} | {row['n']}")
    print("Only recorded target hours are scored; overlapping daily forecast windows count separately.")


def print_table(result):
    print(f"EDDF | issued {result['issued_local']} Europe/Berlin | {result['mode']} | {result['model_version']}")
    print(result["nwp"])
    if result.get("note"):
        print(f"Note: {result['note']}")
    print("Local time        | OD | P(OD25) | P(18 usable) | certainty | rule OD | rule 18 | wind deg/kt/gust")
    for hour in result["hours"]:
        direction = "VRB" if hour["wind_dir_deg"] is None else f"{hour['wind_dir_deg']:.0f}"
        print(f"{hour['local']} | {hour['od']:>2} | {hour['p_od25']:7.1%} | {hour['p_18_usable']:12.1%} | "
              f"{hour['certainty']:8d}% | {hour['rule_od']:>7} | {'open' if hour['rule_18_usable'] else 'closed':>7} | "
              f"{direction}/{hour['wind_kt']:.1f}/{hour['gust_kt']:.1f}")
    change = result["next_change"]
    print(f"Next change: {change['from']} -> {change['to']} at {change['local']} "
          f"(window {change['window_local'][0]} to {change['window_local'][1]})" if change else "Next change: none in 48 hours")
    print("Runway 18 closures (inferred weather usability):")
    for closure in result["closures_18"]:
        print(f"  {closure['local_start']} to {closure['local_end']}; minimum P(usable) {closure['min_p_usable']:.1%}")
    if not result["closures_18"]:
        print("  None in 48 hours")
    if result.get("briefing"):
        print(result["briefing"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--day", type=date.fromisoformat)
    group.add_argument("--now", action="store_true")
    group.add_argument("--score", action="store_true")
    parser.add_argument("--from", type=date.fromisoformat, dest="start")
    parser.add_argument("--to", type=date.fromisoformat, dest="end")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.score and (args.start is None or args.end is None):
        parser.error("--score requires --from and --to")
    if not args.score and (args.start is not None or args.end is not None):
        parser.error("--from and --to require --score")
    try:
        result = score_forecasts(args.start, args.end) if args.score else build_forecast(args.day)
        payload = json.dumps(result, indent=2, allow_nan=False) + "\n"
        destination = args.out or (live.ROOT / "web/public/data/october.json" if args.score else None)
        if destination:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(payload, encoding="utf-8")
        if args.as_json:
            print(payload, end="")
        elif args.score:
            print_score(result)
        else:
            print_table(result)
    except (ValueError, KeyError, OSError, requests.RequestException) as error:
        print(f"Forecast unavailable: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

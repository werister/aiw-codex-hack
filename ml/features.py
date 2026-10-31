"""Shared issue-time feature construction for training and the 48-hour forecast."""

import warnings
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from ml.rules import RULES, od_state_machine, r18_usable, tailwind

BERLIN = ZoneInfo("Europe/Berlin")
PUBLICATION_LAG_H = 6
WIND_COLUMNS = {"wind_speed_10m": "wind_kt", "wind_direction_10m": "wind_dir_deg",
                "wind_gusts_10m": "gust_kt"}
MULTIMODELS = ("ecmwf_ifs025", "gfs_seamless", "icon_seamless")
# METAR / forecast mean wind speed, fitted on 2024 only, before every walk-forward test month.
WIND_SCALE = {"best_match": 1.684, "ecmwf_ifs025": 1.273, "gfs_seamless": 1.344,
              "icon_seamless": 1.684, "80m": 0.829}
BASE_FEATURES = ["od_at_issue", "hours_since_change", "obs_wind_kt", "obs_gust_kt",
                 "obs_tailwind_25", "obs_tailwind_18", "wind_trend_3h", "tailwind_trend_3h",
                 "wind_kt", "gust_kt", "wind_sin", "wind_cos", "tailwind_25_kt",
                 "tailwind_07_kt", "tailwind_18_kt", "rule_od25", "rule_18_usable",
                 "hour_sin", "hour_cos", "season_sin", "season_cos", "lead_h",
                 "pressure_msl", "temperature_2m", "wind_speed_80m"]
ENSEMBLE_FEATURES = ([f"{model}_tailwind_{runway}" for model in MULTIMODELS for runway in ("25", "18")]
                     + ["ens_tailwind_25_mean", "ens_tailwind_25_std", "ens_tailwind_18_mean",
                        "ens_tailwind_18_std", "ens_dir_spread", "ens_votes_25", "tailwind_25_80m",
                        "tailwind_18_80m", "rule_od25_ens", "rule_18_ens"])
# Pressure about 200 km north, south, west and east of FRA (ml/synoptic.py).
SYNOPTIC_FEATURES = ["dp_ns", "dp_ew", "geo_tailwind_25", "geo_tailwind_18"]
FEATURES = BASE_FEATURES + ENSEMBLE_FEATURES + SYNOPTIC_FEATURES


def utc(value):
    value = pd.Timestamp(value)
    if value.tzinfo is None:
        raise ValueError("issue times must have an explicit timezone")
    return value.tz_convert("UTC")


def normalize_obs(obs):
    obs = obs.rename(columns={"valid": "time", "drct": "wind_dir_deg", "sknt": "wind_kt",
                              "gust": "gust_kt"}).copy()
    obs["time"] = pd.to_datetime(obs.time, utc=True)
    if "gust_kt" not in obs:
        obs["gust_kt"] = obs.wind_kt
    for column in ("wind_dir_deg", "wind_kt", "gust_kt"):
        obs[column] = pd.to_numeric(obs[column], errors="coerce")
    obs["gust_kt"] = obs.gust_kt.fillna(obs.wind_kt)
    keys = ["time", "retrieved_at"] if "retrieved_at" in obs else ["time"]
    return obs.dropna(subset=["wind_kt"]).sort_values(keys, kind="stable").drop_duplicates("time", keep="last")


def observations_available_at(obs, issue):
    """Keep only observations that existed by issue time, before resolving duplicates."""
    issue = utc(issue)
    frame = obs.rename(columns={"valid": "time"}).copy().reset_index(drop=True)
    if "retrieved_at" in frame:
        retrieved = pd.to_datetime(frame["retrieved_at"], utc=True, errors="coerce")
        if retrieved.isna().any():
            raise ValueError("Explicit METAR retrieved_at metadata must be valid")
        frame = frame.loc[retrieved <= issue].copy()
        frame["retrieved_at"] = retrieved.loc[frame.index]
    frame = normalize_obs(frame)
    return frame.loc[frame.time <= issue].copy()


def tailwind_since_issue(issue, observations, current_od, od_history=None):
    """Return the start of the current observed positive-tailwind run, if known.

    Use only observations available at issue time and at most five hours of
    history. Gaps longer than one METAR interval break continuity. A known OD
    change also caps the run; unavailable or contradictory states fail closed.
    """
    issue = utc(issue)
    if current_od not in ("25", "07"):
        raise ValueError("current_od must be '25' or '07'")
    known = observations_available_at(observations, issue)
    if known.empty:
        return None
    latest = known.time.iloc[-1]
    if issue - latest > pd.Timedelta(minutes=30):
        return None
    start = issue - pd.Timedelta(hours=5)
    if od_history is not None and not od_history.empty:
        history = od_history.copy()
        history["time"] = pd.to_datetime(history.time, utc=True, errors="coerce")
        history["available_at"] = pd.to_datetime(history.available_at, utc=True, errors="coerce")
        if history[["time", "available_at"]].isna().any().any():
            raise ValueError("OD history timestamps must be valid")
        history = history.loc[(history.available_at <= issue) & (history.time <= issue)]
        history = history.sort_values("time", kind="stable")
        changes = history.od.ne(history.od.shift())
        if len(changes):
            changes.iloc[0] = False
        if changes.any():
            start = max(start, history.loc[changes, "available_at"].iloc[-1])
    known = known.loc[known.time >= start]
    if known.empty or known.time.iloc[-1] != latest:
        return None

    heading = RULES["runway_heading_deg"][current_od]
    since = None
    previous = None
    for row in known.itertuples(index=False):
        time = row.time
        if previous is not None and time - previous > pd.Timedelta(minutes=30):
            since = None
        previous = time
        direction = row.wind_dir_deg
        speed = row.wind_kt
        component = tailwind(speed, direction, heading) if pd.notna(direction) else float("nan")
        if not np.isfinite(component) or speed <= 0 or component <= 1e-9:
            since = None
        elif since is None:
            since = time
    return since


def components(speed, direction, heading):
    # Unknown direction remains missing, rather than becoming an invented wind.
    return speed * np.cos(np.deg2rad(direction - heading - 180))


def nwp_offset_days(lead_h):
    """Smallest offset N with lead_h <= 24*N minus the publication lag."""
    return (lead_h + PUBLICATION_LAG_H + 23) // 24


def select_nwp(issue, nwp):
    """Select day1 for 1..18, day2 for 19..42, day3 for 43..48.

    Offset availability is a proxy, not a verified publication timestamp. Explicit
    issued_at/retrieved_at metadata, when provided, must precede issue time.
    """
    targets = pd.date_range(issue + pd.Timedelta(hours=1), periods=48, freq="h")
    source = nwp.copy().reset_index(drop=True)
    source["time"] = pd.to_datetime(source.time, utc=True)
    archived = "wind_speed_10m_previous_day1" in source
    availability = [name for name in ("issued_at", "retrieved_at") if name in source]
    if availability:
        for stamp in availability:
            source[stamp] = pd.to_datetime(source[stamp], utc=True, errors="coerce")
            if source[stamp].isna().any():
                raise ValueError(f"Explicit forecast {stamp} metadata must be valid")
        available = source[availability].max(axis=1)
        source["_available_at"] = available
        # A row is eligible only if every supplied availability time has passed.
        eligible = pd.Series(True, index=source.index)
        for stamp in availability:
            eligible &= source[stamp].le(issue)
        source = source.loc[eligible].sort_values(["_available_at", "time"], kind="stable")
    elif not archived:
        if not availability:
            raise ValueError("Non-offset forecasts need issued_at or retrieved_at")
    source = source.drop_duplicates("time", keep="last").set_index("time").reindex(targets)
    output = pd.DataFrame({"time": targets, "lead_h": np.arange(1, 49)})
    output["nwp_offset_days"] = nwp_offset_days(output.lead_h) if archived else 0
    for name, destination in WIND_COLUMNS.items():
        if archived:
            output[destination] = np.select(
                [output.nwp_offset_days.eq(day) for day in (1, 2, 3)],
                [source.get(f"{name}_previous_day{day}", np.nan) for day in (1, 2, 3)], default=np.nan)
        else:
            column = destination if destination in source else name
            output[destination] = source[column].to_numpy()
    def pick(name):
        if archived:
            return np.select([output.nwp_offset_days.eq(day) for day in (1, 2, 3)],
                             [source.get(f"{name}_previous_day{day}", np.nan) for day in (1, 2, 3)], default=np.nan)
        return source[name].to_numpy() if name in source else np.full(len(output), np.nan)

    for name in ("pressure_msl", "temperature_2m", "wind_speed_80m"):
        output[name] = pick(name)
    output["wind_dir_80m"] = pick("wind_direction_80m")
    for side in "nswe":
        output[f"pressure_{side}"] = pick(f"pressure_{side}")
    # Separate models are optional inputs; missing ones stay NaN, never another model.
    for model in MULTIMODELS:
        output[f"{model}_kt"] = pick(f"{model}__wind_speed_10m")
        output[f"{model}_dir"] = pick(f"{model}__wind_direction_10m")
    if output[["wind_kt", "gust_kt", "wind_dir_deg"]].isna().any().any():
        raise ValueError("Incomplete 48-hour forecast wind coverage")
    if availability:
        output["nwp_available_proxy"] = source["_available_at"].to_numpy()
    elif archived:
        output["nwp_available_proxy"] = (output.time - pd.to_timedelta(output.nwp_offset_days, unit="D")
                                         + pd.Timedelta(hours=PUBLICATION_LAG_H))
    else:
        output["nwp_available_proxy"] = (output.time - pd.to_timedelta(output.nwp_offset_days, unit="D")
                                         + pd.Timedelta(hours=PUBLICATION_LAG_H))
    return output


def build_features(issue_time_utc, obs, nwp, od_at_issue, od_history=None):
    """Build a full trajectory. od_history has time, od, available_at columns.

    DFLD hourly summaries become available no earlier than time + 1 hour.
    Actual reporting delays are unknown and disclosed in evaluation metadata.
    """
    issue = utc(issue_time_utc)
    if od_at_issue not in ("25", "07"):
        raise ValueError("od_at_issue must be '25' or '07'")
    observations = observations_available_at(obs, issue)
    if observations.empty or issue - observations.time.iloc[-1] > pd.Timedelta(hours=2):
        raise ValueError("No METAR within two hours before issue")
    now = observations.iloc[-1]
    past = observations.loc[observations.time <= issue - pd.Timedelta(hours=3)]
    old = past.iloc[-1] if len(past) and issue - past.time.iloc[-1] <= pd.Timedelta(hours=5) else None
    frame = select_nwp(issue, nwp)
    frame["issue_time"] = issue
    frame["obs_time_max"] = now.time
    frame["od_at_issue"] = int(od_at_issue == "25")
    frame["hours_since_change"] = np.nan
    frame["od_available_max"] = pd.NaT
    if od_history is not None:
        history = od_history.loc[pd.to_datetime(od_history.available_at, utc=True) <= issue].copy()
        if len(history):
            history = history.sort_values("time")
            changed = history.od.ne(history.od.shift())
            # The initial state is left-censored, not a recorded change.
            changed.iloc[0] = False
            if changed.any():
                frame["hours_since_change"] = (issue - pd.Timestamp(history.loc[changed, "available_at"].iloc[-1])).total_seconds() / 3600
            frame["od_available_max"] = history.available_at.iloc[-1]
    frame["obs_wind_kt"] = now.wind_kt
    frame["obs_gust_kt"] = now.gust_kt
    for runway in ("25", "07", "18"):
        heading = RULES["runway_heading_deg"][runway]
        frame[f"tailwind_{runway}_kt"] = components(frame.wind_kt, frame.wind_dir_deg, heading)
    frame["obs_tailwind_25"] = components(now.wind_kt, now.wind_dir_deg, RULES["runway_heading_deg"]["25"])
    frame["obs_tailwind_18"] = components(now.wind_kt, now.wind_dir_deg, RULES["runway_heading_deg"]["18"])
    frame["wind_trend_3h"] = now.wind_kt - old.wind_kt if old is not None else np.nan
    frame["tailwind_trend_3h"] = (frame.obs_tailwind_25 - components(old.wind_kt, old.wind_dir_deg,
        RULES["runway_heading_deg"]["25"])) if old is not None else np.nan
    # Seed at issue time from the known observation, retaining the supplied OD.
    # Future forecast wind is never assumed to have started at T.
    rows = list(frame[["time", "wind_dir_deg", "wind_kt", "gust_kt"]].itertuples(index=False, name=None))
    timer = tailwind_since_issue(issue, observations, od_at_issue, od_history)
    frame["rule_od"] = od_state_machine(rows, initial_od=od_at_issue, tailwind_since=timer)
    frame["rule_od25"] = frame.rule_od.eq("25").astype(int)
    frame["rule_18_usable"] = [r18_usable(s, d, g) for _, d, s, g in rows]
    frame["persistence_18"] = r18_usable(now.wind_kt, now.wind_dir_deg, now.gust_kt)
    add_ensemble(frame, od_at_issue, timer)
    frame["wind_sin"] = np.sin(np.deg2rad(frame.wind_dir_deg))
    frame["wind_cos"] = np.cos(np.deg2rad(frame.wind_dir_deg))
    local = frame.time.dt.tz_convert(BERLIN)
    frame["hour_sin"] = np.sin(2 * np.pi * local.dt.hour / 24)
    frame["hour_cos"] = np.cos(2 * np.pi * local.dt.hour / 24)
    frame["season_sin"] = np.sin(2 * np.pi * local.dt.dayofyear / 365.25)
    frame["season_cos"] = np.cos(2 * np.pi * local.dt.dayofyear / 365.25)
    return frame


def add_ensemble(frame, od_at_issue, tailwind_since=None):
    """Bias-corrected per-model runway components, model spread and rule states.

    Speeds are scaled to METAR level with WIND_SCALE. The ensemble mean wind
    drives a second run of the official state machine from the issue-time OD.
    """
    headings = RULES["runway_heading_deg"]
    names = ["best_match", *MULTIMODELS]
    speed = np.column_stack([frame.wind_kt.to_numpy(float) * WIND_SCALE["best_match"]]
                            + [frame[f"{m}_kt"].to_numpy(float) * WIND_SCALE[m] for m in MULTIMODELS])
    direction = np.column_stack([frame.wind_dir_deg.to_numpy(float)]
                                + [frame[f"{m}_dir"].to_numpy(float) for m in MULTIMODELS])
    tail = {runway: components(speed, direction, headings[runway]) for runway in ("25", "18")}
    for index, model in enumerate(names[1:], 1):
        for runway in ("25", "18"):
            frame[f"{model}_tailwind_{runway}"] = tail[runway][:, index]
    with np.errstate(invalid="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        for runway in ("25", "18"):
            frame[f"ens_tailwind_{runway}_mean"] = np.nanmean(tail[runway], axis=1)
            frame[f"ens_tailwind_{runway}_std"] = np.nanstd(tail[runway], axis=1)
        radians = np.deg2rad(direction)
        frame["ens_dir_spread"] = 1 - np.hypot(np.nanmean(np.sin(radians), axis=1), np.nanmean(np.cos(radians), axis=1))
        frame["ens_votes_25"] = np.nanmean(np.where(np.isnan(tail["25"]), np.nan, tail["25"] <= 0), axis=1)
        # Mean wind vector (direction the wind blows from) across available models.
        u = np.nanmean(-speed * np.sin(radians), axis=1)
        v = np.nanmean(-speed * np.cos(radians), axis=1)
    mean_speed = np.hypot(u, v)
    mean_direction = np.where(mean_speed > 0, np.rad2deg(np.arctan2(-u, -v)) % 360, np.nan)
    rows = [(time, None if np.isnan(d) else float(d), float(s), float(s))
            for time, d, s in zip(frame.time, mean_direction, np.nan_to_num(mean_speed))]
    frame["rule_od25_ens"] = [int(od == "25") for od in od_state_machine(rows, initial_od=od_at_issue,
                                                                           tailwind_since=tailwind_since)]
    gust = frame.gust_kt.to_numpy(float) * WIND_SCALE["best_match"]
    frame["rule_18_ens"] = [np.nan if usable is None else float(usable)
                            for usable in (r18_usable(s, d, g) for (_, d, s, _), g in zip(rows, gust))]
    # Geostrophic flow: u ~ -(p_north - p_south), v ~ (p_east - p_west); air moves toward heading.
    frame["dp_ns"] = frame.pressure_n - frame.pressure_s
    frame["dp_ew"] = frame.pressure_e - frame.pressure_w
    for runway in ("25", "18"):
        heading = np.deg2rad(headings[runway])
        frame[f"geo_tailwind_{runway}"] = -frame.dp_ns * np.sin(heading) + frame.dp_ew * np.cos(heading)
    speed_80m = frame.wind_speed_80m.to_numpy(float) * WIND_SCALE["80m"]
    for runway in ("25", "18"):
        frame[f"tailwind_{runway}_80m"] = components(speed_80m, frame.wind_dir_80m.to_numpy(float), headings[runway])

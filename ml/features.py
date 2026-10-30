"""Shared issue-time feature construction for training and the 48-hour forecast."""

from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from ml.rules import RULES, od_state_machine, r18_usable

BERLIN = ZoneInfo("Europe/Berlin")
WIND_COLUMNS = {"wind_speed_10m": "wind_kt", "wind_direction_10m": "wind_dir_deg",
                "wind_gusts_10m": "gust_kt"}
FEATURES = ["od_at_issue", "hours_since_change", "obs_wind_kt", "obs_gust_kt",
            "obs_tailwind_25", "obs_tailwind_18", "wind_trend_3h", "tailwind_trend_3h",
            "wind_kt", "gust_kt", "wind_sin", "wind_cos", "tailwind_25_kt",
            "tailwind_07_kt", "tailwind_18_kt", "rule_od25", "rule_18_usable",
            "hour_sin", "hour_cos", "season_sin", "season_cos", "lead_h",
            "pressure_msl", "temperature_2m", "wind_speed_80m"]


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
    return obs.dropna(subset=["wind_kt"]).sort_values("time").drop_duplicates("time", keep="last")


def components(speed, direction, heading):
    # Unknown direction remains missing, rather than becoming an invented wind.
    return speed * np.cos(np.deg2rad(direction - heading - 180))


def select_nwp(issue, nwp):
    """Select day1 for 1..24, day2 for 25..48; never substitute day0.

    Offset availability is a proxy, not a verified publication timestamp. Explicit
    issued_at/retrieved_at metadata, when provided, must precede issue time.
    """
    targets = pd.date_range(issue + pd.Timedelta(hours=1), periods=48, freq="h")
    source = nwp.copy()
    source["time"] = pd.to_datetime(source.time, utc=True)
    archived = "wind_speed_10m_previous_day1" in source
    if not archived:
        stamp = "issued_at" if "issued_at" in source else "retrieved_at"
        if stamp not in source:
            raise ValueError("Non-offset forecasts need issued_at or retrieved_at")
        source[stamp] = pd.to_datetime(source[stamp], utc=True)
        source = source.loc[source[stamp] <= issue].sort_values(stamp)
    source = source.drop_duplicates("time", keep="last").set_index("time").reindex(targets)
    output = pd.DataFrame({"time": targets, "lead_h": np.arange(1, 49)})
    output["nwp_offset_days"] = np.where(output.lead_h <= 24, 1, 2) if archived else 0
    for name, destination in WIND_COLUMNS.items():
        if archived:
            output[destination] = np.where(output.lead_h <= 24,
                source[name + "_previous_day1"], source[name + "_previous_day2"])
        else:
            column = destination if destination in source else name
            output[destination] = source[column].to_numpy()
    for name in ("pressure_msl", "temperature_2m", "wind_speed_80m"):
        if archived:
            output[name] = np.where(output.lead_h <= 24,
                source.get(name + "_previous_day1", np.nan),
                source.get(name + "_previous_day2", np.nan))
        else:
            output[name] = source[name].to_numpy() if name in source else np.nan
    if output[["wind_kt", "gust_kt", "wind_dir_deg"]].isna().any().any():
        raise ValueError("Incomplete 48-hour archived wind coverage")
    if archived:
        output["nwp_available_proxy"] = output.time - pd.to_timedelta(output.nwp_offset_days, unit="D")
    else:
        output["nwp_available_proxy"] = source[stamp].to_numpy()
    return output


def build_features(issue_time_utc, obs, nwp, od_at_issue, od_history=None):
    """Build a full trajectory. od_history has time, od, available_at columns.

    DFLD hourly summaries become available no earlier than time + 1 hour.
    Actual reporting delays are unknown and disclosed in evaluation metadata.
    """
    issue = utc(issue_time_utc)
    if od_at_issue not in ("25", "07"):
        raise ValueError("od_at_issue must be '25' or '07'")
    observations = normalize_obs(obs)
    observations = observations.loc[observations.time <= issue]
    if "retrieved_at" in observations:
        observations = observations.loc[pd.to_datetime(observations.retrieved_at, utc=True) <= issue]
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
    frame["rule_od"] = od_state_machine(rows, initial_od=od_at_issue)
    frame["rule_od25"] = frame.rule_od.eq("25").astype(int)
    frame["rule_18_usable"] = [r18_usable(s, d, g) for _, d, s, g in rows]
    frame["persistence_18"] = r18_usable(now.wind_kt, now.wind_dir_deg, now.gust_kt)
    frame["wind_sin"] = np.sin(np.deg2rad(frame.wind_dir_deg))
    frame["wind_cos"] = np.cos(np.deg2rad(frame.wind_dir_deg))
    local = frame.time.dt.tz_convert(BERLIN)
    frame["hour_sin"] = np.sin(2 * np.pi * local.dt.hour / 24)
    frame["hour_cos"] = np.cos(2 * np.pi * local.dt.hour / 24)
    frame["season_sin"] = np.sin(2 * np.pi * local.dt.dayofyear / 365.25)
    frame["season_cos"] = np.cos(2 * np.pi * local.dt.dayofyear / 365.25)
    return frame

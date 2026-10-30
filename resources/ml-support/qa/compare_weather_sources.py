"""Compare archived wind with nearby-in-time observations; no airport labels or ML."""
import bisect
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def dt(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def number(value):
    return float(value) if value not in ('', None) else None


def summary(values):
    if not values:
        return {'n': 0, 'bias_kn': None, 'mae_kn': None, 'rmse_kn': None}
    return {
        'n': len(values),
        'bias_kn': sum(values) / len(values),
        'mae_kn': sum(abs(x) for x in values) / len(values),
        'rmse_kn': math.sqrt(sum(x*x for x in values) / len(values)),
    }


def main():
    obs_path = ROOT / 'observations/eddf_metar_observations.csv'
    forecast_path = ROOT / 'forecast/normalized/open-meteo-icon-global.csv'
    with obs_path.open(newline='') as stream:
        observations = list(csv.DictReader(stream))
    with forecast_path.open(newline='') as stream:
        forecasts = list(csv.DictReader(stream))
    grouped = defaultdict(list)
    for row in observations:
        grouped[dt(row['observation_time_utc'])].append(row)
    times = sorted(grouped)
    ages = Counter()
    excluded = Counter()
    errors = {day: {'speed': [], 'reported_gust': [], 'vector_distance': []} for day in (1, 2, 3)}
    cases = []
    for forecast in forecasts:
        target = dt(forecast['time_utc'])
        index = bisect.bisect_right(times, target) - 1
        if index < 0:
            excluded['no_prior_observation'] += 1
            continue
        observed_time = times[index]
        age = (target-observed_time).total_seconds()/60
        if age > 60:
            excluded['observation_older_than_60_minutes'] += 1
            continue
        candidates = grouped[observed_time]
        signatures = {(r['wind_direction_deg'], r['wind_speed_kt'], r['wind_gust_kt'], r['wind_direction_status'], r['wind_gust_status']) for r in candidates}
        if len(signatures) != 1:
            excluded['conflicting_observations_at_same_time'] += 1
            continue
        observation = candidates[0]
        assert observed_time <= target
        ages[str(age)] += 1
        speed = number(observation['wind_speed_kt'])
        direction = number(observation['wind_direction_deg'])
        gust = number(observation['wind_gust_kt'])
        for day in errors:
            fspeed = number(forecast[f'wind_speed_10m_previous_day{day}_kn'])
            fdir = number(forecast[f'wind_direction_10m_previous_day{day}_deg'])
            fgust = number(forecast[f'wind_gusts_10m_previous_day{day}_kn'])
            if speed is not None and fspeed is not None:
                errors[day]['speed'].append(fspeed-speed)
            if gust is not None and fgust is not None and observation['wind_gust_status'] == 'REPORTED':
                errors[day]['reported_gust'].append(fgust-gust)
            if None not in (speed, direction, fspeed, fdir):
                u = -speed*math.sin(math.radians(direction))
                v = -speed*math.cos(math.radians(direction))
                fu = -fspeed*math.sin(math.radians(fdir))
                fv = -fspeed*math.cos(math.radians(fdir))
                errors[day]['vector_distance'].append(math.hypot(fu-u, fv-v))
        if gust is not None:
            cases.append({'target_time_utc': forecast['time_utc'], 'observation_time_utc': observation['observation_time_utc'], 'reported_gust_kn': gust, 'observed_speed_kn': speed, 'observed_direction_deg': direction})
    result = {
        'purpose': 'Source-data diagnostic, not model/airport-operation accuracy or a fixed-issue-time backtest',
        'inputs_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (obs_path, forecast_path)},
        'forecast_hours': len(forecasts),
        'paired_hours': sum(ages.values()),
        'observation_age_minutes_counts': dict(sorted(ages.items())),
        'excluded': dict(excluded),
        'by_previous_day_offset': {},
        'largest_reported_gust_cases': sorted(cases, key=lambda r: (-r['reported_gust_kn'], r['target_time_utc']))[:12],
        'limitations': [
            'Pairs use the most recent observation at or before forecast valid time, at most 60 minutes old. They are targets for this diagnostic, never issue-time predictor features.',
            'Model grid wind and airport observations have different spatial and temporal sampling.',
            'Gust errors use only explicitly reported gust cases, a selected subset; they do not estimate all-hour gust accuracy.',
            'Day offsets are API archive bands, not verified exact forecast initialization times or model skill at 1/6/24h.',
            'No forecast source or parameters were selected by optimizing these diagnostic metrics.',
        ],
    }
    for day, values in errors.items():
        vectors = values['vector_distance']
        result['by_previous_day_offset'][str(day)] = {
            'speed_error': summary(values['speed']),
            'reported_gust_error': summary(values['reported_gust']),
            'wind_vector_mean_distance_kn': sum(vectors)/len(vectors) if vectors else None,
            'wind_vector_n': len(vectors),
        }
    (ROOT / 'qa/source-comparison.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

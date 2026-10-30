#!/usr/bin/env python3
"""Reproduce wind-source comparability diagnostics; no fitting or calibration."""
import argparse
import bisect
import csv
import hashlib
import json
import math
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
LOCAL = ZoneInfo('Europe/Berlin')
MPS_TO_KT = 1.9438444924406
WIND_FIELDS = [
    f'{base}_previous_day{day}'
    for day in (1, 2, 3)
    for base in ('wind_speed_10m', 'wind_direction_10m', 'wind_gusts_10m')
]
UNITS = {
    'wind_speed_10m': 'kn', 'wind_direction_10m': '°', 'wind_gusts_10m': 'kn',
    'pressure_msl': 'hPa', 'temperature_2m': '°C',
}
WIND_GROUP = re.compile(r'^(?P<dir>VRB|\d{3})(?P<speed>\d{2,3})(?:G(?P<gust>\d{2,3}))?KT$')
SPEED_BANDS = ((0, 5, '[0,5)'), (5, 10, '[5,10)'), (10, 15, '[10,15)'),
               (15, math.inf, '[15,∞)'))
SECTORS = ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW')


def dt(text):
    value = datetime.fromisoformat(text.replace('Z', '+00:00'))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def num(value):
    return float(value) if value not in ('', None) else None


def read_csv(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def summary(errors):
    if not errors:
        return {'n': 0, 'bias_kn': None, 'mae_kn': None, 'rmse_kn': None}
    return {
        'n': len(errors),
        'bias_kn': sum(errors) / len(errors),
        'mae_kn': sum(abs(error) for error in errors) / len(errors),
        'rmse_kn': math.sqrt(sum(error * error for error in errors) / len(errors)),
    }


def raw_forecast_check(support, normalized):
    normalized_by_time = {dt(row['time_utc']): row for row in normalized}
    checked_rows = checked_values = mismatches = 0
    unit_mismatches = []
    timezone_mismatches = []
    coordinate_mismatches = []
    raw_paths = sorted((support / 'forecast/raw/previous-runs').glob('*.json'))
    for path in raw_paths:
        raw = json.loads(path.read_text())
        hourly = raw['hourly']
        if raw.get('utc_offset_seconds') != 0:
            timezone_mismatches.append(path.name)
        if (raw.get('latitude'), raw.get('longitude')) != (50.0, 8.625):
            coordinate_mismatches.append(path.name)
        for field in hourly:
            if field == 'time':
                continue
            base = field.rsplit('_previous_day', 1)[0]
            if raw.get('hourly_units', {}).get(field) != UNITS[base]:
                unit_mismatches.append((path.name, field, raw.get('hourly_units', {}).get(field)))
        for i, stamp in enumerate(hourly['time']):
            key = dt(stamp)
            row = normalized_by_time.get(key)
            if row is None:
                mismatches += len(WIND_FIELDS)
                continue
            checked_rows += 1
            for field in WIND_FIELDS:
                base = field.rsplit('_previous_day', 1)[0]
                raw_value = hourly[field][i]
                norm_value = num(row[f'{field}_' + {'wind_speed_10m': 'kn',
                                                     'wind_direction_10m': 'deg',
                                                     'wind_gusts_10m': 'kn'}[base]])
                checked_values += 1
                if (raw_value is None) != (norm_value is None):
                    mismatches += 1
                elif raw_value is not None and abs(float(raw_value) - norm_value) > 1e-9:
                    mismatches += 1
    return {
        'raw_month_files': len(raw_paths), 'raw_hour_rows_compared': checked_rows,
        'raw_wind_values_compared': checked_values, 'value_mismatches': mismatches,
        'unit_mismatches': unit_mismatches, 'utc_offset_mismatches': timezone_mismatches,
        'grid_coordinate_mismatches': coordinate_mismatches,
        'raw_units_expected': {'speed': 'kn', 'direction': '°', 'gust': 'kn'},
        'all_requested_fields_units_validated': bool(raw_paths) and not unit_mismatches,
    }


def raw_metar_check(observations):
    checked = errors = unit_mismatches = 0
    issue_counts = Counter()
    for row in observations:
        if row.get('raw_wind_group_unit') != 'KT':
            unit_mismatches += 1
        match = WIND_GROUP.match(row.get('raw_wind_group', ''))
        if not match:
            issue_counts['unparsed_raw_wind_group'] += 1
            continue
        checked += 1
        speed = float(match.group('speed'))
        gust = float(match.group('gust')) if match.group('gust') else None
        direction = match.group('dir')
        if num(row['wind_speed_kt']) != speed:
            errors += 1
            issue_counts['speed_mismatch'] += 1
        if num(row['wind_gust_kt']) != gust:
            errors += 1
            issue_counts['gust_mismatch'] += 1
        if direction == 'VRB':
            if row['wind_direction_status'] not in ('VARIABLE_VRB', 'VARIABLE_RANGE'):
                errors += 1
                issue_counts['variable_direction_status_mismatch'] += 1
        elif speed > 0 and row['wind_direction_status'] == 'DIRECTIONAL':
            if num(row['wind_direction_deg']) != float(direction):
                errors += 1
                issue_counts['direction_mismatch'] += 1
    return {'raw_wind_groups_parsed': checked, 'raw_group_value_mismatches': errors,
            'non_KT_unit_rows': unit_mismatches, 'issues': dict(issue_counts)}


def sector(direction):
    return SECTORS[int(((direction + 22.5) % 360) // 45)]


def bucket_speed(speed):
    for low, high, label in SPEED_BANDS:
        if low <= speed < high:
            return label
    return 'outside_expected_range'


def percentile(sorted_values, fraction):
    if not sorted_values:
        return None
    index = (len(sorted_values) - 1) * fraction
    lo, hi = math.floor(index), math.ceil(index)
    if lo == hi:
        return sorted_values[lo]
    return sorted_values[lo] * (hi - index) + sorted_values[hi] * (index - lo)


def daily_block_bootstrap(pairs, replicates, seed):
    daily = defaultdict(list)
    for pair in pairs:
        daily[pair['target'].date().isoformat()].append(pair['error'])
    days = sorted(daily)
    if not days:
        return {'days': 0, 'replicates': 0, 'ci95_kn': [None, None]}
    means_counts = [(sum(daily[day]), len(daily[day])) for day in days]
    rng = random.Random(seed)
    intervals = {}
    for block_length in (1, 3, 7):
        estimates = []
        for _ in range(replicates):
            total, count, sampled = 0.0, 0, 0
            while sampled < len(days):
                start = rng.randrange(max(1, len(days) - block_length + 1))
                take = min(block_length, len(days) - sampled)
                for index in range(start, start + take):
                    day_sum, day_count = means_counts[index]
                    total += day_sum
                    count += day_count
                sampled += take
            estimates.append(total / count)
        estimates.sort()
        intervals[str(block_length)] = [percentile(estimates, .025), percentile(estimates, .975)]
    return {'days': len(days), 'replicates_per_block_length': replicates,
            'ci95_kn_by_block_length_days': intervals,
            'method': 'moving UTC day-block bootstrap; contiguous blocks sampled with replacement; final block truncated'}


def dwd_diagnostic(support, observations):
    path = support / 'observations/dwd_01420_hourly_wind_gust_overlap.csv'
    rows = read_csv(path)
    obs_by_time = defaultdict(list)
    for row in observations:
        obs_by_time[dt(row['observation_time_utc'])].append(row)
    obs_times = sorted(obs_by_time)
    errors_by_shift = {-1: [], 0: [], 1: []}
    counts_by_shift = {-1: Counter(), 0: Counter(), 1: Counter()}
    missing_dwd = 0
    qn3 = Counter()
    conversion_errors = []
    for row in rows:
        target = dt(row['timestamp_utc'])
        qn3[row.get('wind_quality_qn_3', '')] += 1
        dwd = num(row['wind_mean_kt'])
        ms = num(row['wind_mean_ms'])
        if dwd is not None and ms is not None:
            conversion_errors.append(abs(dwd - ms * MPS_TO_KT))
        if dwd is None:
            missing_dwd += 1
            continue
        # 01420 metadata gives a UTC averaging period but does not unambiguously
        # map each period to the row label. A related official DWD hourly-wind
        # description uses SYNOP timing and places the hour's mean 10 minutes
        # before the label. Use that as the central working interpretation and
        # show +/-1h sensitivity, rather than treating it as confirmed for 01420.
        for shift in errors_by_shift:
            window_start = target - timedelta(minutes=70) + timedelta(hours=shift)
            window_end = target - timedelta(minutes=10) + timedelta(hours=shift)
            # The lower endpoint's 10-minute METAR period falls just before the
            # DWD interval; include the upper endpoint.
            first = bisect.bisect_right(obs_times, window_start)
            last = bisect.bisect_right(obs_times, window_end)
            window_obs = [item for stamp in obs_times[first:last] for item in obs_by_time[stamp]]
            speeds = [num(item['wind_speed_kt']) for item in window_obs]
            speeds = [value for value in speeds if value is not None]
            if len(speeds) != 2:
                counts_by_shift[shift]['non_two_point_metar_window'] += 1
                continue
            errors_by_shift[shift].append(sum(speeds) / len(speeds) - dwd)
    return {
        'source': 'DWD station 01420 hourly mean versus two METAR speed samples',
        'dwd_rows': len(rows), 'central_working_window_utc': '(t-70min, t-10min], 10-minute report timestamps',
        'window_interpretation': 'Related DWD SYNOP convention used as a working interpretation; exact 01420 row mapping is not confirmed.',
        'metar_minus_dwd_two_point_mean_by_hour_shift': {
            str(shift): {
                'metar_minus_dwd': summary(errors_by_shift[shift]),
                'window_utc': f'(t{shift:+d}h-70min, t{shift:+d}h-10min]',
                'excluded_windows': dict(counts_by_shift[shift]),
            }
            for shift in errors_by_shift
        },
        'missing_dwd_mean_rows': missing_dwd, 'dwd_qn3_counts': dict(qn3),
        'conversion_ms_to_kn_max_abs_error': max(conversion_errors, default=None),
        'limitations': [
            'Two METAR reports are a sparse sample, not six DWD 10-minute means and not a time-weighted METAR hourly mean.',
            'DWD 01420 is a separate DWD data product/station record named Frankfurt/Main; coordinate proximity does not prove METAR sensor identity or equivalence.',
            'The t-70..t-10 window is a working interpretation only; +/-1h sensitivity exposes timestamp uncertainty.',
        ],
    }


def icon_vs_dwd_diagnostic(support, forecasts):
    path = support / 'observations/dwd_01420_hourly_wind_gust_overlap.csv'
    forecast_by_time = {dt(row['time_utc']): row for row in forecasts}
    errors = {shift: {day: [] for day in (1, 2, 3)} for shift in (-1, 0, 1)}
    excluded = Counter()
    with path.open(newline='') as stream:
        dwd_rows = list(csv.DictReader(stream))
    for row in dwd_rows:
        target = dt(row['timestamp_utc'])
        speed = num(row['wind_mean_kt'])
        if speed is None:
            excluded['missing_dwd_mean'] += 1
            continue
        for shift in errors:
            forecast = forecast_by_time.get(target + timedelta(hours=shift))
            if forecast is None:
                excluded[f'no_forecast_for_shift_{shift:+d}h'] += 1
                continue
            for day in errors[shift]:
                value = num(forecast[f'wind_speed_10m_previous_day{day}_kn'])
                if value is not None:
                    errors[shift][day].append(value - speed)
    return {
        'paired_rows': len(dwd_rows),
        'matching_rule': 'ICON forecast at DWD UTC label plus shift; forecast speed minus DWD hourly mean',
        'excluded': dict(excluded),
        'by_dwd_label_shift_hours': {
            str(shift): {str(day): summary(values) for day, values in offsets.items()}
            for shift, offsets in errors.items()
        },
        'limitation': 'Timestamp labels and hourly averaging periods may not exactly align; DWD is a separate data product and sensor equivalence is unverified.',
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--support-package', '--support-dir', dest='support_dir', type=Path,
                        help='support package root (default: resources/ml-support or weather)')
    parser.add_argument('--bootstrap-replicates', type=int, default=2000)
    parser.add_argument('--seed', type=int, default=20261030)
    parser.add_argument('--output', type=Path,
                        help='JSON output path (default: report.json beside this script)')
    args = parser.parse_args()
    support = args.support_dir
    if support is None:
        candidates = (HERE.parents[2] / 'resources/ml-support', HERE.parents[2] / 'weather')
        support = next((path for path in candidates if path.is_dir()), None)
        if support is None:
            parser.error('pass --support-package PATH (package with observations/ and forecast/)')
    support = support.resolve()
    obs_path = support / 'observations/eddf_metar_observations.csv'
    forecast_path = support / 'forecast/normalized/open-meteo-icon-global.csv'
    observations = read_csv(obs_path)
    forecasts = read_csv(forecast_path)
    grouped = defaultdict(list)
    for row in observations:
        grouped[dt(row['observation_time_utc'])].append(row)
    obs_times = sorted(grouped)

    pairs = {day: [] for day in (1, 2, 3)}
    excluded = Counter()
    observation_ages = Counter()
    for forecast in forecasts:
        target = dt(forecast['time_utc'])
        index = bisect.bisect_right(obs_times, target) - 1
        if index < 0:
            excluded['no_prior_observation'] += 1
            continue
        observed_time = obs_times[index]
        age_minutes = (target - observed_time).total_seconds() / 60
        if age_minutes > 60:
            excluded['observation_older_than_60_minutes'] += 1
            continue
        candidates = grouped[observed_time]
        signatures = {(row['wind_direction_deg'], row['wind_speed_kt'],
                       row['wind_direction_status'], row['wind_speed_status'])
                      for row in candidates}
        if len(signatures) != 1:
            excluded['conflicting_same_time_observations'] += 1
            continue
        obs = candidates[0]
        observed_speed = num(obs['wind_speed_kt'])
        observed_direction = num(obs['wind_direction_deg'])
        observation_ages[str(age_minutes)] += 1
        local_target = target.astimezone(LOCAL)
        for day in pairs:
            field = f'wind_speed_10m_previous_day{day}_kn'
            forecast_speed = num(forecast[field])
            if observed_speed is None or forecast_speed is None:
                continue
            error = forecast_speed - observed_speed
            item = {'target': target, 'local_target': local_target,
                    'error': error, 'observed_speed': observed_speed,
                    'direction': observed_direction,
                    'direction_status': obs['wind_direction_status'],
                    'age_minutes': age_minutes}
            pairs[day].append(item)

    by_offset = {}
    for day, values in pairs.items():
        group_errors = defaultdict(list)
        for item in values:
            local = item['local_target']
            group_errors[('local_month', local.strftime('%Y-%m'))].append(item['error'])
            group_errors[('utc_hour', f'{item["target"].hour:02d}')].append(item['error'])
            group_errors[('local_hour', f'{local.hour:02d}')].append(item['error'])
            group_errors[('observed_speed_band', bucket_speed(item['observed_speed']))].append(item['error'])
            if item['direction'] is not None and item['direction_status'] == 'DIRECTIONAL':
                group_errors[('observed_direction_sector', sector(item['direction']))].append(item['error'])
        stratified = {}
        for dimension in ('local_month', 'utc_hour', 'local_hour',
                          'observed_direction_sector', 'observed_speed_band'):
            stratified[dimension] = {
                key: summary(errors) for (dim, key), errors in sorted(group_errors.items())
                if dim == dimension
            }
        by_offset[str(day)] = {
            'speed_error_forecast_minus_observation': summary([item['error'] for item in values]),
            'daily_block_bootstrap_95ci': daily_block_bootstrap(values, args.bootstrap_replicates,
                                                                args.seed + day),
            'stratified': stratified,
        }

    report = {
        'scope': 'ICON Global support archive only; this is not the current best_match training path.',
        'diagnostic_only': True,
        'input_sha256': {
            'observations/eddf_metar_observations.csv': hashlib.sha256(obs_path.read_bytes()).hexdigest(),
            'forecast/normalized/open-meteo-icon-global.csv': hashlib.sha256(forecast_path.read_bytes()).hexdigest(),
        },
        'forecast_hours': len(forecasts), 'observation_rows': len(observations),
        'paired_hours': len(pairs[1]), 'observation_age_minutes_counts': dict(sorted(observation_ages.items())),
        'excluded_targets': dict(excluded), 'wind_error_sign': 'forecast speed minus METAR speed; negative means forecast lower',
        'raw_source_integrity': {
            'open_meteo': raw_forecast_check(support, forecasts),
            'metar_wind_groups': raw_metar_check(observations),
        },
        'by_previous_day_offset': by_offset,
        'dwd_cross_check': dwd_diagnostic(support, observations),
        'icon_vs_dwd_same_hour_cross_check': icon_vs_dwd_diagnostic(support, forecasts),
        'limitations': [
            'This is valid-time pairing with the latest METAR at or before the target hour (normally 10 min old), not a forecast issue-time backtest.',
            'Model grid (50.000 N, 8.625 E, 105 m) and EDDF observations differ spatially; sampling methods also differ.',
            'The monthly previous-runs archive does not prove the issue-time availability of each forecast value.',
            'Direction sectors include only DIRECTIONAL METAR reports; calm, VRB and variable-range reports are excluded. Local-hour bins combine repeated Europe/Berlin DST fold hours.',
            'No calibration, feature selection, or model comparison was performed; the direction-specific and strength-specific strata are diagnostic and selected on observed conditions.',
            'The support archive requested ICON Global. Current ml/fetch.py requests best_match; metrics here do not characterize the model currently trained by the app.',
        ],
    }
    output = args.output if args.output is not None else HERE / 'report.json'
    if not output.is_absolute():
        output = Path.cwd() / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(output)
    print(json.dumps({
        'paired_hours': report['paired_hours'],
        'raw_integrity': report['raw_source_integrity'],
        'offsets': {key: value['speed_error_forecast_minus_observation'] for key, value in by_offset.items()},
        'bootstrap_ci': {key: value['daily_block_bootstrap_95ci'] for key, value in by_offset.items()},
        'dwd_shifts': report['dwd_cross_check']['metar_minus_dwd_two_point_mean_by_hour_shift'],
        'icon_dwd_shifts': report['icon_vs_dwd_same_hour_cross_check']['by_dwd_label_shift_hours'],
    }, indent=2))


if __name__ == '__main__':
    main()

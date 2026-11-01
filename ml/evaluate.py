"""Inspect published scores, or replay saved monthly fits without retraining.

Replay requires lawfully obtained direction labels and the original fitted
artifacts, which are withheld from the public distribution pending permission.
"""

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = ROOT / "web/public/data/quality.json"


def published_summary(path=PUBLISHED):
    quality = json.loads(Path(path).read_text(encoding="utf-8"))
    return {
        "source": "published historical evaluation; not recomputed predictions",
        "model_version": quality["model_version"],
        "evaluation": quality["evaluation"],
        "folds": len(quality["folds"]),
        "od": quality["significance"]["od"],
        "next_change": quality["next_change"],
        "od_change_events": quality["od_change_events"],
        "r18_events": quality["r18_events"],
        "limitations": quality["limitations"],
    }


def replay():
    """Rebuild inputs and score each saved fit on its original test month."""
    import joblib
    import pandas as pd

    from ml.first_event_experiment import load_half_hour_truth
    from ml.quality import next_change_timing, od_change_events, r18_events
    from ml.significance import compare
    from ml.train import DATA, MODELS, cached_dataset, predict

    required = [DATA / "ground_truth/dfld_hourly.csv",
                DATA / "ground_truth/dfld_half_hourly.csv.gz",
                DATA / "eddf_metar.parquet", DATA / "openmeteo_previous_runs.parquet"]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise ValueError("Replay needs permission-cleared local inputs: " + ", ".join(missing))
    quality = json.loads(PUBLISHED.read_text(encoding="utf-8"))
    frame, _truth, _obs, _skipped = cached_dataset(quality["issue_stride_h"])
    predictions, hashes = [], {}
    for fold in quality["folds"]:
        month = pd.Period(fold["month"], freq="M")
        start = month.start_time.tz_localize("UTC")
        end = (month + 1).start_time.tz_localize("UTC")
        path = MODELS / f"fold-{month}.joblib"
        if not path.exists():
            raise ValueError(f"Replay needs withheld fitted artifact: {path.name}")
        models = joblib.load(path)
        if pd.Timestamp(models["trained_through"]) >= start:
            raise ValueError(f"Training labels cross test boundary: {month}")
        rows = frame.loc[(frame.issue_time >= start) & (frame.issue_time < end)
                         & (frame.label_available_at < end)]
        if len(rows) != fold["test_n"]:
            raise ValueError(f"Original test-row count differs for {month}")
        predictions.append(predict(models, rows))
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        print(f"Replayed {month}: {len(rows):,} rows", flush=True)
    out = pd.concat(predictions, ignore_index=True)
    half_hour, _ = load_half_hour_truth()
    result = {
        "source": "recomputed from saved monthly fits; no fitting performed",
        "model_version": quality["model_version"],
        "folds": len(predictions), "n_prediction_rows": len(out),
        "model_sha256": hashes,
        "od": compare(out, "od"),
        "next_change": next_change_timing(out, half_hour),
        "od_change_events": od_change_events(out, half_hour),
        "r18_events": r18_events(out),
    }
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", action="store_true", help="Requires withheld labels and fits; never trains")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        result = replay() if args.replay else published_summary()
        payload = json.dumps(result, indent=2, allow_nan=False) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(payload, encoding="utf-8")
        print(payload, end="")
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Evaluation unavailable: {error}\n")


if __name__ == "__main__":
    main()

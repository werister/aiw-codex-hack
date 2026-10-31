from datetime import date
import json
from types import SimpleNamespace

import pandas as pd

from ml import fetch


def test_backfill_retains_existing_reports_and_provenance(tmp_path, monkeypatch):
    old = pd.DataFrame({"station": pd.Series(["EDDF"], dtype="string"),
                        "valid": pd.to_datetime(["2024-01-01T00:20Z"]),
                        "drct": [250.], "sknt": [8.], "gust": [None],
                        "metar": pd.Series(["old report"], dtype="string")})
    old.to_parquet(tmp_path / "eddf_metar.parquet", index=False)
    (tmp_path / "inventory.json").write_text(json.dumps({"eddf_metar": {
        "downloads": [{"url": "old", "retrieved_at": "2026-01-01T00:00:00+00:00"}]}}))
    raw = tmp_path / "response.csv"
    raw.write_text("station,valid,drct,sknt,gust,metar\nEDDF,2018-01-01 00:20,90,12,M,older report\n")
    dl = SimpleNamespace(get=lambda *args, **kwargs: raw, used=[{"url": "backfill"}])
    monkeypatch.setattr(fetch, "DATA", tmp_path)
    captured = {}

    def save(frame, *args):
        captured["frame"] = frame.reset_index(drop=True)

    monkeypatch.setattr(fetch, "save", save)
    fetch.fetch_metar(dl, date(2018, 1, 1), date(2019, 1, 1))
    result = captured["frame"]
    assert result.metar.tolist() == ["older report", "old report"]
    assert result.iloc[-1].sknt == 8 and pd.isna(result.iloc[0].gust)
    assert [item["url"] for item in dl.used] == ["old", "backfill"]
    old_downloads = dl.used.copy()
    fetch.fetch_metar(dl, date(2018, 1, 1), date(2019, 1, 1))
    assert dl.used == old_downloads

from datetime import date

import pandas as pd
import pytest

from ml.dfld import hourly, parse_month, retain_existing


def test_display_symbols_do_not_turn_missing_data_into_nonuse():
    directions = ('<img title="00:00 - 00:30: BR07">'
                  '<img title="00:30 - 01:00: BR07">')
    images = ['<img src="Menu/180.gif" title="00:00 - 00:30: 18 West in Betrieb">',
              '<img src="Menu/Undef.gif">', '<img src="Menu/Trans.gif">',
              '<img src="Menu/Trans.gif">'] + ['<img src="Menu/000.gif">'] * 44
    page = f'<tr><td>01.01.2018:</td><td><p></p><p>{directions}</p><p>{"".join(images)}</p></td></tr>'
    od, runway = parse_month(page, "source", date(2018, 1, 1), date(2018, 2, 1))
    assert od.od.tolist() == ["07", "07"]
    assert len(runway) == 48 and runway.r18_in_use.isna().sum() == 3
    hours, excluded = hourly(runway, "r18_in_use", "status changed")
    assert len(hours) == 22 and not hours.r18_in_use.any()
    assert excluded.reason.tolist() == ["missing half hour", "missing half hour"]


def test_hour_end_labels_exclude_changes_and_dst_hours():
    rows = []
    for day, hour, values in [("2024-03-31", 2, ["25", "25"]),
                              ("2024-10-27", 2, ["25", "25"]),
                              ("2024-01-01", 1, ["07", "25"]),
                              ("2024-07-01", 1, ["07", "07"])]:
        rows.extend({"date_local": day, "hour_local": hour, "minute_local": minute,
                     "od": value, "source": "source"} for minute, value in zip((0, 30), values))
    hours, excluded = hourly(pd.DataFrame(rows), "od", "direction differs between half hours")
    assert hours.to_dict("records") == [{"time": "2024-06-30T23:00:00Z", "od": "07", "source": "source"}]
    assert len(excluded) == 3


def test_backfill_preserves_existing_labels_and_rejects_disagreement(tmp_path):
    path = tmp_path / "hourly.csv"
    old = pd.DataFrame({"time": ["2024-01-01T00:00:00Z"], "od": ["07"], "source": ["source"]})
    old.to_csv(path, index=False)
    merged = retain_existing(path, old.copy(), ["time"], dtype={"od": str})
    pd.testing.assert_frame_equal(merged.reset_index(drop=True), old)
    with pytest.raises(ValueError, match="disagrees"):
        retain_existing(path, old.assign(od="25"), ["time"], dtype={"od": str})

import contextlib
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests

from ml import windy


TEST_KEY = "windy-test-fixture-key"
BASE_TS = int(datetime(2026, 10, 30, tzinfo=timezone.utc).timestamp() * 1000)
HOUR_MS = 3_600_000
WEATHER_SENTINELS = (123.456789, -234.567891, 345.678912, 45678.90123)


def response_payload(timestamps=None):
    timestamps = timestamps or [BASE_TS + step * HOUR_MS for step in range(3)]
    return {
        "ts": timestamps,
        "units": dict(windy.UNITS),
        "wind_u-surface": [WEATHER_SENTINELS[0]] * len(timestamps),
        "wind_v-surface": [WEATHER_SENTINELS[1]] * len(timestamps),
        "gust-surface": [WEATHER_SENTINELS[2]] * len(timestamps),
        "pressure-surface": [WEATHER_SENTINELS[3]] * len(timestamps),
    }


def http_response(status=200, payload=None):
    result = Mock()
    result.status_code = status
    result.json.return_value = payload if payload is not None else response_payload()
    return result


class WindyResponseTests(unittest.TestCase):
    def test_connection_returns_only_safe_schema_metadata(self):
        fake_response = http_response()
        with patch.object(windy.requests, "post", return_value=fake_response) as post:
            result = windy.check_connection(TEST_KEY, model="iconEu")

        self.assertEqual(result["provider"], "Windy Point Forecast")
        self.assertEqual(result["purpose"], "connection_test")
        self.assertEqual(result["status"], "ok")
        self.assertFalse(result["operational_use"])
        self.assertTrue(result["warning"].startswith("TEST ONLY:"))
        self.assertEqual(result["location"]["station"], "EDDF")
        self.assertEqual(result["model"], "iconEu")
        self.assertEqual(result["time_steps"], 3)
        self.assertEqual(result["step_hours"], [1.0])
        self.assertEqual(
            result["fields"],
            {name: {"unit": unit, "values": 3, "missing": 0}
             for name, unit in windy.UNITS.items()},
        )
        serialized = json.dumps(result)
        self.assertNotIn(TEST_KEY, serialized)
        for value in WEATHER_SENTINELS:
            self.assertNotIn(str(value), serialized)
        self.assertNotIn("ts", result)

        post.assert_called_once()
        args, kwargs = post.call_args
        self.assertEqual(args, (windy.ENDPOINT,))
        self.assertEqual(kwargs["json"]["key"], TEST_KEY)
        self.assertEqual(kwargs["json"]["model"], "iconEu")
        self.assertEqual(kwargs["allow_redirects"], False)

    def test_nonhourly_timeline_is_reported_without_resampling(self):
        timestamps = [BASE_TS, BASE_TS + 3 * HOUR_MS, BASE_TS + 6 * HOUR_MS]

        result = windy.response_summary(response_payload(timestamps))

        self.assertEqual(result["time_steps"], 3)
        self.assertEqual(result["step_hours"], [3.0])
        self.assertEqual(result["first_time_utc"], "2026-10-30T00:00:00+00:00")
        self.assertEqual(result["last_time_utc"], "2026-10-30T06:00:00+00:00")

    def test_invalid_units_arrays_values_and_timestamps_are_rejected(self):
        cases = []

        missing_units = response_payload()
        missing_units.pop("units")
        cases.append(("missing units", missing_units))

        wrong_unit = response_payload()
        wrong_unit["units"]["wind_u-surface"] = "kn"
        cases.append(("mismatched unit", wrong_unit))

        missing_array = response_payload()
        missing_array.pop("wind_v-surface")
        cases.append(("missing array", missing_array))

        short_array = response_payload()
        short_array["gust-surface"].pop()
        cases.append(("mismatched array length", short_array))

        all_null = response_payload()
        all_null["wind_u-surface"] = [None] * len(all_null["ts"])
        cases.append(("all-null field", all_null))

        nonfinite = response_payload()
        nonfinite["pressure-surface"][0] = float("nan")
        cases.append(("non-finite value", nonfinite))

        duplicate_time = response_payload([BASE_TS, BASE_TS + HOUR_MS, BASE_TS + HOUR_MS])
        cases.append(("duplicate timestamp", duplicate_time))

        for label, payload in cases:
            with self.subTest(label=label), self.assertRaises(windy.WindyError):
                windy.response_summary(payload)


class WindyConfigurationAndCliTests(unittest.TestCase):
    def test_missing_credentials_fails_before_http(self):
        with patch.object(windy.requests, "post") as post:
            with self.assertRaisesRegex(windy.WindyError, windy.KEY_NAME):
                windy.check_connection("")
        post.assert_not_called()

    def test_environment_key_overrides_synthetic_env_local_and_file_is_supported(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            (project_root / ".env.local").write_text(
                f'export {windy.KEY_NAME}="file-test-key"\n', encoding="utf-8"
            )
            with patch.object(windy, "ROOT", project_root):
                with patch.dict(os.environ, {}, clear=True):
                    self.assertEqual(windy.api_key(), "file-test-key")
                with patch.dict(os.environ, {windy.KEY_NAME: "env-test-key"}, clear=True):
                    self.assertEqual(windy.api_key(), "env-test-key")

    def test_auth_rate_limit_server_and_redirect_errors_are_sanitized(self):
        cases = [(400, "HTTP 400"), (401, "HTTP 401"), (403, "HTTP 403"),
                 (429, "HTTP 429"), (503, "HTTP 503"), (302, "HTTP 302")]
        for status, message in cases:
            fake_response = http_response(status)
            fake_response.text = f"provider body includes {TEST_KEY}"
            with self.subTest(status=status), patch.object(
                windy.requests, "post", return_value=fake_response
            ) as post:
                with self.assertRaises(windy.WindyError) as raised:
                    windy.check_connection(TEST_KEY)
                self.assertIn(message, str(raised.exception))
                self.assertNotIn(TEST_KEY, str(raised.exception))
                self.assertNotIn("provider body", str(raised.exception))
                self.assertFalse(post.call_args.kwargs["allow_redirects"])
            fake_response.json.assert_not_called()

    def test_network_failures_are_sanitized(self):
        failures = [
            (requests.Timeout(f"provider detail {TEST_KEY}"), "timed out"),
            (requests.ConnectionError(f"provider detail {TEST_KEY}"), "Cannot connect"),
        ]
        for failure, message in failures:
            with self.subTest(error=type(failure).__name__), patch.object(
                windy.requests, "post", side_effect=failure
            ):
                with self.assertRaises(windy.WindyError) as raised:
                    windy.check_connection(TEST_KEY)
                self.assertIn(message, str(raised.exception))
                self.assertNotIn(TEST_KEY, str(raised.exception))
                self.assertIsNone(raised.exception.__cause__)

    def test_json_cli_marks_output_test_only_and_omits_credentials_and_values(self):
        output = io.StringIO()
        with patch.object(windy, "api_key", return_value=TEST_KEY), patch.object(
            windy.requests, "post", return_value=http_response()
        ), contextlib.redirect_stdout(output):
            status = windy.main(["--json"])

        self.assertEqual(status, 0)
        text = output.getvalue()
        result = json.loads(text)
        self.assertIn("TEST ONLY:", result["warning"])
        self.assertFalse(result["operational_use"])
        self.assertNotIn(TEST_KEY, text)
        for value in WEATHER_SENTINELS:
            self.assertNotIn(str(value), text)


if __name__ == "__main__":
    unittest.main()

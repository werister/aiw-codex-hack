import copy
import json
import unittest
import urllib.error

from tools.forecast_decisions import candidates_for, decision_request, forecast_basis, review_forecast


def fixture():
    return {"issued_at": "2026-10-29T00:00Z", "current_od": "25", "model_version": "test",
            "evidence": {"run_id": "test-run"},
            "rules_version": "test", "nwp": "Test weather", "next_change": None, "closures_18": [],
            "hours": [{"time": f"2026-10-29T0{i}:00Z", "lead_h": i, "od": od,
                       "p_od25": p, "p_18_usable": r18, "rule_od": rule, "rule_18_usable": usable}
                      for i, od, p, r18, rule, usable in [(1, "25", .9, .9, "25", True),
                                                         (2, "07", .2, .2, "25", False),
                                                         (3, "07", .1, .1, "07", False)]],
            "observed": [{"secret_future_label": "MUST_NOT_BE_SENT"}]}


class PlanningReviewTests(unittest.TestCase):
    def test_competing_events_and_disagreement_are_retained(self):
        candidates = candidates_for(fixture())
        by_id = {c["id"]: c for c in candidates}
        self.assertEqual(by_id["direction-1"]["action"], "review")
        self.assertEqual(by_id["runway18-1"]["hour_indices"], [1, 2])
        self.assertIn("disagreement-1", by_id)

    def test_outcomes_are_not_inputs(self):
        f = fixture()
        body = decision_request(forecast_basis(f), candidates_for(f), "test")
        self.assertNotIn("MUST_NOT_BE_SENT", json.dumps(body))
        self.assertNotIn("observed", body["input"][0]["content"][0]["data"]["forecast"])

    def test_partial_day_does_not_invent_a_change_in_the_gap(self):
        f = fixture()
        f["hours"] = f["hours"][1:]
        self.assertFalse(any(c["kind"] == "direction" for c in candidates_for(f)))

    def test_rejects_invalid_probabilities_and_time_alignment(self):
        for field, value in [("p_od25", float("nan")), ("p_18_usable", 1.2), ("lead_h", 4)]:
            f = fixture()
            f["hours"][0][field] = value
            with self.assertRaises(ValueError):
                candidates_for(f)

    def test_refused_unknown_and_missing_answers_fall_back(self):
        for payload in (None, [], {"answers": [None, None]}, {"answers": []}, {"answers": [{"name": "ground_operations", "type": "refusal"},
                          {"name": "forecast_review", "type": "choice", "choice": "invented", "confidence": .9}]}):
            r = review_forecast(fixture(), model="test", key="test", call=lambda *_: payload)
            self.assertEqual(r["status"], "fallback")
            self.assertEqual(r["selections"]["forecast_review"]["candidate_id"], "disagreement-1")

    def test_missing_provenance_has_an_explicit_review_candidate(self):
        f = fixture()
        del f["evidence"]
        r = review_forecast(f, model="test", offline=True)
        self.assertEqual(r["selections"]["forecast_review"]["candidate_id"], "provenance")

    def test_single_supported_issue_needs_no_api_call(self):
        f = fixture()
        f["hours"] = f["hours"][:1]
        def unexpected(*_):
            self.fail("A single candidate requires no external selection")
        r = review_forecast(f, model="test", key="test", call=unexpected)
        self.assertEqual(r["status_reason"], "single_candidate")
        self.assertEqual(r["selections"]["ground_operations"]["candidate_id"], "monitor")

    def test_authentication_failure_is_diagnosable_without_response_body(self):
        def fail(*_):
            raise urllib.error.HTTPError("https://example.invalid", 401, "private details", {}, None)
        r = review_forecast(fixture(), model="test", key="private-key", call=fail)
        self.assertEqual(r["status_reason"], "api_http_401")
        self.assertNotIn("private", json.dumps(r))

    def test_success_can_select_later_focus_without_modifying_forecast(self):
        f = fixture()
        original = copy.deepcopy(f)
        payload = {"id": "test-response", "answers": [
            {"type": "choice", "name": "ground_operations", "choice": "runway18-1", "confidence": .8},
            {"type": "choice", "name": "forecast_review", "choice": "disagreement-1", "confidence": .9}]}
        r = review_forecast(f, model="test", key="test", call=lambda *_: payload)
        self.assertEqual(r["status"], "decisions")
        self.assertEqual(r["selections"]["ground_operations"]["candidate_id"], "runway18-1")
        self.assertEqual(f, original)
        self.assertNotIn("MUST_NOT_BE_SENT", json.dumps(r))

    def test_network_error_does_not_leak_provider_body(self):
        def fail(*_):
            raise urllib.error.URLError("private provider diagnostics")
        r = review_forecast(fixture(), model="test", key="private-key", call=fail)
        self.assertEqual(r["status"], "fallback")
        self.assertNotIn("private", json.dumps(r))


if __name__ == "__main__":
    unittest.main()

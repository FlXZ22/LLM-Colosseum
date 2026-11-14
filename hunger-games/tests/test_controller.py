# This file was written with a help of an ai

import random
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from agents.controller import BudgetCall, Controller

VALID = ("Success", '{"action":"REST","target":null,"reason":"Recover"}', 200)
TRANSIENT = [
    ("Timeout", None, None),
    ("ConnectionError", None, None),
    *[(f"Error: {code}", None, code) for code in (429, 500, 502, 503, 504)],
]
BAD_CONTENT = [
    ("NullContent", None, 200),
    ("JsonError", None, 200),
    ("Success", '{"action":', 200),
    ("Success", "I choose to rest.", 200),
    ("Success", "I cannot answer this request.", 200),
    ("Success", "{}", 200),
    ("Success", '{"action":"FLY"}', 200),
    ("Success", '{"action":"ATTACK","target":"Ghost"}', 200),
    ("Success", '{"action":"ATTACK","target":null}', 200),
]


class TestController(unittest.TestCase):
    def setUp(self):
        self.controller = Controller(random.Random(0))
        # Minimal inputs: a full Game would create unnecessary files and state.
        self.obs = SimpleNamespace(
            legal_actions=["REST", "ATTACK", "FLEE"],
            legal_targets={"ATTACK": ["Bob"], "FLEE": ["Bob"]},
            to_prompt=Mock(return_value="You are hurt. Bob is nearby."),
        )
        self.agent = SimpleNamespace(
            profile=SimpleNamespace(to_prompt=Mock(return_value="Stay alive."))
        )
        self.budget = BudgetCall(0, 10)
        # Replace ask where the controller uses it, not in llm.request.
        api_patch = patch("agents.controller.ask")
        self.ask = api_patch.start()
        self.addCleanup(api_patch.stop)
        sleep_patch = patch("agents.controller.time.sleep")
        self.sleep = sleep_patch.start()
        self.addCleanup(sleep_patch.stop)

    def choose(self):
        return self.controller.choose_action(self.obs, self.agent, self.budget)

    def prepare_case(self, outcomes):
        self.ask.reset_mock()
        self.sleep.reset_mock()
        self.budget = BudgetCall(0, 10)
        self.ask.side_effect = outcomes

    def assert_legal_fallback(self, intent):
        self.assertTrue(intent.is_random)
        self.assertIn(intent.action, self.obs.legal_actions)
        if intent.action in self.obs.legal_targets:
            self.assertIn(intent.target, self.obs.legal_targets[intent.action])
        else:
            self.assertIsNone(intent.target)
        self.assertTrue(intent.reason)

    def test_first_try_success(self):
        self.ask.return_value = VALID
        intent = self.choose()
        self.assertEqual((intent.action, intent.target), ("REST", None))
        self.assertEqual(intent.reason, "Recover")
        self.assertFalse(intent.is_random)
        self.assertEqual(self.budget.used, 1)
        self.ask.assert_called_once()
        self.sleep.assert_not_called()

    def test_valid_target_is_preserved(self):
        self.ask.return_value = (
            "Success", '{"action":"ATTACK","target":"Bob"}', 200
        )
        intent = self.choose()
        self.assertEqual((intent.action, intent.target), ("ATTACK", "Bob"))
        self.assertFalse(intent.is_random)
        self.ask.assert_called_once()

    def test_transient_failures_retry_then_fall_back(self):
        for failure in TRANSIENT:
            with self.subTest(failure=failure):
                self.prepare_case([failure, failure])
                intent = self.choose()
                self.assert_legal_fallback(intent)
                fragment = {
                    "Timeout": "timeout", "ConnectionError": "connection",
                    "Error: 503": "service",
                }.get(failure[0], str(failure[2]))
                self.assertIn(fragment, intent.reason.lower())
                self.assertEqual(self.ask.call_count, 2)
                self.assertEqual(self.budget.used, 2)
                self.sleep.assert_called_once_with(1)

    def test_transient_failure_then_success(self):
        for failure in TRANSIENT:
            with self.subTest(failure=failure):
                self.prepare_case([failure, VALID])
                intent = self.choose()
                self.assertFalse(intent.is_random)
                self.assertEqual(intent.action, "REST")
                self.assertEqual(self.ask.call_count, 2)
                self.assertEqual(self.budget.used, 2)
                self.sleep.assert_called_once_with(1)

    def test_permanent_http_errors_are_not_retried(self):
        for code in (400, 401, 402, 403, 404):
            with self.subTest(status_code=code):
                failure = (f"Error: {code}", None, code)
                self.prepare_case([failure, failure])
                intent = self.choose()
                self.assert_legal_fallback(intent)
                self.assertIn(str(code), intent.reason)
                self.assertEqual(self.ask.call_count, 1)
                self.assertEqual(self.budget.used, 1)
                self.sleep.assert_not_called()

    def test_bad_content_retries_then_falls_back(self):
        for failure in BAD_CONTENT:
            with self.subTest(failure=failure):
                self.prepare_case([failure, failure])
                intent = self.choose()
                self.assert_legal_fallback(intent)
                self.assertEqual(self.ask.call_count, 2)
                self.assertEqual(self.budget.used, 2)
                self.sleep.assert_not_called()
                if failure[0] == "NullContent":
                    self.assertIn("empty", intent.reason.lower())
                elif failure[0] == "JsonError":
                    self.assertIn("json", intent.reason.lower())
                else:
                    self.assertIn("invalid", intent.reason.lower())

    def test_bad_content_then_success(self):
        for failure in BAD_CONTENT:
            with self.subTest(failure=failure):
                self.prepare_case([failure, VALID])
                intent = self.choose()
                self.assertFalse(intent.is_random)
                self.assertEqual(intent.action, "REST")
                self.assertEqual(self.ask.call_count, 2)
                self.assertEqual(self.budget.used, 2)
                self.sleep.assert_not_called()

    def test_generic_request_failure_is_bounded(self):
        self.ask.return_value = ("RequestException", None, None)
        intent = self.choose()
        self.assert_legal_fallback(intent)
        self.assertIn("request", intent.reason.lower())
        self.assertGreaterEqual(self.ask.call_count, 1)
        self.assertLessEqual(self.ask.call_count, 2)
        self.assertEqual(self.budget.used, self.ask.call_count)

    def test_exhausted_budget_makes_no_api_calls(self):
        self.budget = BudgetCall(3, 3)
        intent = self.choose()
        self.assert_legal_fallback(intent)
        self.assertIn("budget", intent.reason.lower())
        self.assertEqual(self.budget.used, 3)
        self.ask.assert_not_called()
        self.sleep.assert_not_called()

    def test_one_remaining_call_cannot_be_used_twice(self):
        self.budget = BudgetCall(2, 3)
        self.ask.return_value = ("NullContent", None, 200)
        intent = self.choose()
        self.assert_legal_fallback(intent)
        self.assertIn("budget", intent.reason.lower())
        self.assertEqual(self.budget.used, 3)
        self.ask.assert_called_once()
        self.sleep.assert_not_called()

    def test_random_mode_skips_api_and_budget(self):
        self.controller.brain = "random"
        intent = self.choose()
        self.assert_legal_fallback(intent)
        self.assertIn("random", intent.reason.lower())
        self.assertEqual(self.budget.used, 0)
        self.ask.assert_not_called()
        self.sleep.assert_not_called()

    def test_latest_attempt_replaces_previous_http_error(self):
        self.ask.side_effect = [
            ("Error: 429", None, 429),
            ("Success", '{"action":"FLY"}', 200),
        ]
        intent = self.choose()
        self.assert_legal_fallback(intent)
        self.assertIn("invalid", intent.reason.lower())
        self.assertNotIn("429", intent.reason)
        self.assertEqual(self.ask.call_count, 2)
        self.assertEqual(self.budget.used, 2)
        self.sleep.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()

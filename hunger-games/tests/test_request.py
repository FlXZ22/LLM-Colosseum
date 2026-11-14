"""Offline tests for ask(): replace HTTP requests with controlled outcomes.

Run from hunger-games:
    python -m unittest tests.test_request tests.test_controller -v
"""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import requests

from config import balance
from llm.request import ask


class TestRequest(unittest.TestCase):
    def setUp(self):
        # No real HTTP requests can leave ask() during these tests.
        post_patch = patch("llm.request.requests.post")
        self.post = post_patch.start()
        self.addCleanup(post_patch.stop)

    def respond(self, body, status=200):
        self.post.return_value = SimpleNamespace(
            status_code=status, text=json.dumps(body)
        )

    def test_success_preserves_model_text(self):
        content = '{"action":"REST","target":null,"reason":"Recover"}'
        self.respond({"choices": [{"message": {"content": content}}]})
        self.assertEqual(ask("Choose an action"), ("Success", content, 200))
        self.post.assert_called_once()

    def test_request_contains_prompt_model_and_timeout(self):
        self.respond({"choices": [{"message": {"content": "hello"}}]})
        ask("My test prompt")
        self.post.assert_called_once()
        sent = self.post.call_args.kwargs
        payload = json.loads(sent["data"])
        self.assertEqual(sent["url"], balance.URL)
        self.assertEqual(payload["model"], balance.MODEL)
        self.assertEqual(
            payload["messages"], [{"role": "user", "content": "My test prompt"}]
        )
        self.assertEqual(sent["timeout"], 30)

    def test_timeout_variants_are_classified_without_retry(self):
        for exception in (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout,
        ):
            with self.subTest(exception=exception.__name__):
                self.post.reset_mock()
                self.post.side_effect = exception("Simulated timeout")
                self.assertEqual(ask("test"), ("Timeout", None, None))
                self.post.assert_called_once()

    def test_connection_error_is_classified_without_retry(self):
        self.post.side_effect = requests.exceptions.ConnectionError("Offline")
        self.assertEqual(ask("test"), ("ConnectionError", None, None))
        self.post.assert_called_once()

    def test_other_request_error_is_classified_without_retry(self):
        self.post.side_effect = requests.exceptions.RequestException("Failed")
        self.assertEqual(ask("test"), ("RequestException", None, None))
        self.post.assert_called_once()

    def test_http_errors_preserve_status_without_parsing_or_retry(self):
        for status in (400, 401, 402, 403, 404, 408, 429, 500, 502, 503, 504):
            with self.subTest(status=status):
                self.post.reset_mock()
                # Error bodies need not be JSON; status should be sufficient.
                self.post.return_value = SimpleNamespace(
                    status_code=status, text="Not a JSON response"
                )
                self.assertEqual(ask("test"), (f"Error: {status}", None, status))
                self.post.assert_called_once()

    def test_null_missing_empty_and_whitespace_content(self):
        for message in (
            {"content": None}, {}, {"content": ""}, {"content": "   \n\t"}
        ):
            with self.subTest(message=message):
                self.respond({"choices": [{"message": message}]})
                self.assertEqual(ask("test"), ("NullContent", None, 200))

    def test_malformed_provider_json(self):
        for text in ("", "Not JSON", '{"choices":'):
            with self.subTest(text=text):
                self.post.return_value = SimpleNamespace(status_code=200, text=text)
                self.assertEqual(ask("test"), ("JsonError", None, 200))

    def test_invalid_provider_structure(self):
        for body in (
            None, [], {}, {"choices": None}, {"choices": []},
            {"choices": [None]}, {"choices": [{}]},
            {"choices": [{"message": None}]},
            {"choices": [{"message": {"content": 123}}]},
            {"choices": {}},
        ):
            with self.subTest(body=body):
                self.respond(body)
                self.assertEqual(ask("test"), ("JsonError", None, 200))

    def test_model_action_parsing_is_left_to_controller(self):
        # The provider envelope is valid; ask must pass model text onward.
        for content in ('{"action":', '{"action":"FLY"}', "I refuse."):
            with self.subTest(content=content):
                self.respond({"choices": [{"message": {"content": content}}]})
                self.assertEqual(ask("test"), ("Success", content, 200))


if __name__ == "__main__":
    unittest.main()

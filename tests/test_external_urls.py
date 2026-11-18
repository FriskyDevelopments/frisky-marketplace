import argparse
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import urllib.error

from scripts.check_external_urls import (
    check_url, collect_urls, main, positive_timeout, request_status,
)


class ExternalURLTests(unittest.TestCase):
    def test_collects_index_interface_and_mcp_urls_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "plugins.json").write_text(json.dumps({"plugins": [
                {"name": "external", "url": "https://example.com/plugin"},
                {"name": "local", "path": "./local"},
            ]}))
            (root / "local").mkdir()
            (root / "local/kimi.plugin.json").write_text(json.dumps({
                "$schema": "https://example.com/schema",
                "interface": {"websiteURL": "https://example.com", "iconUrl": "icon.svg"},
                "mcpServers": {"remote": {"url": "https://example.com/mcp"},
                               "stdio": {"command": "npx"}},
            }))
            self.assertEqual(collect_urls(root), [
                ("external:index", "https://example.com/plugin", False),
                ("local:websiteURL", "https://example.com", False),
                ("local:mcp:remote", "https://example.com/mcp", True),
            ])

    @patch("scripts.check_external_urls.request_status")
    def test_status_policy(self, request):
        for status in (200, 204, 401, 403, 404, 406, 415, 429, 500, 530):
            for is_mcp in (False, True):
                with self.subTest(status=status, is_mcp=is_mcp):
                    request.return_value = status
                    passed, _ = check_url(("plugin", "https://example.com", is_mcp))
                    expected = status in (200, 204) or (is_mcp and status in (401, 403, 406, 415))
                    self.assertEqual(passed, expected)

    @patch("scripts.check_external_urls.request_status", side_effect=[405, 200])
    def test_head_method_rejection_falls_back_to_get(self, request):
        self.assertTrue(check_url(("icon", "https://example.com/icon", False))[0])
        self.assertEqual([call.args[1] for call in request.call_args_list], ["HEAD", "GET"])

    @patch("scripts.check_external_urls.request_status", return_value=405)
    def test_mcp_method_gate_is_not_a_public_page_success(self, request):
        self.assertTrue(check_url(("mcp", "https://example.com/mcp", True))[0])
        self.assertFalse(check_url(("page", "https://example.com", False))[0])

    @patch("scripts.check_external_urls.request_status")
    def test_invalid_and_credential_urls_are_not_requested(self, request):
        for url in ("http://example.com", "https://", "//example.com", "https://user:placeholder@example.com"):
            self.assertFalse(check_url(("plugin", url, False))[0])
        request.assert_not_called()

    @patch("scripts.check_external_urls.request_status")
    def test_network_errors_fail_without_logging_details(self, request):
        for error in (urllib.error.URLError("private-detail"), TimeoutError("private-detail")):
            request.side_effect = error
            passed, message = check_url(("plugin", "https://example.com", False))
            self.assertFalse(passed)
            self.assertNotIn("private-detail", message)

    @patch("scripts.check_external_urls.urllib.request.urlopen")
    def test_http_errors_are_closed_and_reported_as_status(self, urlopen):
        body = MagicMock()
        urlopen.side_effect = urllib.error.HTTPError("https://example.com", 404, "missing", {}, body)
        self.assertEqual(request_status("https://example.com", "HEAD", 3), 404)
        body.close.assert_called_once()
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 3)

    def test_timeout_must_be_finite_and_positive(self):
        for value in ("0", "-1", "inf", "nan"):
            with self.assertRaises(argparse.ArgumentTypeError):
                positive_timeout(value)
        self.assertEqual(positive_timeout("2.5"), 2.5)

    @patch("scripts.check_external_urls.collect_urls", return_value=[("plugin", "https://example.com", False)])
    @patch("scripts.check_external_urls.check_url")
    @patch("builtins.print")
    @patch("sys.argv", ["check_external_urls.py"])
    def test_exit_code_reports_failures(self, output, check, collect):
        check.return_value = (False, "FAIL plugin")
        self.assertEqual(main(), 1)
        check.return_value = (True, "PASS plugin")
        self.assertEqual(main(), 0)


if __name__ == "__main__":
    unittest.main()

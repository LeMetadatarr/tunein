"""Tests for pluggable HTTP transport."""
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

from tunein import TuneIn
from tunein.transport import default_session


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.text = ""

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


class TestTransportInjection(unittest.TestCase):
    def test_session_injected_into_search(self):
        """An injected session should receive the search/post call."""
        sess = MagicMock()
        sess.post.return_value = _FakeResponse({"body": []})
        sess.get.return_value = _FakeResponse({"body": []})

        client = TuneIn(session=sess)
        result = client.search_stations("anything")

        self.assertEqual(result, [])
        # The Search.ashx POST must have been routed through OUR session
        self.assertTrue(sess.post.called)
        called_url = sess.post.call_args[0][0]
        self.assertIn("Search.ashx", called_url)

    def test_session_injected_into_get_stream_urls(self):
        sess = MagicMock()
        sess.get.return_value = _FakeResponse({"body": []})
        TuneIn.get_stream_urls(
            "http://opml.radiotime.com/Tune.ashx?id=s1", session=sess
        )
        self.assertTrue(sess.get.called)


class TestDefaultSession(unittest.TestCase):
    def test_env_unset_returns_requests_session(self):
        import requests
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TUNEIN_TRANSPORT", None)
            sess = default_session()
        self.assertIsInstance(sess, requests.Session)

    def test_env_other_value_returns_requests_session(self):
        import requests
        with patch.dict(os.environ, {"TUNEIN_TRANSPORT": "something_else"}):
            sess = default_session()
        self.assertIsInstance(sess, requests.Session)

    def test_env_curl_cffi_when_unavailable_falls_back(self):
        """If curl_cffi cannot be imported, fall back to requests.Session."""
        import requests
        # Ensure import fails by inserting a sentinel that raises
        with patch.dict(os.environ, {"TUNEIN_TRANSPORT": "curl_cffi"}):
            with patch.dict(sys.modules, {"curl_cffi": None}):
                sess = default_session()
        self.assertIsInstance(sess, requests.Session)

    def test_env_curl_cffi_when_available_uses_it(self):
        """When TUNEIN_TRANSPORT=curl_cffi and the package imports, use it."""
        # Build a minimal fake curl_cffi module with .requests.Session
        fake_session_instance = MagicMock(name="curl_cffi_session")

        class FakeSession:
            def __init__(self, impersonate=None):
                self.impersonate = impersonate
                # delegate identity check below
                fake_session_instance.impersonate = impersonate

            def __new__(cls, *a, **kw):
                fake_session_instance.impersonate = kw.get("impersonate")
                return fake_session_instance

        fake_curl = types.ModuleType("curl_cffi")
        fake_requests_mod = types.ModuleType("curl_cffi.requests")
        fake_requests_mod.Session = FakeSession
        fake_curl.requests = fake_requests_mod

        with patch.dict(os.environ, {"TUNEIN_TRANSPORT": "curl_cffi"}):
            with patch.dict(
                sys.modules,
                {"curl_cffi": fake_curl, "curl_cffi.requests": fake_requests_mod},
            ):
                sess = default_session()

        self.assertIs(sess, fake_session_instance)
        self.assertEqual(fake_session_instance.impersonate, "chrome")


if __name__ == "__main__":
    unittest.main()

"""Shared pytest config — VCR cassettes for HTTP-backed scraper tests.

Cassettes live under ``test/cassettes/<module>/<test>.yaml`` and replay
real upstream responses captured once. Re-record with::

    pytest --vcr-record=all test/test_*_vcr.py

Live re-validation runs in the nightly CI workflow (no cassettes,
hits real endpoints) so cassette drift surfaces within 24 h.
"""
from __future__ import annotations

import copy
import re
from pathlib import Path

import pytest

# Regex patterns for token scrubbing in response bodies.
_PARTNER_TOK_RE = re.compile(r"partnertok=[A-Za-z0-9._\-]+")
_TD_TOK_RE = re.compile(r"tdtok=[A-Za-z0-9._\-]+")
_JWT_RE = re.compile(
    r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"
)
_CF_BM_RE = re.compile(r"__cf_bm=[^;,\s\"]+")

# Headers to strip entirely from recorded responses.
_STRIP_RESPONSE_HEADERS = {"set-cookie", "Set-Cookie",
                           "x-tunein-trace-id", "x-tunein-span-id",
                           "X-Tunein-Trace-Id", "X-Tunein-Span-Id"}


def _scrub_body(text: str) -> str:
    """Replace live tokens with stable placeholders."""
    text = _PARTNER_TOK_RE.sub("partnertok=<PARTNER_TOKEN>", text)
    text = _TD_TOK_RE.sub("tdtok=<TDTOK>", text)
    text = _JWT_RE.sub("<JWT>", text)
    text = _CF_BM_RE.sub("__cf_bm=<CF_BM>", text)
    return text


def _scrub_response(response):
    """VCR before_record_response hook — redact tokens and cookies."""
    response = copy.deepcopy(response)

    # Scrub response body.
    body = response.get("body", {}).get("string", b"")
    if isinstance(body, bytes):
        try:
            scrubbed = _scrub_body(body.decode("utf-8", errors="replace"))
            response["body"]["string"] = scrubbed.encode("utf-8")
        except Exception:
            pass
    elif isinstance(body, str):
        response["body"]["string"] = _scrub_body(body)

    # Strip sensitive headers.
    headers = response.get("headers", {})
    for h in list(headers.keys()):
        if h in _STRIP_RESPONSE_HEADERS or h.lower() in {
            s.lower() for s in _STRIP_RESPONSE_HEADERS
        }:
            del headers[h]

    return response


@pytest.fixture(scope="module")
def vcr_config():
    return {
        "filter_headers": ["User-Agent", "Cookie", "Authorization"],
        "decode_compressed_response": True,
        "record_mode": "none",
        "before_record_response": _scrub_response,
    }


@pytest.fixture(scope="module")
def vcr_cassette_dir(request):
    return str(Path(request.module.__file__).parent / "cassettes" /
               Path(request.module.__file__).stem)

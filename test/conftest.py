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
from urllib.parse import unquote

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


def _scrub_request(request):
    """VCR before_record_request hook — redact tokens from the stored
    request URI so cassettes never persist live credentials, mirroring
    ``_scrub_body`` for response bodies."""
    request.uri = _scrub_body(request.uri)
    return request


def _query_ignoring_tokens(r1, r2):
    """Custom VCR query matcher.

    TuneIn mints a fresh ``partnertok``/``tdtok`` per request (a
    short-lived JWT), so the query string differs on every real HTTP
    call even for the "same" logical request (e.g. following a
    ``.pls`` playlist URL parsed out of a scrubbed cassette body).
    Compare queries with those volatile params scrubbed instead of
    matching them verbatim.
    """
    # Unquote first: a scrubbed placeholder re-embedded into a URL by a
    # fresh request gets percent-encoded (``%3CPARTNER_TOKEN%3E``) while
    # the same placeholder written into the cassette by a raw string
    # substitution stays literal (``<PARTNER_TOKEN>``) -- normalise
    # before comparing so both forms match.
    return _scrub_body(unquote(r1.uri)) == _scrub_body(unquote(r2.uri))


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
        "before_record_request": _scrub_request,
        "match_on": ["method", "scheme", "host", "port", "path",
                     "query_ignoring_tokens"],
    }


@pytest.fixture(scope="module", autouse=True)
def _register_token_agnostic_matcher(vcr):
    """Register the custom query matcher on the module's VCR instance.

    ``vcr_config``'s ``match_on`` can only reference matchers by name,
    so the callable has to be registered on the ``vcr`` fixture (from
    ``pytest-vcr``) before any cassette is used.
    """
    vcr.register_matcher("query_ignoring_tokens", _query_ignoring_tokens)


@pytest.fixture(scope="module")
def vcr_cassette_dir(request):
    return str(Path(request.module.__file__).parent / "cassettes" /
               Path(request.module.__file__).stem)

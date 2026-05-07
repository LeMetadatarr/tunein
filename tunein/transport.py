"""Pluggable HTTP transport for the TuneIn client.

The :class:`TuneIn` client and :class:`TuneInStation` accept any object
that implements the :mod:`requests` ``Session`` API surface we use
(``get`` and ``post``). This module provides :func:`default_session`
which returns a sensible default:

* If the ``TUNEIN_TRANSPORT`` environment variable is set to
  ``curl_cffi`` *and* the ``curl_cffi`` package is importable, return a
  ``curl_cffi.requests.Session`` impersonating a modern browser.
* Otherwise, return a plain :class:`requests.Session`.

This lets callers opt into a stealthier transport (TLS fingerprint
matching a real browser) for sites that block stock ``requests``,
without taking a hard dependency on ``curl_cffi``.
"""
from __future__ import annotations

import os


def default_session():
    """Return a default session-shaped HTTP client.

    Honours ``TUNEIN_TRANSPORT=curl_cffi`` when ``curl_cffi`` is
    available; falls back to :class:`requests.Session` otherwise.
    """
    transport = (os.environ.get("TUNEIN_TRANSPORT") or "").strip().lower()
    if transport == "curl_cffi":
        try:
            from curl_cffi import requests as curl_requests  # type: ignore
            return curl_requests.Session(impersonate="chrome")
        except Exception:
            pass
    import requests
    return requests.Session()

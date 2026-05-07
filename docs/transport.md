# Transport and Sessions

`tunein/transport.py`

## `default_session()`

`default_session` — `tunein/transport.py:22`

Returns a session-shaped HTTP client. Behaviour depends on the
`TUNEIN_TRANSPORT` environment variable at call time:

| `TUNEIN_TRANSPORT` | Result |
|---|---|
| `curl_cffi` (and package importable) | `curl_cffi.requests.Session(impersonate="chrome")` |
| anything else / unset | `requests.Session()` |

`TuneIn.session` — `tunein/__init__.py:395` — calls `default_session()`
lazily on first use when no session was injected.

## Injecting a Custom Session

Any object that exposes `get(url, **kwargs)` and `post(url, **kwargs)`
with the same signatures as `requests.Session` is accepted.

**Class instantiation:**

```python
import requests
from tunein import TuneIn

s = requests.Session()
s.headers["User-Agent"] = "my-bot/1.0"
client = TuneIn(session=s)
stations = client.search_stations("jazz")
```

**One-shot via classmethod:**

```python
stations = TuneIn.search("jazz", session=s)
featured = TuneIn.featured(session=s)
urls = TuneIn.get_stream_urls(tune_url, session=s)
```

`TuneInStation.enrich()` also reuses the session stored at construction
time (`TuneInStation._session`).

## Stealth Transport

Install the optional extra and set the env var:

```bash
pip install tunein[stealth]
export TUNEIN_TRANSPORT=curl_cffi
```

`curl_cffi` impersonates a real Chrome TLS fingerprint, reducing the
likelihood of being blocked by TuneIn's CDN. Falls back to
`requests.Session()` silently if `curl_cffi` is not importable.

## `_get_session(session)`

`_get_session` — `tunein/__init__.py:8`

Internal helper used by all classmethods. Returns `session` when provided,
otherwise returns the `requests` module itself (which exposes top-level
`get`/`post` helpers compatible with the `Session` duck-type). This
preserves the historical test-patching behaviour (`tunein.requests.get`).

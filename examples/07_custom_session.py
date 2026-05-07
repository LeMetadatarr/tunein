"""07_custom_session.py — inject a custom requests.Session.

TuneIn(session=s) and TuneIn.search(..., session=s) both accept any
object exposing get() and post() in the requests.Session style.

This example injects a Session with a custom User-Agent and a short
timeout enforced via an event hook.

Run:
    python examples/07_custom_session.py
"""

import requests
from tunein import TuneIn

# Build a custom session.
s = requests.Session()
s.headers.update({"User-Agent": "my-radio-app/1.0"})

# --- Option A: instance-level injection (session reused across calls) ---
client = TuneIn(session=s)
stations = client.search_stations("classical music")
print(f"[instance] found {len(stations)} results")

# --- Option B: one-shot classmethod injection ---
stations2 = TuneIn.search("jazz", session=s)
print(f"[classmethod] found {len(stations2)} results")

# --- Stealth transport via env var (no code change needed) ---
# export TUNEIN_TRANSPORT=curl_cffi
# pip install tunein[stealth]
# TuneIn() will then use curl_cffi.requests.Session(impersonate="chrome")
print("\nSet TUNEIN_TRANSPORT=curl_cffi for stealth mode.")

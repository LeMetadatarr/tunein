"""02_featured.py — fetch locally featured / trending stations.

TuneIn's Browse.ashx?c=local returns a curated list of stations relevant
to the server's geo-IP. Results vary by location.

Run:
    python examples/02_featured.py
"""

from tunein import TuneIn

stations = TuneIn.featured()

print(f"Found {len(stations)} featured station variants.\n")

seen = set()
for s in stations:
    if s.station_id not in seen:
        seen.add(s.station_id)
        print(f"[{s.station_id or '?':>8}]  {s.title}")

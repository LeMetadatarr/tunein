"""03_search_with_enrich.py — search with Describe.ashx enrichment.

enrich=True fires one extra Describe.ashx request per unique station to
populate genre, language, country, call-sign, slogan, and frequency.

Run:
    python examples/03_search_with_enrich.py
"""

from tunein import TuneIn

stations = TuneIn.search("jazz radio", enrich=True)

for s in stations:
    raw = s.raw
    print(f"Title     : {s.title}")
    print(f"Station ID: {s.station_id}")
    print(f"Genre     : {raw.get('genre_name', '')}")
    print(f"Language  : {raw.get('language', '')}")
    print(f"Location  : {raw.get('location', '')}")
    print(f"Slogan    : {raw.get('slogan', '')}")
    print(f"Stream    : {s.stream}")
    print()

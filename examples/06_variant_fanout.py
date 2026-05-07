"""06_variant_fanout.py — stream variant fan-out: one station, many Releases.

TuneIn returns multiple stream URLs per station (different codecs and
bitrates). TuneIn._get_stations yields one TuneInStation per URL, so a
single call to search() for a popular station may return 3–5 variants.

This example shows how to group variants by station_id and produce one
Release per variant, which is the correct mediavocab representation
(each Release = a distinct rendition / distribution copy).

Run:
    python examples/06_variant_fanout.py
"""

from collections import defaultdict
from tunein import TuneIn

stations = TuneIn.search("NPR News")

# Group by station_id (or title if id unavailable).
groups = defaultdict(list)
for s in stations:
    key = s.station_id or s.title
    groups[key].append(s)

for station_id, variants in groups.items():
    print(f"Station {station_id} — {len(variants)} variant(s):")
    for v in sorted(variants, key=lambda x: x.bit_rate or 0, reverse=True):
        release = v.to_release()
        print(f"  {release.codec:6s}  {release.bitrate:>5} kbps  {release.uri}")
    print()

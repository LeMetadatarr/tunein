"""01_quickstart.py — search TuneIn and print stream URLs.

Run:
    python examples/01_quickstart.py
"""

from tunein import TuneIn

stations = TuneIn.search("BBC Radio 4")

if not stations:
    print("No results.")
else:
    for s in stations:
        print(f"{s.title:40s}  {s.bit_rate or '?':>5} kbps  {s.media_type or '?':6s}  {s.stream}")

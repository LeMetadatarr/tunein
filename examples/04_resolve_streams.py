"""04_resolve_streams.py — resolve a Tune.ashx URL to direct stream URLs.

TuneIn.get_stream_urls handles:
  - .pls playlists  → fetches File1= and returns the direct URL
  - .m3u playlists  → returned as-is (HLS manifests handled by player)
  - direct URLs     → returned as-is

Run:
    python examples/04_resolve_streams.py
"""

from tunein import TuneIn

# Find the Tune.ashx URL for a station first via search.
stations = TuneIn.search("Radio Paradise")
if not stations:
    print("No results.")
    raise SystemExit(1)

# The raw Tune.ashx URL is in raw["url"] — before stream resolution.
tune_url = stations[0].raw.get("url", "")
print(f"Tune.ashx URL: {tune_url}\n")

entries = TuneIn.get_stream_urls(tune_url)
print(f"Resolved {len(entries)} stream entry/entries:\n")
for e in entries:
    print(f"  {e.get('media_type', '?'):6s}  {e.get('bitrate', '?'):>5} kbps  {e['url']}")

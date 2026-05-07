# TuneIn

Unofficial Python client for the TuneIn OPML API with first-class
[mediavocab](https://github.com/JarbasAl/mediavocab) integration.

## Install

```bash
pip install tunein
```

Stealth transport (TLS fingerprint matching a real browser via
[curl_cffi](https://github.com/lexiforest/curl_cffi)):

```bash
pip install tunein[stealth]
export TUNEIN_TRANSPORT=curl_cffi
```

## Quick Start

```python
from tunein import TuneIn

for station in TuneIn.search("BBC Radio 4"):
    print(station.title, station.stream, station.bit_rate)
```

```bash
tunein search "BBC Radio 4"
tunein search "BBC Radio 4" --format json
```

## Public API

### `TuneIn`

| Method | Description |
|---|---|
| `TuneIn.search(query, enrich=False, session=None)` | Search stations by keyword |
| `TuneIn.featured(enrich=False, session=None)` | Local/featured stations |
| `TuneIn.get_stream_urls(url, session=None)` | Resolve a Tune.ashx URL to playable stream entries |
| `TuneIn(session=s).search_stations(query)` | Instance wrapper — reuses injected session |
| `TuneIn(session=s).featured_stations()` | Instance wrapper |
| `TuneIn(session=s).stream_urls(url)` | Instance wrapper |

`enrich=True` fires an extra `Describe.ashx` call per station to populate
genre, language, country, call-sign, slogan, and frequency. Off by default.

### `TuneInStation`

| Property / Method | Description |
|---|---|
| `.title` | Station display name |
| `.artist` | Broadcaster name |
| `.description` | Subtitle / tagline from search payload |
| `.stream` | Playable stream URL (resolved) |
| `.bit_rate` | Bitrate reported by TuneIn |
| `.media_type` | Codec string (`mp3`, `aac`, `ogg`, …) |
| `.image` | Logo URL |
| `.station_id` | Canonical TuneIn id (e.g. `s12345`) |
| `.match(phrase)` | Fuzzy title score 0–100 |
| `.dict` | Dict snapshot of the above |
| `.enrich()` | Fetch `Describe.ashx` and merge extra metadata in-place; returns `self` |
| `.to_release()` | Return a `mediavocab.Release` |

## Stream URL Resolution

`TuneIn.get_stream_urls(url)` resolves a `Tune.ashx` redirect URL:

1. Fetches `Tune.ashx?render=json` over HTTP then HTTPS.
2. For each stream entry ending in `.pls`, parses `File1=` and replaces
   the entry URL with the real direct stream.
3. `.m3u` playlist URLs and direct streams are returned as-is.

Each entry in the returned list is a dict with keys `url`, `bitrate`,
`media_type`. `TuneIn._get_stations` calls this once per search/browse
result and fans out — one `TuneInStation` per stream variant.

Source: `TuneIn.get_stream_urls` — `tunein/__init__.py:419`

## mediavocab Integration

```python
from tunein import TuneIn

for station in TuneIn.search("BBC Radio 4", enrich=True):
    release = station.to_release()
    print(release.uri)                    # stream URL
    print(release.work.title)             # "BBC Radio 4"
    print(release.work.media_type)        # MediaType.RADIO
    print(release.stream_mode)            # StreamMode.CONTINUOUS
    print(release.work.country)           # "GB"
    print(release.work.language)          # "en"
    print(release.work.content_genres)    # ["news"]
    print(release.work.aka)               # call-sign / alternate name
```

`TuneInStation.to_release()` — `tunein/__init__.py:276`

- Each station is a `Work` with `MediaType.RADIO`.
- Each stream URL becomes a `Release` with `StreamMode.CONTINUOUS`
  (live linear broadcast, not seekable).
- Multiple stream variants (bitrates, codecs) each produce their own
  `Release`; call `to_release()` on every item returned by `search()`.

External ids emitted on both `work` and `release`:

| Key | Source |
|---|---|
| `tunein_station_id` | `guide_id` / `preset_id` |
| `tunein_url` | OPML `Tune.ashx` URL |
| `tunein_web_url` | Public `tunein.com` station page |
| `tunein_logo_url` | Station logo URL |

## Pluggable Session / `TUNEIN_TRANSPORT`

```python
import requests
from tunein import TuneIn

s = requests.Session()
s.headers["User-Agent"] = "my-bot/1.0"
client = TuneIn(session=s)
results = client.search_stations("jazz")
```

`default_session()` — `tunein/transport.py:22` — checks
`TUNEIN_TRANSPORT` at call time:

- `TUNEIN_TRANSPORT=curl_cffi` → `curl_cffi.requests.Session(impersonate="chrome")`
- anything else → `requests.Session()`

The class methods `search`, `featured`, and `get_stream_urls` each accept
`session=` directly for one-shot use without instantiating the class.

## CLI

```
tunein search <query> [--format {table,json}]
```

Table output renders station title as an OSC-8 hyperlink to the stream URL.
Exit code 1 when no results are found.

Source: `tunein/cli.py`, `tunein/subcommands/search.py`

## Docs

See [`/docs/`](docs/) for full reference.

## License

Apache 2.0

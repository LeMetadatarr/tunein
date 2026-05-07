# TuneInStation Reference

`TuneInStation` — `tunein/__init__.py:145`

Wraps a single resolved stream variant from a TuneIn search or browse
result. Multiple `TuneInStation` objects may share the same station
(different bitrates or codecs); each has its own `.stream` URL.

## Constructor

```python
TuneInStation(raw: dict, session=None)
```

`raw` — the merged dict built by `TuneIn._get_stations`. `session` is
forwarded to `enrich()`.

## Properties

| Property | Source key in `raw` | Notes |
|---|---|---|
| `.title` | `title` | Display name (falls back to `current_track` or `text`) |
| `.artist` | `artist` | Broadcaster / station name (`text` field) |
| `.description` | `description` | Subtitle / `subtext` from search |
| `.stream` | `stream` | Resolved playable stream URL |
| `.bit_rate` | `bitrate` | Numeric bitrate or `None` |
| `.media_type` | `media_type` | Codec string: `mp3`, `aac`, `ogg`, `hls`, … |
| `.image` | `image` | Station logo URL |
| `.station_id` | `station_id` or parsed from `url` | Canonical TuneIn id, e.g. `s12345` |

`TuneInStation.station_id` — `tunein/__init__.py:205`

When `station_id` is absent from `raw`, the property parses the `id=`
query parameter from the `Tune.ashx` URL stored in `raw["url"]`.

## Methods

### `.match(phrase=None) -> float`

`TuneInStation.match` — `tunein/__init__.py:178`

Returns a fuzzy match score 0–100 between `phrase` (or `raw["query"]`)
and `.title`. Uses `rapidfuzz` when installed; falls back to
`difflib.SequenceMatcher`.

### `.dict`

`TuneInStation.dict` — `tunein/__init__.py:191`

Returns a plain dict snapshot: `title`, `artist`, `description`, `image`,
`stream`, `bit_rate`, `media_type`, `match`.

### `.enrich() -> TuneInStation`

`TuneInStation.enrich` — `tunein/__init__.py:224`

Fetches `Describe.ashx?id=<station_id>&render=json` and merges the
following keys into `self.raw` without overwriting existing values:

`name`, `call_sign`, `slogan`, `frequency`, `band`, `location`,
`language`, `genre_name`, `genre_id`, `is_music`, `has_schedule`,
`tunein_url`, `logo`, `content_classification`, `twitter_id`,
`description`.

Returns `self`. HTTP failures are swallowed — enrichment is best-effort.

### `.to_release() -> mediavocab.Release`

`TuneInStation.to_release` — `tunein/__init__.py:276`

Converts the station to a `mediavocab.Release`. See
[mediavocab converters](converters.md) for the full field mapping.

## Stream Variant Fan-Out

`TuneIn._get_stations` calls `get_stream_urls` once per station entry and
yields one `TuneInStation` per stream URL. To get a single `Release` per
station, pick the best variant before calling `to_release()`, or call
`to_release()` on all of them and let the consumer select.

```python
# All variants:
releases = [s.to_release() for s in TuneIn.search("jazz")]

# Best by bitrate:
stations = sorted(TuneIn.search("jazz"), key=lambda s: s.bit_rate or 0, reverse=True)
best = stations[0].to_release()
```

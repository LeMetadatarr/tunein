# TuneIn

TuneIn is an unofficial Python client for the TuneIn radio API. It integrates
with [mediavocab](https://github.com/JarbasAl/mediavocab) so callers get
typed, canonical media objects instead of raw API responses.

## Install

```bash
pip install tunein
```

## Usage

### From the command line

`tunein` ships a basic CLI for searching. Output is available in both
`json` and table formats. The default is the table layout.

```bash
tunein search "Radio paradise"
tunein search "Radio paradise" --format json
```

Run `tunein --help` to see the full command list.

### From Python

```python
from tunein import TuneIn

for station in TuneIn.search("BBC Radio 4"):
    print(station.title, station.stream, station.bit_rate)
```

### mediavocab integration

`TuneInStation.to_release()` returns a canonical `mediavocab.Release`. This
lets downstream consumers, such as OCP, recommendation engines, and catalogue
importers, ingest TuneIn data without custom glue code.

Under mediavocab axiom 8 (station identity), each TuneIn channel is a `Work`
with `MediaType.RADIO`. The playable stream URL is a `Release` with
`StreamMode.CONTINUOUS`, since it is a live linear broadcast rather than
seekable on-demand audio.

```python
from tunein import TuneIn

# Fast path: search payload only.
for release in (s.to_release() for s in TuneIn.search("BBC Radio 4")):
    print(release.uri, release.codec, release.bitrate)

# Rich path: opt in to the per-station Describe.ashx call to get
# genre, language, country, call sign, slogan, and more.
for station in TuneIn.search("BBC Radio 4", enrich=True):
    release = station.to_release()
    print(release.work.title)            # "BBC Radio 4"
    print(release.work.country)          # "GB"  (parsed from "London, UK")
    print(release.work.language)         # "en"  (mapped from "English")
    print(release.work.content_genres)   # ["news"]  (mapped to GENRE_NEWS)
    print(release.work.aka)              # ["BBC R4"]   (call sign)
    print(release.codec, release.bitrate)  # "aac", "128"
    print(release.audio_channels)        # "stereo"
```

TuneIn's `Tune.ashx` endpoint returns several stream URLs per station, at
different bitrates, mirrors, and protocols (HLS, MP3, AAC). Each stream
becomes its own `Release`, so a consumer can pick the best fit at playback
time.

TuneIn emits these mediavocab external ids:

| key                  | source                                    |
| -------------------- | ----------------------------------------- |
| `tunein_station_id`  | `guide_id` / `preset_id`                  |
| `tunein_url`         | OPML `Tune.ashx` URL                      |
| `tunein_web_url`     | Public `tunein.com/station/?stationId=…`  |
| `tunein_logo_url`    | Station logo URL                          |

Enriched stations also carry `slogan`, `location`, `frequency`, `band`,
`twitter_id`, and `content_classification` under `work.extra`. The
now-playing label, when present, stays in `work.extra["current_track"]`.

#### Why no `Programme` or `Schedule`?

mediavocab 0.3 added `Programme` and `Schedule` for EPG data. The TuneIn
search and browse endpoints expose a now-playing label but no start or end
timestamps, and `Programme` requires an ISO-validated `starts_at`. TuneIn
keeps the now-playing string in `work.extra["current_track"]` instead of
fabricating a timestamp. If a future TuneIn endpoint exposes a real schedule
feed, that data can move into `Programme(work=show_ref, channel=station_ref,
starts_at=...)` without changing the existing interface.

## Pluggable HTTP transport

By default the client uses `requests`. For scraping that is harder to
block, install the `stealth` extra, which matches the TLS fingerprint of a
real browser via [curl_cffi](https://github.com/lexiforest/curl_cffi), and
set the `TUNEIN_TRANSPORT` environment variable:

```bash
pip install tunein[stealth]
export TUNEIN_TRANSPORT=curl_cffi
```

You can also pass in any session-shaped object directly:

```python
from tunein import TuneIn
import requests

s = requests.Session()
s.headers["User-Agent"] = "my-bot/1.0"
client = TuneIn(session=s)
results = client.search_stations("BBC Radio 4")
```

`TuneIn.search`, `TuneIn.featured`, and `TuneIn.get_stream_urls` also accept
a `session=` keyword for one-shot calls that skip creating a client.

## Related projects

- [mediavocab](https://github.com/JarbasAl/mediavocab) — the shared media
  vocabulary this client emits data into.

## License

Apache-2.0. See [LICENSE](LICENSE).

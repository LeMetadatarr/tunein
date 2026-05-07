# TuneIn

Unofficial python api for TuneIn, with first-class
[mediavocab](https://github.com/JarbasAl/mediavocab) integration.

## Usage

### From the command line

`tunein` ships a basic CLI for searching. Output is available in both
`json` and table formats; the default is the table layout.

```bash
tunein search "Radio paradise"
tunein search "Radio paradise" --format json
```

CLI help is available with `tunein --help`.

### From Python

```python
from tunein import TuneIn

for station in TuneIn.search("BBC Radio 4"):
    print(station.title, station.stream, station.bit_rate)
```

### mediavocab integration

`TuneInStation.to_release()` emits a canonical `mediavocab.Release` so
downstream consumers (OCP, recommendation engines, catalogue importers)
can ingest TuneIn data without bespoke glue code.

Per mediavocab axiom 8 (station identity), each TuneIn channel is
modelled as a `Work` with `MediaType.RADIO`, and the playable stream
URL is a `Release` with `StreamMode.CONTINUOUS` (live linear
broadcast — not seekable on-demand audio).

```python
from tunein import TuneIn

# Fast path — search payload only.
for release in (s.to_release() for s in TuneIn.search("BBC Radio 4")):
    print(release.uri, release.codec, release.bitrate)

# Rich path — opt in to the per-station Describe.ashx call to populate
# genre, language, country, call-sign, slogan, etc.
for station in TuneIn.search("BBC Radio 4", enrich=True):
    release = station.to_release()
    print(release.work.title)            # "BBC Radio 4"
    print(release.work.country)          # "GB"  (parsed from "London, UK")
    print(release.work.language)         # "en"  (mapped from "English")
    print(release.work.content_genres)   # ["news"]  (mapped to GENRE_NEWS)
    print(release.work.aka)              # ["BBC R4"]   (call-sign)
    print(release.codec, release.bitrate)  # "aac", "128"
    print(release.audio_channels)        # "stereo"
```

TuneIn's `Tune.ashx` endpoint returns multiple stream URLs per station
(different bitrates, mirrors, and protocols — HLS, MP3, AAC). Each
stream becomes its own `Release` so consumers can pick the best fit at
playback time.

The full set of mediavocab external ids emitted is:

| key                  | source                                    |
| -------------------- | ----------------------------------------- |
| `tunein_station_id`  | `guide_id` / `preset_id`                  |
| `tunein_url`         | OPML `Tune.ashx` URL                      |
| `tunein_web_url`     | Public `tunein.com/station/?stationId=…`  |
| `tunein_logo_url`    | Station logo URL                          |

Enriched stations also carry `slogan`, `location`, `frequency`, `band`,
`twitter_id`, and `content_classification` under `work.extra`. The
now-playing label (when present) is preserved in
`work.extra["current_track"]`.

#### Why no `Programme` / `Schedule`?

mediavocab 0.3 introduced `Programme` and `Schedule` for EPG data. The
TuneIn search/browse endpoints expose a *now-playing* label but no
start/end timestamps, and `Programme` requires an ISO-validated
`starts_at`. This client therefore preserves the now-playing string in
`work.extra["current_track"]` rather than fabricating a timestamp. If a
future TuneIn endpoint exposes a real schedule feed, it can be lifted
into `Programme(work=show_ref, channel=station_ref, starts_at=...)`
without changing the existing surface.

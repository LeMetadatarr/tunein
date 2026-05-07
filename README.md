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

station = next(iter(TuneIn.search("BBC Radio 4")))
release = station.to_release()

release.work.title          # "BBC Radio 4"
release.work.media_type     # MediaType.RADIO
release.stream_mode         # StreamMode.CONTINUOUS
release.uri                 # the actual mp3/aac/hls stream URL
release.codec               # "aac" / "mp3" / "hls" / ...
release.bitrate             # "128"
release.work.external_ids   # {"tunein_url": "...", "tunein_station_id": "s12345"}
```

The `tunein_station_id` is parsed from the OPML `Tune.ashx?id=...` URL
and is the canonical, stable handle for the channel. Now-playing
metadata (when present) is preserved in `work.extra["current_track"]`.

#### Why no `Programme` / `Schedule`?

mediavocab 0.3 introduced `Programme` and `Schedule` for EPG data. The
TuneIn search/browse endpoints expose a *now-playing* label but no
start/end timestamps, and `Programme` requires an ISO-validated
`starts_at`. This client therefore preserves the now-playing string in
`work.extra["current_track"]` rather than fabricating a timestamp. If a
future TuneIn endpoint exposes a real schedule feed, it can be lifted
into `Programme(work=show_ref, channel=station_ref, starts_at=...)`
without changing the existing surface.

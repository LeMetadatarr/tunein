# Getting Started

## Install

```bash
pip install tunein
```

For stealthier scraping (TLS fingerprint matching a modern browser):

```bash
pip install tunein[stealth]
export TUNEIN_TRANSPORT=curl_cffi
```

## Search

```python
from tunein import TuneIn

stations = TuneIn.search("BBC Radio 4")
for s in stations:
    print(s.title, s.stream, s.bit_rate, s.media_type)
```

`TuneIn.search` returns a list of `TuneInStation` objects — one per
resolved stream variant. A single station with three codec variants
(MP3/128, AAC/64, HLS) appears as three items.

## Featured / Local Stations

```python
stations = TuneIn.featured()
```

Calls `Browse.ashx?c=local` with the standard format query. Returns
the same `TuneInStation` list as `search`.

## Enrichment

```python
stations = TuneIn.search("BBC Radio 4", enrich=True)
```

With `enrich=True`, an additional `Describe.ashx` request is made per
unique station to populate genre, language, country, call-sign, slogan,
frequency, band, and scheduling flags. The extra call is per station, not
per stream variant — results are merged before fan-out.

## Resolving Stream URLs

```python
from tunein import TuneIn

urls = TuneIn.get_stream_urls("http://opml.radiotime.com/Tune.ashx?id=s12345")
for entry in urls:
    print(entry["url"], entry["bitrate"], entry["media_type"])
```

See [Stream resolution](stream-resolution.md) for `.pls` / `.m3u` handling.

## Converting to mediavocab

```python
for station in TuneIn.search("BBC Radio 4", enrich=True):
    release = station.to_release()
    print(release.work.title, release.uri, release.stream_mode)
```

See [mediavocab converters](converters.md) for the full shape.

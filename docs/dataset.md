# Dataset products

The `tunein` package is an unofficial Python client for the TuneIn radio
catalogue. It can produce a JSONL dataset of internet radio stations. Each
station may expose multiple stream URLs, so one TuneIn station can yield one or
more dataset rows.

## What this repo produces

A dataset of radio station streams. The client searches TuneIn's OPML/JSON
endpoints, resolves playable stream URLs, and optionally enriches each station
with metadata from `Describe.ashx` (genre, language, country, call-sign,
slogan, frequency, band, logo, and more). Rows are emitted as plain
dictionaries ready for JSONL output or conversion to `mediavocab.Release`
objects.

## Dataset format

One JSON object per line. One row per station stream.

Common fields:

| Field | Type | Description |
| ----- | ---- | ----------- |
| `title` | string | Station display title or current track label. |
| `artist` | string | Station name or owner label. |
| `description` | string | Station subtext or description. |
| `image` | string | Station logo URL. |
| `stream` | string | Resolved playable stream URL. |
| `bitrate` | integer \| null | Stream bitrate, when declared. |
| `media_type` | string | Stream codec or container, e.g. `aac`, `mp3`. |
| `url` | string | OPML `Tune.ashx` URL for the station. |
| `station_id` | string | TuneIn station identifier. |
| `genre_id` | string \| null | TuneIn genre identifier. |
| `genre_name` | string \| null | Human-readable genre. |
| `language` | string \| null | ISO-639-1 language code when mapped. |
| `country` | string \| null | ISO-3166-1 alpha-2 country code when mapped. |
| `location` | string \| null | Station location string. |
| `call_sign` | string \| null | Broadcast call sign. |
| `slogan` | string \| null | Station slogan. |
| `frequency` | string \| null | Broadcast frequency. |
| `band` | string \| null | Broadcast band, e.g. `FM`. |
| `is_music` | boolean \| null | Whether TuneIn classifies the station as music. |
| `has_schedule` | boolean \| null | Whether TuneIn reports schedule support. |
| `tunein_url` | string \| null | Public TuneIn web URL. |
| `logo` | string \| null | Logo URL from `Describe.ashx`. |
| `content_classification` | string \| null | TuneIn content classification. |
| `twitter_id` | string \| null | Station Twitter handle. |
| `current_track` | string \| null | Now-playing label, when present. |
| `formats` | string \| null | Declared format list. |
| `reliability` | string \| null | TuneIn reliability score. |

Example row:

```json
{
  "title": "BBC Radio 4",
  "artist": "BBC",
  "description": "Talk and current affairs",
  "image": "https://example.com/r4.png",
  "stream": "https://stream.example.com/r4.aac",
  "bitrate": 128,
  "media_type": "aac",
  "url": "http://opml.radiotime.com/Tune.ashx?id=s25419",
  "station_id": "s25419",
  "genre_name": "News",
  "language": "en",
  "country": "GB",
  "location": "London, UK",
  "call_sign": "BBC R4",
  "slogan": "Inquisitive speech radio"
}
```

## How to generate it

Search TuneIn with enrichment enabled and write each station's dictionary to a
JSONL file.

```python
import json
from tunein import TuneIn

with open("tunein_stations.jsonl", "w", encoding="utf-8") as fh:
    for query in ("jazz", "news", "classical", "sports"):
        for station in TuneIn.search(query, enrich=True):
            fh.write(json.dumps(station.dict, ensure_ascii=False) + "\n")
```

For richer, normalised output, convert each station to a `mediavocab.Release`:

```python
from tunein import TuneIn

for station in TuneIn.search("BBC Radio 4", enrich=True):
    release = station.to_release()
    print(release.uri, release.codec, release.bitrate)
```

To list local/featured stations instead of searching:

```python
for station in TuneIn.featured(enrich=True):
    print(station.title, station.stream)
```

## Worth publishing on Hugging Face?

Yes. A harvested TuneIn dataset is a structured media-metadata product: radio
station identities, stream endpoints, genres, languages and countries. It is
useful for media-player catalogues, recommendation engines, and speech/audio
research that needs labelled radio sources. When published, it fits the
`media-metadata` collection alongside other LeMetadatarr sources.

## ML tasks served

- Station genre, language and country classification.
- Audio-stream metadata linking and duplicate detection.
- Retrieval and RAG for radio-station questions.
- Named entity recognition on station names, call signs and locations.
- Recommendation and playlist construction by genre or region.

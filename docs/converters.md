# mediavocab Converters

`TuneInStation.to_release` — `tunein/__init__.py:276`

## Overview

`to_release()` maps a `TuneInStation` to a `mediavocab.Release`. Per
mediavocab axiom 8 (station identity):

- The station is a `Work` with `MediaType.RADIO`.
- Each playable stream URL is a `Release` with `StreamMode.CONTINUOUS`
  (live linear broadcast — not seekable on-demand).

## Work Fields

| `Work` field | Source |
|---|---|
| `title` | `TuneInStation.title` |
| `media_type` | `MediaType.RADIO` (or `MediaType.TV` if `raw["media_type_kind"] == "tv"`) |
| `country` | `raw["country"]`, or parsed from `raw["location"]` tail |
| `language` | `raw["language"]` mapped to ISO-639-1 |
| `content_genres` | `raw["genre_name"]` mapped to `mediavocab.taxonomy.genre.GENRE_*` |
| `aka` | `call_sign` and `name` when they differ from `title` |
| `external_ids` | See external IDs table below |
| `extra` | `description`, `current_track`, `slogan`, `frequency`, `band`, `twitter_id`, `content_classification`, `location` |

`TuneInStation._resolve_media_type` — `tunein/__init__.py:262`

## Release Fields

| `Release` field | Source |
|---|---|
| `work` | The `Work` above |
| `uri` | `TuneInStation.stream` |
| `image` | `TuneInStation.image` |
| `codec` | `TuneInStation.media_type` (`mp3`, `aac`, …) |
| `bitrate` | `str(TuneInStation.bit_rate)` |
| `audio_channels` | `raw["audio_channels"]` or `"stereo"` |
| `audio_language` | `raw["audio_language"]` or same as `language` |
| `stream_mode` | `StreamMode.CONTINUOUS` |
| `external_ids` | Same as `Work.external_ids` |
| `region` | `raw["region"]` (when present) |
| `regions_available` | `raw["regions_available"]` (when present) |

## External IDs

| Key | Source |
|---|---|
| `tunein_station_id` | `guide_id` / `preset_id` |
| `tunein_url` | `raw["url"]` — OPML `Tune.ashx` URL |
| `tunein_web_url` | `raw["tunein_url"]` — public `tunein.com` page URL |
| `tunein_logo_url` | `TuneInStation.image` |

Both `Work.external_ids` and `Release.external_ids` receive the same dict.

## Genre Mapping

`_map_tunein_genre` — `tunein/__init__.py:33`

TuneIn's `genre_name` is a free-form string. The function normalises and
maps common labels to `mediavocab.taxonomy.genre.GENRE_*` constants.
Unrecognised labels are preserved verbatim.

Mapped values include: `news`, `news/talk`, `talk`, `sports`, `comedy`,
`classical`, `jazz`, `blues`, `rock`, `indie`, `metal`, `punk`, `pop`,
`country`, `folk`, `electronic`, `house`, `techno`, `trance`, `dubstep`,
`drum and bass`, `hip hop`, `r&b`, `soul`, `funk`, `disco`, `reggae`,
`latin`, `ambient`.

## Country Derivation

`_country_from_location` — `tunein/__init__.py:117`

TuneIn's `location` field is `"City, Country"` or `"City, ST"` (US state
abbreviation). The function splits on the last comma, maps US state codes
to `"US"`, and maps country names/abbreviations to ISO-3166-1 alpha-2.

## Language Mapping

`_language_to_iso` — `tunein/__init__.py:139`

Maps English-language names (`"English"`, `"Spanish"`, …) to ISO-639-1
codes. ISO codes already in the raw payload are returned verbatim.

## Why No `Programme` / `Schedule`

TuneIn's search/browse endpoints return a `current_track` now-playing
label but no `starts_at`/`ends_at` timestamps. `mediavocab.Programme`
requires an ISO-validated `starts_at`. The now-playing string is therefore
preserved in `work.extra["current_track"]` rather than fabricated into a
`Programme`.

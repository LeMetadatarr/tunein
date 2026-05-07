# TuneIn Reference

`TuneIn` — `tunein/__init__.py:379`

## Class Attributes

| Attribute | Value |
|---|---|
| `search_url` | `https://opml.radiotime.com/Search.ashx` |
| `featured_url` | `http://opml.radiotime.com/Browse.ashx` |
| `describe_url` | `http://opml.radiotime.com/Describe.ashx` |
| `stnd_query` | `{"formats": "mp3,aac,ogg,html,hls", "render": "json"}` |

## Constructor

```python
TuneIn(session=None)
```

`session` — any object exposing `get(url, **kw)` and `post(url, **kw)` in
the `requests.Session` style. When omitted, `default_session()` is called
lazily on first use.

`TuneIn.__init__` — `tunein/__init__.py:385`

## Instance Methods

These are thin wrappers that forward the injected session to the
corresponding classmethod.

### `search_stations(query, enrich=False)`

`TuneIn.search_stations` — `tunein/__init__.py:409`

### `featured_stations(enrich=False)`

`TuneIn.featured_stations` — `tunein/__init__.py:412`

### `stream_urls(url)`

`TuneIn.stream_urls` — `tunein/__init__.py:415`

## Class Methods

### `TuneIn.search(query, enrich=False, session=None)`

`TuneIn.search` — `tunein/__init__.py:465`

POSTs to `Search.ashx` with `stnd_query + {"query": query}`. Passes each
station entry through `_get_stations` which resolves stream URLs and
optionally enriches via `Describe.ashx`.

Returns `list[TuneInStation]`.

### `TuneIn.featured(enrich=False, session=None)`

`TuneIn.featured` — `tunein/__init__.py:453`

POSTs to `Browse.ashx` with `stnd_query + {"c": "local"}`. Parses
`body[0]["children"]` for audio station entries.

Returns `list[TuneInStation]`.

### `TuneIn.get_stream_urls(url, session=None)`

`TuneIn.get_stream_urls` — `tunein/__init__.py:419`

Resolves a `Tune.ashx` URL to a list of stream-entry dicts. Tries HTTP
then HTTPS. Each `.pls` entry is fetched and its `File1=` line extracted.
Direct and `.m3u` URLs are returned as-is.

Each dict in the returned list has keys: `url`, `bitrate`, `media_type`
(plus any other fields TuneIn includes in its JSON body).

Returns `list[dict]`.

## Internal

### `TuneIn._get_stations(stations, query="", enrich=False, session=None)`

`TuneIn._get_stations` — `tunein/__init__.py:483`

Generator. Filters entries where `type != "audio"` or `item != "station"`
or `key == "unavailable"`. For each passing entry, resolves stream URLs
and yields one `TuneInStation` per stream variant. When `enrich=True`,
fetches `Describe.ashx` once per station (keyed on `guide_id` /
`preset_id`) and merges the result before fan-out.

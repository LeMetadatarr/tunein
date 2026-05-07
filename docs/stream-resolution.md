# Stream Resolution

`TuneIn.get_stream_urls` — `tunein/__init__.py:419`

## What TuneIn Returns

`Search.ashx` and `Browse.ashx` return station entries that include a
`URL` field pointing to `Tune.ashx?id=<station_id>&...`. That URL is not
a playable stream — it is a redirect/resolver that returns a JSON body
with one or more stream entries.

## Resolution Steps

1. Append `&render=json` to the `Tune.ashx` URL.
2. Try HTTP first, then HTTPS (some entries specify one scheme explicitly).
3. Parse `body` as a list of stream-entry dicts.
4. For each entry whose `url` ends in `.pls`:
   - Fetch the `.pls` file.
   - Extract `File1=<url>` from the response text.
   - Replace `entry["url"]` with that direct stream URL.
5. Entries with `.m3u` or direct stream URLs pass through unchanged.
6. Return the full list.

## Entry Dict Shape

Each entry returned is a dict from TuneIn's JSON body, guaranteed to have:

| Key | Type | Description |
|---|---|---|
| `url` | `str` | Resolved playable URL |
| `bitrate` | `int` or `None` | Bitrate in kbps |
| `media_type` | `str` | `mp3`, `aac`, `ogg`, `hls`, etc. |

Additional keys (`reliability`, `is_direct`, `guide_id`, …) may be
present depending on TuneIn's response.

## Example

```python
from tunein import TuneIn

entries = TuneIn.get_stream_urls("http://opml.radiotime.com/Tune.ashx?id=s15119")
for e in entries:
    print(e["url"], e["bitrate"], e["media_type"])
# http://stream.example.com/radio.mp3  128  mp3
# http://stream.example.com/radio.aac   64  aac
```

## Error Handling

- If both HTTP and HTTPS fail (`raise_for_status`), returns `[]`.
- If an individual `.pls` fetch fails, that entry is skipped (`continue`).
- The `body` key missing or not a list → returns `[]`.

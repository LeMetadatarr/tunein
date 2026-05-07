"""05_to_mediavocab.py — convert a TuneInStation to a mediavocab Release.

TuneInStation.to_release() maps:
  - station  -> Work  (MediaType.RADIO)
  - stream   -> Release (StreamMode.CONTINUOUS)

Enrich before converting to get genre, country, language, and aka.

Run:
    python examples/05_to_mediavocab.py
"""

from tunein import TuneIn

stations = TuneIn.search("BBC Radio 4", enrich=True)
if not stations:
    print("No results.")
    raise SystemExit(1)

# Pick the highest-bitrate variant.
best = max(stations, key=lambda s: s.bit_rate or 0)
release = best.to_release()

work = release.work
print("=== Work ===")
print(f"  title          : {work.title}")
print(f"  media_type     : {work.media_type}")
print(f"  country        : {work.country}")
print(f"  language       : {work.language}")
print(f"  content_genres : {work.content_genres}")
print(f"  aka            : {work.aka}")
print(f"  external_ids   : {work.external_ids}")
print(f"  extra keys     : {list(work.extra.keys())}")

print("\n=== Release ===")
print(f"  uri            : {release.uri}")
print(f"  codec          : {release.codec}")
print(f"  bitrate        : {release.bitrate}")
print(f"  audio_channels : {release.audio_channels}")
print(f"  stream_mode    : {release.stream_mode}")
print(f"  external_ids   : {release.external_ids}")

# AGENTS.md — tunein

Unofficial Python client for the TuneIn OPML/`radiotime.com` API that emits typed `mediavocab` Releases for linear-radio (and optionally IPTV/`tv`) stations.

## Setup

```bash
pip install -e .[test]        # adds pytest, vcrpy, pytest-vcr
pip install -e .[stealth]     # optional curl_cffi transport
```

Runtime deps: `requests`, `mediavocab>=1.0.0`. Optional: `curl-cffi` (stealth), `rapidfuzz` (better fuzzy matching; `parse.py` falls back to `difflib.SequenceMatcher`).

## Test

```bash
pytest test/
```

Tests are split into `test/unittests/` (pure unit, no network) and `test/test_tunein_vcr.py` (VCR cassette replay). VCR `record_mode` is `none` (see `test/conftest.py`), so the suite is fully offline; cassettes live under `test/cassettes/test_tunein_vcr/`. Re-record locally with `pytest --vcr-record=all test/test_*_vcr.py` — cassettes are token/cookie-scrubbed by `conftest._scrub_response` and are committed.

## Lint

```bash
ruff check .
```

Ruff is the configured linter (CI `lint.yml`, `ruff: true`). No mypy config present though `.mypy_cache` is gitignored.

## Layout

- `tunein/__init__.py` — the whole client. `TuneIn` (classmethods `search`, `featured`, `get_stream_urls` + instance wrappers `search_stations`/`featured_stations`/`stream_urls`) and `TuneInStation` (lazy wrapper over the raw OPML dict; `.enrich()` hits `Describe.ashx`, `.to_release()` builds the `mediavocab.Release`). Also holds the genre/country/language normalisation tables (`_map_tunein_genre`, `_country_from_location`, `_language_to_iso`).
- `tunein/transport.py` — `default_session()`; honours `TUNEIN_TRANSPORT=curl_cffi` at call time, else `requests.Session()`.
- `tunein/parse.py` — `fuzzy_match` and `MatchStrategy`; rapidfuzz-optional.
- `tunein/cli.py` + `tunein/subcommands/search.py` — argparse CLI (`tunein search <query> [--format json|table]`); table output renders titles as OSC-8 hyperlinks.
- `examples/` — 8 runnable usage snippets (quickstart, featured, enrich, stream resolution, mediavocab conversion, variant fanout, custom session, CLI pipeline).
- `docs/` — full reference (stations, stream resolution, transport, converters, CLI).
- `scripts/` — local version-bump helpers (do not hand-run for releases; CI owns versioning).

## Data flow

`search`/`featured` POST to `Search.ashx`/`Browse.ashx` → filter to `type=audio` + `item=station` → `get_stream_urls` resolves each `Tune.ashx` URL (tries http then https, `render=json`, expands `.pls` `File1=` to the direct stream) → one `TuneInStation` is yielded **per stream variant** (each bitrate/codec). `enrich=True` does one extra `Describe.ashx` call per station to add genre/language/location/call-sign. `to_release()` maps each station to a `Work(MediaType.RADIO)` + `Release(StreamMode.CONTINUOUS)`.

## Conventions (Org hard rules)

- Branches: `dev` (work) / `master` (stable). NEVER `main`.
- NEVER edit `tunein/version.py`; gh-automations bumps semver from conventional-commit prefixes (`feat:`/`fix:`/`feat!:`).
- New repos private by default.
- Commit identity: `JarbasAi <jarbasai@mailfence.com>`.
- CI is provided by `OpenVoiceOS/gh-automations` reusable workflows, referenced at `@dev`.
- No Neon / `neon-*` references.
- No meta-commentary (no history, dates, "before times", or "design mistake" notes) in docs, commits, code comments, or PRs — describe current state only.

## Gotchas

- `_get_session(None)` returns the `requests` **module**, not a `Session` — done deliberately so tests can patch `tunein.requests.get`/`post`. Only `TuneIn.session` (the property) lazily builds a real `default_session()`.
- Stream fan-out means N stations in equals M (>= N) `TuneInStation`s out; de-dup downstream if you want one entry per station.
- `to_release()` is best-effort on metadata: genre/country/language fall back to the raw label when no mediavocab/ISO mapping matches.
- `enrich` HTTP failures are swallowed silently (returns un-enriched).
- `pyproject.toml` `Homepage` URL still points at `OpenJarbas/tunein`; the canonical repo is `TigreGotico/tunein`.
- `.coverage` and `tunein.egg-info/` are committed even though `.gitignore` lists them.
- `MediaType.TV` is only reachable when a caller seeds `raw["media_type_kind"] = "tv"`; the stock `search`/`featured` paths always produce `RADIO`.

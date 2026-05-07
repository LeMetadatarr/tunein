# TuneIn

Unofficial Python client for the TuneIn OPML API with first-class mediavocab integration.

## Overview

Wraps TuneIn's undocumented OPML endpoints (`Search.ashx`, `Browse.ashx`,
`Tune.ashx`, `Describe.ashx`) and exposes a typed Python API. Stream URLs
are resolved from `.pls` and `.m3u` playlists to direct URLs. Stations can
be converted to `mediavocab.Release` objects for downstream consumption by
OCP, recommendation engines, and catalogue importers.

## Key Classes

| Class | Purpose | Source |
|---|---|---|
| `TuneIn` | Search, browse, and stream-URL resolution | `tunein/__init__.py:379` |
| `TuneInStation` | Typed wrapper around a single stream variant | `tunein/__init__.py:145` |

## Contents

- [Installation and quick start](../README.md#install)
- [Getting started](getting-started.md)
- [TuneIn reference](tunein-reference.md)
- [TuneInStation reference](station-reference.md)
- [Stream resolution](stream-resolution.md)
- [mediavocab converters](converters.md)
- [Transport and sessions](transport.md)
- [CLI reference](cli-reference.md)

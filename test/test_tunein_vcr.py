"""Cassette-backed parser tests for the TuneIn API client.

These tests replay real captured HTTP responses against the parser so
upstream OPML/JSON changes surface as test failures rather than silent
empty results.

Re-record cassettes::

    pytest --vcr-record=all test/test_tunein_vcr.py

The nightly CI workflow runs without cassettes against the live API.
"""
from __future__ import annotations

import pytest

from tunein import TuneIn, TuneInStation


pytestmark = pytest.mark.vcr


def _first(it):
    for x in it:
        return x
    return None


# --- TuneIn.search (Search.ashx) ----------------------------------------
def test_search_yields_typed_stations():
    results = TuneIn.search("kuow")
    assert isinstance(results, list)
    assert len(results) > 0
    station = results[0]
    assert isinstance(station, TuneInStation)
    assert station.title
    assert station.stream, "expected resolved stream URL"


def test_search_with_enrich_populates_metadata():
    results = TuneIn.search("kuow", enrich=True)
    assert results, "expected at least one station"
    # Enrichment should populate at least one of these fields on at
    # least one station from the search result set.
    enriched = [s for s in results if s.raw.get("genre_name")
                or s.raw.get("language") or s.raw.get("location")]
    assert enriched, "expected enrich=True to populate metadata"


# --- TuneIn.featured (Browse.ashx, c=local) -----------------------------
def test_featured_yields_typed_stations():
    stations = TuneIn.featured()
    assert isinstance(stations, list)
    assert len(stations) > 0
    assert isinstance(stations[0], TuneInStation)
    assert stations[0].title


# --- TuneIn.get_stream_urls (Tune.ashx) ---------------------------------
def test_get_stream_urls_returns_playable_entries():
    # Pull a known station's tune URL from a search result, then
    # exercise the static stream resolver directly.
    results = TuneIn.search("kuow")
    assert results, "search prerequisite failed"
    tune_url = results[0].raw.get("url")
    assert tune_url, "expected OPML tune URL on search result"
    streams = TuneIn.get_stream_urls(tune_url)
    assert isinstance(streams, list)
    assert streams, "expected at least one stream entry"
    first = streams[0]
    assert "url" in first
    assert first["url"].startswith(("http://", "https://"))


# --- TuneInStation.enrich (Describe.ashx) -------------------------------
def test_station_enrich_merges_describe_metadata():
    results = TuneIn.search("kuow")
    assert results, "search prerequisite failed"
    station = results[0]
    sid = station.station_id
    assert sid, "expected station_id parsed from OPML tune URL"
    enriched = station.enrich()
    assert enriched is station
    # Describe.ashx should expose at least one of these richer fields.
    assert any(station.raw.get(k) for k in (
        "genre_name", "language", "location", "call_sign", "slogan",
        "tunein_url",
    )), "expected Describe.ashx to populate at least one field"


# --- TuneInStation.to_release (no network; mediavocab shape) ------------
def test_to_release_returns_mediavocab_release_shape():
    from mediavocab import MediaType, Release, StreamMode, Work

    results = TuneIn.search("kuow", enrich=True)
    assert results, "search prerequisite failed"
    station = results[0]
    release = station.to_release()

    assert isinstance(release, Release)
    assert isinstance(release.work, Work)
    assert release.work.media_type == MediaType.RADIO
    assert release.stream_mode == StreamMode.CONTINUOUS
    # uri should be the resolved stream URL
    assert release.uri
    assert release.uri.startswith(("http://", "https://"))
    # Work title populated from station title
    assert release.work.title
    # external_ids should at minimum carry the OPML tune URL
    assert release.external_ids.get("tunein_url")
    # station_id mirrored into external_ids
    assert release.external_ids.get("tunein_station_id")

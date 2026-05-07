"""Offline tests targeting coverage gaps in the tunein package.

These tests do not hit the network — they mock ``requests`` directly,
exercise pure-python helpers, and drive the CLI with stubbed argv.
"""
from __future__ import annotations

import io
import contextlib
import json
import sys
import runpy
from unittest.mock import patch, MagicMock

import pytest
import requests

from tunein import (
    TuneIn,
    TuneInStation,
    _country_from_location,
    _language_to_iso,
    _map_tunein_genre,
)
from tunein import parse as tparse
from tunein.cli import Cli, main


# --- Pure helpers --------------------------------------------------------
class TestHelpers:
    def test_map_genre_empty(self):
        assert _map_tunein_genre("") == ""

    def test_map_genre_known(self):
        # English genre maps to a non-raw constant.
        out = _map_tunein_genre("Jazz")
        assert out and out != "Jazz"

    def test_map_genre_unknown_returns_raw(self):
        assert _map_tunein_genre("ZorgleMusic") == "ZorgleMusic"

    def test_map_genre_mediavocab_import_failure(self):
        # Force the inline import to fail; helper must return raw label.
        import builtins
        real_import = builtins.__import__

        def fake_import(name, *a, **kw):
            if name.startswith("mediavocab"):
                raise ImportError("simulated")
            return real_import(name, *a, **kw)

        with patch.object(builtins, "__import__", side_effect=fake_import):
            assert _map_tunein_genre("jazz") == "jazz"

    def test_country_from_location_empty(self):
        assert _country_from_location("") == ""

    def test_country_from_location_only_comma(self):
        # rsplit yields empty tail.
        assert _country_from_location("Somewhere,   ") == ""

    def test_country_from_location_us_state(self):
        assert _country_from_location("Seattle, WA") == "US"

    def test_country_from_location_country_name(self):
        assert _country_from_location("London, UK") == "GB"

    def test_country_from_location_unknown(self):
        assert _country_from_location("Foo, Mars") == ""

    def test_language_to_iso_empty(self):
        assert _language_to_iso("") == ""

    def test_language_to_iso_known(self):
        assert _language_to_iso("English") == "en"

    def test_language_to_iso_unknown_returns_raw(self):
        assert _language_to_iso("Klingon") == "Klingon"


# --- TuneInStation properties / branches ---------------------------------
class TestTuneInStation:
    def test_str_repr_and_match_no_phrase(self):
        st = TuneInStation({"title": "Hello"})
        assert str(st) == "Hello"
        assert repr(st) == "Hello"
        # No phrase, no query => 0
        assert st.match() == 0

    def test_match_with_query_in_raw(self):
        st = TuneInStation({"title": "Hello", "query": "hello"})
        assert st.match() == 100

    def test_station_id_from_explicit_field(self):
        st = TuneInStation({"station_id": 12345})
        assert st.station_id == "12345"

    def test_station_id_from_url(self):
        st = TuneInStation({"url": "http://x?id=s99&foo=1"})
        assert st.station_id == "s99"

    def test_station_id_missing(self):
        assert TuneInStation({}).station_id == ""
        assert TuneInStation({"url": "http://x"}).station_id == ""

    def test_station_id_parse_qs_exception(self):
        st = TuneInStation({"url": "http://x?id=abc"})
        with patch("tunein.parse_qs", side_effect=Exception("boom")):
            assert st.station_id == ""

    def test_dict_shape(self):
        st = TuneInStation({"title": "T", "stream": "http://s", "bitrate": 128,
                            "media_type": "mp3", "image": "http://img",
                            "description": "d", "artist": "a"})
        d = st.dict
        assert d["title"] == "T"
        assert d["bit_rate"] == 128
        assert d["stream"] == "http://s"

    # --- enrich -----------------------------------------------------------
    def test_enrich_no_station_id_returns_self(self):
        st = TuneInStation({})
        assert st.enrich() is st

    def test_enrich_http_failure_swallowed(self):
        st = TuneInStation({"station_id": "s1"})
        with patch("tunein.requests.get", side_effect=requests.RequestException("x")):
            assert st.enrich() is st

    def test_enrich_empty_body(self):
        st = TuneInStation({"station_id": "s1"})
        resp = MagicMock()
        resp.json.return_value = {"body": []}
        resp.raise_for_status.return_value = None
        with patch("tunein.requests.get", return_value=resp):
            assert st.enrich() is st

    def test_enrich_merges_without_clobbering(self):
        st = TuneInStation({
            "station_id": "s1",
            "language": "Existing",  # should NOT be overwritten
        })
        resp = MagicMock()
        resp.json.return_value = {"body": [{
            "language": "English",
            "genre_name": "Jazz",
            "call_sign": "KZZZ",
            "slogan": "All jazz, all the time",
            "is_music": True,
        }]}
        resp.raise_for_status.return_value = None
        with patch("tunein.requests.get", return_value=resp):
            st.enrich()
        assert st.raw["language"] == "Existing"  # preserved
        assert st.raw["genre_name"] == "Jazz"
        assert st.raw["call_sign"] == "KZZZ"

    # --- to_release branches ---------------------------------------------
    def test_to_release_minimal(self):
        from mediavocab import MediaType, StreamMode
        st = TuneInStation({
            "title": "Radio X",
            "stream": "http://s/x.mp3",
            "url": "http://opml?id=s1",
            "image": "http://img",
            "bitrate": 128,
            "media_type": "mp3",
        })
        rel = st.to_release()
        assert rel.work.title == "Radio X"
        assert rel.work.media_type == MediaType.RADIO
        assert rel.stream_mode == StreamMode.CONTINUOUS
        assert rel.external_ids["tunein_station_id"] == "s1"
        assert rel.external_ids["tunein_logo_url"] == "http://img"

    def test_to_release_full_fanout(self):
        st = TuneInStation({
            "title": "Radio Y",
            "stream": "http://s/y.aac",
            "url": "http://opml?id=s2",
            "tunein_url": "https://tunein.com/r/s2",
            "image": "http://img",
            "bitrate": 256,
            "media_type": "aac",
            "description": "desc",
            "current_track": "Some Song - Some Artist",
            "slogan": "Slo",
            "frequency": "98.7",
            "band": "FM",
            "twitter_id": "@radioy",
            "content_classification": "GA",
            "location": "Seattle, WA",
            "call_sign": "KYYY",
            "name": "Radio Y Official",
            "genre_name": "Rock",
            "language": "English",
            "audio_channels": "mono",
            "audio_language": "es",
            "region": "US",
            "regions_available": ["US", "CA"],
        })
        rel = st.to_release()
        assert rel.work.country == "US"
        assert rel.work.language == "en"
        assert "KYYY" in rel.work.aka
        assert "Radio Y Official" in rel.work.aka
        assert rel.audio_channels == "mono"
        assert rel.audio_language == "es"
        assert rel.region == "US"
        assert rel.regions_available == ["US", "CA"]
        assert rel.external_ids["tunein_web_url"] == "https://tunein.com/r/s2"
        assert rel.work.extra["current_track"]
        assert rel.work.extra["location"] == "Seattle, WA"

    def test_to_release_explicit_country_wins(self):
        st = TuneInStation({
            "title": "T",
            "country": "PT",
            "location": "Lisbon, Portugal",  # would map to PT anyway
            "stream": "http://s",
        })
        rel = st.to_release()
        assert rel.work.country == "PT"

    def test_resolve_media_type_tv_kind(self):
        from mediavocab import MediaType
        st = TuneInStation({"title": "T", "media_type_kind": "tv",
                            "stream": "http://s"})
        rel = st.to_release()
        assert rel.work.media_type == MediaType.TV


# --- TuneIn.get_stream_urls branches -------------------------------------
class TestGetStreamUrls:
    def test_all_schemes_fail(self):
        bad = MagicMock()
        bad.raise_for_status.side_effect = requests.exceptions.RequestException("bad")
        with patch("tunein.requests.get", return_value=bad):
            out = TuneIn.get_stream_urls("http://opml?id=s1")
        assert out == "Failed to get stream url"

    def test_pls_fallback_extracts_file1(self):
        # First call: returns body with .pls station; second call fetches pls.
        ok_json = MagicMock()
        ok_json.raise_for_status.return_value = None
        ok_json.json.return_value = {"body": [
            {"url": "http://x/playlist.pls", "bitrate": 128, "media_type": "mp3"},
        ]}
        pls = MagicMock()
        pls.text = "[playlist]\nFile1=http://stream.example/audio.mp3\nLength1=-1\n"

        calls = {"n": 0}
        def fake_get(url, *a, **kw):
            calls["n"] += 1
            if calls["n"] == 1:
                return ok_json
            return pls

        with patch("tunein.requests.get", side_effect=fake_get):
            out = TuneIn.get_stream_urls("http://opml?id=s1")
        assert out[0]["url"] == "http://stream.example/audio.mp3"

    def test_pls_no_file1_keeps_url(self):
        ok_json = MagicMock()
        ok_json.raise_for_status.return_value = None
        ok_json.json.return_value = {"body": [
            {"url": "http://x/playlist.pls", "bitrate": 64, "media_type": "mp3"},
        ]}
        pls = MagicMock()
        pls.text = "[playlist]\nNumberOfEntries=0\n"

        seq = [ok_json, pls]
        with patch("tunein.requests.get", side_effect=lambda *a, **kw: seq.pop(0)):
            out = TuneIn.get_stream_urls("http://opml?id=s1")
        assert out[0]["url"] == "http://x/playlist.pls"


# --- TuneIn.search / featured / _get_stations branches --------------------
class TestStationsPipeline:
    def _mk_search_resp(self, body):
        r = MagicMock()
        r.json.return_value = {"body": body}
        return r

    def test_search_skips_unavailable_and_non_audio(self):
        body = [
            {"key": "unavailable", "type": "audio", "item": "station", "URL": "x"},
            {"type": "link", "item": "station", "URL": "x"},
            {"type": "audio", "item": "topic", "URL": "x"},
        ]
        with patch("tunein.requests.post", return_value=self._mk_search_resp(body)):
            out = TuneIn.search("foo")
        assert out == []

    def test_search_yields_stations(self):
        body = [{
            "type": "audio", "item": "station",
            "URL": "http://opml?id=s1",
            "text": "Cool Radio",
            "subtext": "desc",
            "image": "http://img",
            "guide_id": "s1",
            "current_track": "Now Playing",
        }]
        post = MagicMock()
        post.json.return_value = {"body": body}

        streams = [{"url": "http://stream/1.mp3", "bitrate": 128, "media_type": "mp3"}]
        with patch("tunein.requests.post", return_value=post), \
             patch.object(TuneIn, "get_stream_urls", return_value=streams):
            out = TuneIn.search("cool")
        assert len(out) == 1
        assert out[0].title == "Now Playing"  # current_track preferred
        assert out[0].artist == "Cool Radio"

    def test_search_enrich_swallows_exception(self):
        body = [{
            "type": "audio", "item": "station",
            "URL": "http://opml?id=s1",
            "text": "R",
            "guide_id": "s1",
        }]
        post = MagicMock()
        post.json.return_value = {"body": body}
        streams = [{"url": "http://stream/1.mp3", "bitrate": 96, "media_type": "mp3"}]

        with patch("tunein.requests.post", return_value=post), \
             patch.object(TuneIn, "get_stream_urls", return_value=streams), \
             patch("tunein.requests.get",
                   side_effect=requests.RequestException("describe down")):
            out = TuneIn.search("r", enrich=True)
        assert len(out) == 1
        # No describe data merged.
        assert "language" not in out[0].raw or not out[0].raw.get("language")

    def test_search_enrich_merges(self):
        body = [{
            "type": "audio", "item": "station",
            "URL": "http://opml?id=s1",
            "text": "R",
            "guide_id": "s1",
        }]
        post = MagicMock()
        post.json.return_value = {"body": body}
        streams = [{"url": "http://stream/1.mp3", "bitrate": 96, "media_type": "mp3"}]

        describe = MagicMock()
        describe.raise_for_status.return_value = None
        describe.json.return_value = {"body": [{
            "language": "English", "genre_name": "Rock", "call_sign": "KRRR",
        }]}

        with patch("tunein.requests.post", return_value=post), \
             patch.object(TuneIn, "get_stream_urls", return_value=streams), \
             patch("tunein.requests.get", return_value=describe):
            out = TuneIn.search("r", enrich=True)
        assert out[0].raw["language"] == "English"
        assert out[0].raw["call_sign"] == "KRRR"

    def test_featured_empty_body(self):
        post = MagicMock()
        post.json.return_value = {"body": [{"children": []}]}
        with patch("tunein.requests.post", return_value=post):
            assert TuneIn.featured() == []


# --- CLI -----------------------------------------------------------------
class TestCli:
    def test_main_invokes_search(self):
        argv = ["tunein", "search", "kuow", "-f", "json"]
        fake_station = TuneInStation({
            "title": "KUOW", "stream": "http://s", "bitrate": 128,
            "media_type": "mp3", "artist": "a", "description": "d",
            "image": "http://i",
        })
        with patch.object(sys, "argv", argv), \
             patch("tunein.subcommands.search.TuneIn.search",
                   return_value=[fake_station]):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                main()
        data = json.loads(buf.getvalue())
        assert data[0]["title"] == "KUOW"

    def test_search_no_results_exits(self):
        argv = ["tunein", "search", "nothing", "-f", "table"]
        with patch.object(sys, "argv", argv), \
             patch("tunein.subcommands.search.TuneIn.search", return_value=[]):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                with pytest.raises(SystemExit) as ei:
                    cli = Cli()
                    cli.parse_args()
                    cli.run()
        assert ei.value.code == 1
        assert "No results" in buf.getvalue()

    def test_module_main_block(self):
        # Execute tunein.cli as __main__ to cover the guard.
        argv = ["tunein", "search", "kuow", "-f", "json"]
        fake_station = TuneInStation({
            "title": "KUOW", "stream": "http://s", "bitrate": 128,
            "media_type": "mp3", "artist": "a", "description": "d",
            "image": "http://i",
        })
        with patch.object(sys, "argv", argv), \
             patch("tunein.subcommands.search.TuneIn.search",
                   return_value=[fake_station]):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                runpy.run_module("tunein.cli", run_name="__main__")


# --- parse.py strategies --------------------------------------------------
class TestParse:
    @pytest.mark.parametrize("strategy", [
        tparse.MatchStrategy.RATIO,
        tparse.MatchStrategy.PARTIAL_RATIO,
        tparse.MatchStrategy.TOKEN_SORT_RATIO,
        tparse.MatchStrategy.TOKEN_SET_RATIO,
        tparse.MatchStrategy.PARTIAL_TOKEN_SORT_RATIO,
        tparse.MatchStrategy.PARTIAL_TOKEN_SET_RATIO,
        tparse.MatchStrategy.PARTIAL_TOKEN_RATIO,
        tparse.MatchStrategy.SIMPLE_RATIO,
    ])
    def test_strategies(self, strategy):
        score = tparse.fuzzy_match("hello world", "hello world", strategy)
        assert 0.0 <= score <= 1.0

    def test_validate_falls_back_when_rapidfuzz_missing(self, capsys):
        with patch.object(tparse, "rapidfuzz", None):
            out = tparse._validate_matching_strategy(
                tparse.MatchStrategy.TOKEN_SORT_RATIO
            )
        assert out == tparse.MatchStrategy.SIMPLE_RATIO
        captured = capsys.readouterr()
        assert "rapidfuzz" in captured.out


# --- version --------------------------------------------------------------
def test_version_module():
    from tunein import version as v
    assert v.__version__
    assert isinstance(v.VERSION_MAJOR, int)

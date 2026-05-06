"""Offline unit test for ``TuneInStation.to_release()``."""
from __future__ import annotations

from mediavocab import MediaType, StreamMode

from tunein import TuneInStation


def _station(**overrides):
    raw = dict(
        title="BBC Radio 4",
        artist="BBC",
        bitrate=128,
        media_type="aac",
        image="https://example.com/r4.png",
        description="Talk and current affairs",
        stream="https://stream.example.com/r4.aac",
        url="https://tunein.com/radio/BBC-Radio-4",
        query="bbc radio 4",
    )
    raw.update(overrides)
    return TuneInStation(raw)


def test_to_release_uses_radio_media_type():
    rel = _station().to_release()
    assert rel.work.media_type == MediaType.RADIO


def test_to_release_uses_continuous_stream_mode():
    rel = _station().to_release()
    assert rel.stream_mode == StreamMode.CONTINUOUS


def test_to_release_carries_stream_uri_and_image():
    rel = _station().to_release()
    assert rel.uri == "https://stream.example.com/r4.aac"
    assert rel.image == "https://example.com/r4.png"


def test_to_release_codec_and_bitrate():
    rel = _station().to_release()
    assert rel.codec == "aac"
    assert rel.bitrate == "128"


def test_to_release_carries_tunein_url_in_external_ids():
    rel = _station().to_release()
    assert rel.work.external_ids.get("tunein_url") == "https://tunein.com/radio/BBC-Radio-4"
    assert rel.external_ids.get("tunein_url") == "https://tunein.com/radio/BBC-Radio-4"


def test_to_release_description_in_extra():
    rel = _station().to_release()
    assert rel.work.extra.get("description") == "Talk and current affairs"


def test_to_release_handles_missing_fields():
    s = TuneInStation({"title": "Empty Station", "stream": "http://e/1.mp3"})
    rel = s.to_release()
    assert rel.work.title == "Empty Station"
    assert rel.uri == "http://e/1.mp3"
    assert rel.codec == ""
    assert rel.bitrate == ""
    assert rel.image == ""

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


def test_to_release_station_id_parsed_from_url():
    s = _station(url="http://opml.radiotime.com/Tune.ashx?id=s12345")
    rel = s.to_release()
    assert rel.work.external_ids.get("tunein_station_id") == "s12345"
    assert rel.external_ids.get("tunein_station_id") == "s12345"


def test_to_release_explicit_station_id_wins():
    s = _station(station_id="s99999",
                 url="http://opml.radiotime.com/Tune.ashx?id=s12345")
    rel = s.to_release()
    assert rel.work.external_ids.get("tunein_station_id") == "s99999"


def test_to_release_country_and_language_when_known():
    s = _station(country="GB", language="en")
    rel = s.to_release()
    assert rel.work.country == "GB"
    assert rel.work.language == "en"


def test_to_release_current_track_in_extra():
    s = _station(current_track="Some Song - Some Artist")
    rel = s.to_release()
    assert rel.work.extra.get("current_track") == "Some Song - Some Artist"


def test_to_release_external_ids_are_strings():
    rel = _station().to_release()
    for k, v in rel.work.external_ids.items():
        assert isinstance(k, str)
        assert isinstance(v, str)


def test_to_release_default_audio_channels_stereo():
    rel = _station().to_release()
    assert rel.audio_channels == "stereo"


def test_to_release_audio_channels_override():
    s = _station(audio_channels="mono")
    rel = s.to_release()
    assert rel.audio_channels == "mono"


def test_to_release_logo_url_in_external_ids():
    rel = _station().to_release()
    assert rel.work.external_ids.get("tunein_logo_url") == \
        "https://example.com/r4.png"


def test_to_release_news_maps_to_programme_format():
    """News / talk / sports are broadcast formats, not genres (T1): they
    land on Work.programme_format, never content_genres."""
    from mediavocab.taxonomy import ProgrammeFormat
    s = _station(genre_name="News")
    rel = s.to_release()
    assert rel.work.programme_format == ProgrammeFormat.NEWS
    assert rel.work.content_genres == []


def test_to_release_talk_maps_to_programme_format():
    from mediavocab.taxonomy import ProgrammeFormat
    s = _station(genre_name="Talk")
    rel = s.to_release()
    assert rel.work.programme_format == ProgrammeFormat.TALK_SHOW


def test_to_release_genre_mapping_jazz():
    s = _station(genre_name="Jazz")
    rel = s.to_release()
    from mediavocab.taxonomy.genre import GENRE_JAZZ
    assert GENRE_JAZZ in rel.work.content_genres


def test_to_release_genre_unknown_label_preserved():
    s = _station(genre_name="Polka Hour")
    rel = s.to_release()
    # Work normalises content_genres to lowercase; the label survives.
    assert "polka hour" in rel.work.content_genres


def test_to_release_country_from_location_uk():
    s = _station(location="London, UK")
    rel = s.to_release()
    assert rel.work.country == "GB"


def test_to_release_country_from_us_state_code():
    s = _station(location="Seattle, WA")
    rel = s.to_release()
    assert rel.work.country == "US"


def test_to_release_explicit_country_wins_over_location():
    s = _station(country="FR", location="London, UK")
    rel = s.to_release()
    assert rel.work.country == "FR"


def test_to_release_language_iso_mapping():
    s = _station(language="English")
    rel = s.to_release()
    assert rel.work.language == "en"
    # audio_language defaults to the work language when not given.
    assert rel.audio_language == "en"


def test_to_release_aka_from_call_sign_and_name():
    s = _station(call_sign="BBC R4", name="BBC Radio 4 FM")
    rel = s.to_release()
    # title = "BBC Radio 4"; both call_sign and name differ.
    assert "BBC R4" in rel.work.aka
    assert "BBC Radio 4 FM" in rel.work.aka


def test_to_release_extra_carries_slogan_and_location():
    s = _station(slogan="Inquisitive speech radio",
                 location="London, UK", frequency="93.5", band="FM")
    rel = s.to_release()
    assert rel.work.extra.get("slogan") == "Inquisitive speech radio"
    assert rel.work.extra.get("location") == "London, UK"
    assert rel.work.extra.get("frequency") == "93.5"
    assert rel.work.extra.get("band") == "FM"


def test_to_release_tv_media_type_when_seeded():
    from mediavocab import MediaType
    s = _station(media_type_kind="tv")
    rel = s.to_release()
    assert rel.work.media_type == MediaType.TV


def test_to_release_audio_language_explicit():
    s = _station(language="English", audio_language="es")
    rel = s.to_release()
    assert rel.audio_language == "es"


def test_to_release_region_and_regions_available():
    s = _station(region="EU", regions_available=["GB", "IE"])
    rel = s.to_release()
    assert rel.region == "EU"
    assert rel.regions_available == ["GB", "IE"]


def test_to_release_tunein_web_url_separate_from_opml_url():
    s = _station(url="http://opml.radiotime.com/Tune.ashx?id=s25419",
                 tunein_url="http://tunein.com/station/?stationId=25419")
    rel = s.to_release()
    assert rel.work.external_ids["tunein_url"].startswith("http://opml")
    assert rel.work.external_ids["tunein_web_url"] == \
        "http://tunein.com/station/?stationId=25419"

from urllib.parse import urlparse, urlunparse, parse_qs

import requests
from tunein.parse import fuzzy_match
from tunein.transport import default_session


def _get_session(session=None):
    """Return ``session`` when injected, else the :mod:`requests` module
    itself.

    The :mod:`requests` module exposes top-level ``get``/``post``
    helpers with the same signatures as ``Session.get``/``post``, so it
    is duck-type compatible. Returning the module (rather than building
    a default :class:`~requests.Session`) preserves the historical
    behaviour where callers can patch ``tunein.requests.get`` or
    ``tunein.requests.post`` to intercept HTTP traffic in tests.

    Callers that explicitly want a stealth/curl_cffi session should
    inject one (or call :func:`tunein.transport.default_session`
    themselves).
    """
    if session is not None:
        return session
    return requests


# --- TuneIn genre_name -> mediavocab GENRE_* constant -------------------
# TuneIn's `genre_name` field (from Describe.ashx) is a free-form string,
# but the values cluster around a small set of recognisable buckets. Map
# the common ones to mediavocab taxonomy constants; anything unknown is
# preserved verbatim so downstream consumers can still see the raw label.
#
# News / talk / sports are *programme formats*, not genres (T1) — they map
# to `ProgrammeFormat` via `_map_tunein_format` and land on
# `Work.programme_format`, never `content_genres`.
def _map_tunein_format(label: str):
    """Return a ``mediavocab.taxonomy.ProgrammeFormat`` when the TuneIn
    label names a non-fiction broadcast format, else ``None``.
    """
    if not label:
        return None
    try:
        from mediavocab.taxonomy import ProgrammeFormat as PF
    except Exception:
        return None
    return {
        "news": PF.NEWS,
        "news/talk": PF.NEWS,
        "talk": PF.TALK_SHOW,
        "talk show": PF.TALK_SHOW,
        "talk radio": PF.TALK_SHOW,
        "sports": PF.SPORTS,
        "sport": PF.SPORTS,
    }.get(label.strip().lower())


def _map_tunein_genre(label: str) -> str:
    """Return a ``mediavocab.taxonomy.genre.GENRE_*`` value when the
    TuneIn label is recognisable; otherwise return the raw label.
    """
    if not label:
        return ""
    try:
        from mediavocab.taxonomy import genre as G
    except Exception:
        return label

    norm = label.strip().lower()
    table = {
        "comedy": G.GENRE_COMEDY,
        "classical": G.GENRE_CLASSICAL,
        "classical music": G.GENRE_CLASSICAL,
        "jazz": G.GENRE_JAZZ,
        "blues": G.GENRE_BLUES,
        "rock": G.GENRE_ROCK,
        "indie": G.GENRE_INDIE,
        "metal": G.GENRE_METAL,
        "punk": G.GENRE_PUNK,
        "pop": G.GENRE_POP,
        "country": G.GENRE_COUNTRY,
        "folk": G.GENRE_FOLK,
        "electronic": G.GENRE_ELECTRONIC,
        "electronica": G.GENRE_ELECTRONIC,
        "dance": G.GENRE_ELECTRONIC,
        "house": G.GENRE_HOUSE,
        "techno": G.GENRE_TECHNO,
        "trance": G.GENRE_TRANCE,
        "dubstep": G.GENRE_DUBSTEP,
        "drum and bass": G.GENRE_DRUM_AND_BASS,
        "hip hop": G.GENRE_HIP_HOP,
        "hip-hop": G.GENRE_HIP_HOP,
        "rap": G.GENRE_HIP_HOP,
        "r&b": G.GENRE_RNB,
        "rnb": G.GENRE_RNB,
        "soul": G.GENRE_SOUL,
        "funk": G.GENRE_FUNK,
        "disco": G.GENRE_DISCO,
        "reggae": G.GENRE_REGGAE,
        "latin": G.GENRE_LATIN,
        "ambient": G.GENRE_AMBIENT,
        "religious": getattr(G, "GENRE_RELIGIOUS", "religious"),
    }
    return table.get(norm, label)


# --- ISO-3166 country derivation from TuneIn location strings -----------
# TuneIn's `location` is "City, Country" where Country is often a US
# state ("Seattle, WA") or a country name ("London, UK"). Map the most
# common tails to ISO-3166-1 alpha-2 codes; otherwise return the raw
# trailing token so the caller still has *something*.
_LOCATION_TAIL_TO_ISO = {
    "uk": "GB", "u.k.": "GB", "united kingdom": "GB", "england": "GB",
    "scotland": "GB", "wales": "GB", "northern ireland": "GB",
    "usa": "US", "u.s.a.": "US", "united states": "US",
    "ireland": "IE", "france": "FR", "germany": "DE", "spain": "ES",
    "portugal": "PT", "italy": "IT", "netherlands": "NL", "belgium": "BE",
    "canada": "CA", "australia": "AU", "new zealand": "NZ",
    "brazil": "BR", "brasil": "BR", "argentina": "AR", "mexico": "MX",
    "japan": "JP", "china": "CN", "india": "IN", "russia": "RU",
    "sweden": "SE", "norway": "NO", "denmark": "DK", "finland": "FI",
    "poland": "PL", "greece": "GR", "turkey": "TR", "switzerland": "CH",
    "austria": "AT",
}
# US state codes -> US (TuneIn returns "Seattle, WA" style locations).
_US_STATES = {
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga", "hi",
    "id", "il", "in", "ia", "ks", "ky", "la", "me", "md", "ma", "mi",
    "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj", "nm", "ny", "nc",
    "nd", "oh", "ok", "or", "pa", "ri", "sc", "sd", "tn", "tx", "ut",
    "vt", "va", "wa", "wv", "wi", "wy", "dc",
}


def _country_from_location(location: str) -> str:
    if not location:
        return ""
    tail = location.rsplit(",", 1)[-1].strip().lower()
    if not tail:
        return ""
    if tail in _US_STATES:
        return "US"
    return _LOCATION_TAIL_TO_ISO.get(tail, "")


# --- Language name -> ISO-639-1 ----------------------------------------
_LANGUAGE_TO_ISO = {
    "english": "en", "spanish": "es", "french": "fr", "german": "de",
    "italian": "it", "portuguese": "pt", "dutch": "nl", "russian": "ru",
    "japanese": "ja", "chinese": "zh", "korean": "ko", "arabic": "ar",
    "hindi": "hi", "swedish": "sv", "norwegian": "no", "danish": "da",
    "finnish": "fi", "polish": "pl", "greek": "el", "turkish": "tr",
    "catalan": "ca", "galician": "gl", "basque": "eu",
}


def _language_to_iso(label: str) -> str:
    if not label:
        return ""
    return _LANGUAGE_TO_ISO.get(label.strip().lower(), label)


class TuneInStation:
    def __init__(self, raw, session=None):
        self.raw = raw
        self._session = session

    @property
    def title(self):
        return self.raw.get("title", "")

    @property
    def artist(self):
        return self.raw.get("artist", "")

    @property
    def bit_rate(self):
        return self.raw.get("bitrate")

    @property
    def media_type(self):
        return self.raw.get("media_type")

    @property
    def image(self):
        return self.raw.get("image")

    @property
    def description(self):
        return self.raw.get("description", "")

    @property
    def stream(self):
        return self.raw.get("stream")

    def match(self, phrase=None):
        phrase = phrase or self.raw.get("query")
        if not phrase:
            return 0
        return fuzzy_match(phrase.lower(), self.title.lower()) * 100

    def __str__(self):
        return self.title

    def __repr__(self):
        return self.title

    @property
    def dict(self):
        """Return a dict representation of the station."""
        return {
            "artist": self.artist,
            "bit_rate": self.bit_rate,
            "description": self.description,
            "image": self.image,
            "match": self.match(),
            "media_type": self.media_type,
            "stream": self.stream,
            "title": self.title,
        }

    @property
    def station_id(self) -> str:
        """Return the canonical TuneIn station id (e.g. ``s12345``).

        Parsed from the OPML ``Tune.ashx?id=...`` URL when present;
        falls back to an explicit ``station_id`` in the raw payload.
        """
        sid = self.raw.get("station_id")
        if sid:
            return str(sid)
        url = self.raw.get("url") or ""
        if "id=" in url:
            try:
                qs = parse_qs(urlparse(url).query)
                if qs.get("id"):
                    return str(qs["id"][0])
            except Exception:
                pass
        return ""

    def enrich(self) -> "TuneInStation":
        """Fetch ``Describe.ashx`` for the station and merge richer
        metadata (genre, language, location, call-sign, slogan,
        is_music, has_schedule, tunein_url) into ``self.raw``.

        Returns ``self`` so callers can chain. Any HTTP failure is
        swallowed — enrichment is best-effort.
        """
        sid = self.station_id
        if not sid:
            return self
        try:
            sess = _get_session(self._session)
            res = sess.get(
                "http://opml.radiotime.com/Describe.ashx",
                params={"id": sid, "render": "json"},
                timeout=10,
            )
            res.raise_for_status()
            body = res.json().get("body") or []
            if not body:
                return self
            details = body[0]
        except Exception:
            return self

        # Merge — never clobber values the search payload already gave us.
        merge_keys = (
            "name", "call_sign", "slogan", "frequency", "band",
            "location", "language", "genre_name", "genre_id",
            "is_music", "has_schedule", "tunein_url", "logo",
            "content_classification", "twitter_id", "description",
        )
        for k in merge_keys:
            if k in details and self.raw.get(k) in (None, ""):
                self.raw[k] = details[k]
        return self

    def _resolve_media_type(self):
        """Pick the right ``MediaType`` for this station.

        TuneIn's search/browse endpoints filter by ``type=audio`` so
        results are radio. If a future caller seeds ``raw["media_type_kind"]``
        with ``"tv"`` (e.g. an IPTV browse), honour it.
        """
        from mediavocab import MediaType

        kind = (self.raw.get("media_type_kind") or "").lower()
        if kind == "tv":
            return MediaType.TV
        return MediaType.RADIO

    def to_release(self):
        """Return a mediavocab ``Release`` for this TuneIn station.

        Per mediavocab axiom 8 (station identity), a TuneIn channel is a
        ``Work`` with ``MediaType.RADIO`` and the playable stream URL is
        a ``Release`` with ``StreamMode.CONTINUOUS`` (live linear
        broadcast, not seekable on-demand audio).
        """
        from mediavocab import Release, StreamMode, Work

        external_ids: dict[str, str] = {}
        if self.raw.get("url"):
            external_ids["tunein_url"] = str(self.raw["url"])
        # Describe.ashx exposes a public web URL distinct from the OPML
        # tune URL; preserve it under a separate key when available.
        if self.raw.get("tunein_url"):
            external_ids["tunein_web_url"] = str(self.raw["tunein_url"])
        if self.image:
            external_ids["tunein_logo_url"] = str(self.image)
        sid = self.station_id
        if sid:
            external_ids["tunein_station_id"] = sid

        extra: dict[str, str] = {}
        if self.description:
            extra["description"] = self.description
        # TuneIn's "current_track" is a now-playing label (no timestamps,
        # so it can't be promoted to a Programme); keep it in extra.
        if self.raw.get("current_track"):
            extra["current_track"] = str(self.raw["current_track"])
        for k in ("slogan", "frequency", "band", "twitter_id",
                  "content_classification"):
            if self.raw.get(k):
                extra[k] = str(self.raw[k])
        if self.raw.get("location"):
            extra["location"] = str(self.raw["location"])

        # --- Work fields ----------------------------------------------
        # `aka` — when both display title and call_sign are present and
        # differ, lift the alternate.
        aka: list[str] = []
        call_sign = (self.raw.get("call_sign") or "").strip()
        name = (self.raw.get("name") or "").strip()
        for alt in (call_sign, name):
            if alt and alt != self.title and alt not in aka:
                aka.append(alt)

        # `content_genres` / `programme_format` — TuneIn's single genre_name
        # may name an aesthetic genre (jazz) or a broadcast format (talk). A
        # format goes on programme_format (T1); only real genres go in
        # content_genres.
        content_genres: list[str] = []
        programme_format = None
        gname = (self.raw.get("genre_name") or "").strip()
        if gname:
            programme_format = _map_tunein_format(gname)
            if programme_format is None:
                content_genres.append(_map_tunein_genre(gname))

        # `country` — prefer explicit raw country, fall back to parsing
        # the location string.
        country = str(self.raw.get("country") or "")
        if not country:
            country = _country_from_location(self.raw.get("location") or "")

        # `language` — accept ISO codes verbatim, map English-language
        # names to ISO-639-1.
        lang_raw = str(self.raw.get("language") or "")
        language = _language_to_iso(lang_raw) if lang_raw else ""

        # Country lives in the per-MediaType slot (broadcaster_country for
        # RADIO/TV), not a flat `country` field — route it there.
        media_type = self._resolve_media_type()
        country_kwargs: dict[str, str] = {}
        if country:
            from mediavocab.models.work import COUNTRY_SLOT_FOR
            slot = COUNTRY_SLOT_FOR.get(media_type, "broadcaster_country")
            country_kwargs[slot] = country

        work = Work(
            title=self.title,
            media_type=media_type,
            language=language,
            content_genres=content_genres,
            programme_format=programme_format,
            aka=aka,
            external_ids=dict(external_ids),
            extra=extra,
            **country_kwargs,
        )

        # --- Release fields -------------------------------------------
        # Stations are stereo by convention; explicit overrides win.
        audio_channels = str(self.raw.get("audio_channels") or "stereo")
        audio_language = (
            str(self.raw.get("audio_language") or "") or language
        )

        release_kwargs = dict(
            work=work,
            uri=self.stream or "",
            image=self.image or "",
            codec=self.media_type or "",
            bitrate=str(self.bit_rate) if self.bit_rate else "",
            audio_channels=audio_channels,
            audio_language=audio_language,
            stream_mode=StreamMode.CONTINUOUS,
            external_ids=dict(external_ids),
        )
        # Optional rights / regional fields when TuneIn declares them.
        if self.raw.get("region"):
            release_kwargs["region"] = str(self.raw["region"])
        if self.raw.get("regions_available"):
            release_kwargs["regions_available"] = list(
                self.raw["regions_available"]
            )
        return Release(**release_kwargs)


class TuneIn:
    search_url = "https://opml.radiotime.com/Search.ashx"
    featured_url = "http://opml.radiotime.com/Browse.ashx"  # local stations
    describe_url = "http://opml.radiotime.com/Describe.ashx"
    stnd_query = {"formats": "mp3,aac,ogg,html,hls", "render": "json"}

    def __init__(self, session=None):
        """Optional ``session`` is any object exposing ``get``/``post``
        in the :mod:`requests` ``Session`` style. If omitted, a default
        session (see :func:`tunein.transport.default_session`) is built
        lazily and reused.
        """
        self._session = session

    @property
    def session(self):
        """Return the injected session, or build a default lazily.

        The default honours ``TUNEIN_TRANSPORT=curl_cffi`` (see
        :func:`tunein.transport.default_session`).
        """
        if self._session is None:
            self._session = default_session()
        return self._session

    # ------------------------------------------------------------------
    # Instance wrappers — pass the injected session through to the
    # underlying classmethods so callers can do
    # ``TuneIn(session=s).search("jazz")`` and have ``s`` reused.
    # ------------------------------------------------------------------
    def search_stations(self, query, enrich: bool = False):
        return type(self).search(query, enrich=enrich, session=self.session)

    def featured_stations(self, enrich: bool = False):
        return type(self).featured(enrich=enrich, session=self.session)

    def stream_urls(self, url):
        return type(self).get_stream_urls(url, session=self.session)

    @classmethod
    def get_stream_urls(cls, url, session=None):
        sess = _get_session(session)
        _url = urlparse(url)
        for scheme in ("http", "https"):
            url_str = urlunparse(
                _url._replace(scheme=scheme, query=_url.query + "&render=json")
            )
            res = sess.get(url_str, timeout=10)
            try:
                res.raise_for_status()
                break
            except requests.exceptions.RequestException:
                continue
        else:
            return []

        stations = res.json().get("body") or []
        if not isinstance(stations, list):
            return []

        for station in stations:
            if station.get("url", "").endswith(".pls"):
                try:
                    res = sess.get(station["url"], timeout=10)
                    res.raise_for_status()
                except requests.exceptions.RequestException:
                    continue
                file1 = [line for line in res.text.split("\n") if line.startswith("File1=")]
                if file1:
                    station["url"] = file1[0].split("File1=")[1]

        return stations

    @classmethod
    def featured(cls, enrich: bool = False, session=None):
        sess = _get_session(session)
        res = sess.post(
            cls.featured_url,
            data={**cls.stnd_query, **{"c": "local"}},
            timeout=10,
        )
        res.raise_for_status()
        stations = res.json().get("body", [{}])[0].get("children", [])
        return list(cls._get_stations(stations, enrich=enrich, session=sess))

    @classmethod
    def search(cls, query, enrich: bool = False, session=None):
        """Search TuneIn.

        ``enrich=True`` issues an extra ``Describe.ashx`` call per
        station to populate genre, language, country/location and other
        rich metadata. Off by default to keep the fast path cheap.
        """
        sess = _get_session(session)
        res = sess.post(
            cls.search_url,
            data={**cls.stnd_query, **{"query": query}},
            timeout=10,
        )
        res.raise_for_status()
        stations = res.json().get("body", [])
        return list(cls._get_stations(stations, query, enrich=enrich, session=sess))

    @classmethod
    def _get_stations(cls, stations, query: str = "", enrich: bool = False, session=None):
        sess = _get_session(session)
        for entry in stations:
            if (
                entry.get("key") == "unavailable"
                or entry.get("type") != "audio"
                or entry.get("item") != "station"
            ):
                continue
            streams = cls.get_stream_urls(entry["URL"], session=sess)
            # Preload Describe.ashx once per station (not per stream).
            details: dict = {}
            if enrich:
                sid = entry.get("guide_id") or entry.get("preset_id")
                if sid:
                    try:
                        r = sess.get(
                            cls.describe_url,
                            params={"id": sid, "render": "json"},
                            timeout=10,
                        )
                        r.raise_for_status()
                        body = r.json().get("body") or []
                        if body:
                            details = body[0]
                    except Exception:
                        details = {}
            for stream in streams:
                raw = {
                    "stream": stream["url"],
                    "bitrate": stream["bitrate"],
                    "media_type": stream["media_type"],
                    "url": entry["URL"],
                    "title": entry.get("current_track") or entry.get("text"),
                    "artist": entry.get("text"),
                    "description": entry.get("subtext"),
                    "image": entry.get("image"),
                    "query": query,
                    "current_track": entry.get("current_track"),
                    "station_id": entry.get("guide_id") or entry.get("preset_id"),
                    "genre_id": entry.get("genre_id"),
                    "formats": entry.get("formats"),
                    "reliability": entry.get("reliability"),
                }
                # Merge enriched details (Describe.ashx) without clobbering
                # values already present from the search payload.
                for k in (
                    "name", "call_sign", "slogan", "frequency", "band",
                    "location", "language", "genre_name", "genre_id",
                    "is_music", "has_schedule", "tunein_url",
                    "content_classification", "twitter_id",
                ):
                    if details.get(k) and not raw.get(k):
                        raw[k] = details[k]
                yield TuneInStation(raw, session=sess)

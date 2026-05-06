from urllib.parse import urlparse, urlunparse

import requests
from tunein.parse import fuzzy_match


class TuneInStation:
    def __init__(self, raw):
        self.raw = raw

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

    def to_release(self):
        """Return a mediavocab ``Release`` for this TuneIn station.

        The Work is a radio station (``MediaType.RADIO``); the Release
        carries the actual stream URL, codec hint, and bitrate.
        ``StreamMode.CONTINUOUS`` reflects that radio is live linear
        broadcast, not seekable on-demand audio.
        """
        from mediavocab import MediaType, Release, StreamMode, Work

        external_ids = {}
        if self.raw.get("url"):
            external_ids["tunein_url"] = self.raw["url"]

        work = Work(
            title=self.title,
            media_type=MediaType.RADIO,
            external_ids=external_ids,
            extra={"description": self.description} if self.description else {},
        )
        return Release(
            work=work,
            uri=self.stream or "",
            image=self.image or "",
            codec=self.media_type or "",
            bitrate=str(self.bit_rate) if self.bit_rate else "",
            stream_mode=StreamMode.CONTINUOUS,
            external_ids=external_ids,
        )


class TuneIn:
    search_url = "https://opml.radiotime.com/Search.ashx"
    featured_url = "http://opml.radiotime.com/Browse.ashx"  # local stations
    stnd_query = {"formats": "mp3,aac,ogg,html,hls", "render": "json"}

    @staticmethod
    def get_stream_urls(url):
        _url = urlparse(url)
        for scheme in ("http", "https"):
            url_str = urlunparse(
                _url._replace(scheme=scheme, query=_url.query + "&render=json")
            )
            res = requests.get(url_str)
            try:
                res.raise_for_status()
                break
            except requests.exceptions.RequestException:
                continue
        else:
            return "Failed to get stream url"

        stations = res.json().get("body", {})

        for station in stations:
            if station.get("url", "").endswith(".pls"):
                res = requests.get(station["url"])
                file1 = [line for line in res.text.split("\n") if line.startswith("File1=")]
                if file1:
                    station["url"] = file1[0].split("File1=")[1]

        return stations

    @staticmethod
    def featured():
        res = requests.post(
            TuneIn.featured_url,
            data={**TuneIn.stnd_query, **{"c": "local"}}
        )
        stations = res.json().get("body", [{}])[0].get("children", [])
        return list(TuneIn._get_stations(stations))

    @staticmethod
    def search(query):
        res = requests.post(
            TuneIn.search_url,
            data={**TuneIn.stnd_query, **{"query": query}}
        )
        stations = res.json().get("body", [])
        return list(TuneIn._get_stations(stations, query))

    @staticmethod
    def _get_stations(stations: requests.Response, query: str = ""):
        for entry in stations:
            if (
                entry.get("key") == "unavailable"
                or entry.get("type") != "audio"
                or entry.get("item") != "station"
            ):
                continue
            streams = TuneIn.get_stream_urls(entry["URL"])
            for stream in streams:
                yield TuneInStation(
                    {
                        "stream": stream["url"],
                        "bitrate": stream["bitrate"],
                        "media_type": stream["media_type"],
                        "url": entry["URL"],
                        "title": entry.get("current_track") or entry.get("text"),
                        "artist": entry.get("text"),
                        "description": entry.get("subtext"),
                        "image": entry.get("image"),
                        "query": query,
                    }
                )

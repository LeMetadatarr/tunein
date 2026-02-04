import os
import requests
from dead_simple_cache import SimpleCache
from urllib.parse import urlparse, urlunparse
from tunein.parse import fuzzy_match

BASE_DIR = os.getenv("HOME") or os.path.dirname(os.path.abspath(__file__))
DEFAULT_CACHE_PATH = os.path.join(BASE_DIR, ".cache", "radios")


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


class TuneIn:
    search_url = "https://opml.radiotime.com/Search.ashx"
    featured_url = "http://opml.radiotime.com/Browse.ashx"  # local stations
    stnd_query = {"formats": "mp3,aac,ogg,html,hls", "render": "json"}
    cache = SimpleCache(file_path=DEFAULT_CACHE_PATH)

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

        working_stations = []
        for station in stations:
            if station.get("url", "").endswith(".pls"):
                # TODO: come up with a better fix 
                # Catch and avoid invalid certificate errors
                try:
                    res = requests.get(station["url"])
                except Exception:
                    continue
                file1 = [line for line in res.text.split("\n") if line.startswith("File1=")]
                if file1:
                    station["url"] = file1[0].split("File1=")[1]
                working_stations.append(station)
        return working_stations

    @staticmethod
    def featured():
        res = requests.post(
            TuneIn.featured_url,
            data={**TuneIn.stnd_query, **{"c": "local"}}
        )
        stations = res.json().get("body", [{}])[0].get("children", [])
        return list(TuneIn._get_stations(stations))

    @staticmethod
    def search_cache(query):
        """Search for cached stations."""
        items = TuneIn.cache.get(query, fuzzy=True)
        server_alive = {}
        for key, stations in items.items():
            for station in stations:
                url = station["url"]
                # Check whether each server is alive
                if url not in server_alive:
                    # TODO: find a faster way to check whether each server is up
                    # response = requests.head(url, timeout=1)
                    # code = response.status_code
                    # server_alive[url] = str(code).startswith('2') or str(code).startswith('3')
                    server_alive[url] = True
                if not server_alive[url]:
                    stations.remove(station)
        for key, stations in items.items():
            if stations:
                TuneIn.cache.replace(key=key, data=stations)
            else:
                TuneIn.cache.delete(key=key)
        return sum(list(items.values()), [])

    @staticmethod
    def search(query):
        # NOTE: to make the cache persistent on disk, it is necessary to sync it,
        # but since the cache is a static attribute, one must open/close it explicitly.
        # To make the cache persistent on disk, uncomment the following line.
        # TuneIn.cache.open()
        cached_items = TuneIn.search_cache(query)
        if cached_items:
            stations = [TuneInStation(item) for item in cached_items]
        else:
            # Search again
            res = requests.post(
                TuneIn.search_url,
                data={**TuneIn.stnd_query, **{"query": query}}
            )
            stations = list(
                TuneIn._get_stations(res.json().get("body", []), query)
            )
            # Update cache
            for station in filter(lambda s: s.title != '', stations):
                TuneIn.cache.add(key=query, data=station.raw)
        # NOTE: to make the cache persistent on disk, it is necessary to sync it,
        # but since the cache is a static attribute, one must open/close it explicitly.
        # To make the cache persistent on disk, uncomment the following line.
        # TuneIn.cache.close()
        return stations

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

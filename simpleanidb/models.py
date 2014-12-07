from __future__ import absolute_import
from datetime import date
import requests
import xml.etree.ElementTree as ET

from .helper import date_to_date

class Anime(object):

    def __init__(self, anidb, id, auto_load=True, xml=None):
        self.anidb = anidb
        self.id = id
        self.titles = []
        self.episodes = []
        if xml:
            self.fill_from_xml(xml)

        self._loaded = False
        if auto_load:
            self.load()

    def __repr__(self):
        return "<Anime:{} loaded:{}>".format(self.id, self.loaded)

    @property
    def loaded(self):
        return self._loaded

    def load(self):
        """
        http://api.anidb.net:9001/httpapi?request=anime&client={str}&clientver={int}&protover=1&aid={int}
        :return:
        """
        params = {
            "request": "anime",
            "client": "adbahttp",
            "clientver": 100,
            "protover": 1,
            "aid": self.id
        }
        r = requests.get("http://api.anidb.net:9001/httpapi", params=params)
        self._xml = ET.fromstring(r.text.encode("UTF-8"))
        self.fill_from_xml(self._xml)
        self._loaded = True

    def fill_from_xml(self, xml):
        if xml.find("titles") is not None:
            self.titles = [Title(self, n) for n in xml.find("titles")]
        else:
            self.titles = [Title(self, n) for n in xml.findall("title")]
            return
        self.all_episodes = sorted([Episode(self, n) for n in xml.find("episodes")])
        self.episodes = {e.number:e for e in self.all_episodes if e.type == 1}
        self.picture = Picture(self, xml.find("picture"))
        self.start_date = date_to_date(xml.find("startdate").text)
        self.end_date = date_to_date(xml.find("enddate").text)
        self.description = xml.find("description").text

    @property
    def title(self):
        return self.get_title()

    def get_title(self, lang=None):
        if not lang:
            lang = self.anidb.lang
        for t in self.titles:
            if t.lang == lang:
                return t

class BaseAttribute(object):

    def __init__(self, anime, xml_node):
        self.anime = anime
        self._xml = xml_node

    def __str__(self):
        return self._xml.text

    def __repr__(self):
        return u"<{}: {}>".format(
            self.__class__.__name__,
            unicode(self)
        )

class Title(BaseAttribute):

    def __init__(self, anime, xml_node):
        super(Title, self).__init__(anime, xml_node)
        # apperently xml:lang is "{http://www.w3.org/XML/1998/namespace}lang"
        self.lang = self._xml.attrib["{http://www.w3.org/XML/1998/namespace}lang"]

class Picture(BaseAttribute):

    def __str__(self):
        return self.url

    @property
    def url(self):
        return "http://img7.anidb.net/pics/anime/{}".format(self._xml.text)


class Episode(BaseAttribute):

    def __init__(self, anime, xml_node):
        super(Episode, self).__init__(anime, xml_node)
        self.id = int(self._xml.attrib["id"])
        self.titles = [Title(self, n) for n in self._xml.findall("title")]
        try:
            self.airdate = date_to_date(self._xml.find("airdate").text)
        except (AttributeError, TypeError):
            self.airdate = None
        self.type = int(self._xml.find("epno").attrib["type"])
        self.number = self._xml.find("epno").text
        if self.type == 1:
            self.number = int(self.number)
        self.length = self._xml.find("length").text

    @property
    def title(self):
        return self.get_title()

    def get_title(self, lang=None):
        if not lang:
            lang = self.anime.anidb.lang
        for t in self.titles:
            if t.lang == lang:
                return t

    def __str__(self):
        return u"{}: {}".format(self.number, self.title)

    def __cmp__(self, other):
        if self.type > other.type:
            return -1
        elif self.type < other.type:
            return 1

        if self.number < other.number:
            return -1
        return 1






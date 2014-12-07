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
        self.synonyms = []
        self.all_episodes = []
        self.episodes = {}
        self.picture = None
        self.rating_permanent = None
        self.rating_temporary = None
        self.rating_review = None
        self.categories = []
        self.tags = []
        self.start_date = None
        self.end_date = None
        self.description = None

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
        self.synonyms = [t for t in self.titles if t.type == "synonym"]
        if xml.find("episodes") is not None:
            self.all_episodes = sorted([Episode(self, n) for n in xml.find("episodes")])
            self.episodes = {e.number:e for e in self.all_episodes if e.type == 1}
        if xml.find("picture") is not None:
            self.picture = Picture(self, xml.find("picture"))
        if xml.find("ratings") is not None:
            if xml.find("ratings").find("permanent"):
                self.rating_permanent = xml.find("ratings").find("permanent").text
            if xml.find("ratings").find("temporary"):
                self.rating_temporary = xml.find("ratings").find("temporary").text
            if xml.find("ratings").find("review"):
                self.rating_review = xml.find("ratings").find("review").text
        if xml.find("categories") is not None:
            self.categories = [Category(self, c) for c in xml.find("categories")]
        if xml.find("tags") is not None:
            self.tags = sorted([Tag(self, t) for t in xml.find("tags")])
        if xml.find("startdate") is not None:
            self.start_date = date_to_date(xml.find("startdate").text)
        if xml.find("enddate") is not None:
            self.end_date = date_to_date(xml.find("enddate").text)
        if xml.find("description") is not None:
            self.description = xml.find("description").text


    @property
    def title(self):
        return self.get_title("main")

    def get_title(self, type=None, lang=None):
        if not type:
            type = "main"
        for t in self.titles:
            if t.type == type:
                return t
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

class Category(BaseAttribute):

    def __init__(self, anime, xml_node):
        super(Category, self).__init__(anime, xml_node)
        self.id = self._xml.attrib["id"]
        self.hentai = self._xml.attrib["hentai"] == "true"
        self.weigth = self._xml.attrib["weight"]
        self.name = self._xml.find("name").text
        self.description = self._xml.find("description").text

class Tag(BaseAttribute):

    def __init__(self, anime, xml_node):
        super(Tag, self).__init__(anime, xml_node)
        self.id = self._xml.attrib["id"]
        self.spoiler = self._xml.attrib["spoiler"] == "true"
        self.localspoiler = self._xml.attrib["localspoiler"] == "true"
        self.globalspoiler = self._xml.attrib["globalspoiler"] == "true"
        self.update = date_to_date(self._xml.attrib["update"])
        self.name = self._xml.find("name").text
        self.description = None
        if self._xml.find("description") is not None:
            self.description = self._xml.find("description").text
        self.count = int(self._xml.find("count").text)

    def __cmp__(self, other):
        if self.count > other.count:
            return 1
        return -1

class Title(BaseAttribute):

    def __init__(self, anime, xml_node):
        super(Title, self).__init__(anime, xml_node)
        # apperently xml:lang is "{http://www.w3.org/XML/1998/namespace}lang"
        self.lang = self._xml.attrib["{http://www.w3.org/XML/1998/namespace}lang"]
        self.type = self._xml.attrib.get("type")

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






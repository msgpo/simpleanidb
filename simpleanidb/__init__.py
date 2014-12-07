from __future__ import absolute_import
import os
import xml.etree.cElementTree as etree
from datetime import datetime, timedelta

from appdirs import *

from .helper import download_file
from .models import *

__version__ = "0.1.0"
__author__ = "Dennis Lutter"

ANIME_LIST_URL = "http://anidb.net/api/anime-titles.xml.gz"

class Anidb(object):

    def __init__(self, cache_dir=None, auto_download=True, lang=None):
        if not cache_dir:
            self._cache_dir = user_cache_dir("simpleanidb")
            if not os.path.isdir(self._cache_dir):
                os.mkdir(self._cache_dir)
        else:
            self._cache_dir = cache_dir
        if not os.path.isdir(self._cache_dir):
            raise ValueError("'%s' does not exist" % self._cache_dir)
        elif not os.access(self._cache_dir, os.W_OK):
            raise IOError("'%s' is not writable" % self._cache_dir)

        self.anime_list_path = os.path.join(
            self._cache_dir, "anime-titles.xml.gz")
        self.auto_download = auto_download
        self._xml = None
        self.lang = lang
        if not lang:
            self.lang = "en"

    def search(self, term):
        if not self._xml:
            try:
                self._xml = self._read_file(self.anime_list_path)
            except IOError:
                if self.auto_download:
                    self.download_anime_list()
                    self._xml = self._read_file(self.anime_list_path)
                else:
                    raise

        term = term.lower()
        anime_ids = []
        for anime in self._xml.findall("anime"):
            for title in anime.findall("title"):
                if term in title.text.lower():
                    anime_ids.append((int(anime.get("aid")), anime))
                    break
        return [Anime(self, aid, False, xml_node) for aid, xml_node in anime_ids]

    def anime(self, aid):
        return Anime(self, aid)

    def _read_file(self, path):
        f = open(path, 'rb')
        return etree.ElementTree(file=f)

    def download_anime_list(self, force=False):
        if not force and os.path.exists(self.anime_list_path):
            modified_date = datetime.fromtimestamp(
                os.path.getmtime(self.anime_list_path))
            if modified_date + timedelta(1) > datetime.now():
                return False
        return download_file(self.anime_list_path, ANIME_LIST_URL)

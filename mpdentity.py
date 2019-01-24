from __future__ import print_function
from .ticker import Ticker

class MPDEntity(object):
    def __init__(self, mpd_data, path):
        self._name = ""
        self._path = path
        self._ticker = Ticker(8)
        self._file = False
        self._directory = False
        self._selected = False

        if 'directory' in mpd_data:
            self._directory = True
            self._name = mpd_data["directory"]
        if 'file' in mpd_data:
            self._file = True
            self._name = mpd_data["file"]
        self._ticker.setText(self._name)

    def get_name(self):
        return self._name

    def get_full_path(self):
        tmp_path = self._path + self._name
        if self.is_directory():
            tmp_path += "/"
        return tmp_path

    def is_directory(self):
        return self._directory

    def is_file(self):
        return self._file

    def is_selected(self):
        return self._selected

    def set_selected(self, select):
        self._selected = select

    def set_ticker_length(self, tlen):
        self._ticker.setMaximumStrLen(tlen)

    def pulse(self):
        if self.is_selected():
            self._ticker.pulse()
        else:
            self._ticker.reset()

    def get_ticker_txt(self):
        return self._ticker.getText()

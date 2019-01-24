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
        self._ticker.setText(self._name.replace(self._path + "/", ""))

    def get_name(self):
        return self._name

    def get_full_path(self):
        return self._name

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

# Functions to enable sorting
#####################################################################################################
    def __eq__(self, other):
        if (self.is_directory() == other.is_directory()) and (self.get_name() == other.get_name()):
            return True
        else:
            return False

    def __ne__(self, other):
        if (self.is_directory() == other.is_file()) or (self.get_name() != other.get_name()):
            return True
        else:
            return False

    def __lt__(self, other):
        if (self.is_directory() and other.is_file()):
            return True
        elif (self.is_directory() == other.is_directory()) and (self.get_name() < other.get_name()):
            return True
        else:
            return False

    def __le__(self, other):
        if (self.is_directory() == other.is_directory()) and (self.get_name() == other.get_name()):
            return True
        elif (self.is_directory() and other.is_file()):
            return True
        elif (self.is_directory() == other.is_directory()) and (self.get_name() < other.get_name()):
            return True
        else:
            return False

    def __gt__(self, other):
        if (self.is_file() and other.is_directory()):
            return True
        elif (self.is_directory() == other.is_directory()) and (self.get_name() > other.get_name()):
            return True
        else:
            return False

    def __ge__(self, other):
        if (self.is_directory() == other.is_directory()) and (self.get_name() == other.get_name()):
            return True
        elif (self.is_file() and other.is_directory()):
            return True
        elif (self.is_directory() == other.is_directory()) and (self.get_name() > other.get_name()):
            return True
        else:
            return False

    def __repr__(self):
        self_is_file = str(int(self.is_file()))
        return "%s%s" % (self_is_file,self.get_name())

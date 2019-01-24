#from __future__ import print_function
import os
import logging
import socket
import threading
import time
from mpd import MPDClient
from .ticker import Ticker

#####################################################################################################
# Class requests a directory listing from MPD, handled in a seperate thread
#####################################################################################################
class mpd_request_files(threading.Thread):
    def __init__(self, mpdc, path):
        threading.Thread.__init__(self)
        self._mpd_client = mpdc
        self._path = path
        self._directory_listing = None
        self._error = False
        self._retries = 3

        self._logger = logging.getLogger(__name__)

    def run(self):
        loop = True
        while loop:
            try:
                self._logger.debug("Requesting directory listing for /" + self._path)
                self._directory_listing = self._mpd_client.lsinfo(self._path)
                self._error = False
                loop = False
            except socket.timeout:
                self._logger.debug("An error occured requesting listing: Socket timeout.")
                self._error = True
                self._retries -= 1
                if self._retries == 0: loop = False

    def error_occurred(self):
        return self._error

    def retries_left(self):
        return self._retries

    def get_path(self):
        return self._path

    def get_directory_list(self):
        return self._directory_listing

#####################################################################################################
# Encapsulates individual entries, returned from a MPD directory listing
#####################################################################################################
class mpd_entity(object):
    def __init__(self, mpd_data):
        self._name = ""
        self._full_path = ""
        self._ticker = Ticker(8)
        self._file = False
        self._directory = False
        self._selected = False

        if 'directory' in mpd_data:
            self._directory = True
            self._full_path = mpd_data["directory"]
        if 'file' in mpd_data:
            self._file = True
            self._full_path = mpd_data["file"]

        self._name = os.path.basename(self._full_path)
        self._ticker.setText(self._name)

    def __str__(self):
        if self.is_directory():
            return "DIR: " + self.get_name()
        else:
            return "FILE: " + self.get_name()

    def get_name(self):
        return self._name

    def get_full_path(self):
        return self._full_path

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

# MPD helper functions
#####################################################################################################
class MPDClient_extra(MPDClient):
    REPEAT_MODE_NONE = 0
    REPEAT_MODE_ALL = 1
    REPEAT_MODE_SINGLE = 2

    def __init__(self, conf):
        MPDClient.__init__(self)
        self._config = conf

    def load_config(self):
        # Load settings from config
        self.setvol(self._config.get("volume_current"))
        self.set_repeat(self._config.get("mpd_repeat"))
        self.set_shuffle(self._config.get("mpd_shuffle"))
        self.apply_source_config()

    def play_radio_station(self, station):
        set_station = True
        song_info = self.currentsong()

        if 'file' in song_info:
            if song_info['file'] == station.get_url():
                set_station = False

        if set_station:
            self.stop()
            self.clear()
            self.add(station.get_url())
            self.play()

    def play_track(self, songid = None):
        if songid is None:
            self.play()
        else:
            self.playid(songid)

    def set_repeat(self, mode):
        self._config.set("mpd_repeat", mode)
        if mode == self.REPEAT_MODE_ALL:
            self.repeat(1)
            self.single(0)
        elif mode == self.REPEAT_MODE_SINGLE:
            self.repeat(1)
            self.single(1)
        else:
            self.repeat(0)
            self.single(0)

    def toggle_repeat(self):
        cur_mode = self._config.get("mpd_repeat")
        new_mode = cur_mode + 1
        if new_mode > self.REPEAT_MODE_SINGLE:
            new_mode = 0
        self.set_repeat(new_mode)

    def set_shuffle(self, mode):
        if mode:
            self._config.set("mpd_shuffle", 1)
            self.random(1)
        else:
            self._config.set("mpd_shuffle", 0)
            self.random(0)

    def toggle_shuffle(self):
        if self._config.get("mpd_shuffle"):
            self.set_shuffle(0)
        else:
            self.set_shuffle(1)

    def mute(self):
        self._config.set("volume_b4_mute", self._config.get("volume_current"))
        self.set_volume(0)

    def unmute(self):
        current_vol = self._config.get("volume_b4_mute")
        self.set_volume(current_vol)

    def toggle_mute(self):
        if self._config.get("volume_current") == 0:
            self.unmute()
        else:
            self.mute()

    def volume_down(self):
        current_vol = self._config.get("volume_current")
        if current_vol > 0:
            current_vol -= 1
            self.set_volume(current_vol)

    def volume_up(self):
        current_vol = self._config.get("volume_current")
        if current_vol < 100:
            current_vol += 1
            self.set_volume(current_vol)

    def set_volume(self, current_vol):
        self._config.set("volume_current", current_vol)
        self.setvol(current_vol)

    def apply_source_config(self):
        network_path = self._config.get("mpd_source_dir") + "network"
        if os.path.islink(network_path):
            os.unlink(network_path)
        if self._config.get("mpd_source_net"):
            if not os.path.exists(network_path):
                os.symlink("/media/network", network_path)

        usb_path = self._config.get("mpd_source_dir") + "usb"
        if os.path.islink(usb_path):
            os.unlink(usb_path)
        if self._config.get("mpd_source_usb"):
            if not os.path.exists(usb_path):
                os.symlink("/media/usb", usb_path)


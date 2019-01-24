from __future__ import print_function
import logging
import socket
import threading
import time

class dlna_request_files(threading.Thread):

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
                self._directory_listing = self._mpd_client.listfiles(self._path)
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

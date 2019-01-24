from __future__ import print_function
import logging
import os.path
from .mpd_request_files import *
from .mpdentity import MPDEntity
from .screen_utils import *
from .ticker import Ticker
from . import commands

class Browser(object):
    BROWSER_STATE_INIT = 0
    BROWSER_STATE_SHOW_DIR = 1
    BROWSER_STATE_PLAYBACK = 2

    PLAYLIST_ACTION_CLEAR_THEN_ADD_DIR = 0
    PLAYLIST_ACTION_ADD = 1

    def __init__(self, home):
        self._parent = home
        self._curses = home.get_curses()
        self._sched = home.get_scheduler()
        self._active = False
        self._selected = False
        self._state = Browser.BROWSER_STATE_INIT

        self._paths = []
        self._last_path = None
        self._directory_list = None
        self._request_thread = None

        self._page = 0
        self._alt_display = False

        self._line1 = Ticker(20)
        self._line2 = Ticker(20)

        self._logger = logging.getLogger(__name__)
        self._job_main = self._sched.add_job(self._io_handler_main, 'interval', seconds=0.1)

    def close(self):
        self._active = False

    def __str__(self):
        return 'Browser(screen=%s)' % (self._curses.get_screen())

    def __repr__(self):
        return str(self)

    def control_name(self):
        return "Browser"

    def is_active(self):
        return self._active

    def set_active(self, act):
        self._active = act

    def is_selected(self):
        return self._selected

    def set_selected(self, val):
        self._selected = val

# Method called by the scheduler, proceeds based on current state
#####################################################################################################
    def _io_handler_main(self):
        self._logger.debug("Executing scheduled main task")
        # Pause job (stops lots of warnings)
        self._job_main.pause()

        # Get button presses
        if self.is_active():
            fp_command = self._curses.get_command()
            self._logger.debug("Currnet command: " + str(fp_command))

            # Check for a change of command
            if self._curses.has_command_changed():
                # Handle over arching button events seperately
                if fp_command == commands.CMD_POWER:
                    self._parent.set_poweroff(True)
                elif fp_command == commands.CMD_CDHD:
                    self.set_active(False)
                    self._parent.set_active(True)

            # Process directory request
            if self._request_thread is None:
                self._parent.get_MPDclient().ping()
            else:
                if not self._request_thread.isAlive():
                    if not self._request_thread.error_occurred():
                        dlist = []
                        for item in self._request_thread.get_directory_list():
                            tmp_mpde = MPDEntity(item)
                            dlist.append(tmp_mpde)
                        if len(dlist) == 0:
                            dlist.append(MPDEntity({ "Error": "N/A" }))
                        dlist.sort()
                        self._directory_list = screen_utils.convert_2_pages(dlist, 8)
                        self._request_thread = None

                        # Set appropriate page, and select item
                        if self._last_path is None:
                            self._page = 0
                            self._directory_list[0][0].set_selected(True)
                        else:
                            tmp_page_index = 0
                            for dentry_page in self._directory_list:
                                if self._last_path is None:
                                    break
                                else:
                                    for dentry in dentry_page:
                                        if self._last_path is None:
                                            break
                                        else:
                                            if dentry.is_directory():
                                                if self._last_path == dentry:
                                                    dentry.set_selected(True)
                                                    self._page = tmp_page_index
                                                    self._last_path = None
                                tmp_page_index += 1

            # Actions are dependent on machine state
            # No state
            if self._state == Browser.BROWSER_STATE_INIT:
                self._move_into_directory(MPDEntity({ "directory": "" }))
                self._state = Browser.BROWSER_STATE_SHOW_DIR
            # show current directory contents
            elif (self._state == Browser.BROWSER_STATE_SHOW_DIR):
                self._show_directory_contents(fp_command)
            # Show stream playback
            elif (self._state == Browser.BROWSER_STATE_PLAYBACK):
                self._show_stream_playback(fp_command)

        # Resume job
        self._job_main.resume()

# Method displays a list of files/directories
#####################################################################################################
    def _show_directory_contents(self, fp_command):
        screen_size = self._curses.get_screen().getmaxyx()

        if self._request_thread is None:
            # Check for a change of command
            if self._curses.has_command_changed():
                if fp_command == commands.CMD_UP:
                    last_dentry = None
                    for dentry in self._directory_list[self._page]:
                        if dentry.is_selected():
                            if last_dentry is None:
                                # Check there's another page
                                if self._page == 0:
                                    self._page = len(self._directory_list) - 1
                                else:
                                    self._page -= 1
                                dentry.set_selected(False)
                                tmp_dlist = self._directory_list[self._page]
                                tmp_dlist[-1].set_selected(True)
                            else:
                                last_dentry.set_selected(True)
                                dentry.set_selected(False)
                            break
                        last_dentry = dentry
                elif fp_command == commands.CMD_DOWN:
                    last_dentry = None
                    for dentry in self._directory_list[self._page]:
                        if not last_dentry is None:
                            last_dentry.set_selected(False)
                            dentry.set_selected(True)
                            break
                        if dentry.is_selected():
                            last_dentry = dentry
                    # We've reached the end of the page
                    if last_dentry.is_selected():
                        # Check there's another page
                        if len(self._directory_list) == (self._page + 1):
                            self._page = 0
                        else:
                            self._page += 1
                        last_dentry.set_selected(False)
                        self._directory_list[self._page][0].set_selected(True)
                elif (fp_command == commands.CMD_SELECT) or (fp_command == commands.CMD_RIGHT):
                    for dentry in self._directory_list[self._page]:
                        if dentry.is_selected():
                            if dentry.is_directory():
                                self._move_into_directory(dentry)
                            if dentry.is_file():
                                songid = self._generate_playlist(Browser.PLAYLIST_ACTION_ADD)
                                self._start_playback(songid)
                                self._state = Browser.BROWSER_STATE_PLAYBACK
                elif fp_command == commands.CMD_PLAY:
                    songid = self._generate_playlist(Browser.PLAYLIST_ACTION_CLEAR_THEN_ADD_DIR)
                    self._start_playback(songid)
                    self._state = Browser.BROWSER_STATE_PLAYBACK
                elif fp_command == commands.CMD_MODE:
                    self._state = Browser.BROWSER_STATE_PLAYBACK
                elif fp_command == commands.CMD_LEFT:
                    if len(self._paths) > 1:
                        self._move_outof_directory()
                    else:
                        self.set_active(False)
                        self._parent.set_active(True)

            # Draw screen
            self._curses.get_screen().clear()

            dentry_count = 0
            screen_line_num = 0
            screen_row_offset = 0
            ticker_length = 19

            if len(self._directory_list[self._page]) > 4:
                ticker_length = 8

            for dentry in self._directory_list[self._page]:
                dentry.set_ticker_length(ticker_length)

                if dentry_count == 4:
                    screen_line_num = 0
                    screen_row_offset = 11

                if dentry.is_selected():
                    self._curses.get_screen().addch(screen_line_num,screen_row_offset,'>')
                else:
                    self._curses.get_screen().addch(screen_line_num,screen_row_offset,' ')

                self._curses.get_screen().addstr(dentry.get_ticker_txt())
                dentry.pulse()
                screen_line_num += 1
                dentry_count += 1

            self._curses.get_screen().refresh()

#        elif self._request_thread.error_occurred():
#            self._curses.get_screen().clear()
#            self._curses.get_screen().addstr(1,0,('Retrying... ' + str(self._request_thread.retries_left())).center(20))
#            self._curses.get_screen().refresh()
        elif self._request_thread.isAlive():
            self._curses.get_screen().clear()
            self._curses.get_screen().addstr(1,0,'Please wait'.center(20))
            self._curses.get_screen().refresh()
#        else:
#            self._curses.get_screen().clear()
#            self._curses.get_screen().addstr(1,0,'Error'.center(20))
#            self._curses.get_screen().refresh()

# Method displays the playback of a particular file
#####################################################################################################
    def _show_stream_playback(self, fp_command):
        screen_size = self._curses.get_screen().getmaxyx()

        mpd_status = self._parent.get_MPDclient().status()
        current_volume = int(mpd_status["volume"])
        playback_state = mpd_status["state"]
        if "time" in mpd_status:
            playback_time = mpd_status["time"]
        else:
            playback_time = ""
        if "bitrate" in mpd_status:
            stream_bitrate = mpd_status["bitrate"]
        else:
           stream_bitrate = ""
        if "audio" in mpd_status:
            audiostream_info = mpd_status["audio"]
        else:
            audiostream_info = ""

        mpd_songinfo = self._parent.get_MPDclient().currentsong()
        if "album" in mpd_songinfo:
            song_album = mpd_songinfo["album"]
        else:
            song_album = None
        if "artist" in mpd_songinfo:
            song_artist = mpd_songinfo["artist"]
        else:
            song_artist = None
        if "file" in mpd_songinfo:
            song_file = os.path.basename(mpd_songinfo["file"])
        else:
            song_file = None
        if "title" in mpd_songinfo:
            song_title = mpd_songinfo["title"]
        else:
            song_title = None

        # Check for a change of command
        if self._curses.has_command_changed():
            if fp_command == commands.CMD_UP:
                self._volume_up(current_volume)
            elif fp_command == commands.CMD_DOWN:
                self._volume_down(current_volume)
            elif fp_command == commands.CMD_PLAY:
                self._start_playback()
            elif fp_command == commands.CMD_PAUSE:
                self._pause_playback()
            elif fp_command == commands.CMD_STOP:
                self._stop_playback()
            elif fp_command == commands.CMD_MODE:
                self._state = Browser.BROWSER_STATE_SHOW_DIR
            elif (fp_command == commands.CMD_LEFT) | (fp_command == commands.CMD_RIGHT):
                self._alt_display = self._alt_display ^ True
            elif fp_command == commands.CMD_PREVIOUS:
                self._prev_playback()
            elif fp_command == commands.CMD_NEXT:
                self._next_playback()

#            elif (fp_command & commands.CMD_DSPSEL_MASK) == commands.CMD_DSPSEL_MASK:
#                if fp_command == commands.CMD_DSPSEL1:
#                    self._presets_buttondown_count[0] += 1
#                elif fp_command == commands.CMD_DSPSEL2:
#                    self._presets_buttondown_count[1] += 1
#                elif fp_command == commands.CMD_DSPSEL3:
#                    self._presets_buttondown_count[2] += 1
#                elif fp_command == commands.CMD_DSPSEL4:
#                    self._presets_buttondown_count[3] += 1
#            elif (fp_command & commands.CMD_DSPSEL_MASK) == 0:
#                for i in range(0,4):
#                    if self._presets_buttondown_count[i] > 50:
#                        if playback_state == "play":
#                            for station in self._stations[self._page]:
#                                if station.is_selected():
#                                    self._presets[i + 1] = station
#                        else:
#                            self._presets[i + 1] = None
#                    # There's some 'bounce' so ignore any fast transitions, otherwise you start playing instead of clearing
#                    elif self._presets_buttondown_count[i] > 5:
#                        tmp_preset = self._presets[i + 1]
#                        if not tmp_preset is None:
#                            self.play_station(tmp_preset)
#                    self._presets_buttondown_count[i] = 0

        # Draw screen
        song_artist_album = None
        if not song_artist is None:
            song_artist_album = song_artist
        if not song_album is None:
            if not song_artist_album is None:
                song_artist_album += " - "
            song_artist_album += song_album
        if song_artist_album is None:
            self._line1.setText("")
        else:
            self._line1.setText(song_artist_album)

        if not song_title is None:
            self._line2.setText(song_title)
        elif not song_file is None:
            self._line2.setText(song_file)
        else:
            self._line2.setText()

        self._curses.get_screen().clear()
        if playback_state == "play":
            state_str = "Playing   "
        elif playback_state == "pause":
            state_str = "Paused    "
        else:
            state_str = "          "
        state_str += "  Vol: " + str(current_volume).rjust(3)
        self._curses.get_screen().addstr(0,0,state_str)
        if self._alt_display:
            line1 = stream_bitrate.rjust(4) + " kbps " + audiostream_info
            line2 = playback_time.rjust(11)
        else:
            line1 = self._line1.getText()
            line2 = self._line2.getText()
        self._curses.get_screen().addstr(1,0,line1)
        self._curses.get_screen().addstr(2,0,line2)
#        menu_str = ""
#        for i in range(1,5):
#            tmp_preset = self._presets[i]
#            if tmp_preset is None:
#                menu_str += "     "
#            else:
#                menu_str += tmp_preset.get_initials().center(5)
#        self._curses.get_screen().addstr(3,0,menu_str)

        self._line1.pulse()
        self._line2.pulse()

        self._curses.get_screen().refresh()

# Browser functions
#####################################################################################################
    def _move_into_directory(self, dentry):
        self._paths.append(dentry)
        self._logger.debug("Path stack:")
        for tmp_path in self._paths:
	        self._logger.debug(str(tmp_path))
        self._get_directory_list(self._paths[-1].get_full_path())

    def _move_outof_directory(self):
        self._last_path = self._paths[-1]
        del self._paths[-1]
        self._logger.debug("Path stack:")
        for tmp_path in self._paths:
	        self._logger.debug(str(tmp_path))
        self._get_directory_list(self._paths[-1].get_full_path())

    def _get_directory_list(self, path):
        self._request_thread = mpd_request_files(self._parent.get_MPDclient(), path)
        self._request_thread.start()

    def _generate_playlist(self, action):
        if action == Browser.PLAYLIST_ACTION_CLEAR_THEN_ADD_DIR:
            mpd_client = self._parent.get_MPDclient()
            mpd_client.clear()

            selected_dentry = None
            # First find what is selected
            for dentry in self._directory_list[self._page]:
                if dentry.is_selected():
                    selected_dentry = dentry

            # Add only the selected file, and the rest of the files in the directory
            selected_song_id = None
            if selected_dentry.is_file():
                for dentry_page in self._directory_list:
                    for dentry in dentry_page:
                        if dentry.is_file():
                            self._logger.debug("Adding track: " + str(dentry))
                            tmp_song_id = mpd_client.addid(dentry.get_full_path())
                            if selected_dentry == dentry:
                                self._logger.debug("Track matched, song ID: " + tmp_song_id)
                                selected_song_id = tmp_song_id
                return selected_song_id
            # Add everything in this directory
            elif selected_dentry.is_directory():
                self._generate_playlist_recursive(selected_dentry.get_full_path())
                return None
        elif action == Browser.PLAYLIST_ACTION_ADD:
            mpd_client = self._parent.get_MPDclient()

            selected_dentry = None
            # First find what is selected
            for dentry in self._directory_list[self._page]:
                if dentry.is_selected():
                    if dentry.is_file():
                        mpd_client.add(dentry.get_full_path())

    def _generate_playlist_recursive(self, path):
        mpd_client = self._parent.get_MPDclient()
        mpd_client.add(path)

# MPD functions
#####################################################################################################
    def _start_playback(self, songid = None):
        if songid is None:
            self._parent.get_MPDclient().play()
        else:
            self._parent.get_MPDclient().playid(songid)

    def _pause_playback(self):
        self._parent.get_MPDclient().pause()

    def _stop_playback(self):
        self._parent.get_MPDclient().stop()

    def _next_playback(self):
        self._parent.get_MPDclient().next()

    def _prev_playback(self):
        self._parent.get_MPDclient().previous()

    def _volume_down(self, current_vol):
        if current_vol > 0:
            current_vol -= 1
        self._parent.get_MPDclient().setvol(current_vol)

    def _volume_up(self, current_vol):
        if current_vol < 100:
            current_vol += 1
        self._parent.get_MPDclient().setvol(current_vol)

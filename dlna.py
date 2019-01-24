from __future__ import print_function
import logging
from .dlna_request_files import *
from .mpdentity import MPDEntity
from .screen_utils import *
from .ticker import Ticker
from . import commands

class DLNA(object):
    DLNA_STATE_INIT = 0
    DLNA_STATE_SHOW_DIR = 1
    DLNA_STATE_PLAYBACK = 2

    def __init__(self, home):
        self._parent = home
        self._curses = home.get_curses()
        self._sched = home.get_scheduler()
        self._active = False
        self._selected = False
        self._state = DLNA.DLNA_STATE_INIT

        self._paths = []
        self._directory_list = None
        self._request_thread = None

        self._page = 0
        self._alt_display = False

        self._line1 = Ticker(20)
        self._line2 = Ticker(20)

        self._logger = logging.getLogger(__name__)
        self._job_main = self._sched.add_job(self.io_handler_main, 'interval', seconds=0.1)

    def close(self):
        self._active = False

    def __str__(self):
        return 'DLNA(screen=%s)' % (self._curses.get_screen())

    def __repr__(self):
        return str(self)

    def control_name(self):
        return "DLNA"

    def is_active(self):
        return self._active

    def set_active(self, act):
        self._active = act

    def is_selected(self):
        return self._selected

    def set_selected(self, val):
        self._selected = val

    def io_handler_main(self):
        self._logger.debug("Executing scheduled main task")
        # Pause job (stops lots of warnings)
        self._job_main.pause()

        # Get button presses
        if self.is_active():
            fp_command = self._curses.get_command()

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
                            tmp_mpde = MPDEntity(item, self._request_thread.get_path())
                            if len(dlist) == 0:
                                tmp_mpde.set_selected(True)
                            dlist.append(tmp_mpde)
                        if len(dlist) == 0:
                            dlist.append(MPDEntity({ "Error": "N/A" }, ""))
                        self._directory_list = screen_utils.convert_2_pages(dlist, 8)
                        self._page = 0
                        self._request_thread = None

            # Actions are dependent on machine state
            # No state
            if self._state == DLNA.DLNA_STATE_INIT:
                self.move_into_directory("")
                self._state = DLNA.DLNA_STATE_SHOW_DIR
            # show current directory contents
            elif (self._state == DLNA.DLNA_STATE_SHOW_DIR):
                self.show_directory_contents(fp_command)
            # Show stream playback
            elif (self._state == DLNA.DLNA_STATE_PLAYBACK):
                self.show_stream_playback(fp_command)

        # Resume job
        self._job_main.resume()

#####################################################################################################
# I/O routines
    def show_directory_contents(self, fp_command):
        screen_size = self._curses.get_screen().getmaxyx()

        if self._request_thread is None:
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
            elif fp_command == commands.CMD_SELECT:
                for dentry in self._directory_list[self._page]:
                    if dentry.is_selected():
                        if dentry.is_directory():
                            self.move_into_directory(dentry.get_full_path())
                        if dentry.is_file():
                            songid = self.generate_playlist()
                            self.start_playback(songid)
                            self._state = DLNA.DLNA_STATE_PLAYBACK
            elif fp_command == commands.CMD_PLAY:
                songid = self.generate_playlist()
                self.start_playback(songid)
                self._state = DLNA.DLNA_STATE_PLAYBACK
            elif fp_command == commands.CMD_MODE:
                if len(self._paths) > 1:
                    self.move_out_directory()
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

        elif self._request_thread.error_occurred():
            self._curses.get_screen().clear()
            self._curses.get_screen().addstr(1,0,('Retrying... ' + str(self._request_thread.retries_left())).center(20))
            self._curses.get_screen().refresh()
        elif self._request_thread.isAlive():
            self._curses.get_screen().clear()
            self._curses.get_screen().addstr(1,0,'Please wait'.center(20))
            self._curses.get_screen().refresh()
        else:
            self._curses.get_screen().clear()
            self._curses.get_screen().addstr(1,0,'Error'.center(20))
            self._curses.get_screen().refresh()

    def show_stream_playback(self, fp_command):
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
            song_album = ""
        if "artist" in mpd_songinfo:
            song_artist = mpd_songinfo["artist"]
        else:
            song_artist = ""
        if "title" in mpd_songinfo:
            song_title = mpd_songinfo["title"]
        else:
            song_title = ""

        if fp_command == commands.CMD_UP:
            self.volume_up(current_volume)
        elif fp_command == commands.CMD_DOWN:
            self.volume_down(current_volume)
        elif fp_command == commands.CMD_PLAY:
            self.start_playback()
        elif fp_command == commands.CMD_PAUSE:
            self.pause_playback()
        elif fp_command == commands.CMD_STOP:
            self.stop_playback()
        elif fp_command == commands.CMD_MODE:
            self._state = DLNA.DLNA_STATE_SHOW_DIR
        elif (fp_command == commands.CMD_LEFT) | (fp_command == commands.CMD_RIGHT):
            self._alt_display = self._alt_display ^ True
        elif fp_command == commands.CMD_PREVIOUS:
            self.prev_playback()
        elif fp_command == commands.CMD_NEXT:
            self.next_playback()

#        elif (fp_command & commands.CMD_DSPSEL_MASK) == commands.CMD_DSPSEL_MASK:
#            if fp_command == commands.CMD_DSPSEL1:
#                self._presets_buttondown_count[0] += 1
#            elif fp_command == commands.CMD_DSPSEL2:
#                self._presets_buttondown_count[1] += 1
#            elif fp_command == commands.CMD_DSPSEL3:
#                self._presets_buttondown_count[2] += 1
#            elif fp_command == commands.CMD_DSPSEL4:
#                self._presets_buttondown_count[3] += 1
#        elif (fp_command & commands.CMD_DSPSEL_MASK) == 0:
#            for i in range(0,4):
#                if self._presets_buttondown_count[i] > 50:
#                    if playback_state == "play":
#                        for station in self._stations[self._page]:
#                            if station.is_selected():
#                                self._presets[i + 1] = station
#                    else:
#                        self._presets[i + 1] = None
#                # There's some 'bounce' so ignore any fast transitions, otherwise you start playing instead of clearing
#                elif self._presets_buttondown_count[i] > 5:
#                    tmp_preset = self._presets[i + 1]
#                    if not tmp_preset is None:
#                        self.play_station(tmp_preset)
#                self._presets_buttondown_count[i] = 0

        # Draw screen
        self._line1.setText(song_artist + " - " + song_album)
        self._line2.setText(song_title)
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

#####################################################################################################
# DLNA functions
    def move_into_directory(self, path):
        self._paths.append(path)
        self.get_directory_list(self._paths[-1])

    def move_out_directory(self):
        del self._paths[-1]
        self.get_directory_list(self._paths[-1])

    def get_directory_list(self, path):
        self._request_thread = dlna_request_files(self._parent.get_MPDclient(), path)
        self._request_thread.start()

    def generate_playlist(self):
        selected_dentry = None
        # First find what is selected
        for dentry_page in self._directory_list:
            for dentry in dentry_page:
                 selected_dentry = dentry

        mpd_client = self._parent.get_MPDclient()
        mpd_client.clear()
        songid = None

        if selected_dentry.is_file():
            mpd_client.add(selected_dentry.get_full_path())
#            # Add everything in this directory
#        elif selected_dentry.is_directory():
#            # Add everything in the selected directory
#
#        #mpd_client.add(self._paths[-1])
#        #return songid
#
#    def generate_playlist_recursive(self):


#####################################################################################################
# MPD functions
    def start_playback(self, songid = None):
        if songid is None:
            self._parent.get_MPDclient().play()
        else:
            self._parent.get_MPDclient().playid(songid)

    def pause_playback(self):
        self._parent.get_MPDclient().pause()

    def stop_playback(self):
        self._parent.get_MPDclient().stop()

    def next_playback(self):
        self._parent.get_MPDclient().next()

    def prev_playback(self):
        self._parent.get_MPDclient().previous()

    def volume_down(self, current_vol):
        if current_vol > 0:
            current_vol -= 1
        self._parent.get_MPDclient().setvol(current_vol)

    def volume_up(self, current_vol):
        if current_vol < 100:
            current_vol += 1
        self._parent.get_MPDclient().setvol(current_vol)

######################################################################################################
## SQL functions
#    def set_preset(self, preset, name, url):
#        sql_csr = self._parent.get_sqlcon().cursor()
#        sql_update = "REPLACE INTO radio_presets (preset, station_name, station_url) VALUES (\"" + str(preset) + "\", \"" + name + "\", \"" + url + "\")"
#        sql_csr.execute(sql_update)
#        self._parent.get_sqlcon().commit()
#
#    def del_preset(self, preset):
#        sql_csr = self._parent.get_sqlcon().cursor()
#        sql_update = "DELETE FROM radio_presets WHERE preset=\"" + str(preset) + "\""
#        sql_csr.execute(sql_update)
#        self._parent.get_sqlcon().commit()
#
#    def load_presets(self):
#        presets = [ None, None, None, None, None ]
#        sql_csr = self._parent.get_sqlcon().cursor()
#        sql_presets = "select preset, station_name, station_url from radio_presets"
#        sql_csr.execute(sql_presets)
#        rows = sql_csr.fetchall()
#        for tmp_preset in rows:
#            tmp_station = {}
#            tmp_station["name"] = tmp_preset[1]
#            tmp_station["url"] = tmp_preset[2]
#            presets[tmp_preset[0]] = tmp_station
#        self._presets = presets
#
#    def add_station(self, name, url):
#        sql_csr = self._parent.get_sqlcon().cursor()
#        sql_update = "INSERT INTO radio_stations (station_name, station_url) VALUES (\"" + name + "\", \"" + url + "\")"
#        sql_csr.execute(sql_update)
#        self._parent.get_sqlcon().commit()
#
#    def del_station(self, name):
#        sql_csr = self._parent.get_sqlcon().cursor()
#        sql_update = "DELETE FROM radio_stations WHERE station_name=\"" + name + "\""
#        sql_csr.execute(sql_update)
#        self._parent.get_sqlcon().commit()
#
#    def load_stations(self):
#        stations = []
#        sql_csr = self._parent.get_sqlcon().cursor()
#        sql_stations = "select station_name, station_url from radio_stations order by station_name"
#        sql_csr.execute(sql_stations)
#        rows = sql_csr.fetchall()
#        for tmp_station in rows:
#            tmp_entry = {}
#            tmp_entry['name'] = tmp_station[0]
#            tmp_entry['url'] = tmp_station[1]
#            if len(stations) == 0:
#                tmp_entry['selected'] = True
#            else:
#                tmp_entry['selected'] = False
#            stations.append(tmp_entry)
#        self._stations = stations
#
#    def create_tables(self):
#        sql_csr = self._parent.get_sqlcon().cursor()
#
#        # Check if table exist
#        sql_table_check = "SELECT name FROM sqlite_master WHERE type='table' AND name='radio_presets';"
#        sql_csr.execute(sql_table_check)
#        table_exists = sql_csr.fetchone()
#
#        if table_exists is None:
#            sql_table_create = "CREATE TABLE radio_presets (preset INTEGER PRIMARY KEY, station_name TEXT, station_url TEXT)"
#            sql_csr.execute(sql_table_create)
#            self._parent.get_sqlcon().commit()
#
#        # Check if table exist
#        sql_table_check = "SELECT name FROM sqlite_master WHERE type='table' AND name='radio_stations';"
#        sql_csr.execute(sql_table_check)
#        table_exists = sql_csr.fetchone()
#
#        if table_exists is None:
#            sql_table_create = "CREATE TABLE radio_stations (station_name TEXT, station_url TEXT)"
#            sql_csr.execute(sql_table_create)
#            self._parent.get_sqlcon().commit()
#
#            # Add some stations
#            self.add_station("Jolly Ol' Soul", "http://ice.somafm.com/jollysoul")
#            self.add_station("Xmas in Frisko", "http://ice.somafm.com/xmasinfrisko")
#            self.add_station("Christmas Rocks!", "http://ice.somafm.com/xmasrocks")
#            self.add_station("Christmas Lounge", "http://ice.somafm.com/christmas")
#            self.add_station("SF in SF", "http://ice.somafm.com/sfinsf")
#            self.add_station("PopTron", "http://ice.somafm.com/poptron")
#            self.add_station("BAGeL Radio", "http://ice.somafm.com/bagel")
#            self.add_station("Seven Inch Soul", "http://ice.somafm.com/7soul")
#            self.add_station("Beat Blender", "http://ice.somafm.com/beatblender")
#            self.add_station("The Trip", "http://ice.somafm.com/thetrip")
#            self.add_station("cliqhop idm", "http://ice.somafm.com/cliqhop")
#            self.add_station("Dub Step Beyond", "http://ice.somafm.com/dubstep")
#            self.add_station("ThistleRadio", "http://ice.somafm.com/thistle")
#            self.add_station("Folk Forward", "http://ice.somafm.com/folkfwd")
#            self.add_station("Covers", "http://ice.somafm.com/covers")
#            self.add_station("Doomed", "http://ice.somafm.com/doomed")
#            self.add_station("Secret Agent", "http://ice.somafm.com/secretagent")
#            self.add_station("Groove Salad", "http://ice.somafm.com/groovesalad")
#            self.add_station("Drone Zone", "http://ice.somafm.com/dronezone")
#            self.add_station("Fluid", "http://ice.somafm.com/fluid")
#            self.add_station("Lush", "http://ice.somafm.com/lush")
#            self.add_station("Illinois Street Lounge", "http://ice.somafm.com/illstreet")
#            self.add_station("Indie Pop Rocks!", "http://ice.somafm.com/indiepop")
#            self.add_station("Left Coast 70s", "http://ice.somafm.com/seventies")
#            self.add_station("Underground 80s", "http://ice.somafm.com/u80s")
#            self.add_station("Boot Liquor", "http://ice.somafm.com/bootliquor")
#            self.add_station("Digitalis", "http://ice.somafm.com/digitalis")
#            self.add_station("Metal Detector", "http://ice.somafm.com/metal")
#            self.add_station("Mission Control", "http://ice.somafm.com/missioncontrol")
#            self.add_station("SF 10-33", "http://ice.somafm.com/sf1033")
#            self.add_station("Deep Space One", "http://ice.somafm.com/deepspaceone")
#            self.add_station("Space Station Soma", "http://ice.somafm.com/spacestation")
#            self.add_station("Sonic Universe", "http://ice.somafm.com/sonicuniverse")
#            self.add_station("Suburbs of Goa", "http://ice.somafm.com/suburbsofgoa")
#            self.add_station("Black Rock FM", "http://ice.somafm.com/brfm")
#            self.add_station("DEF CON Radio", "http://ice.somafm.com/defcon")
#            self.add_station("Earwaves", "http://sfstream1.somafm.com:5100")
#            self.add_station("The Silent Channel", "http://ice.somafm.com/silent")

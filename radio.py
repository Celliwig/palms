from __future__ import print_function
import logging
import re
from .curses_wrapper import curses_wrapper
from .screen_utils import *
from .station import Station
from .ticker import Ticker
from . import commands

class Radio(object):
    RADIO_STATE_INIT = 0					# Start playback of previously selected station, or display station list
    RADIO_STATE_LIST_STATIONS = 1				# Display station list
    RADIO_STATE_PLAYBACK = 2					# Show playback of station

    def __init__(self, home):
        self._parent = home
        self._curses = home.get_curses()
        self._sched = home.get_scheduler()
        self._active = False
        self._selected = False
        self._state = Radio.RADIO_STATE_INIT
        self._current_station = ""
        self._page = -1
        self._alt_display = False

        self._station_ticker = Ticker(20)
        self._song_ticker = Ticker(20)

        # Create tables if necesary
        self.create_tables()

        self._presets = None
        self._presets_buttondown_count = [ 0, 0, 0, 0 ]
        self.load_presets()
        self._stations = None
        self.load_stations()

        self._logger = logging.getLogger(__name__)
        self._job = self._sched.add_job(self.io_handler, 'interval', seconds=0.1)

    def close(self):
        self._active = False

        # Save preset configuration
        for i in range(0,5):
            tmp_preset = self._presets[i]
            if tmp_preset is None:
                self.del_preset(i)
            else:
                self.set_preset(i, tmp_preset)

    def __str__(self):
        return 'Radio(screen=%s)' % (self._curses.get_screen())

    def __repr__(self):
        return str(self)

    def control_name(self):
        return "Radio"

    def is_active(self):
        return self._active

    def set_active(self, act):
        self._active = act
        if act:
            self._job.resume()
        else:
            self._job.pause()

    def is_selected(self):
        return self._selected

    def set_selected(self, val):
        self._selected = val

# Method called by the scheduler, proceeds based on current state
#####################################################################################################
    def io_handler(self):
        self._logger.debug("Executing scheduled task")
        # Pause job (stops lots of warnings)
        self._job.pause()

        # Get button presses
        if self.is_active():
            self._parent.get_MPDclient().ping()
            buttons = self._curses.get_command()

            # Check for a change of command
            if self._curses.has_command_changed():
                # Handle over arching button events seperately
                if buttons == commands.CMD_POWER:
                    # Save the current station as default if playing
                    mpd_status = self._parent.get_MPDclient().status()
                    playback_state = mpd_status["state"]
                    if playback_state == "play":
                        if not self._current_station == '':
                            tmp_station = Station("default", self._current_station)
                            self._presets[0] = tmp_station
                    else:
                        # Clear default station only if at some point we have started playback of a radio station
                        if not self._current_station == '':
                            self._presets[0] = None

                    self._parent.set_poweroff(True)

                # Home button
                elif buttons == commands.CMD_CDHD:
                    self.set_active(False)
                    self._parent.set_active(True)

            # Actions are dependent on machine state
            # Init
            if self._state == Radio.RADIO_STATE_INIT:
                # Check to see if there is a default station, otherwise just list
                if self._presets[0] is None:
                    self._state = Radio.RADIO_STATE_LIST_STATIONS
                else:
                    self.play_station(self._presets[0])
                    self._state = Radio.RADIO_STATE_PLAYBACK
            # List radio stations
            elif (self._state == Radio.RADIO_STATE_LIST_STATIONS):
                # Set the display start
                if self._page == -1:
                    tmp_page = 0
                    for station_page in self._stations:
                        for tmp_station in station_page:
                            if tmp_station.is_selected():
                                self._page = tmp_page
                        tmp_page += 1

                self.list_radio_stations(buttons)
            # Station selected
            elif (self._state == Radio.RADIO_STATE_PLAYBACK):
                self.show_stream_playback(buttons)

        # Resume job (should probably put this in a mutex)
        if self.is_active():
            self._job.resume()

# Display a list of stored radio stations
#####################################################################################################
    def list_radio_stations(self, buttons):
        screen_size = self._curses.get_screen().getmaxyx()

        # Check for a change of command
        if self._curses.has_command_changed():
            if buttons == commands.CMD_UP:
                last_station = None
                for station in self._stations[self._page]:
                    if station.is_selected():
                        if last_station is None:
                            # Check there's another page
                            if self._page == 0:
                                self._page = len(self._stations) - 1
                            else:
                                self._page -= 1
                            station.set_selected(False)
                            tmp_stations = self._stations[self._page]
                            tmp_stations[len(tmp_stations) - 1].set_selected(True)
                        else:
                            last_station.set_selected(True)
                            station.set_selected(False)
                        break
                    last_station = station
            elif buttons == commands.CMD_DOWN:
                last_station = None
                for station in self._stations[self._page]:
                    if not last_station is None:
                        last_station.set_selected(False)
                        station.set_selected(True)
                        break
                    if station.is_selected():
                        last_station = station
                # We've reached the end of the page
                if last_station.is_selected():
                    # Check there's another page
                    if len(self._stations) == (self._page + 1):
                        self._page = 0
                    else:
                        self._page += 1
                    last_station.set_selected(False)
                    self._stations[self._page][0].set_selected(True)
            elif buttons == commands.CMD_SELECT:
                for station in self._stations[self._page]:
                    if station.is_selected():
                        self.play_station(station)
                        self._state = Radio.RADIO_STATE_PLAYBACK
            # Back button
            elif buttons == commands.CMD_MODE:
                self.set_active(False)
                self._parent.set_active(True)

        # Draw screen
        self._curses.get_screen().clear()
        station_count = 0
        screen_line_num = 0
        screen_row_offset = 0
        for station in self._stations[self._page]:
            if station_count == 4:
                screen_line_num = 0
                screen_row_offset = 11
            if station.is_selected():
                self._curses.get_screen().addch(screen_line_num,screen_row_offset,'>')
            else:
                self._curses.get_screen().addch(screen_line_num,screen_row_offset,' ')
            self._curses.get_screen().addstr(station.get_ticker_txt())
            station.pulse()
            screen_line_num += 1
            station_count += 1

        self._curses.get_screen().refresh()

# Display playback information
#####################################################################################################
    def show_stream_playback(self, buttons):
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
        if "name" in mpd_songinfo:
            song_station = mpd_songinfo["name"]
            song_station = self.extract_station_name(song_station)
        else:
            song_station = ""
        if "title" in mpd_songinfo:
            song_name = mpd_songinfo["title"]
        else:
            song_name = ""

        # Check for a change of command
        if self._curses.has_command_changed():
            if buttons == commands.CMD_UP:
                self.volume_up(current_volume)
            elif buttons == commands.CMD_DOWN:
                self.volume_down(current_volume)
            elif buttons == commands.CMD_PLAY:
                self.start_playback()
            elif buttons == commands.CMD_PAUSE:
                self.pause_playback()
            elif buttons == commands.CMD_STOP:
                self.stop_playback()
            elif buttons == commands.CMD_MODE:
                self._state = Radio.RADIO_STATE_LIST_STATIONS
            elif (buttons == commands.CMD_LEFT) | (buttons == commands.CMD_RIGHT):
                self._alt_display = self._alt_display ^ True
            # Support selecting radio preset from IR remote, using numeric keys
            elif buttons == commands.CMD_1:
                #self._logger.debug("IR remoted selected radio preset 1.")
                tmp_preset = self._presets[1]
                if not tmp_preset is None:
                    self.play_station(tmp_preset)
            elif buttons == commands.CMD_2:
                #self._logger.debug("IR remoted selected radio preset 2.")
                tmp_preset = self._presets[2]
                if not tmp_preset is None:
                    self.play_station(tmp_preset)
            elif buttons == commands.CMD_3:
                #self._logger.debug("IR remoted selected radio preset 3.")
                tmp_preset = self._presets[3]
                if not tmp_preset is None:
                    self.play_station(tmp_preset)
            elif buttons == commands.CMD_4:
                #self._logger.debug("IR remoted selected radio preset 4.")
                tmp_preset = self._presets[4]
                if not tmp_preset is None:
                    self.play_station(tmp_preset)
            # Handle preset selection, and saving
            elif (buttons & commands.CMD_DSPSEL_MASK) == commands.CMD_DSPSEL_MASK:
                if buttons == commands.CMD_DSPSEL1:
                    # If the button has been depressed for more than 5 secs
                    if self._presets_buttondown_count[0] > 15:
                        if playback_state == "play":
                            for station in self._stations[self._page]:
                                if station.is_selected():
                                    self._presets[1] = station
                        else:
                            self._presets[1] = None
                    else:
                        self._presets_buttondown_count[0] += 1
                elif buttons == commands.CMD_DSPSEL2:
                    # If the button has been depressed for more than 5 secs
                    if self._presets_buttondown_count[1] > 15:
                        if playback_state == "play":
                            for station in self._stations[self._page]:
                                if station.is_selected():
                                    self._presets[2] = station
                        else:
                            self._presets[2] = None
                    else:
                        self._presets_buttondown_count[1] += 1
                elif buttons == commands.CMD_DSPSEL3:
                    # If the button has been depressed for more than 5 secs
                    if self._presets_buttondown_count[2] > 15:
                        if playback_state == "play":
                            for station in self._stations[self._page]:
                                if station.is_selected():
                                    self._presets[3] = station
                        else:
                            self._presets[3] = None
                    else:
                        self._presets_buttondown_count[2] += 1
                elif buttons == commands.CMD_DSPSEL4:
                    # If the button has been depressed for more than 5 secs
                    if self._presets_buttondown_count[3] > 15:
                        if playback_state == "play":
                            for station in self._stations[self._page]:
                                if station.is_selected():
                                    self._presets[4] = station
                        else:
                            self._presets[4] = None
                    else:
                        self._presets_buttondown_count[3] += 1
            # This is a catch all, so has to be last
            elif (buttons & commands.CMD_DSPSEL_MASK) == 0:
                for i in range(0,4):
                    # There's some 'bounce' so ignore any fast transitions, otherwise you start playing instead of clearing
                    if self._presets_buttondown_count[i] > 1:
                        tmp_preset = self._presets[i + 1]
                        if not tmp_preset is None:
                            self.play_station(tmp_preset)
                    self._presets_buttondown_count[i] = 0

        # Draw screen
        self._station_ticker.setText(song_station)
        self._song_ticker.setText(song_name)
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
            line1 = self._station_ticker.getText()
            line2 = self._song_ticker.getText()
        self._curses.get_screen().addstr(1,0,line1)
        self._curses.get_screen().addstr(2,0,line2)
        menu_str = ""
        for i in range(1,5):
            tmp_preset = self._presets[i]
            if tmp_preset is None:
                menu_str += "     "
            else:
                menu_str += tmp_preset.get_initials().center(5)
        self._curses.get_screen().addstr(3,0,menu_str)

        self._station_ticker.pulse()
        self._song_ticker.pulse()

        self._curses.get_screen().refresh()

#####################################################################################################
# MPD functions
    def play_station(self, station):
        if station.get_url() != self._current_station:
            self._current_station = station.get_url()

            self.stop_playback()
            self._parent.get_MPDclient().clear()
            self._parent.get_MPDclient().add(self._current_station)
            self.start_playback()

    def start_playback(self):
        self._parent.get_MPDclient().play()

    def pause_playback(self):
        self._parent.get_MPDclient().pause()

    def stop_playback(self):
        self._parent.get_MPDclient().stop()

    def volume_down(self, current_vol):
        if current_vol > 0:
            current_vol -= 1
        self._parent.get_MPDclient().setvol(current_vol)

    def volume_up(self, current_vol):
        if current_vol < 100:
            current_vol += 1
        self._parent.get_MPDclient().setvol(current_vol)

    def extract_station_name(self, station):
        return re.search('^([0-9A-Za-z ]+)', station).group(1)

#####################################################################################################
# SQL functions
    def set_preset(self, preset, station):
        sql_csr = self._parent.get_sqlcon().cursor()
        sql_update = "REPLACE INTO radio_presets (preset, station_name, station_url) VALUES (\"" + str(preset) + "\", \"" + station.get_name() + "\", \"" + station.get_url() + "\")"
        sql_csr.execute(sql_update)
        self._parent.get_sqlcon().commit()

    def del_preset(self, preset):
        sql_csr = self._parent.get_sqlcon().cursor()
        sql_update = "DELETE FROM radio_presets WHERE preset=\"" + str(preset) + "\""
        sql_csr.execute(sql_update)
        self._parent.get_sqlcon().commit()

    def load_presets(self):
        presets = [ None, None, None, None, None ]
        sql_csr = self._parent.get_sqlcon().cursor()
        sql_presets = "select preset, station_name, station_url from radio_presets"
        sql_csr.execute(sql_presets)
        rows = sql_csr.fetchall()
        for tmp_preset in rows:
            tmp_station = Station(tmp_preset[1], tmp_preset[2])
            presets[tmp_preset[0]] = tmp_station
        self._presets = presets

    def add_station(self, name, url):
        sql_csr = self._parent.get_sqlcon().cursor()
        sql_update = "INSERT INTO radio_stations (station_name, station_url) VALUES (\"" + name + "\", \"" + url + "\")"
        sql_csr.execute(sql_update)
        self._parent.get_sqlcon().commit()

    def del_station(self, name):
        sql_csr = self._parent.get_sqlcon().cursor()
        sql_update = "DELETE FROM radio_stations WHERE station_name=\"" + name + "\""
        sql_csr.execute(sql_update)
        self._parent.get_sqlcon().commit()

    def load_stations(self):
        stations = []
        sql_csr = self._parent.get_sqlcon().cursor()
        sql_stations = "select station_name, station_url from radio_stations order by station_name"
        sql_csr.execute(sql_stations)
        rows = sql_csr.fetchall()
        tmp_selected = True
        for tmp_station in rows:
            tmp_station = Station(tmp_station[0], tmp_station[1], tmp_selected)
            tmp_selected = False
            stations.append(tmp_station)
        self._stations = screen_utils.convert_2_pages(stations,8)

    def create_tables(self):
        sql_csr = self._parent.get_sqlcon().cursor()

        # Check if table exist
        sql_table_check = "SELECT name FROM sqlite_master WHERE type='table' AND name='radio_presets';"
        sql_csr.execute(sql_table_check)
        table_exists = sql_csr.fetchone()

        if table_exists is None:
            sql_table_create = "CREATE TABLE radio_presets (preset INTEGER PRIMARY KEY, station_name TEXT, station_url TEXT)"
            sql_csr.execute(sql_table_create)
            self._parent.get_sqlcon().commit()

        # Check if table exist
        sql_table_check = "SELECT name FROM sqlite_master WHERE type='table' AND name='radio_stations';"
        sql_csr.execute(sql_table_check)
        table_exists = sql_csr.fetchone()

        if table_exists is None:
            sql_table_create = "CREATE TABLE radio_stations (station_name TEXT, station_url TEXT)"
            sql_csr.execute(sql_table_create)
            self._parent.get_sqlcon().commit()

            # Add some stations
            # SomaFM
            self.add_station("Jolly Ol' Soul", "http://ice.somafm.com/jollysoul")
            self.add_station("Xmas in Frisko", "http://ice.somafm.com/xmasinfrisko")
            self.add_station("Christmas Rocks!", "http://ice.somafm.com/xmasrocks")
            self.add_station("Christmas Lounge", "http://ice.somafm.com/christmas")
            self.add_station("SF in SF", "http://ice.somafm.com/sfinsf")
            self.add_station("PopTron", "http://ice.somafm.com/poptron")
            self.add_station("BAGeL Radio", "http://ice.somafm.com/bagel")
            self.add_station("Seven Inch Soul", "http://ice.somafm.com/7soul")
            self.add_station("Beat Blender", "http://ice.somafm.com/beatblender")
            self.add_station("The Trip", "http://ice.somafm.com/thetrip")
            self.add_station("cliqhop idm", "http://ice.somafm.com/cliqhop")
            self.add_station("Dub Step Beyond", "http://ice.somafm.com/dubstep")
            self.add_station("ThistleRadio", "http://ice.somafm.com/thistle")
            self.add_station("Folk Forward", "http://ice.somafm.com/folkfwd")
            self.add_station("Covers", "http://ice.somafm.com/covers")
            self.add_station("Doomed", "http://ice.somafm.com/doomed")
            self.add_station("Secret Agent", "http://ice.somafm.com/secretagent")
            self.add_station("Groove Salad", "http://ice.somafm.com/groovesalad")
            self.add_station("Drone Zone", "http://ice.somafm.com/dronezone")
            self.add_station("Fluid", "http://ice.somafm.com/fluid")
            self.add_station("Lush", "http://ice.somafm.com/lush")
            self.add_station("Illinois Street Lounge", "http://ice.somafm.com/illstreet")
            self.add_station("Indie Pop Rocks!", "http://ice.somafm.com/indiepop")
            self.add_station("Left Coast 70s", "http://ice.somafm.com/seventies")
            self.add_station("Underground 80s", "http://ice.somafm.com/u80s")
            self.add_station("Boot Liquor", "http://ice.somafm.com/bootliquor")
            self.add_station("Digitalis", "http://ice.somafm.com/digitalis")
            self.add_station("Metal Detector", "http://ice.somafm.com/metal")
            self.add_station("Mission Control", "http://ice.somafm.com/missioncontrol")
            self.add_station("SF 10-33", "http://ice.somafm.com/sf1033")
            self.add_station("Deep Space One", "http://ice.somafm.com/deepspaceone")
            self.add_station("Space Station Soma", "http://ice.somafm.com/spacestation")
            self.add_station("Sonic Universe", "http://ice.somafm.com/sonicuniverse")
            self.add_station("Suburbs of Goa", "http://ice.somafm.com/suburbsofgoa")
            self.add_station("Black Rock FM", "http://ice.somafm.com/brfm")
            self.add_station("DEF CON Radio", "http://ice.somafm.com/defcon")
            self.add_station("Earwaves", "http://sfstream1.somafm.com:5100")
            self.add_station("The Silent Channel", "http://ice.somafm.com/silent")
            # FolkAlley
            self.add_station("Folk Alley", "https://stream.wksu.org/wksu2.mp3.128")

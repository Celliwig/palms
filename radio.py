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

    def __init__(self, home, conf, mpdc):
        self._parent = home
        self._config = conf
        self._mpd_client = mpdc

        self._curses = home.get_curses()
        self._sched = home.get_scheduler()
        self._active = False
        self._selected = False
        self._state = Radio.RADIO_STATE_INIT
        self._page = -1
        self._alt_display = False

        self._station_ticker = Ticker(20)
        self._song_ticker = Ticker(20)

        # Create tables if necesary
        self._create_tables()

        self._presets = None
        self._presets_buttondown_count = [ 0, 0, 0, 0 ]
        self._load_presets()
        self._stations = None
        self._load_stations()

        self._logger = logging.getLogger(__name__)
        self._job = self._sched.add_job(self._io_handler, 'interval', seconds=0.1)

    def close(self):
        self._active = False

        # Save preset configuration
        for i in range(0,9):
            tmp_preset = self._presets[i]
            if tmp_preset is None:
                self._del_preset(i)
            else:
                self._set_preset(i, tmp_preset)

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

    def _save_default(self):
        # Save the current station as default if playing
        tmp_station = None

        mpd_status = self._mpd_client.status()
        if mpd_status["state"] == "play":
            song_info = self._mpd_client.currentsong()
            if 'file' in song_info:
                tmp_station = Station("default", song_info['file'])

        self._presets[0] = tmp_station

    def _extract_station_name(self, station):
        return re.search('^([0-9A-Za-z ]+)', station).group(1)

# Method called by the scheduler, proceeds based on current state
#####################################################################################################
    def _io_handler(self):
        self._logger.debug("Executing scheduled task")
        # Pause job (stops lots of warnings)
        self._job.pause()

        # Get button presses
        if self.is_active():
            self._mpd_client.ping()
            fp_command = self._curses.get_command()

            # Actions are dependent on machine state
            # Init
            if self._state == Radio.RADIO_STATE_INIT:
                # Check to see if there is a default station, otherwise just list
                if self._presets[0] is None:
                    self._state = Radio.RADIO_STATE_LIST_STATIONS
                else:
                    self._mpd_client.play_radio_station(self._presets[0])
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

                self._list_radio_stations(fp_command)
            # Station selected
            elif (self._state == Radio.RADIO_STATE_PLAYBACK):
                self._show_stream_playback(fp_command)

            # Handle over arching button events seperately
            # Check for a change of command
            if self._curses.has_command_changed():
                # Power button
                if fp_command == commands.CMD_POWER:
                    self._save_default()
                    self._parent.set_poweroff(True)
                # Home button
                elif fp_command == commands.CMD_CDHD:
                    self._save_default()
                    self.set_active(False)
                    self._parent.set_active(True)
                    self._state = Radio.RADIO_STATE_INIT
                elif fp_command == commands.CMD_MUTE:
                    self._mpd_client.toggle_mute()

        # Resume job (should probably put this in a mutex)
        if self.is_active():
            self._job.resume()

# Display a list of stored radio stations
#####################################################################################################
    def _list_radio_stations(self, fp_command):
        screen_size = self._curses.get_screen().getmaxyx()

        # Check for a change of command
        if self._curses.has_command_changed():
            if fp_command == commands.CMD_UP:
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
            elif fp_command == commands.CMD_DOWN:
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
            elif (fp_command == commands.CMD_SELECT) or (fp_command == commands.CMD_RIGHT):
                for station in self._stations[self._page]:
                    if station.is_selected():
                        self._mpd_client.play_radio_station(station)
                        self._state = Radio.RADIO_STATE_PLAYBACK
            elif fp_command == commands.CMD_MODE:
                self._state = Radio.RADIO_STATE_PLAYBACK
            elif fp_command == commands.CMD_LEFT:
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
    def _show_stream_playback(self, fp_command):
        screen_size = self._curses.get_screen().getmaxyx()

        mpd_status = self._mpd_client.status()
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

        mpd_songinfo = self._mpd_client.currentsong()
        if "name" in mpd_songinfo:
            song_station = mpd_songinfo["name"]
            song_station = self._extract_station_name(song_station)
        else:
            song_station = ""
        if "title" in mpd_songinfo:
            song_name = mpd_songinfo["title"]
        else:
            song_name = ""

        # Check for a change of command
        if self._curses.has_command_changed():
            if fp_command == commands.CMD_UP:
                self._mpd_client.volume_up()
            elif fp_command == commands.CMD_DOWN:
                self._mpd_client.volume_down()
            elif fp_command == commands.CMD_PLAY:
                self._mpd_client.play()
            elif fp_command == commands.CMD_PAUSE:
                self._mpd_client.pause()
            elif fp_command == commands.CMD_STOP:
                self._mpd_client.stop()
            elif fp_command == commands.CMD_MODE:
                self._state = Radio.RADIO_STATE_LIST_STATIONS
            elif (fp_command == commands.CMD_LEFT) | (fp_command == commands.CMD_RIGHT):
                self._alt_display = self._alt_display ^ True
            # Support selecting radio preset from IR remote, using numeric keys
            elif fp_command == commands.CMD_1:
                #self._logger.debug("IR remoted selected radio preset 1.")
                tmp_preset = self._presets[1]
                if not tmp_preset is None:
                    self._mpd_client.play_radio_station(tmp_preset)
            elif fp_command == commands.CMD_2:
                #self._logger.debug("IR remoted selected radio preset 2.")
                tmp_preset = self._presets[2]
                if not tmp_preset is None:
                    self._mpd_client.play_radio_station(tmp_preset)
            elif fp_command == commands.CMD_3:
                #self._logger.debug("IR remoted selected radio preset 3.")
                tmp_preset = self._presets[3]
                if not tmp_preset is None:
                    self._mpd_client.play_radio_station(tmp_preset)
            elif fp_command == commands.CMD_4:
                #self._logger.debug("IR remoted selected radio preset 4.")
                tmp_preset = self._presets[4]
                if not tmp_preset is None:
                    self._mpd_client.play_radio_station(tmp_preset)
            elif fp_command == commands.CMD_5:
                #self._logger.debug("IR remoted selected radio preset 5.")
                tmp_preset = self._presets[5]
                if not tmp_preset is None:
                    self._mpd_client.play_radio_station(tmp_preset)
            elif fp_command == commands.CMD_6:
                #self._logger.debug("IR remoted selected radio preset 6.")
                tmp_preset = self._presets[6]
                if not tmp_preset is None:
                    self._mpd_client.play_radio_station(tmp_preset)
            elif fp_command == commands.CMD_7:
                #self._logger.debug("IR remoted selected radio preset 7.")
                tmp_preset = self._presets[7]
                if not tmp_preset is None:
                    self._mpd_client.play_radio_station(tmp_preset)
            elif fp_command == commands.CMD_8:
                #self._logger.debug("IR remoted selected radio preset 8.")
                tmp_preset = self._presets[8]
                if not tmp_preset is None:
                    self._mpd_client.play_radio_station(tmp_preset)

            # Handle preset selection, and saving
            elif (fp_command & commands.CMD_DSPSEL_MASK) == commands.CMD_DSPSEL_MASK:
                presets_bank = 0					# Select which bank of presets to update
                if self._alt_display: presets_bank = 4

                if fp_command == commands.CMD_DSPSEL1:
                    # If the button has been depressed for more than 5 secs
                    if self._presets_buttondown_count[0] > 15:
                        if playback_state == "play":
                            for station in self._stations[self._page]:
                                if station.is_selected():
                                    self._presets[1 + presets_bank] = station
                        else:
                            self._presets[1 + presets_bank] = None
                    else:
                        self._presets_buttondown_count[0] += 1
                elif fp_command == commands.CMD_DSPSEL2:
                    # If the button has been depressed for more than 5 secs
                    if self._presets_buttondown_count[1] > 15:
                        if playback_state == "play":
                            for station in self._stations[self._page]:
                                if station.is_selected():
                                    self._presets[2 + presets_bank] = station
                        else:
                            self._presets[2 + presets_bank] = None
                    else:
                        self._presets_buttondown_count[1] += 1
                elif fp_command == commands.CMD_DSPSEL3:
                    # If the button has been depressed for more than 5 secs
                    if self._presets_buttondown_count[2] > 15:
                        if playback_state == "play":
                            for station in self._stations[self._page]:
                                if station.is_selected():
                                    self._presets[3 + presets_bank] = station
                        else:
                            self._presets[3 + presets_bank] = None
                    else:
                        self._presets_buttondown_count[2] += 1
                elif fp_command == commands.CMD_DSPSEL4:
                    # If the button has been depressed for more than 5 secs
                    if self._presets_buttondown_count[3] > 15:
                        if playback_state == "play":
                            for station in self._stations[self._page]:
                                if station.is_selected():
                                    self._presets[4 + presets_bank] = station
                        else:
                            self._presets[4 + presets_bank] = None
                    else:
                        self._presets_buttondown_count[3] += 1
            # This is a catch all, so has to be last
            elif (fp_command & commands.CMD_DSPSEL_MASK) == 0:
                for i in range(0,4):
                    # There's some 'bounce' so ignore any fast transitions, otherwise you start playing instead of clearing
                    if self._presets_buttondown_count[i] > 1:
                        if self._alt_display:
                            tmp_preset = self._presets[i + 5]
                        else:
                            tmp_preset = self._presets[i + 1]

                        if not tmp_preset is None:
                            self._mpd_client.play_radio_station(tmp_preset)
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
            if self._alt_display:
                tmp_preset = self._presets[i + 4]
            else:
                tmp_preset = self._presets[i]
            if tmp_preset is None:
                menu_str += "     "
            else:
                menu_str += tmp_preset.get_initials().center(5)
        self._curses.get_screen().addstr(3,0,menu_str)

        self._station_ticker.pulse()
        self._song_ticker.pulse()

        self._curses.get_screen().refresh()

# SQL functions
#####################################################################################################
    def _set_preset(self, preset, station):
        sql_csr = self._config.get_sqlcon().cursor()
        sql_update = "REPLACE INTO radio_presets (preset, station_name, station_url) VALUES (\"" + str(preset) + "\", \"" + station.get_name() + "\", \"" + station.get_url() + "\")"
        sql_csr.execute(sql_update)
        self._config.get_sqlcon().commit()

    def _del_preset(self, preset):
        sql_csr = self._config.get_sqlcon().cursor()
        sql_update = "DELETE FROM radio_presets WHERE preset=\"" + str(preset) + "\""
        sql_csr.execute(sql_update)
        self._config.get_sqlcon().commit()

    def _load_presets(self):
        presets = [ None, None, None, None, None, None, None, None, None ]
        sql_csr = self._config.get_sqlcon().cursor()
        sql_presets = "select preset, station_name, station_url from radio_presets"
        sql_csr.execute(sql_presets)
        rows = sql_csr.fetchall()
        for tmp_preset in rows:
            tmp_station = Station(tmp_preset[1], tmp_preset[2])
            presets[tmp_preset[0]] = tmp_station
        self._presets = presets

    def _add_station(self, name, url):
        sql_csr = self._config.get_sqlcon().cursor()
        sql_update = "INSERT INTO radio_stations (station_name, station_url) VALUES (\"" + name + "\", \"" + url + "\")"
        sql_csr.execute(sql_update)
        self._config.get_sqlcon().commit()

    def _del_station(self, name):
        sql_csr = self._config.get_sqlcon().cursor()
        sql_update = "DELETE FROM radio_stations WHERE station_name=\"" + name + "\""
        sql_csr.execute(sql_update)
        self._config.get_sqlcon().commit()

    def _load_stations(self):
        stations = []
        sql_csr = self._config.get_sqlcon().cursor()
        sql_stations = "select station_name, station_url from radio_stations order by station_name"
        sql_csr.execute(sql_stations)
        rows = sql_csr.fetchall()
        tmp_selected = True
        for tmp_station in rows:
            tmp_station = Station(tmp_station[0], tmp_station[1], tmp_selected)
            tmp_selected = False
            stations.append(tmp_station)
        self._stations = screen_utils.convert_2_pages(stations,8)

    def _create_tables(self):
        sql_csr = self._config.get_sqlcon().cursor()

        # Check if table exist
        sql_table_check = "SELECT name FROM sqlite_master WHERE type='table' AND name='radio_presets';"
        sql_csr.execute(sql_table_check)
        table_exists = sql_csr.fetchone()

        if table_exists is None:
            sql_table_create = "CREATE TABLE radio_presets (preset INTEGER PRIMARY KEY, station_name TEXT, station_url TEXT)"
            sql_csr.execute(sql_table_create)
            self._config.get_sqlcon().commit()

        # Check if table exist
        sql_table_check = "SELECT name FROM sqlite_master WHERE type='table' AND name='radio_stations';"
        sql_csr.execute(sql_table_check)
        table_exists = sql_csr.fetchone()

        if table_exists is None:
            sql_table_create = "CREATE TABLE radio_stations (station_name TEXT, station_url TEXT)"
            sql_csr.execute(sql_table_create)
            self._config.get_sqlcon().commit()

            # Add some stations
            # SomaFM
            self._add_station("Jolly Ol' Soul", "http://ice.somafm.com/jollysoul")
            self._add_station("Xmas in Frisko", "http://ice.somafm.com/xmasinfrisko")
            self._add_station("Christmas Rocks!", "http://ice.somafm.com/xmasrocks")
            self._add_station("Christmas Lounge", "http://ice.somafm.com/christmas")
            self._add_station("SF in SF", "http://ice.somafm.com/sfinsf")
            self._add_station("PopTron", "http://ice.somafm.com/poptron")
            self._add_station("BAGeL Radio", "http://ice.somafm.com/bagel")
            self._add_station("Seven Inch Soul", "http://ice.somafm.com/7soul")
            self._add_station("Beat Blender", "http://ice.somafm.com/beatblender")
            self._add_station("The Trip", "http://ice.somafm.com/thetrip")
            self._add_station("cliqhop idm", "http://ice.somafm.com/cliqhop")
            self._add_station("Dub Step Beyond", "http://ice.somafm.com/dubstep")
            self._add_station("ThistleRadio", "http://ice.somafm.com/thistle")
            self._add_station("Folk Forward", "http://ice.somafm.com/folkfwd")
            self._add_station("Covers", "http://ice.somafm.com/covers")
            self._add_station("Doomed", "http://ice.somafm.com/doomed")
            self._add_station("Secret Agent", "http://ice.somafm.com/secretagent")
            self._add_station("Groove Salad", "http://ice.somafm.com/groovesalad")
            self._add_station("Drone Zone", "http://ice.somafm.com/dronezone")
            self._add_station("Fluid", "http://ice.somafm.com/fluid")
            self._add_station("Lush", "http://ice.somafm.com/lush")
            self._add_station("Illinois Street Lounge", "http://ice.somafm.com/illstreet")
            self._add_station("Indie Pop Rocks!", "http://ice.somafm.com/indiepop")
            self._add_station("Left Coast 70s", "http://ice.somafm.com/seventies")
            self._add_station("Underground 80s", "http://ice.somafm.com/u80s")
            self._add_station("Boot Liquor", "http://ice.somafm.com/bootliquor")
            self._add_station("Digitalis", "http://ice.somafm.com/digitalis")
            self._add_station("Metal Detector", "http://ice.somafm.com/metal")
            self._add_station("Mission Control", "http://ice.somafm.com/missioncontrol")
            self._add_station("SF 10-33", "http://ice.somafm.com/sf1033")
            self._add_station("Deep Space One", "http://ice.somafm.com/deepspaceone")
            self._add_station("Space Station Soma", "http://ice.somafm.com/spacestation")
            self._add_station("Sonic Universe", "http://ice.somafm.com/sonicuniverse")
            self._add_station("Suburbs of Goa", "http://ice.somafm.com/suburbsofgoa")
            self._add_station("Black Rock FM", "http://ice.somafm.com/brfm")
            self._add_station("DEF CON Radio", "http://ice.somafm.com/defcon")
            self._add_station("Earwaves", "http://sfstream1.somafm.com:5100")
            self._add_station("The Silent Channel", "http://ice.somafm.com/silent")
            # FolkAlley
            self._add_station("Folk Alley", "https://stream.wksu.org/wksu2.mp3.128")

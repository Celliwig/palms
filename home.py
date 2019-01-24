from __future__ import print_function
import logging
from .radio import Radio
from .browser import Browser
from .setup import Setup
from . import commands

class Home(object):
    def __init__(self, ncrs, schd, conf, mpdc):
        self._curses = ncrs
        self._sched = schd
        self._config = conf
        self._mpd_client = mpdc
        self._active = True
        self._poweroff = False

        # Add widgets
        self._controls = []
        self._controls.append(Radio(self, conf, mpdc))
        self._controls.append(Browser(self, conf, mpdc))
        self._controls.append(Setup(self, conf, mpdc))
        # Select the first widget
        self._controls[0].set_selected(True)

        self._logger = logging.getLogger(__name__)
        self._job = self._sched.add_job(self._io_handler, 'interval', seconds=0.1)

    def close(self):
        self._active = False

        for control in self._controls:
            control.close()

        self._mpd_client.stop()

    def __str__(self):
        return 'Home(screen=%s)' % (self._curses.get_screen())

    def __repr__(self):
        return str(self)

    def get_scheduler(self):
        return self._sched

    def get_curses(self):
        return self._curses

    def get_config(self):
        return self._config

    def get_MPDclient(self):
        return self._mpd_client

    def is_active(self):
        return self._active

    def set_active(self, act):
        self._active = act
        if act:
            self._job.resume()
        else:
            self._job.pause()

    def is_poweroff(self):
        return self._poweroff

    def set_poweroff(self, pwroff):
        self._poweroff = pwroff

    def _io_handler(self):
        self._logger.debug("Executing scheduled task.")
        # Pause job (stops lots of warnings)
        self._job.pause()

        # Get button presses
        if self.is_active():
            self._mpd_client.ping()
            fp_command = self._curses.get_command();

            # Check for a change of command
            if self._curses.has_command_changed():
                # Action button events
                if fp_command == commands.CMD_POWER:
                    self._poweroff = True
                elif fp_command == commands.CMD_UP:
                    last_control = None
                    for control in self._controls:
                        if control.is_selected():
                            if not last_control is None:
                                last_control.set_selected(True)
                                control.set_selected(False)
                                break
                        last_control = control
                elif fp_command == commands.CMD_DOWN:
                    last_control = None
                    for control in self._controls:
                        if not last_control is None:
                            last_control.set_selected(False)
                            control.set_selected(True)
                            break
                        if control.is_selected():
                            last_control = control
                elif (fp_command == commands.CMD_SELECT):
                    for control in self._controls:
                        if control.is_selected():
                            self.set_active(False)
                            control.set_active(True)
                            break

            # Draw screen
            line = 0
            self._curses.get_screen().clear()
            for control in self._controls:
# LCD does not support reversed fonts
#                attributes = curses.A_NORMAL
#                if control.is_selected():
#                    attributes = curses.A_REVERSE
                if control.is_selected():
                    tmp_txt  = '   >>> ' + control.control_name().ljust(5) + ' <<<    '
                else:
                    tmp_txt  = '       ' + control.control_name().ljust(5) + '        '
                self._curses.get_screen().addstr(line, 0, tmp_txt)
                line += 1

            self._curses.get_screen().refresh()

        # Resume job (should probably put this in a mutex)
        if self.is_active():
            self._job.resume()

from __future__ import print_function
from .radio import Radio
from .dlna import DLNA
from .usb import USB
from .setup import Setup
from . import commands

class Home(object):
    def __init__(self, ncrs, schd, sqlc, mpdc):
        self._curses = ncrs
        self._sched = schd
        self._sqlcon = sqlc
        self._mpd_client = mpdc
        self._active = True
        self._poweroff = False

        # Add widgets
        self._controls = []
        self._controls.append(Radio(self))
        self._controls.append(DLNA(self))
        self._controls.append(USB(self))
        self._controls.append(Setup(self))
        # Select the first widget
        self._controls[0].set_selected(True)

        self._job = self._sched.add_job(self.io_handler, 'interval', seconds=0.1)

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

    def get_sqlcon(self):
        return self._sqlcon

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

    def io_handler(self):
        # Pause job (stops lots of warnings)
        self._job.pause()

        # Get button presses
        if self.is_active():
            self._mpd_client.ping()
            buttons = self._curses.get_command();

            # Check for a change of command
            if self._curses.has_command_changed():
                # Action button events
                if buttons == commands.CMD_POWER:
                    self._poweroff = True
                elif buttons == commands.CMD_UP:
                    last_control = None
                    for control in self._controls:
                        if control.is_selected():
                            if not last_control is None:
                                last_control.set_selected(True)
                                control.set_selected(False)
                                break
                        last_control = control
                elif buttons == commands.CMD_DOWN:
                    last_control = None
                    for control in self._controls:
                        if not last_control is None:
                            last_control.set_selected(False)
                            control.set_selected(True)
                            break
                        if control.is_selected():
                            last_control = control
                elif (buttons & commands.CMD_SELECT) > 0:
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
                    self._curses.get_screen().addch(line,0,'>')
                else:
                    self._curses.get_screen().addch(line,0,' ')
                self._curses.get_screen().addstr(control.control_name())
                line += 1

            self._curses.get_screen().refresh()

        # Resume job (should probably put this in a mutex)
        if self.is_active():
            self._job.resume()

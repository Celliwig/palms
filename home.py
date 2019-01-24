from __future__ import print_function
import curses
from . import commands
from .curses_panel import curses_panel
from .radio import Radio
from .dlna import DLNA
from .usb import USB
from .setup import Setup

class Home(object):
    def __init__(self, scrn, schd, sqlc, mpdc):
        self._screen = scrn
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

        self._sched.add_job(self.io_handler, 'interval', seconds=0.1)

    def close(self):
        self._active = False

        for control in self._controls:
            control.close()

        self._mpd_client.stop()

    def __str__(self):
        return 'Home(screen=%s)' % (self._screen)

    def __repr__(self):
        return str(self)

    def get_scheduler(self):
        return self._sched

    def get_screen(self):
        return self._screen

    def get_sqlcon(self):
        return self._sqlcon

    def get_MPDclient(self):
        return self._mpd_client

    def is_active(self):
        return self._active

    def set_active(self, act):
        self._active = act

    def is_poweroff(self):
        return self._poweroff

    def set_poweroff(self, pwroff):
        self._poweroff = pwroff

    def io_handler(self):
        # Get button presses
        if self.is_active():
            buttons = curses_panel.getbuttons(self._screen)

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
            self._screen.clear()
            for control in self._controls:
# LCD does not support reversed fonts
#                attributes = curses.A_NORMAL
#                if control.is_selected():
#                    attributes = curses.A_REVERSE
                if control.is_selected():
                    self._screen.addch(line,0,'>')
                else:
                    self._screen.addch(line,0,' ')
                self._screen.addstr(control.control_name())
                line += 1

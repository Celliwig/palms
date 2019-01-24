from __future__ import print_function
import curses
from .curses_wrapper import curses_wrapper
from . import commands

class Setup(object):
    def __init__(self, home):
        self._parent = home
        self._screen = home.get_screen()
        self._sched = home.get_scheduler()
        self._active = False
        self._selected = False

        self._sched.add_job(self.io_handler, 'interval', seconds=0.1)

    def close(self):
        self._active = False

    def __str__(self):
        return 'Setup(screen=%s)' % (self._screen)

    def __repr__(self):
        return str(self)

    def control_name(self):
        return "Setup"

    def is_active(self):
        return self._active

    def set_active(self, act):
        self._active = act

    def is_selected(self):
        return self._selected

    def set_selected(self, val):
        self._selected = val

    def io_handler(self):
        # Get button presses
        if self.is_active():
            self._parent.get_MPDclient().ping()
            buttons = curses_wrapper.getbuttons(self._screen)

            # Action button events
            if buttons == commands.CMD_POWER:
                self._parent.set_poweroff(True)
            elif buttons == commands.CMD_CDHD:
                self.set_active(False)
                self._parent.set_active(True)
#            elif buttons == commands.CMD_UP:
#                last_control = None
#                for control in self._controls:
#                    if control.is_selected():
#                        if not last_control is None:
#                            last_control.set_selected(True)
#                            control.set_selected(False)
#                            break
#                    last_control = control
#            elif buttons == commands.CMD_DOWN:
#                last_control = None
#                for control in self._controls:
#                    if not last_control is None:
#                        last_control.set_selected(False)
#                        control.set_selected(True)
#                        break
#                    if control.is_selected():
#                        last_control = control

#            # Draw screen
#            line = 0
#            for control in self._controls:
## LCD does not support reversed fonts
##                attributes = curses.A_NORMAL
##                if control.is_selected():
##                    attributes = curses.A_REVERSE
#                if control.is_selected():
#                    self._screen.addch(line,0,'>')
#                else:
#                    self._screen.addch(line,0,' ')
#                self._screen.addstr(control.control_name())
#                line += 1
            self._screen.clear()
            self._screen.addstr(1,9,'Not')
            self._screen.addstr(2,4,'Implemented')
            self._screen.refresh()

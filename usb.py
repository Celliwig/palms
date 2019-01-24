from __future__ import print_function
import curses
from .curses_panel import curses_panel

class USB(object):
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
        return 'USB(screen=%s)' % (self._screen)

    def __repr__(self):
        return str(self)

    def control_name(self):
        return "USB"

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
            buttons = curses_panel.getbuttons(self._screen)

            # Action button events
            if (buttons & curses_panel.BUTTON_POWER) > 0:
                self._parent.set_poweroff(True)
            elif (buttons & curses_panel.BUTTON_MENU) > 0:
                self.set_active(False)
                self._parent.set_active(True)
#            elif (buttons & curses_panel.BUTTON_UP) > 0:
#                last_control = None
#                for control in self._controls:
#                    if control.is_selected():
#                        if not last_control is None:
#                            last_control.set_selected(True)
#                            control.set_selected(False)
#                            break
#                    last_control = control
#            elif (buttons & curses_panel.BUTTON_DOWN) > 0:
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

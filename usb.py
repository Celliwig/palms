from __future__ import print_function
from . import commands

class USB(object):
    def __init__(self, home):
        self._parent = home
        self._curses = home.get_curses()
        self._sched = home.get_scheduler()
        self._active = False
        self._selected = False

        self._job = self._sched.add_job(self._io_handler, 'interval', seconds=0.1)

    def close(self):
        self._active = False

    def __str__(self):
        return 'USB(screen=%s)' % (self._curses.get_screen())

    def __repr__(self):
        return str(self)

    def control_name(self):
        return "USB"

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

    def _io_handler(self):
        # Pause job (stops lots of warnings)
        self._job.pause()

        # Get button presses
        if self.is_active():
            self._parent.get_MPDclient().ping()
            buttons = self._curses.get_command()

            # Check for a change of command
            if self._curses.has_command_changed():
                # Action button events
                if buttons == commands.CMD_POWER:
                    self._parent.set_poweroff(True)
                elif buttons == commands.CMD_CDHD:
                    self.set_active(False)
                    self._parent.set_active(True)

            # Draw screen
            self._curses.get_screen().clear()
            self._curses.get_screen().addstr(1,0,'Not'.center(20))
            self._curses.get_screen().addstr(2,0,'Implemented'.center(20))
            self._curses.get_screen().refresh()

        # Resume job (should probably put this in a mutex)
        if self.is_active():
            self._job.resume()


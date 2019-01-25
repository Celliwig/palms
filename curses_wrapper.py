#############################################################################
#
# This is a wrapper class to allow the either the device specific driver to
# used, or the command line curses library to be used
#
#############################################################################

import curses
import logging
from . import commands
from .dev_panel import *

class curses_wrapper(object):
    SCREEN_TYPE_NONE = 0
    SCREEN_TYPE_NCURSES = 1
    SCREEN_TYPE_FPDEVICE = 2

    KEY_REPEAT_DELAY = 4			# Repeat at about 2.5 Hz
    KEY_REPEAT_DELAY_START = 10			# Delay for about 1 second

    # Glyph byte codes (configured based on device type)
    GLYPH_CODE_0 = " "
    GLYPH_CODE_1 = " "
    GLYPH_CODE_2 = " "
    GLYPH_CODE_3 = " "
    GLYPH_CODE_4 = " "
    GLYPH_CODE_5 = " "
    GLYPH_CODE_6 = " "
    GLYPH_CODE_7 = " "

    def __init__(self, screen_type):
        self._command_current = None
        self._command_previous = None
        self._command_changed = False
        self._command_repeat = 0
        self._command_repeat_delay = 0

        self._screen = None
        self._screen_type = screen_type

        self._logger = logging.getLogger(__name__)

        if self._screen_type == self.SCREEN_TYPE_NCURSES:
            self._logger.debug('Creating ncurses screen.')
            self._screen = curses.initscr()
            curses.cbreak()
            curses.noecho()
            curses.raw()
            curses.curs_set(False)
            self._screen.keypad(True)
            self._screen.nodelay(True)

            # Glyph byte codes
            self.GLYPH_CODE_0 = "0"
            self.GLYPH_CODE_1 = "1"
            self.GLYPH_CODE_2 = "2"
            self.GLYPH_CODE_3 = "3"
            self.GLYPH_CODE_4 = "4"
            self.GLYPH_CODE_5 = "5"
            self.GLYPH_CODE_6 = "6"
            self.GLYPH_CODE_7 = "7"

        if self._screen_type == self.SCREEN_TYPE_FPDEVICE:
            self._logger.debug('Connecting to /dev backed FP screen.')
            self._screen = dev_panel()

            # Glyph byte codes
            self.GLYPH_CODE_0 = chr(0)
            self.GLYPH_CODE_1 = chr(1)
            self.GLYPH_CODE_2 = chr(2)
            self.GLYPH_CODE_3 = chr(3)
            self.GLYPH_CODE_4 = chr(4)
            self.GLYPH_CODE_5 = chr(5)
            self.GLYPH_CODE_6 = chr(6)
            self.GLYPH_CODE_7 = chr(7)

    # Destroy screen
    def close(self):
        self._logger.debug('Closing screen.')

        if self._screen_type == self.SCREEN_TYPE_NCURSES:
            self._screen.keypad(False)
            curses.curs_set(True)
            curses.noraw()
            curses.echo()
            curses.nocbreak()
            curses.endwin()

        if self._screen_type == self.SCREEN_TYPE_FPDEVICE:
            self._screen.close()

    def set_glyph(self, glyph_index, glyph_data):
        if self._screen_type == self.SCREEN_TYPE_FPDEVICE:
            self._screen.set_glyph(glyph_index, glyph_data)

    def get_screen(self):
        return self._screen

    def get_screen_type(self):
        return self._screen_type

    def get_command(self):
        rtn = 0
        self._command_previous = self._command_current

        if self._screen_type == self.SCREEN_TYPE_NCURSES:
            key = self._screen.getch()
            #print(key)
            if key == ord('e'):
                rtn = rtn | commands.CMD_EJECT
            elif key == ord('m'):
                rtn = rtn | commands.CMD_CDHD
            elif key == curses.KEY_F5:
                rtn = rtn | commands.CMD_DSPSEL1
            elif key == curses.KEY_F6:
                rtn = rtn | commands.CMD_DSPSEL2
            elif key == curses.KEY_F7:
                rtn = rtn | commands.CMD_DSPSEL3
            elif key == curses.KEY_F8:
                rtn = rtn | commands.CMD_DSPSEL4
            elif key == curses.KEY_UP:
                rtn = rtn | commands.CMD_UP
            elif key == curses.KEY_DOWN:
                rtn = rtn | commands.CMD_DOWN
            elif key == 10:
                rtn = rtn | commands.CMD_SELECT
            elif key == curses.KEY_LEFT:
                rtn = rtn | commands.CMD_LEFT
            elif key == curses.KEY_RIGHT:
                rtn = rtn | commands.CMD_RIGHT
            elif key == ord('7'):
                rtn = rtn | commands.CMD_PAUSE
            elif key == ord('8'):
                rtn = rtn | commands.CMD_PLAY
            elif key == ord('9'):
                rtn = rtn | commands.CMD_STOP
            elif key == ord('4'):
                rtn = rtn | commands.CMD_PREVIOUS
            elif key == ord('5'):
                rtn = rtn | commands.CMD_MODE
            elif key == ord('6'):
                rtn = rtn | commands.CMD_NEXT
            elif key == curses.KEY_F12:
                rtn = rtn | commands.CMD_POWER
            elif key == ord('v'):
                rtn = rtn | commands.CMD_MUTE
            elif key == ord('r'):
                rtn = rtn | commands.CMD_ALT2
            elif key == ord('s'):
                rtn = rtn | commands.CMD_ALT1

        elif self._screen_type == self.SCREEN_TYPE_FPDEVICE:
            rtn = self._screen.getbuttons();

        self._command_current = rtn

        self._logger.debug("Read command value: " + str(self._command_current))

        # Set the flag to indicate if the command has changed sinece it was last read
        if self._command_current == self._command_previous:
            self._command_changed = False
        else:
            self._command_changed = True
            self._command_repeat_delay = curses_wrapper.KEY_REPEAT_DELAY_START
            self._command_repeat = curses_wrapper.KEY_REPEAT_DELAY

        # Some keys need to be repeated however
        if self._command_changed == False:
            repeat_key = False
            repeat_key_no_delay = False
            if self._command_current == commands.CMD_UP: repeat_key = True
            if self._command_current == commands.CMD_DOWN: repeat_key = True
            if self._command_current == commands.CMD_DSPSEL1: repeat_key_no_delay = True
            if self._command_current == commands.CMD_DSPSEL2: repeat_key_no_delay = True
            if self._command_current == commands.CMD_DSPSEL3: repeat_key_no_delay = True
            if self._command_current == commands.CMD_DSPSEL4: repeat_key_no_delay = True

            if repeat_key or repeat_key_no_delay:
                if (self._command_repeat_delay > 0) and (not repeat_key_no_delay):
                    self._command_repeat_delay -= 1
                else:
                    self._logger.debug("Repeating previous command value: " + str(self._command_current))
                    self._command_changed = True
                    self._command_repeat = curses_wrapper.KEY_REPEAT_DELAY

        return self._command_current

    def has_command_changed(self):
        return self._command_changed

def main():
    print(display_wrapper.SCREEN_TYPE_NONE)

if __name__ == "__main__":
    main()


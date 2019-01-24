#############################################################################
#
# This is a wrapper class to allow the either the device specific driver to
# used, or the command line curses library to be used
#
#############################################################################

import curses
from . import commands

class curses_wrapper(object):

    def getbuttons(screen):
        if screen.__class__.__name__ == 'curses window':
            rtn = 0
            key = screen.getch()
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

            return rtn
        elif screen.__class__.__name__ == 'dev_panel':
            return screen.getbuttons();
        else:
            print(screen.__class__.__name__)
            return 0;

    def convert_2_pages(item_list, page_length):
        return [item_list[i:i + page_length] for i in range(0, len(item_list), page_length)]


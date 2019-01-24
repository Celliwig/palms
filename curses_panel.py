import curses

class curses_panel(object):

#Define available buttons
    BUTTON_OPEN_CLOSE = 2**0
    BUTTON_MENU = 2**1
    BUTTON_F1 = 2**2
    BUTTON_F2 = 2**3
    BUTTON_F3 = 2**4
    BUTTON_F4 = 2**5
    BUTTON_Fn = (2**2) | (2**3) | (2**4) | (2**5)
    BUTTON_UP = 2**6
    BUTTON_DOWN = 2**7
    BUTTON_OK = 2**8
    BUTTON_LEFT = 2**9
    BUTTON_RIGHT = 2**10
    BUTTON_PAUSE = 2**11
    BUTTON_PLAY = 2**12
    BUTTON_STOP = 2**13
    BUTTON_REWIND = 2**14
    BUTTON_BACK = 2**15
    BUTTON_FORWARD = 2**16
    BUTTON_POWER = 2**17

    def getbuttons(screen):
        if screen.__class__.__name__ == 'curses window':
            rtn = 0
            key = screen.getch()
            #print(key)
            if key == ord('e'):
                rtn = rtn | curses_panel.BUTTON_OPEN_CLOSE
            elif key == ord('m'):
                rtn = rtn | curses_panel.BUTTON_MENU
            elif key == curses.KEY_F5:
                rtn = rtn | curses_panel.BUTTON_F1
            elif key == curses.KEY_F6:
                rtn = rtn | curses_panel.BUTTON_F2
            elif key == curses.KEY_F7:
                rtn = rtn | curses_panel.BUTTON_F3
            elif key == curses.KEY_F8:
                rtn = rtn | curses_panel.BUTTON_F4
            elif key == curses.KEY_UP:
                rtn = rtn | curses_panel.BUTTON_UP
            elif key == curses.KEY_DOWN:
                rtn = rtn | curses_panel.BUTTON_DOWN
            elif key == 10:
                rtn = rtn | curses_panel.BUTTON_OK
            elif key == curses.KEY_LEFT:
                rtn = rtn | curses_panel.BUTTON_LEFT
            elif key == curses.KEY_RIGHT:
                rtn = rtn | curses_panel.BUTTON_RIGHT
            elif key == ord('7'):
                rtn = rtn | curses_panel.BUTTON_PAUSE
            elif key == ord('8'):
                rtn = rtn | curses_panel.BUTTON_PLAY
            elif key == ord('9'):
                rtn = rtn | curses_panel.BUTTON_STOP
            elif key == ord('4'):
                rtn = rtn | curses_panel.BUTTON_REWIND
            elif key == ord('5'):
                rtn = rtn | curses_panel.BUTTON_BACK
            elif key == ord('6'):
                rtn = rtn | curses_panel.BUTTON_FORWARD
            elif key == curses.KEY_F12:
                rtn = rtn | curses_panel.BUTTON_POWER

            return rtn
        elif screen.__class__.__name__ == 'curses_i2c':
            return 0;
        else:
            return 0;

    def convert_2_pages(item_list, page_length):
        return [item_list[i:i + page_length] for i in range(0, len(item_list), page_length)]


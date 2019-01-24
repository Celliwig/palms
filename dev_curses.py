
class curses_dev(object):

Define available buttons
    CMD_POWER = 0x01
    CMD_TESTMODE = 0x02
    CMD_MODE = 0x03
    CMD_CDHD = 0x04
    CMD_EJECT = 0x05

; Transport
    CMD_PLAY = 0x11
    CMD_STOP = 0x12
    CMD_PAUSE = 0x13
    CMD_PREVIOUS = 0x14
    CMD_REWIND = 0x15
    CMD_NEXT = 0x16
    CMD_FASTFOWARD = 0x17
    CMD_RECORD = 0x18

; Navigation
    CMD_UP = 0x21
    CMD_DOWN = 0x22
    CMD_LEFT = 0x23
    CMD_RIGHT = 0x24
    CMD_SELECT = 0x25
    CMD_BACK = 0x26

; Display Select
    CMD_DSPSEL1 = 0x31
    CMD_DSPSEL2 = 0x32
    CMD_DSPSEL3 = 0x33
    CMD_DSPSEL4 = 0x34

; Numbers
    CMD_0 = 0x40
    CMD_1 = 0x41
    CMD_2 = 0x42
    CMD_3 = 0x43
    CMD_4 = 0x44
    CMD_5 = 0x45
    CMD_6 = 0x46
    CMD_7 = 0x47
    CMD_8 = 0x48
    CMD_9 = 0x49

; Audio
    CMD_MUTE = 0x51
    CMD_AUDIO = 0x52

; Unassigned
    CMD_ALT1 = 0x61
    CMD_ALT2 = 0x62
    CMD_ALT3 = 0x63
    CMD_ALT4 = 0x64
    CMD_ALT5 = 0x65
    CMD_ALT6 = 0x66



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


    def __init__(self):
        self._bus = smbus.SMBus(1)                  # Front panel connected to bus 1
        self._panel_address = 0x11                  # Front panel address

# Full screen clear
    def clear(self):
        data = [1,1]
        self._bus.write_i2c_block_data(self._panel_address, 0, data)

    def clear_row(self, row):
        data = [1,1,row]
        self._bus.write_i2c_block_data(self._panel_address, 0, data)

    def clear_partial(self, row, column, characters = 0):
        rc_data = (column << 2) | row
        if characters > 0:
            data = [1,1,rc_data,characters]
        else:
            data = [1,1,rc_data]
        self._bus.write_i2c_block_data(self._panel_address, 0, data)

    def addch(self, row, column, character):
        rc_data = (column << 2) | row
        data = [3,2,rc_data,character[0:0]]
        self._bus.write_i2c_block_data(self._panel_address, 0, data)

    def addstr(self, row, column, string):
        rc_data = (column << 2) | row
        cmd_size = len(string) + 2
        data = [cmd_size,2,rc_data]
        data += list(map(ord, string))
        self._bus.write_i2c_block_data(self._panel_address, 0, data)

    def getmaxyx(self):
        return (4, 20)

    def getbuttons(self):
        button_status = self._bus.read_i2c_block_data(self._panel_address,0,3)
        return button_status


def main():
    stdscr = curses_i2c()
    stdscr.clear()
    stdscr.addstr(0,0,"Hello")
    stdscr.addstr(1,3,"World")

if __name__ == "__main__":
    main()

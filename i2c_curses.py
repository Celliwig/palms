import smbus

class curses_i2c(object):
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

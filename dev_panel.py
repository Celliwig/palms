import os, sys

class dev_panel(object):
    lcd_rows = 4
    lcd_columns = 20
    piadagio_devname = '/dev/piadagio_fp'
#    piadagio_devname = '/dev/null'

    def __init__(self):
        self._device_fd = os.open(self.piadagio_devname, os.O_RDWR)

    def close(self):
        if not self._device_fd is None:
            os.close(self._device_fd)
            self._device_fd = None

# Full screen clear
    def clear(self):
        if not self._device_fd is None:
            tmp_str = ""
            for i in range(self.lcd_rows * self.lcd_columns):
                tmp_str = tmp_str + " "
            os.lseek(self._device_fd, 0, os.SEEK_SET)
            os.write(self._device_fd, tmp_str.encode())

    def clear_row(self, row):
        if not self._device_fd is None:
            tmp_str = ""
            for i in range(self.lcd_columns):
                tmp_str = tmp_str + " "
            os.lseek(self._device_fd, (row * self.lcd_columns), os.SEEK_SET)
            os.write(self._device_fd, tmp_str.encode())

    def clear_partial(self, row, column, characters = 0):
        if not self._device_fd is None:
            tmp_str = ""
            for i in range(characters):
                tmp_str = tmp_str + " "
            os.lseek(self._device_fd, ((row * self.lcd_columns) + column), os.SEEK_SET)
            os.write(self._device_fd, tmp_str.encode())

#    def addch(self, row, column, character):
#        if not self._device_fd is None:
#            os.lseek(self._device_fd, ((row * self.lcd_columns) + column), os.SEEK_SET)
#            os.write(self._device_fd, character.encode())

    def addch(self, *args):
        if not self._device_fd is None:
            string = None
            row = None
            column = None

            if len(args) <= 3:
                for tmp_arg in reversed(args):
                    if string is None:
                        string = tmp_arg
                    elif column is None:
                        column = tmp_arg
                    else:
                        row = tmp_arg

            offset = None
            if not row is None:
                offset = row * 20
            if not column is None:
                offset += column

            if not offset is None:
                os.lseek(self._device_fd, offset, os.SEEK_SET)
            os.write(self._device_fd, string.encode())

#    def addstr(self, row, column, string):
#        if not self._device_fd is None:
#            os.lseek(self._device_fd, ((row * self.lcd_columns) + column), os.SEEK_SET)
#            os.write(self._device_fd, string.encode())

    def addstr(self, *args):
        if not self._device_fd is None:
            string = None
            row = None
            column = None

            if len(args) <= 3:
                for tmp_arg in reversed(args):
                    if string is None:
                        string = tmp_arg
                    elif column is None:
                        column = tmp_arg
                    else:
                        row = tmp_arg

            offset = None
            if not row is None:
                offset = row * 20
            if not column is None:
                offset += column

            if not offset is None:
                os.lseek(self._device_fd, offset, os.SEEK_SET)
            os.write(self._device_fd, string.encode())

    def refresh(self):
        if not self._device_fd is None:
            os.fsync(self._device_fd)
            return 0

    def getmaxyx(self):
        return (self.lcd_rows, self.lcd_columns)

    def getbuttons(self):
        button_status = int.from_bytes(os.read(self._device_fd, 1), byteorder='little')
        return button_status


def main():
    import time

    stdscr = dev_panel()
    stdscr.clear()
    stdscr.clear_row(0)
    #stdscr.clear_row(4)
    stdscr.clear_partial(0,5,4)
    #stdscr.clear_partial(4,5,4)
    stdscr.addch(2,19,'A')
    stdscr.addch(3,18,'B')
    stdscr.addstr(0,0,"Hello")
    stdscr.addstr(1,3,"World ")
    stdscr.addstr("Charlie!")
    #stdscr.addstr(4,3,"World")

    while True:
        button_cmd = stdscr.getbuttons()
        print("Read: " + format(button_cmd, '#04x'))
        time.sleep(0.5)

if __name__ == "__main__":
    main()

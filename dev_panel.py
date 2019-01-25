import os, subprocess, sys

class dev_panel(object):
    # Glyph byte sequences
    GLYPH_HOUR_GLASS1 = bytes([0x1F, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x1F, 0x00])
    GLYPH_HOUR_GLASS2 = bytes([0x1F, 0x1F, 0x0E, 0x04, 0x0A, 0x11, 0x1F, 0x00])
    GLYPH_HOUR_GLASS3 = bytes([0x1F, 0x1F, 0x0E, 0x04, 0x0A, 0x1F, 0x1F, 0x00])
    GLYPH_HOUR_GLASS4 = bytes([0x1F, 0x11, 0x0E, 0x04, 0x0A, 0x1F, 0x1F, 0x00])
    GLYPH_HOUR_GLASS5 = bytes([0x1F, 0x11, 0x0E, 0x04, 0x0E, 0x1F, 0x1F, 0x00])
    GLYPH_HOUR_GLASS6 = bytes([0x1F, 0x11, 0x0A, 0x04, 0x0E, 0x1F, 0x1F, 0x00])

    GLYPH_MODE_MUSIC = bytes([0x00, 0x07, 0x0D, 0x0B, 0x1B, 0x18, 0x00, 0x00])
    GLYPH_MODE_RADIO = bytes([0x1F, 0x15, 0x0E, 0x04, 0x04, 0x04, 0x04, 0x00])
    GLYPH_MODE_SPANNER = bytes([0x00, 0x0C, 0x14, 0x1E, 0x07, 0x03, 0x00, 0x00])

    GLYPH_TRANSPORT_PAUSE = bytes([0x00, 0x1B, 0x1B, 0x1B, 0x1B, 0x1B, 0x00, 0x00])
    GLYPH_TRANSPORT_PLAY = bytes([0x10, 0x18, 0x1c, 0x1e, 0x1c, 0x18, 0x10, 0x00])
    GLYPH_TRANSPORT_STOP = bytes([0x00, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x00, 0x00])

    GLYPH_REPEAT_1 = bytes([0x0e, 0x1b, 0x13, 0x1b, 0x1b, 0x11, 0x0e, 0x00])
    GLYPH_REPEAT = bytes([0x0e, 0x13, 0x15, 0x13, 0x15, 0x15, 0x0e, 0x00])
    GLYPH_SHUFFLE = bytes([0x0e, 0x19, 0x17, 0x11, 0x1d, 0x13, 0x0e, 0x00])
    GLYPH_SPEAKER = bytes([0x01, 0x03, 0x1D, 0x11, 0x1D, 0x03, 0x01, 0x00])

    # (1,2)/(1,3) - (2,1)/(2,2)/(2,3) - (3,1)
    GLYPH_LARGE_MUSIC = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x0c, 0x00, 0x00, 0x00, 0x03, 0x0d, 0x11, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x01, 0x01, 0x01, 0x07, 0x0f, 0x0f, 0x07, 0x01, 0x07, 0x0f, 0x0f, 0x07, 0x00, 0x00, 0x00])
    # (1,1)/(1,2)/(1,3) - (2,1)/(2,2)/(2,3)
    GLYPH_LARGE_RADIO = bytes([0x00, 0x00, 0x07, 0x0c, 0x11, 0x15, 0x15, 0x15, 0x00, 0x00, 0x1f, 0x00, 0x10, 0x14, 0x14, 0x14, 0x00, 0x00, 0x1c, 0x06, 0x01, 0x01, 0x01, 0x01, 0x15, 0x15, 0x15, 0x15, 0x11, 0x0c, 0x07, 0x03, 0x14, 0x14, 0x14, 0x14, 0x10, 0x00, 0x1f, 0x11, 0x1d, 0x15, 0x1d, 0x01, 0x01, 0x06, 0x1c, 0x18])
    # (1,1)/(1,2) - (2,1)/(2,2)/(2,3) - (3,2)/(3,3)
    GLYPH_LARGE_SPANNER = bytes([0x00, 0x00, 0x00, 0x00, 0x07, 0x04, 0x03, 0x01, 0x00, 0x00, 0x00, 0x00, 0x10, 0x08, 0x08, 0x08, 0x18, 0x15, 0x12, 0x10, 0x0f, 0x00, 0x00, 0x00, 0x08, 0x04, 0x02, 0x01, 0x00, 0x10, 0x08, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10, 0x08, 0x04, 0x02, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x02, 0x04, 0x18, 0x00, 0x00, 0x00, 0x00])

    lcd_rows = 4
    lcd_columns = 20
    piadagio_devname = '/dev/piadagio_fp'
#    piadagio_devname = '/dev/null'

    def __init__(self):
        self._device_fd = os.open(self.piadagio_devname, os.O_RDWR)
        self._device_fd_version = "N/A"
        self._glyph_buffer = [None, None, None, None, None, None, None, None]

        # Get the module version
        module_version_info = subprocess.check_output(args=["modinfo", "piadagio_fp"]).decode().split('\n')
        for tmp_mod_info in module_version_info:
            if tmp_mod_info.startswith('version:'):
                self._device_fd_version = tmp_mod_info.replace("version:", "").strip()

    def close(self):
        if not self._device_fd is None:
            os.close(self._device_fd)
            self._device_fd = None

    def get_device_module_version(self):
        return self._device_fd_version

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

    def set_glyph(self, glyph_index, glyph_data):
        if self._glyph_buffer[glyph_index] != glyph_data:
            self._glyph_buffer[glyph_index] = glyph_data
            os.lseek(self._device_fd, 128 + (glyph_index * 8), os.SEEK_SET)
            os.write(self._device_fd, glyph_data)

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

#####################################################################################
# Class to assign commands a value. This value is also the command value from the
# PiAdagio front panel.
#####################################################################################

# General
CMD_POWER = 0x01
CMD_TESTMODE = 0x02
CMD_MODE = 0x03
CMD_CDHD = 0x04
CMD_EJECT = 0x05

# Transport
CMD_PLAY = 0x11
CMD_STOP = 0x12
CMD_PAUSE = 0x13
CMD_PREVIOUS = 0x14
CMD_REWIND = 0x15
CMD_NEXT = 0x16
CMD_FASTFOWARD = 0x17
CMD_RECORD = 0x18

# Navigation
CMD_UP = 0x21
CMD_DOWN = 0x22
CMD_LEFT = 0x23
CMD_RIGHT = 0x24
CMD_SELECT = 0x25
CMD_BACK = 0x26

# Display Select
CMD_DSPSEL_MASK = 0x30
CMD_DSPSEL1 = 0x31
CMD_DSPSEL2 = 0x32
CMD_DSPSEL3 = 0x33
CMD_DSPSEL4 = 0x34

# Numbers
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

# Audio
CMD_MUTE = 0x51
CMD_AUDIO = 0x52

# Unassigned
CMD_ALT1 = 0x61
CMD_ALT2 = 0x62
CMD_ALT3 = 0x63
CMD_ALT4 = 0x64
CMD_ALT5 = 0x65
CMD_ALT6 = 0x66

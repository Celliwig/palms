#!/usr/bin/env python
from __future__ import print_function
from mpd import MPDClient
import sys
from time import sleep
import argparse
from apscheduler.schedulers.background import BackgroundScheduler
import curses
import sqlite3

from . import *
from .home import Home
#from .i2c_curses import curses_i2c

def usage():
    print(USAGE % sys.argv[0])

def main():
    # Create argument parser and help
    parser = argparse.ArgumentParser()
    ui_interface = parser.add_mutually_exclusive_group(required=True)
    ui_interface.add_argument("-c","--console",action="store_true",help="The UI is console based")
    ui_interface.add_argument("-p","--panel",action="store_false",help="The UI is routed to the front panel")
    parser.add_argument("-s","--simulate",action="store_true",default=False,help="When using a console based UI, simulate an LCD screen size")
    parser.add_argument("--lcd_cols",type=int,default=20,help="Specify the number of columns of the LCD")
    parser.add_argument("--lcd_rows",type=int,default=4,help="Specify the number of rows of the LCD")
    parser.add_argument("--mpd_host",default=None,help="Specify the hostname/IP of the MPD server")
    parser.add_argument("--mpd_port",type=int,default=6600,help="Specify the port of the MPD server")
    parser.add_argument("--mpd_socket",default=MPD_default_socket_path,help="Specify the path to the MPD server socket (default): " + MPD_default_socket_path)
    args = parser.parse_args()

    # Setup connection tp MPD Server
    mpd_client = MPDClient()
    mpd_client.timeout = 30
    mpd_client.idletimeout = None
    mpd_client.connect(MPD_default_socket_path,None)

    # Connect to SQLite DB
    sqlcon = sqlite3.connect(HOWDIE_SQLPATH)

    # Setup the scheduler to read meta data from mplayer
    sched = BackgroundScheduler(daemon=False)
    sched.start()

    # Create a screen
    if args.console:
        stdscr = curses.initscr()
        curses.noecho()
        curses.raw()
        stdscr.keypad(True)
        stdscr.nodelay(True)
    elif args.panel:
        stdscr = curses_i2c()
    else:
        stdscr = None

# Init Home
    home = Home(stdscr, sched, sqlcon, mpd_client)

# Idle loop
    while not home.is_poweroff():
        sleep(0.5)

    # Close down widgets (this will save changes)
    home.close()

    # Destroy screen
    if args.console:
        stdscr.keypad(False)
        curses.noraw()
        curses.echo()
        curses.endwin()
    else:
        stdscr = None

    # Shutdown screen
    sched.shutdown()

    # Close DB connection
    sqlcon.close()

    # Close MPD connection
    mpd_client.close()
    mpd_client.disconnect()

    return 0

if __name__ == "__main__":
#    main(sys.argv[1:])
    main()

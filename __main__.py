#!/usr/bin/env python

from __future__ import print_function
from mpd import MPDClient
import sys
from time import sleep
import argparse
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
import os, pwd

from . import *
from .home import Home
from .curses_wrapper import *

def usage():
    print(USAGE % sys.argv[0])

def main():
    # Create argument parser and help
    parser = argparse.ArgumentParser()
    ui_interface = parser.add_mutually_exclusive_group(required=True)
    ui_interface.add_argument("-c","--console",action="store_true",help="The UI is console based")
    ui_interface.add_argument("-p","--panel",action="store_true",help="The UI is routed to the front panel")
    #parser.add_argument("--lcd_cols",type=int,default=20,help="Specify the number of columns of the LCD")
    #parser.add_argument("--lcd_rows",type=int,default=4,help="Specify the number of rows of the LCD")
    parser.add_argument("--mpd_host",default=None,help="Specify the hostname/IP of the MPD server")
    parser.add_argument("--mpd_port",type=int,default=6600,help="Specify the port of the MPD server")
    parser.add_argument("--mpd_socket",default=MPD_default_socket_path,help="Specify the path to the MPD server socket (default): " + MPD_default_socket_path)
    parser.add_argument("--user",default="palms",help="User to run as.")
    args = parser.parse_args()

    # Are we running as root?
    if os.getuid() == 0:
        PALMS_DIR = "/var/lib/palms/"

        try:
            pwnam = pwd.getpwnam(args.user)
        except:
            print("PALMS: Could not find user - " + args.user)
            return -1

        # Check directory exists
        if os.path.exists(PALMS_DIR):
            stat_info = os.stat(PALMS_DIR)

            # Check directory permissions
            if (pwnam.pw_uid != stat_info.st_uid) or (pwnam.pw_gid != stat_info.st_gid):
                print("PALMS: Check permissions for data directory " + PALMS_DIR)
                return -1
        else:
            print("PALMS: Data directory " + PALMS_DIR + " does not exist.")
            return -1

        # Drop privileges
        # Remove group privileges
        os.setgroups(os.getgrouplist(pwnam.pw_name, pwnam.pw_gid))

        # Try setting the new uid/gid
        os.setgid(pwnam.pw_gid)
        os.setuid(pwnam.pw_uid)

        # Update 'HOME' environment variable
        os.environ['HOME'] = pwnam.pw_dir

#        # Change to directory
#        os.chdir(pwnam.pw_dir)

        #Ensure a reasonable umask
        old_umask = os.umask(0o22)
    else:
        PALMS_DIR = os.environ['HOME']

    # Check that privileges have dropped
    if os.getuid() == 0:
        print("PALMS: Privileges not dropped still root.")
        return -1

    PALMS_SQLPATH = PALMS_DIR + "/palms.dat"

    # Setup connection tp MPD Server
    mpd_client = MPDClient()
    mpd_client.timeout = 30
    mpd_client.idletimeout = None
    mpd_client.connect(MPD_default_socket_path,None)

    # Connect to SQLite DB
    try:
        sqlcon = sqlite3.connect(PALMS_SQLPATH)
    except:
        print("PALMS: Could not open SQL file - " + PALMS_SQLPATH)
        return -1

    # Setup the scheduler to read meta data from mplayer
    sched = BackgroundScheduler(daemon=False)
    sched.start()

    # Create a screen
    scr_typ = curses_wrapper.SCREEN_TYPE_NONE
    if args.console:
        scr_typ = curses_wrapper.SCREEN_TYPE_NCURSES
    elif args.panel:
        scr_typ = curses_wrapper.SCREEN_TYPE_FPDEVICE
    stdscr = curses_wrapper(scr_typ)

# Init Home
    home = Home(stdscr, sched, sqlcon, mpd_client)

# Idle loop
    while not home.is_poweroff():
        sleep(0.5)

    # Close down widgets (this will save changes)
    home.close()

    # Destroy screen
    stdscr.close()

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

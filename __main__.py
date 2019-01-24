#!/usr/bin/env python

from __future__ import print_function
from mpd import MPDClient
import sys
from time import sleep
import argparse
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import sqlite3
import os, pwd

from . import *
from .config import config
from .home import Home
from .curses_wrapper import *

def usage():
    print(USAGE % sys.argv[0])

def main():
    MPD_default_socket_path = "/run/mpd/socket"

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
    parser.add_argument("--loglevel",default="INFO",help="Level to log at. Should be one of DEBUG/INFO/WARNING/ERROR/CRITICAL.")
    args = parser.parse_args()

    # Are we running as root?
    if os.getuid() == 0:
        PALMS_DATA_DIR = "/var/lib/palms/"
        PALMS_LOG_DIR = "/var/log/palms/"

        try:
            pwnam = pwd.getpwnam(args.user)
        except:
            print("PALMS: Could not find user - " + args.user)
            return -1

        # Check data directory exists
        if os.path.exists(PALMS_DATA_DIR):
            stat_info = os.stat(PALMS_DATA_DIR)

            # Check data directory permissions
            if (pwnam.pw_uid != stat_info.st_uid) or (pwnam.pw_gid != stat_info.st_gid):
                print("PALMS: Check permissions for data directory " + PALMS_DATA_DIR)
                return -1
        else:
            print("PALMS: Data directory " + PALMS_DATA_DIR + " does not exist.")
            return -1

        # Check log directory exists
        if os.path.exists(PALMS_LOG_DIR):
            stat_info = os.stat(PALMS_LOG_DIR)

            # Check log directory permissions
            if (pwnam.pw_uid != stat_info.st_uid) or (pwnam.pw_gid != stat_info.st_gid):
                print("PALMS: Check permissions for log directory " + PALMS_LOG_DIR)
                return -1
        else:
            print("PALMS: Log directory " + PALMS_LOG_DIR + " does not exist.")
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
        PALMS_DATA_DIR = os.environ['HOME']
        PALMS_LOG_DIR = os.environ['HOME']

    # Check that privileges have dropped
    if os.getuid() == 0:
        print("PALMS: Privileges not dropped still root.")
        return -1

    PALMS_SQLPATH = PALMS_DATA_DIR + "/palms.dat"

    # Start logging
    palms_logfile = PALMS_LOG_DIR + "/palms.log"
    numeric_loglevel = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_loglevel, int):
        raise ValueError('Invalid log level: %s' % args.loglevel)
    log_format = '%(asctime)s - %(name)s:%(levelname)s; %(message)s'
    logging.basicConfig(filename=palms_logfile, format=log_format, level=numeric_loglevel)
    logger = logging.getLogger(__name__)

    # Reduce the log level of libraries
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("mpd").setLevel(logging.WARNING)

    # Setup connection tp MPD Server
    logger.debug("Preparing to connect to MPD daemon using socket: " + MPD_default_socket_path)
    mpd_client = MPDClient()
    mpd_client.timeout = 240
    mpd_client.idletimeout = 240
    mpd_client.connect(MPD_default_socket_path,None)
    logger.info("Connected to MPD daemon.")

    # Connect to SQLite DB
    logger.debug("Preparing to open SQL data file: " + PALMS_SQLPATH)
    try:
        sqlcon = sqlite3.connect(PALMS_SQLPATH)
    except:
        print("PALMS: Could not open SQL file - " + PALMS_SQLPATH)
        return -1
    logger.info("Opened SQL data file.")

    # Create configuration
    conf = config(sqlcon)

    # Setup the scheduler to read meta data from mplayer
    sched = BackgroundScheduler(daemon=False)
    sched.start()
    logger.debug("Started task scheduler.")

    # Create a screen
    scr_typ = curses_wrapper.SCREEN_TYPE_NONE
    if args.console:
        scr_typ = curses_wrapper.SCREEN_TYPE_NCURSES
    elif args.panel:
        scr_typ = curses_wrapper.SCREEN_TYPE_FPDEVICE
    stdscr = curses_wrapper(scr_typ)

# Init Home
    logger.info("Starting P.A.L.M.S.")
    home = Home(stdscr, sched, conf, mpd_client)

# Idle loop
    while not home.is_poweroff():
        sleep(0.5)
    logger.info("Shutting down P.A.L.M.S.")

    # Close down widgets (this will save changes)
    home.close()

    # Destroy screen
    stdscr.close()

    # Shutdown screen
    logger.debug("Shutting down task scheduler.")
    sched.shutdown()

    # Save configuration
    conf.save_config()

    # Close DB connection
    logger.info("Closing SQL data file.")
    sqlcon.close()

    # Close MPD connection
    logger.info("Closing MPD connection.")
    mpd_client.close()
    mpd_client.disconnect()

    return 0

if __name__ == "__main__":
#    main(sys.argv[1:])
    main()

from __future__ import print_function
import platform
import subprocess
from socket import AF_INET
from pyroute2 import IPRoute
from . import commands
from .curses_wrapper import *

class Setup(object):
    SETUP_STATE_LIST = 0
    SETUP_STATE_SYSTEM = 1
    SETUP_STATE_NETWORK = 2

    def __init__(self, home):
        self._parent = home
        self._curses = home.get_curses()
        self._sched = home.get_scheduler()
        self._active = False
        self._selected = False
        self._state = Setup.SETUP_STATE_LIST

        self._ip = IPRoute()

        self._gadget_list = [ "System Info", "Network Info" ]
        self._selected_gadget = 1
        self._list_offset = 0

        self._job = self._sched.add_job(self.io_handler, 'interval', seconds=0.1)

    def close(self):
        self._active = False

    def __str__(self):
        return 'Setup(screen=%s)' % (self._curses.get_screen())

    def __repr__(self):
        return str(self)

    def control_name(self):
        return "Setup"

    def is_active(self):
        return self._active

    def set_active(self, act):
        self._active = act
        if act:
            self._job.resume()
        else:
            self._job.pause()

    def is_selected(self):
        return self._selected

    def set_selected(self, val):
        self._selected = val

    def io_handler(self):
        # Pause job (stops lots of warnings)
        self._job.pause()

        # Get button presses
        if self.is_active():
            self._parent.get_MPDclient().ping()
            fp_command = self._curses.get_command()

            # Check for a change of command
            if self._curses.has_command_changed():
                # Action button events
                if fp_command == commands.CMD_POWER:
                    self._parent.set_poweroff(True)
                if fp_command == commands.CMD_MODE:
                    if self._state > 0:
                        self._state = 0
                    else:
                        self.set_active(False)
                        self._parent.set_active(True)
                elif fp_command == commands.CMD_CDHD:
                    self.set_active(False)
                    self._parent.set_active(True)

            if self._state == Setup.SETUP_STATE_LIST:
                self.list_gadgets(fp_command)
            elif self._state == Setup.SETUP_STATE_SYSTEM:
                self.system_info(fp_command)
            elif self._state == Setup.SETUP_STATE_NETWORK:
                self.network_info(fp_command)

        # Resume job (should probably put this in a mutex)
        if self.is_active():
            self._job.resume()

# List the configable items
#####################################################################################################
    def list_gadgets(self, fp_command):
        list_gadgets = []
        tmp_index = 1
        for tmp_gadget in self._gadget_list:
            if self._selected_gadget == tmp_index:
                tmp_txt = "> " + tmp_gadget
            else:
                tmp_txt = "  " + tmp_gadget

            list_gadgets.append(tmp_txt)
            tmp_index += 1

        # Check for a change of command
        if self._curses.has_command_changed():
            # Action button events
            if fp_command == commands.CMD_UP:
                if self._selected_gadget > 1:
                    self._selected_gadget -= 1
            if fp_command == commands.CMD_DOWN:
                if self._selected_gadget < len(self._gadget_list):
                    self._selected_gadget += 1
            if fp_command == commands.CMD_SELECT:
                self._list_offset = 0
                self._state = self._selected_gadget

        self._curses.get_screen().clear()
        for i in range(0,len(list_gadgets)):
            self._curses.get_screen().addstr(i, 0, list_gadgets[i])
        self._curses.get_screen().refresh()

# Displays network information
#####################################################################################################
    def network_info(self, fp_command):
        network_info = []
        network_info.append("Network".center(20))
        network_info.append("")

        iface_devices = self._ip.get_links()
        for iface in iface_devices:
            iface_name = iface.get_attr('IFLA_IFNAME')
            if iface_name != "lo":
                iface_state = iface.get_attr('IFLA_OPERSTATE').capitalize()
                network_info.append(iface_name.center(20))
                network_info.append('--------------------')
                iface_addr = 'N/A'
                if iface_state == 'Up':
                    for iface_address in self._ip.get_addr(index=iface["index"]):
                        if iface_address['family'] == 2:
                            iface_addr = iface_address.get_attr('IFA_ADDRESS')

                network_info.append("State:" + iface_state)
                network_info.append("Network Address")
                network_info.append(iface_addr.rjust(20))
                network_info.append("")

        iface_gateway = 'N/A'
        for tmp_route in self._ip.get_routes():
            if (not tmp_route.get_attr('RTA_GATEWAY') is None) and (tmp_route['family'] == 2):
                iface_gateway = tmp_route.get_attr('RTA_GATEWAY')
        network_info.append("Gateway:")
        network_info.append(iface_gateway.rjust(20))
        network_info.append("")

        dns_ips = []
        for tmp_line in open('/etc/resolv.conf', 'r'):
            tmp_data = tmp_line.split()
            if tmp_data[0] == 'nameserver':
                dns_ips.append(tmp_data[1])
        network_info.append("DNS:")
        for tmp_dns_ip in dns_ips:
            network_info.append("Name Server:")
            network_info.append(tmp_dns_ip.rjust(20))
        network_info.append("")

        # Check for a change of command
        if self._curses.has_command_changed():
            # Action button events
            if fp_command == commands.CMD_UP:
                if self._list_offset > 0:
                    self._list_offset -= 1
            if fp_command == commands.CMD_DOWN:
                if self._list_offset < (len(network_info) - 4):
                    self._list_offset += 1

        self._curses.get_screen().clear()
        for i in range(0,4):
            self._curses.get_screen().addstr(i, 0, network_info[self._list_offset + i])
        self._curses.get_screen().refresh()

# Displays system information
#####################################################################################################
    def system_info(self, fp_command):
        os_distro = platform.linux_distribution()

        system_info = []
        system_info.append("System".center(20))
        system_info.append('OS:  ' + platform.system())
        system_info.append('Distro:  ' + os_distro[0].capitalize() + " " + os_distro[1])
        system_info.append('Release: ' + platform.release())
        system_info.append('Proc:    ' + platform.machine())
        if platform.machine().startswith("arm"):
            rpi_model = subprocess.check_output(args=["/bin/cat","/proc/device-tree/model"]).replace(b'\x00', b'').decode()
            rpi_model = rpi_model.replace('Raspberry Pi ', '')
            rpi_model = rpi_model.replace(' Model ', '')
            system_info.append("RPi: " + rpi_model)

        mem_total = None
        mem_free = None
        mem_info = subprocess.check_output(args=["/bin/cat","/proc/meminfo"]).decode().split('\n')
        for tmp_mem_info in mem_info:
            if tmp_mem_info.startswith("MemFree"): mem_free = tmp_mem_info.replace("MemFree:", "").strip()
            if tmp_mem_info.startswith("MemTotal"): mem_total = tmp_mem_info.replace("MemTotal:", "").strip()
        system_info.append("")
        system_info.append("Memory".center(20))
        system_info.append("Total Mem: " + mem_total)
        system_info.append("Free Mem: " + mem_free)

        system_info.append("")
        system_info.append("Display".center(20))
        if self._curses.get_screen_type() == curses_wrapper.SCREEN_TYPE_NCURSES:
            system_info.append("Type: ncurses")
        if self._curses.get_screen_type() == curses_wrapper.SCREEN_TYPE_FPDEVICE:
            system_info.append("Type: PiAdagio FP")
            system_info.append("Mod Ver: " + self._curses.get_screen().get_device_module_version())

        # Check for a change of command
        if self._curses.has_command_changed():
            # Action button events
            if fp_command == commands.CMD_UP:
                if self._list_offset > 0:
                    self._list_offset -= 1
            if fp_command == commands.CMD_DOWN:
                if self._list_offset < (len(system_info) - 4):
                    self._list_offset += 1

        self._curses.get_screen().clear()
        for i in range(0,4):
            self._curses.get_screen().addstr(i, 0, system_info[self._list_offset + i])
        self._curses.get_screen().refresh()

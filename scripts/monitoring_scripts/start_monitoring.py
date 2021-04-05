#!/usr/bin/python3.9

import os
import signal
import time
import subprocess

from sig_helper import GracefulKiller

#=============================
#   Some General Definitions
#=============================
PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER_PATH = f'{PROGRAM_PATH}/../data'
TOP_OUTPUT_FILE = f'{DATA_FOLDER_PATH}/top_output.txt'
NETWORK_OUTPUT_FILE = f'{DATA_FOLDER_PATH}/network_output.txt'

#=============================
#       Main code
#=============================

# Cheking if this program is running under supdo provileges.
if(os.getuid() != 0):
  print("Please run this script with sudo privileges.")
  exit(1)

# Checking if the monitorinf folder exists.
if(not os.path.isdir(DATA_FOLDER_PATH)):
  # Creating monitoring folder
  subprocess.call(['mkdir', DATA_FOLDER_PATH])

# Defining output-file from top execution
top_output = open(TOP_OUTPUT_FILE, "w+")

# Calling 'top' and 'iptraf-ng' processes.
top = subprocess.Popen(["top","-u", "libvirt-qemu", "-d", "1", "-b"], stdout = top_output)
network = subprocess.Popen(["iptraf", "-u", "-i", "all", "-B", "-L", NETWORK_OUTPUT_FILE])


print(f'Monitoring environment with top (PID=[{top.pid}]) and iptraf (PID=[{network.pid}])...')
killer = GracefulKiller()
while not killer.kill_now:
  time.sleep(1)
print(f'Killing monitoring processes top (PID=[{top.pid}]) and iptraf (PID=[{network.pid}])...')

# killing the 'top' and 'iptraf-ng' processes.
#(NOTE) for some unknow reason, it 'iptraf' calls two pocesses when called by python, so its in needed to kill 'network.pid' as wall as 'network.pid + 1'
subprocess.call(["kill",  "-USR2", str(top.pid), str(network.pid), str(network.pid + 1)])

print(f'Exiting monitoring processes halder.')

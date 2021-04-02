#!/usr/bin/python3.9

import os
import signal
import subprocess

#=============================
#   Some General Definitions
#=============================
PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))




# Cheking if this program is running under supdo provileges.
if(os.getuid() != 0):
  print("Please run this script with sudo privileges.")
  exit(1)

# Checking if the monitorinf folder exists.
if(not os.path.isdir(f'{PROGRAM_PATH}/monitoring')):
  # Creating monitoring folder
  subprocess.call(['mkdir', f'{PROGRAM_PATH}/monitoring'])

# Defining output-file from top execution
top_output = open(f'{PROGRAM_PATH}/monitoring/top_output.txt', "w+")

# Calling 'top' and 'iptraf-ng' processes.
top = subprocess.Popen(["top","-u", "libvirt-qemu", "-d", "1", "-b"], stdout = top_output)
network = subprocess.Popen(["iptraf", "-u", "-i", "all", "-B", "-L", f'{PROGRAM_PATH}/monitoring/network_output.txt'])


# Waiting for users input to finish the monitoring process
input("Press any key to interrupt monitoring:")


# killing the 'top' and 'iptraf-ng' processes.
#(NOTE) for some unknow reason, it 'iptraf-ng' calls two pocesses when called by python, so its in needed to kill 'network.pid' as wall as 'network.pid + 1'
subprocess.call(["kill",  "-USR2", str(top.pid), str(network.pid), str(network.pid + 1)])

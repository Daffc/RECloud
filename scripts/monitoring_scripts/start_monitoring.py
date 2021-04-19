#!/usr/bin/env python3.9

import os
import sys
import time
import subprocess
import setproctitle

#=============================
#   Some General Definitions
#=============================
setproctitle.setthreadtitle(os.path.basename(__file__))
PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))

DATA_FOLDER_PATH = f'{PROGRAM_PATH}/../data'
CPU_MEM_OUTPUT_FILE = f'{DATA_FOLDER_PATH}/cpu_mem_output.txt'
NETWORK_OUTPUT_FILE = f'{DATA_FOLDER_PATH}/network_output.txt'
VENV_PATH =  f'{PROGRAM_PATH}/../../venv/bin/python3.9'

#=============================
#   Including Project Libs
#=============================
sys.path.append(f'{PROGRAM_PATH}/../libs')

from sig_helper import GracefulKiller

#=============================
#       Main code
#=============================

if __name__ == "__main__":
  # Cheking if this program is running under supdo provileges.
  if(os.getuid() != 0):
    print("Please run this script with sudo privileges.")
    exit(1)

  # Checking if the monitorinf folder exists.
  if(not os.path.isdir(DATA_FOLDER_PATH)):
    # Creating monitoring folder
    subprocess.call(['mkdir', DATA_FOLDER_PATH])

  # Calling 'top' and 'iptraf-ng' processes.
  cpu_mem = subprocess.Popen([VENV_PATH, f"{PROGRAM_PATH}/cpu_mem_monitor.py", CPU_MEM_OUTPUT_FILE])
  network = subprocess.Popen(["iptraf", "-u", "-i", "all", "-B", "-L", NETWORK_OUTPUT_FILE])

  print(f'Monitoring environment with  "cpu_mem_monitor.py" (PID=[{cpu_mem.pid}]) and iptraf (PID=[{network.pid}, {network.pid + 1}])...')
  killer = GracefulKiller()
  while not killer.kill_now:
    time.sleep(1)
  print(f'Killing monitoring processes "cpu_mem_monitor.py" (PID=[{cpu_mem.pid}]) and iptraf (PID=[{network.pid}, {network.pid + 1}])...')

  # killing the 'top' and 'iptraf-ng' processes.
  #(NOTE) for some unknow reason, it 'iptraf' calls two pocesses when called by python, so its in needed to kill 'network.pid' as wall as 'network.pid + 1'
  subprocess.call(["kill",  "-USR2", str(network.pid), str(network.pid + 1)])
  network.terminate()
  print(f'Exiting monitoring processes halder.')

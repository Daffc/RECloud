#!/usr/bin/env python3.9

import os
import sys
import time
import signal
import errno
import subprocess
import setproctitle

#=============================
#   Some General Definitions
#=============================
setproctitle.setproctitle(os.path.basename(__file__)[:-3])
PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))

DATA_FOLDER_PATH = os.path.normpath(f'{PROGRAM_PATH}/../data')
CPU_MEM_OUTPUT_FILE = os.path.normpath(f'{DATA_FOLDER_PATH}/cpu_mem_output.txt')
NETWORK_OUTPUT_FILE = os.path.normpath(f'{DATA_FOLDER_PATH}/network_output.txt')
TCPDUMP_OUTPUT_FILE = os.path.normpath(f'{DATA_FOLDER_PATH}/network_output.pcap')
VENV_PATH =  os.path.normpath(f'{PROGRAM_PATH}/../../venv/bin/python3.9')

#=============================
#   Including Project Libs
#=============================
sys.path.append(f'{PROGRAM_PATH}/../libs')

import helper
from sig_helper import GracefulKiller

#=============================
#   Local Functions
#=============================
# Exclude file in 'path' if it exists.
def removeNetworkFile(path):
  if os.path.exists(path):
      os.remove(path)

# Check if process with 'pid' has finished.
def hasProcessEnd(pid):        
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # If process does no exists, return True
            return True
    return False

# Wait until all subprocesses with pid in 'subprocess id' has finished.
def waitSubprocessesDie(subprocess_id):
  print("Wait for subprocesses to finish...")
  exit_codes = [hasProcessEnd(p) for p in subprocess_id]
  while(not all(exit_codes)):
    time.sleep(1)
    exit_codes = [hasProcessEnd(p) for p in subprocess_id]
  print("Done!")
#=============================
#       Main code
#=============================

if __name__ == "__main__":
  # Cheking if this program is running under supdo provileges.
  if(os.getuid() != 0):
    print("Please run this script with sudo privileges.")
    exit(1)

  # Creating monitoring folder
  helper.createFolder(DATA_FOLDER_PATH)

  # Removing Network Monitoring file from previous experiments.
  removeNetworkFile(NETWORK_OUTPUT_FILE)

  # Calling 'top' and 'iptraf-ng' processes.
  cpu_mem = subprocess.Popen([VENV_PATH, f"{PROGRAM_PATH}/cpuMemMonitor.py", "-o", CPU_MEM_OUTPUT_FILE])
  network = subprocess.Popen([f"{PROGRAM_PATH}/iptraf-ng/iptraf-ng", "-i", "all", "-B", "-L", NETWORK_OUTPUT_FILE])
  tcpdump = subprocess.Popen([f"tcpdump", "-U", "-i", "br0", "-s", "96", "-w", TCPDUMP_OUTPUT_FILE])
  
  print(f'Monitoring environment with  "cpuMemMonitor.py" (PID=[{cpu_mem.pid}]) and iptraf-ng (PID=[{network.pid}, {network.pid + 1}])...')
  killer = GracefulKiller()
  while not killer.kill_now:
    time.sleep(1)
  print(f'Killing monitoring processes "cpuMemMonitor.py" (PID=[{cpu_mem.pid}]) and iptraf-ng (PID=[{network.pid}, {network.pid + 1}])...')
  
  # killing the 'cpuMemMonitor.py' and 'iptraf-ng' processes.
  #(NOTE) When called, "iptraf-ng" creates two processes, while the first becomes <defunct> the second does the traffic monitoring.
  os.kill((network.pid + 1), signal.SIGUSR2)
  cpu_mem.terminate()
  tcpdump.terminate()

  # Avoiding subprocesses to remain as zombies.
  cpu_mem.communicate()
  network.communicate()
  tcpdump.communicate()

  # Wainting for subprocesses conclusion.
  waitSubprocessesDie([cpu_mem.pid, (network.pid + 1), tcpdump.pid])
  
  print(f'Exiting monitoring processes halder.')

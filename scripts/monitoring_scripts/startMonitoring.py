#!/usr/bin/env python3.9

import os
import sys
import time
import signal
import errno
import subprocess
import setproctitle
import argparse

#=============================
#   Some General Definitions
#=============================
setproctitle.setproctitle(os.path.basename(__file__)[:-3])
PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))

DATA_FOLDER_PATH = os.path.normpath(f'{PROGRAM_PATH}/../data')
CPU_MEM_OUTPUT_FILE = os.path.normpath(f'{DATA_FOLDER_PATH}/cpu_mem_output.txt')
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
def removeFile(path: str):
  if os.path.exists(path):
      os.remove(path)

# Check if process with 'pid' has finished.
def hasProcessEnd(pid: int):        
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # If process does no exists, return True
            return True
    return False

# Wait until all subprocesses with pid in 'subprocess id' has finished.
def waitSubprocessesDie(subprocess_id: list):
  print("Wait for subprocesses to finish...")
  exit_codes = [hasProcessEnd(p) for p in subprocess_id]
  while(not all(exit_codes)):
    time.sleep(1)
    exit_codes = [hasProcessEnd(p) for p in subprocess_id]
  print("Done!")


# Parsing program initialization arguments. 
def parsingArguments():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description="program to manage Networn (tcpdump), and CPU and Memory (CpuMemMonitor) processes.")
    parser.add_argument("-d", default=0.5, required=False, help="The time interval between sampling the CPU and Moemory statistics in seconds (must bee between 5 and 0.05, default is 0.5)")
    args = parser.parse_args()

    return float(args.d)

#=============================
#       Main code
#=============================

if __name__ == "__main__":
  # Cheking if this program is running under supdo provileges.
  if(os.getuid() != 0):
    print("Please run this script with sudo privileges.")
    exit(1)

  # Defining delay between CPU and memory samplings.
  sampling_delay = parsingArguments()

  # Creating monitoring folder
  helper.createFolder(DATA_FOLDER_PATH)

  # Removing Monitoring files from previous experiments.
  removeFile(CPU_MEM_OUTPUT_FILE)
  removeFile(TCPDUMP_OUTPUT_FILE)

  # Calling 'cpu_mem' and 'tcpdump' processes, defining highest priority (-20).
  cpu_mem = subprocess.Popen([f"{PROGRAM_PATH}/Cscripts/cpuMemMonitor", "-o", CPU_MEM_OUTPUT_FILE, "-d", str(sampling_delay)], preexec_fn=lambda : os.nice(-20))
  tcpdump = subprocess.Popen([f"tcpdump", "-U", "-i", "br0", "-s", "96", "-w", TCPDUMP_OUTPUT_FILE], preexec_fn=lambda : os.nice(-20))

  print(f'Monitoring environment with  cpuMemMonitor (PID=[{cpu_mem.pid}]) and tcpdump ([{tcpdump.pid}]])...')
  killer = GracefulKiller()

  while not killer.kill_now:
    time.sleep(1)

  print(f'Killing monitoring processes cpuMemMonitor (PID=[{cpu_mem.pid}]) and tcpdump ([{tcpdump.pid}]])...')
  
  # killing the 'cpuMemMonitor' and 'tcpdump' processes.
  cpu_mem.terminate()
  tcpdump.terminate()

  # Avoiding subprocesses to remain as zombies.
  cpu_mem.communicate()
  tcpdump.communicate()

  # Wainting for subprocesses conclusion.
  waitSubprocessesDie([cpu_mem.pid, tcpdump.pid])
  
  print(f'Exiting monitoring processes handler.')

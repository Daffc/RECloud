#!/usr/bin/env python3.9

import os
import sys
import time
import signal
import errno
import subprocess
import setproctitle
import argparse
import json

#=============================
#   Some General Definitions
#=============================
setproctitle.setproctitle(os.path.basename(__file__)[:-3])
PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))

DATA_FOLDER_PATH = os.path.normpath(f'{PROGRAM_PATH}/../data')
CPU_MEM_OUTPUT_FILE = os.path.normpath(f'{DATA_FOLDER_PATH}/cpu_mem_output.txt')
TCPDUMP_OUTPUT_FILE = os.path.normpath(f'{DATA_FOLDER_PATH}/network_output.pcap')

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


# If 'env_file_path' is defined, recover the virtual machines IP and assemble the filter string to TcpDump.
def recoverVirtualEnvironmentIP(env_file_path):
  set_filter = ""
  if(env_file_path != ""):
    if(not os.path.isfile(env_file_path)):
      exit(f"ERROR: '{env_file_path}' either does not exists or is not a valid file.")
    with open(env_file_path, "r") as file:
      data = json.load(file)
      if(data['virtual_machines'][0]):
        ips = [ vm["ip"] for vm in data['virtual_machines']]
        set_filter = f" host {' or '.join(ips)} "

  return set_filter
      
# Parsing program initialization arguments. 
def parsingArguments():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description="Program to manage Networn (tcpdump), and CPU and Memory (CpuMemMonitor) probe processes.")
    parser.add_argument("-d", default=0.5, required=False, help="The time interval between sampling the CPU and Memory statistics in seconds (must bee between 5 and 0.05, default is 0.5)")
    parser.add_argument("-e", default= "", required=False, help="Path to 'environments.json' file that should be used as filter to Network probe.")
    args = parser.parse_args()

    return float(args.d), args.e

#=============================
#       Main code
#=============================

if __name__ == "__main__":
  # Cheking if this program is running under supdo provileges.
  if(os.getuid() != 0):
    print("Please run this script with sudo privileges.")
    exit(1)

  # Defining delay between CPU and memory samplings.
  sampling_delay, env_file_path = parsingArguments()

  # Creating monitoring folder
  helper.createFolder(DATA_FOLDER_PATH)

  # Removing Monitoring files from previous experiments.
  removeFile(CPU_MEM_OUTPUT_FILE)
  removeFile(TCPDUMP_OUTPUT_FILE)

  # Recoverting Network probe ip filters if 'env_file_path' is defined.
  filter_ips = recoverVirtualEnvironmentIP(env_file_path)

  # Calling 'cpu_mem' and 'tcpdump' processes, defining highest priority (-20).
  cpu_mem = subprocess.Popen([f"{PROGRAM_PATH}/Cscripts/cpuMemMonitor", "-o", CPU_MEM_OUTPUT_FILE, "-d", str(sampling_delay)], preexec_fn=lambda : os.nice(-20))
  tcpdump = subprocess.Popen([f"tcpdump", "-U", "-i", "br0", "-s", "96", "-w", TCPDUMP_OUTPUT_FILE, filter_ips], preexec_fn=lambda : os.nice(-20))

  print(f'Monitoring environment with  cpuMemMonitor (PID=[{cpu_mem.pid}]) and tcpdump ([{tcpdump.pid}]])...')
  killer = GracefulKiller()

  while not killer.kill_now:

    if(cpu_mem.poll() != None):
        print(f'ERROR: Cpu / Memory probe is not running. Finishing monitoring processes.',  flush=True)
        break;
    if(tcpdump.poll() != None):
        print(f'ERROR: Network probe (tcpdump) is not running. Finishing monitoring processes.',  flush=True)
        break

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

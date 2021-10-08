#!/usr/bin/env python3.9

import os
import sys
import time
import setproctitle
import argparse
from datetime import datetime
import json

#=============================
#   Some General Definitions
#=============================
PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))
setproctitle.setproctitle(os.path.basename(__file__)[:-3])

EXPERIMENT_ID = f'experiment_{datetime.now().strftime("%d-%m-%Y_%H:%M:%S")}'

VENV_PATH = os.path.normpath(f'{PROGRAM_PATH}/../../venv/bin/activate')
ENV_EXEC_PATH = os.path.normpath(f'{PROGRAM_PATH}/../environment_scripts/environment.py')
COMPILE_PATH = os.path.normpath(f'{PROGRAM_PATH}/Cscripts')
MONITOR_PATH = os.path.normpath(f'{PROGRAM_PATH}/startMonitoring.py')
DATA_PATH = os.path.normpath(f'{PROGRAM_PATH}/../data')

WAIT_END_INTERVAL = 0.5
#=============================
#   Including Project Libs
#=============================

# for the purpose of run this script, after that this SHOULD BE MODIFIED.
sys.path.append(f'{PROGRAM_PATH}/../libs')

import helper
from helper import RemoteCommand
from helper import FileType

from sig_helper import GracefulKiller


#=============================
#   Local Functions
#=============================

def setAllEnvironments(clients, password):

  print(f'Calling \'environment.py\' for all clients ({clients.hosts})... ', flush=True)
  RemoteCommand(clients, f'echo {password} | sudo -S -- sh -c ". {VENV_PATH} && {ENV_EXEC_PATH}"', 10, False).remoteCommandHandler()
  print('OK!', flush=True)

  # Compiling 'cpuMemMonitor' scripts.
  print(f'Compiling "cpuMemMonitor" for all remote nodes ({COMPILE_PATH})... ')
  RemoteCommand(clients, f"make -C {COMPILE_PATH}", 10, False).remoteCommandHandler()
  print('OK!', flush=True)

# Initiates the monitoring processes for all 'clients' machines.
def runAllMonitoring(clients, password):

  print(f'Calling \'startMonitoring.py\' for all clients ({clients.hosts})... ', flush=True)
  # clients.run_command('echo '+ password +' | sudo -S -- sh -c ". ~/tg_scripts/venv/bin/activate && ~/tg_scripts/scripts/monitoring_scripts/startMonitoring.py" ')
  clients.run_command(f'echo {password} | sudo -S -- sh -c ". {VENV_PATH} && {MONITOR_PATH}"')

# Calling Chrony to synchonize nodes pointed be 'clients'
def synchronizeNodes(clients, password):

  print(f'Synchronizing clock for clients ({clients.hosts})... ', flush=True)
  RemoteCommand(clients, f'echo {password} | sudo -S -- sh -c "chronyc -a \'burst 4/4\'; chronyc -a makestep "', 10, False).remoteCommandHandler()
  print('OK!', flush=True)


# Checking if 'startMonitoring' process has been ended.
def checkMonitorsEnd(clients):
  
  # List to store the name of hosts where 'startMonitoring' still running.
  unfinished_hosts = []

  saida = clients.run_command(f'pgrep startMonitoring')
  for host_out in saida:
    for line in host_out.stdout:
      if(line):
        unfinished_hosts.append(host_out.host)

  return unfinished_hosts

# Kill the 'startMonitoring.py' processes for all 'clients' machines.
def killMonitoringProcesses(clients, password):
  print(f'Killing processes in clients {clients.hosts}...', flush=True)
  RemoteCommand(clients,'echo '+ password +' | sudo -S killall startMonitoring', 10, False).remoteCommandHandler()

  # Recover the list of hosts where 'startMonitoring' is still running.
  unfinished_hosts = checkMonitorsEnd(clients)  

  # If there are still hoss running 'startMonitoring', wait until the process is finished.
  while(unfinished_hosts):

    for host_name in unfinished_hosts:
      print(f'\t[{host_name}] Process "startMonitoring" not finished, waiting {WAIT_END_INTERVAL} seconds and trying again...', flush=True)

    time.sleep(WAIT_END_INTERVAL)
    unfinished_hosts = checkMonitorsEnd(clients)

  print('OK!', flush=True)


def checkPaths(host_file, output_folder):
  if(not os.path.isfile(host_file)):
    exit(f"ERROR: '{host_file}' either does not exists or is not a file.")
  if(not os.path.isdir(output_folder)):
    exit(f"ERROR: '{output_folder}' either does not exists or is not a folder.")

def recoverDataFromNodes(clients, password, output_folder):

  output = os.path.abspath(f'{output_folder}/{EXPERIMENT_ID}')+'/'

  helper.createFolder(output)

  helper.receiveFiles(clients, DATA_PATH, output, separator='')

  data_folders = [x[0] for x in os.walk(output)]

  print(f"Defining 'environments.json' file for {clients.hosts}.", flush=True)
  
  envs = {"hosts": []}
  for node_dir in data_folders[1:]:
    with open(f"{node_dir}/environment.json", "r") as file:
      data =  json.load(file)
      envs["hosts"].append(data)
  with open(f"{output}/environments.json", "w") as file:
    json.dump(envs, file)

  print('OK!', flush=True)


# Parsing program initialization arguments. 
def parsingArguments():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description="Program to start CPU, Memory and Network monitorinment across the node machines listed into 'host_file' trough 'startMonitoring.py' in each of them.\nAter the conclusion of the monitoring proceses, the monitoring  and the environment data are stored into 'output_folder'.")
    parser.add_argument("host_file", help="Path to file that lists the hosts that will be monitored.")
    parser.add_argument("output_folder", help="Path to folder that will store the result data.")
    args = parser.parse_args()

    return args.host_file, args.output_folder

#=============================
#       Main code
#=============================
if __name__ == "__main__":

  host_file, output_folder = parsingArguments()

  host_file = os.path.normpath(host_file)
  output_folder = os.path.normpath(output_folder)

  # Verify if 'host_file' and 'output_folder' are valid.
  checkPaths(host_file, output_folder)

  user, password = helper.recoverCredentials()
  hosts = helper.recoverHosts(host_file, FileType.TEXT)
  
  # Definind Connection with Node Machines
  clients = helper.defineConnection(user, password, hosts)

  # Setting client's shell as non-interactive.
  helper.settingNonItectivity(clients, password)

  # Run script 'environment.py' for all 'clients'
  setAllEnvironments(clients, password)
  
  # Forcing clients Synchronization
  synchronizeNodes(clients, password)

  # Run script 'startMonitoring.py' for all 'clients'
  runAllMonitoring(clients, password)

  # Waiting for user input in order to stop monitoring process for all the 'client' machines
  print(f'\'CTRL+C\' or kill this process to stop all the monitoring processes.')
  killer = GracefulKiller()
  while not killer.kill_now:

    time.sleep(1)

    # Recover all hosts where "startMonitoring" still running.
    unfinished_hosts = checkMonitorsEnd(clients)

    # Defining hosts where "startMonitoring" stopped running.
    finished_hosts = list(set(clients.hosts) - set(unfinished_hosts))
    
    # If any of the hosts is not executing "startMonitoring", print the error message and finish processes.
    if finished_hosts:
      for host_name in finished_hosts:
        print(f'ERROR: Process "startMonitoring" is not running for host [{host_name}]. Finishing monitoring processes.',  flush=True)

      break;   

  # Killing monitoring processes for all the 
  killMonitoringProcesses(clients, password)

  # Recovering Data from Nodes
  recoverDataFromNodes(clients, password, output_folder)


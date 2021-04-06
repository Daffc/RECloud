#!/usr/bin/env python3.9

import os
import sys
import time
import setproctitle

#=============================
#   Some General Definitions
#=============================
PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))
setproctitle.setthreadtitle(os.path.basename(__file__))

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
# Initiates the monitoring processes for all 'clients' machines.
def runAllMonitoring(clients, user, password):


  print(f'Setting commands to "Noninteractive"... ', flush=True)
  RemoteCommand(clients, 'echo "debconf debconf/frontend select Noninteractive" | echo '+ password +' | sudo -S debconf-set-selections', 10, False).remoteCommandHandler()
  print('OK!', flush=True)

  print(f'Calling \'start_monitoring.py\' for all clients ({clients.hosts})... ', flush=True)

  clients.run_command('source ~/tg_scripts/venv/bin/activate && echo '+ password +' | sudo -S ~/tg_scripts/scripts/monitoring_scripts/start_monitoring.py')


# Kill the 'start_monitoring.py' processes for all 'clients' machines.
def killMonitoringProcesses(clients, user, password):
  print(f'Killing processes in clients {clients.hosts}...', flush=True)
  RemoteCommand(clients,'echo '+ password +' | sudo -S killall start_monitoring.py', 10, False).remoteCommandHandler()
  print('OK!', flush=True)


#=============================
#       Main code
#=============================
user, password = helper.recoverCredentials()
hosts = helper.recoverHosts(f"{PROGRAM_PATH}/host_list", FileType.TEXT)

# Definind Connection with Virtual Machines
clients = helper.defineConnection(user, password, hosts)

# Run script 'set_environment.py' for all 'clients'
runAllMonitoring(clients, user, password)

# Waiting for user input in order to stop monitoring process for all the 'client' machines
print(f'\'CTRL+C\' or kill this process in order to stop all the monitorinment processes.')
killer = GracefulKiller()
while not killer.kill_now:
  time.sleep(1)

# Killing monitoring processes for all the 
killMonitoringProcesses(clients, user, password)

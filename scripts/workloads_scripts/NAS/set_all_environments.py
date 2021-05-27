#!/usr/bin/env python3.9

import os
import sys
import setproctitle
import argparse

#=============================
#   Some General Definitions
#=============================

PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))
setproctitle.setthreadtitle(os.path.basename(__file__))

VENV_PATH = os.path.normpath(f'{PROGRAM_PATH}/../../../venv/bin/activate')
ENV_EXEC_PATH = os.path.normpath(f'{PROGRAM_PATH}/../../environment_scripts/environment.py')
SET_ENV_PATH = os.path.normpath(f'{PROGRAM_PATH}/set_environment.py')
#=============================
#   Including Project Libs
#=============================

# for the purpose of run this script, after that this SHOULD BE MODIFIED.
sys.path.append(f'{PROGRAM_PATH}/../../libs')

import helper
from helper import RemoteCommand
from helper import FileType

#=============================
#   Local Functions
#=============================

# Calling 'set_envirnment.py' for all 'clients'.
def setAllEnvironments(clients, user, password):
  print(f'Setting commands to "Noninteractive"... ', flush=True)
  RemoteCommand(clients, f'echo "debconf debconf/frontend select Noninteractive" | echo {password} | sudo -S debconf-set-selections', 10, False).remoteCommandHandler()
  print('OK!', flush=True)

  print(f'Calling \'environment.py\' for all clients ({clients.hosts})... ', flush=True)
  RemoteCommand(clients, f'echo {password} | sudo -S -- sh -c ". {VENV_PATH} && {ENV_EXEC_PATH}"', 10, False).remoteCommandHandler()
  print('OK!', flush=True)

  print(f'Running \'set_environment.py\' for all clients ... ', flush=True)
  RemoteCommand(clients,f'. {VENV_PATH} && echo \'{user}\n{password}\nN\'| {SET_ENV_PATH}', 10, False).remoteCommandHandler()
  print('OK!', flush=True)

# Parsing program initialization arguments. 
def parsingArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("hostFile", default='', help="Path to file storing list of hosts.")
    args = parser.parse_args()

    return args.hostFile

#=============================
#	Main code
#=============================
if __name__ == "__main__":

  host_list_path = parsingArguments()
  host_list_path = os.path.normpath(host_list_path)
  hosts = helper.recoverHosts(host_list_path, FileType.TEXT)
  
  user, password = helper.recoverCredentials()
 
  # Definind Connection with Virtual Machines
  clients = helper.defineConnection(user, password, hosts)
  
  # Run script 'set_environment.py' for all 'clients'
  setAllEnvironments(clients, user, password)

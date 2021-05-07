#!/usr/bin/env python3.9

import json
import os
import shutil
import sys
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
sys.path.append(f'{PROGRAM_PATH}/../../libs')

import helper
from helper import FileType
from helper import RemoteCommand

#=============================
#   Local Functions
#=============================

def outputVMList(clients, origin, destination):
 
  print(f'Creating \'environment.json\' for {clients.hosts}... ', flush=True)
  RemoteCommand(clients, f'echo {password} | sudo -S -- sh -c ". ~/tg_scripts/venv/bin/activate && ~/tg_scripts/scripts/environment_scripts/environment.py"', 10, False).remoteCommandHandler()
  print('OK!', flush=True)
 
  # Receiving environment files from 'clients'
  helper.receiveFiles(clients, f'{PROGRAM_PATH}/../../data/environment.json', f'{PROGRAM_PATH}/environments/')

  print(f'Listing VM from {clients.hosts}...', flush=True)
  
  envirnment_files = os.listdir(origin)
  with open(destination,"w") as output_file:
    for ef in envirnment_files:
      print(f'\t from \'{ef}\':')
      with open(f'{origin}/{ef}', "r") as environment_file:
        env = json.load(environment_file)
        for vm in env["virtualMachines"]:
          print(f'\t\t \'{vm["ip"]}\'')
          output_file.write(f'{vm["ip"]}\n')

  print('OK!', flush=True)
  
  print(f'Removing Temporary files \'{PROGRAM_PATH}/environments/\'', flush=True)
  shutil.rmtree(f'{PROGRAM_PATH}/environments/')
  print('OK!', flush=True)


def crossConnectAll(user, password, vm_file_path):

  vm_hosts = helper.recoverHosts(f'{vm_file_path}', FileType.TEXT)
  vm_clients = helper.defineConnection(user, password, vm_hosts)
  
  helper.crossConnect(vm_hosts, vm_clients)

#=============================
#	Main code
#=============================
user, password = helper.recoverCredentials()
hosts = helper.recoverHosts(f'{PROGRAM_PATH}/host_list', FileType.TEXT)

# Definind Connection with 'host' Machines
clients = helper.defineConnection(user, password, hosts)

# Listing Virtual Machines from 'clients' Files
outputVMList( clients, f'{PROGRAM_PATH}/environments', f'{PROGRAM_PATH}/VM_list.txt')

# Cross connecting all Virtual Machines
crossConnectAll(user, password, f'{PROGRAM_PATH}/VM_list.txt')

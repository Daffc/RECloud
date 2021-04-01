#!/usr/bin/env python3.9

import json
import os
import helper
import shutil
from helper import FileType

#=============================
#   Some General Definitions
#=============================
PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))


def outputVMList(clients, origin, destination):
  
  # Receiving environment files from 'clients'
  helper.receiveFiles(clients, f'{PROGRAM_PATH}/../../monitoring/environment.json', f'{PROGRAM_PATH}/environments/')

  print(f'Listing VM from {clients.hosts}...', flush=True)
  
  envirnment_files = os.listdir(origin)
  with open(f'{destination}',"w") as output_file:
    for ef in envirnment_files:
      print(f'\t from \'{ef}\':')
      with open(f'{origin}/{ef}', "r") as environment_file:
        env = json.load(environment_file)
        for vm in env["machines"]:
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

# Definind Connection with Virtual Machines
clients = helper.defineConnection(user, password, hosts)

# Listing Virtual Machines from 'clients' Files
outputVMList( clients, f'{PROGRAM_PATH}/environments', f'{PROGRAM_PATH}/VM_list.txt')

# Cross connecting all Virtual Machines
crossConnectAll(user, password, f'{PROGRAM_PATH}/VM_list.txt')

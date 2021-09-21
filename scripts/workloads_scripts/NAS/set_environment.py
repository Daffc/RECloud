#!/usr/bin/env python3.9

import os
import sys
import setproctitle
#=============================
#   Some General Definitions
#=============================
NPB_VERSION = 'NPB3.3.1'

PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))
setproctitle.setthreadtitle(os.path.basename(__file__))

VENV_PATH = os.path.normpath(f'{PROGRAM_PATH}/../../../venv/bin/activate')
ENV_EXEC_PATH = os.path.normpath(f'{PROGRAM_PATH}/../../environment_scripts/environment.py')

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

# Installing NPB dependencies for each VM in 'clients'
def installDependences(clients, password):

  print(f'Updating the package manager (\'apt update\')... ', flush=True)
  RemoteCommand(clients,'echo '+ password +' | sudo -S apt-get update -y', 10, False).remoteCommandHandler()
  print('OK!', flush=True)
  
  dependencies = ['gfortran', 'build-essential', 'mpich']

  for dependence in dependencies:

    print(f'Install \'{dependence}\'... ', flush=True)
    RemoteCommand(clients, 'echo '+ password +' | sudo -S apt-get install '+ dependence +' -y', 20, False).remoteCommandHandler()
    print('OK!', flush=True)
  
# Installing NPB in each VM in 'clients'
def installNPB(clients, password):

  print(f'Downloading {NPB_VERSION}.tar.gz... ', flush=True)
  RemoteCommand(clients,f'wget \'https://www.nas.nasa.gov/assets/npb/{NPB_VERSION}.tar.gz\'', 10, False).remoteCommandHandler()
  print('OK!', flush=True)

  print(f'Decompressing {NPB_VERSION}.tag.gz... ', flush=True)
  RemoteCommand(clients,f'tar -xf {NPB_VERSION}.tar.gz', 10, False).remoteCommandHandler()
  RemoteCommand(clients,f'rm {NPB_VERSION}.tar.gz', 10, False).remoteCommandHandler()
  print('OK!', flush=True)

  print(f'Sending  \'make.def\' and \'suite.def\'... ', flush=True)
  helper.sendFiles(clients, f'{PROGRAM_PATH}/config/', f"./{NPB_VERSION}/NPB3.3-MPI/config/")
  print('OK!', flush=True)

  print(f'Compiling {NPB_VERSION} Programs according to \'suite.def\'... ', flush=True)
  RemoteCommand(clients,f'make suite -C ~/NPB3.3.1/NPB3.3-MPI ', 10, False).remoteCommandHandler()
  print('OK!', flush=True)

def setAllEnvironments(clients, password):

  print(f'Calling \'environment.py\' for all clients ({clients.hosts})... ', flush=True)
  RemoteCommand(clients, f'echo {password} | sudo -S -- sh -c ". {VENV_PATH} && {ENV_EXEC_PATH}"', 10, False).remoteCommandHandler()
  print('OK!', flush=True)

#=============================
#	Main code
#=============================
if __name__ == '__main__':
  user, password = helper.recoverCredentials()
  
  hosts = helper.recoverHosts(PROGRAM_PATH +"/../../data/environment.json", FileType.JSON)
  
  # Definind Connection with Virtual Machines
  clients = helper.defineConnection(user, password, hosts)
  
  # Setting client's shell as non-interactive.
  helper.settingNonItectivity(clients, password)

  # Run script 'environment.py' for all 'clients'
  setAllEnvironments(clients, password)
  
  # Creating Temporary folder.
  helper.createFolder(f'{PROGRAM_PATH}/keys')
  
  # Sending keys and authorized_keys to the clients
  helper.sendFiles(clients, f'{PROGRAM_PATH}/keys/', "./.ssh")
  
  # Changing permission of keys and authorized_keys in clients.
  helper.changeKeyPermissions(clients)
  
  # Cross defining fingerprint for all Virtual Machines.
  helper.crossConnect(hosts, clients)
  
  # Intalling Dependeces for MPI
  installDependences(clients, password)
  
  # Installing NPB3.3.1
  installNPB(clients, password)
  

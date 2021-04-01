#!/usr/bin/env python3.9

import os
import helper
from helper import RemoteCommand
from helper import FileType


#=============================
#   Some General Definitions
#=============================
NPB_VERSION = 'NPB3.3.1'
PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))


# Cross connecting all the Virtual Machines
def crossConnect(hosts, clients):
 
  print(f'Generating \'know_hosts\' file for each Virtual Machine... ', flush=True)   
  # Joining all the hosts in the 'strHost ' string, separated by one space.
  strHosts = ' '.join(map(str, hosts))
   
  # Generating the 'known_hosts' file with fingerprint of all the VM.
  RemoteCommand(clients, 'ssh-keyscan -t rsa -H ' + strHosts + '> ~/.ssh/known_hosts', 10, False).remoteCommandHandler()

  print('OK!', flush=True)  

# Installing NPB dependencies for each VM in 'clients'
def installDependences(clients, password):
  
  print(f'Setting commands to "Noninteractive"... ', flush=True) 
  RemoteCommand(clients, 'echo "debconf debconf/frontend select Noninteractive" | echo '+ password +' | sudo -S debconf-set-selections', 10, False).remoteCommandHandler()
  print('OK!', flush=True)

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

  print(f'Setting commands to "Noninteractive"... ', flush=True)
  RemoteCommand(clients, 'echo "debconf debconf/frontend select Noninteractive" | echo '+ password +' | sudo -S debconf-set-selections', 10, False).remoteCommandHandler()
  print('OK!', flush=True)

  print(f'Downloading {NPB_VERSION}.tar.gz... ', flush=True)
  RemoteCommand(clients,f'wget \'https://www.nas.nasa.gov/assets/npb/{NPB_VERSION}.tar.gz\'', 10, False).remoteCommandHandler()
  print('OK!', flush=True)

  print(f'Decompressing {NPB_VERSION}.tag.gz... ', flush=True)
  RemoteCommand(clients,f'tar -xf {NPB_VERSION}.tar.gz', 10, False).remoteCommandHandler()
  RemoteCommand(clients,f'rm {NPB_VERSION}.tar.gz', 10, False).remoteCommandHandler()
  print('OK!', flush=True)

  print(f'Sending  \'make.def\' and \'suite.def\'... ', flush=True)
  helper.sendFiles(clients, PROGRAM_PATH + "/config/", f"./{NPB_VERSION}/NPB3.3-MPI/config/")
  print('OK!', flush=True)

  print(f'Compiling {NPB_VERSION} Programs according to \'suite.def\'... ', flush=True)
  RemoteCommand(clients,f'make suite -C ~/NPB3.3.1/NPB3.3-MPI ', 10, False).remoteCommandHandler()
  print('OK!', flush=True)

#=============================
#	Main code
#=============================
user, password = helper.recoverCredentials()
hosts = helper.recoverHosts(PROGRAM_PATH +"/../../monitoring/environment.json", FileType.JSON)


# Definind Connection with Virtual Machines
clients = helper.defineConnection(user, password, hosts)

# Creating Temporary folder.
helper.createFolder("./keys")

# Generating RSA keys.
helper.createSSHKeys("./keys/.ssh")

# Sending keys and authorized_keys to the clients
helper.sendFiles(clients, "./keys/.ssh/", "./.ssh")

# Changing permission of keys and authorized_keys in clients.
helper.changeKeyPermissions(clients)

# Cross defining fingerprint for all Virtual Machines.
crossConnect(hosts, clients)

# Intalling Dependeces for MPI
installDependences(clients, password)

# Installing NPB3.3.1
installNPB(clients, password)


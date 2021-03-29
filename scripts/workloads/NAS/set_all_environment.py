#!/usr/bin/env python3.9

import json
import os
import sys
from getpass import getpass
from pssh.clients import ParallelSSHClient
from pssh.exceptions import Timeout
from gevent import joinall

#=============================
#   Some General Definitions
#=============================
PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))

class RemoteCommand:

  def __init__(self, clients, command, timeout, sudo):
    self._clients = clients
    self._command = command
    self._timeout = timeout

  def remoteCommandHandler(self):
    tries = 0

    while(tries < 5):

      output = self._clients.run_command(self._command)

      try:
        for host_out in output:
          for line in host_out.stdout:
            print(f'\t [{host_out.host}] {line}')
          for line in host_out.stderr:
            print(f'\t [{host_out.host}] {line}')
        return
      except Timeout:
        tries += 1
        self._timeout += self._timeout
        print(f'\tTimeout: trying again with {self._timeout}s')

    print(f'Limit Attemptions ({tries}) during \'{self._command}\'. Exiting program.', file=sys.stderr)
    exit(1)

# Create, verify and return connection with Vitual Machines.
def defineConnection(user, password, hosts):
  print(f'Defining connection with hosts ({hosts})...', flush=True) 
  clients = ParallelSSHClient(hosts, user=user, password=password)

  output = clients.connect_auth()
  joinall(output, raise_error=True)

  print('OK!', flush=True)

  return clients

# Creating array with virtual machines addresses.
def recoverHosts(path):
  hosts = []

  if(not os.path.isfile(path)):
    sys.exit(f"File '{path}' does not exist.")

  with open(path, "r") as host_list:
    hosts = host_list.readlines()
  hosts = [x.strip() for x in hosts]
  print(hosts) 
  return hosts

# Receiving credentials to access the virtual machines.
def recoverCredentials():
  
  print("Inform the User and Password to access the Vitual Machines:")
  user = input("Inform the User:")
  password = getpass()

  return user, password

# Sending keys to Virtual Machines
def sendFiles(clients, origin, destination):
  print(f'Distributing keys among the hosts (\'{origin}\' to \'{destination}\')... ', flush=True)
  
  output = clients.scp_send(origin, destination, recurse=True)
  joinall(output, raise_error=True)
  
  print('OK!', flush=True)

def setAllDependences(clients, user, password):                                                                            
                                                                                                                      
  print(f'Setting commands to "Noninteractive"... ', flush=True)                                                      
  RemoteCommand(clients, 'echo "debconf debconf/frontend select Noninteractive" | echo '+ password +' | sudo -S debconf-set-selections', 10, False).remoteCommandHandler()                                                                  
  print('OK!', flush=True)                                                                                            
                                                                                                                      
  print(f'Running \'set_environment.py\' for all clients ... ', flush=True)                                            
  RemoteCommand(clients,f'source ~/tg_scripts/venv/bin/activate && echo \'{user}\n{password}\nN\'| ~/tg_scripts/scripts/workloads/NAS/set_environment.py', 10, False).remoteCommandHandler()          
  print('OK!', flush=True)                                                                                            
                                                                                                                      
                                                                                                                      
#=============================
#	Main code
#=============================
user, password = recoverCredentials()
hosts = recoverHosts(f"{PROGRAM_PATH}/host_list")

# Definind Connection with Virtual Machines
clients = defineConnection(user, password, hosts)

# Run script 'set_environment.py' for all 'clients'
setAllDependences(clients, user, password)

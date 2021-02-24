#!/usr/bin/env python3.9

import json
import os
import sys
from getpass import getpass
from pssh.clients import ParallelSSHClient
from pssh.exceptions import Timeout
from gevent import joinall

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


#=============================
#	Main code
#=============================
user, password = recoverCredentials()
hosts = recoverHosts("./host_list")

# Definind Connection with Virtual Machines
clients = defineConnection(user, password, hosts)

# Sending keys among the hosts 
sendFiles(clients, "./keys", os.getcwd() + "/keys/")

#!/usr/bin/env python3.9

import json
import os
import sys
from Crypto.PublicKey import RSA
from getpass import getpass
from pssh.clients import ParallelSSHClient
from pssh.exceptions import Timeout
from gevent import joinall
from enum import Enum

class FileType(Enum):
	TEXT = 0
	JSON = 1

# Class responsable for instantiating and controll remote commands.
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

# Create, verify and return connection with 'hosts' machines.
def defineConnection(user, password, hosts):
  print(f'Defining connection with hosts ({hosts})...', flush=True) 
  clients = ParallelSSHClient(hosts, user=user, password=password)

  output = clients.connect_auth()
  joinall(output, raise_error=True)

  print('OK!', flush=True)

  return clients

# Creating array with virtual machines addresses.
def recoverHosts(path, structure):
  hosts = []

  if(not os.path.isfile(path)):
    sys.exit(f"File '{path}' does not exist.")

  if(structure is FileType.TEXT):
    with open(path, "r") as host_list:
      hosts = host_list.readlines()
    hosts = [x.strip() for x in hosts]
  
  elif(structure is FileType.JSON):
    print(f'Recovering json informtion (\'{path}\')... ', flush=True)
    with open(path, "r") as environment_file:
      env = json.load(environment_file)  
      for vm in env["machines"]:
        hosts.append(vm["ip"])
  
  else:
    print(f'TypeFile not Defined.', file=sys.stderr)
    exit(1)  

  return hosts

# Creating folders.
def createFolder(path):
   
  print(f'Verifying existence of \'{path}\'... ', flush=True) 
  # Checking if the monitorinf folder exists.
  if(not os.path.isdir(path)):
    # Creating monitoring folder
    os.mkdir(path)
    print(f'Created!', flush=True)
    return

  print(f'Exists!', flush=True)

# Sending files across the "clients" according to the 'origin' and 'destination' folders.
def sendFiles(clients, origin, destination):
  print(f'Sending files to {clients.hosts} (from \'{origin}\' to \'{destination}\')... ', flush=True)

  output = clients.scp_send(origin, destination, recurse=True)
  joinall(output, raise_error=True)

  print('OK!', flush=True)

# Receiving credentials to access the virtual machines.
def recoverCredentials():
  
  print("Inform the User and Password to access the Machines:")
  user = input("Inform the User:")
  password = getpass()

  return user, password


# Generate SSH keys inside 'path'
def createSSHKeys(path):

  # Create folder to store RSA keys.
  createFolder(path)

  print(f'Generating key to access the Virtual machines... ', flush=True)
  key = RSA.generate(2048)

  # Checking if the key files alread exists.
  if(os.path.isfile(path+"/id_rsa") and os.path.isfile(path+"/id_rsa.pub") and os.path.isfile(path+"/authorized_keys")):
    while True:
      overwrite = input("\t\033[1;33;40mThe keys already exist. Do you want to overwrite them? 'Y', 'N': \033[0m")
      if(overwrite.lower() == 'y'):
        print("\tProceeding with key generation...")
        break
      elif(overwrite.lower() == 'n'):
        print("\tKey generation canceled!")
        return
      else:
        print("\t\033[1;33;40m Please, answer with 'Y' or 'N': \033[0m")

  # Generating keys
  private_key = key.exportKey('PEM')
  with open(path + "/id_rsa", "wb") as private:
    private.write(private_key)

  public_key = key.exportKey('OpenSSH')
  with open(path + "/id_rsa.pub", "wb") as public:
    public.write(public_key)

  with open(path + "/authorized_keys", "wb") as public:
    public.write(public_key)

  print('OK!', flush=True)

# Changing key permission inside the Virtual Machines.
def changeKeyPermissions(clients):

  print(f'Changing key permissions in Virtual Machines (\'id_rsa\', \'id_rsa.pub\' and \'authorized_keys\' )... ', flush=True)
 
  RemoteCommand(clients, 'chmod 644 .ssh/id_rsa.pub .ssh/authorized_keys', 10, False).remoteCommandHandler()
  RemoteCommand(clients, 'chmod 600 .ssh/id_rsa', 10, False).remoteCommandHandler()
  
  print('OK!', flush=True)

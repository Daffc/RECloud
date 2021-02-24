#!/usr/bin/env python3.9

import json
import os
import sys
from Crypto.PublicKey import RSA
from getpass import getpass
from pssh.clients import ParallelSSHClient
from pssh.exceptions import Timeout
from gevent import joinall


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

# Creating array with virtual machines addresses.
def recoverHosts(environment):
  hosts = []

  for vm in environment["machines"]:
    hosts.append(vm["ip"])
  
  return hosts

# Receiving credentials to access the virtual machines.
def recoverCredentials():
  
  print("Inform the User and Password to access the Vitual Machines:")
  user = input("Inform the User:")
  password = getpass()

  return user, password

#Recovering json environment information.
def recoverEnvironmentInformation():
  
  path =  "../../monitoring/environment.json" 
  print(f'Recovering environment informtion (\'{path}\')... ', flush=True)
  
  with open(path, "r") as environment_file:
    env = json.load(environment_file)

  print('OK!', flush=True)
  
  return env

# Generate SSH keys inside 'path'
def createSSHKeys(path):

  # Create folder to store RSA keys.
  createFolder(path)

  print(f'Generating key to access the Virtual machines... ', flush=True)
  key = RSA.generate(2048)

  # Checking if the key files alread exists.
  if(os.path.isfile(path+"/id_rsa") and os.path.isfile(path+"/id_rsa.pub") and os.path.isfile(path+"/authorized_keys")):
    while True:
      overwrite = input("\t\033[1;33;40m The keys already exist. Do you want to overwrite them? 'Y', 'N': \033[0m")
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

# Sending keys to Virtual Machines
def sendFiles(clients, origin, destination):
  print(f'Sending files to Virtual Machines (\'{origin}\' to \'{destination}\')... ', flush=True)
  
  output = clients.scp_send(origin, destination, recurse=True)
  joinall(output, raise_error=True)
  
  print('OK!', flush=True)

# Changing key permission inside the Virtual Machines.
def changeKeyPermissions(clients):

  print(f'Changing key permissions in Virtual Machines (\'id_rsa\', \'id_rsa.pub\' and \'authorized_keys\' )... ', flush=True)
 
  RemoteCommand(clients, 'chmod 644 .ssh/id_rsa.pub .ssh/authorized_keys', 10, False).remoteCommandHandler()
  RemoteCommand(clients, 'chmod 600 .ssh/id_rsa', 10, False).remoteCommandHandler()
  
  print('OK!', flush=True)
  
# Cross connecting all the Virtual Machines
def crossConnect(hosts, clients):
 
  print(f'Generating \'know_hosts\' file for each Virtual Machine... ', flush=True)   
  # Joining all the hosts in the 'strHost ' string, separated by one space.
  strHosts = ' '.join(map(str, hosts))
   
  # Generating the 'known_hosts' file with fingerprint of all the VM.
  RemoteCommand(clients, 'ssh-keyscan -t rsa -H ' + strHosts + '> ~/.ssh/known_hosts', 10, False).remoteCommandHandler()

  print('OK!', flush=True)  

def isntallDependences(clients, password):
  
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
  

#=============================
#	Main code
#=============================
user, password = recoverCredentials()
environment = recoverEnvironmentInformation()
hosts = recoverHosts(environment)


# Definind Connection with Virtual Machines
clients = defineConnection(user, password, hosts)

# Creating Temporary folder.
createFolder("./keys")

# Generating RSA keys.
createSSHKeys("./keys/.ssh")

# Sending keys and authorized_keys to the clients
sendFiles(clients, "./keys/.ssh/", "./.ssh")

# Changing permission of keys and authorized_keys in clients.
changeKeyPermissions(clients)

# Cross defining fingerprint for all Virtual Machines.
crossConnect(hosts, clients)

# Intalling Dependeces for MPI
isntallDependences(clients, password)

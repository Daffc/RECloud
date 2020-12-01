import json
import os
from Crypto.PublicKey import RSA
from getpass import getpass
from pssh.clients import ParallelSSHClient
from pssh.exceptions import Timeout
from gevent import joinall


def remoteCommandHandler(clients, command, timeout):
  if (timeout > 30):
    print(f'Timeout during \'{command}\'. Exiting program.')
    exit()
  
  output = clients.run_command(command, timeout=timeout)
  
  try:
    for host_out in output:
       for line in host_out.stderr:
         print(f'\t [{host_out.host}] {line}')
    return
  except Timeout:
    print(f'\tTimeout: trying again with {timeout + 5}s')
    remoteCommandHandler(clients, command, timeout + 5)

# Creating folders
def createFolder(path):
   
  print(f'Verifying existence of \'{path}\'... ', end='', flush=True) 
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
  print(f'Recovering environment informtion (\'{path}\')... ', end='', flush=True)
  
  with open(path, "r") as environment_file:
    env = json.load(environment_file)

  print('OK!', flush=True)
  
  return env

def createSSHKeys(path):

  # Create folder to store RSA keys.
  createFolder(path)
  
  print(f'Generating key to access the Virtual machines... ', end='', flush=True)
  key = RSA.generate(2048)
 
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
  print(f'Sending files to Virtual Machines (\'{origin}\' to \'{destination}\')... ', end='', flush=True)
  
  output = clients.scp_send(origin, destination, recurse=True)
  joinall(output, raise_error=True)
  
  print('OK!', flush=True)

# Changing key permission inside the Virtual Machines.
def changeKeyPermissions(clients):

  print(f'Changing key permissions in Virtual Machines (\'id_rsa\', \'id_rsa.pub\' and \'authorized_keys\' )... ', end='', flush=True)
  
  remoteCommandHandler(clients, 'chmod 644 .ssh/id_rsa.pub .ssh/authorized_keys',10)
  remoteCommandHandler(clients, 'chmod 600 .ssh/id_rsa',10)
  
  print('OK!', flush=True)
  
# Cross connecting all the Virtual Machines
def crossConnect(hosts, clients):
 
  print(f'Generating \'know_hosts\' file for each Virtual Machine... ', end='', flush=True)   
  # Joining all the hosts in the 'strHost ' string, separated by one space.
  strHosts = ' '.join(map(str, hosts))
   
  # Generating the 'known_hosts' file with fingerprint of all the VM.
  remoteCommandHandler(clients, 'ssh-keyscan -t rsa -H ' + strHosts + '> ~/.ssh/known_hosts', 10)

  print('OK!', flush=True)  

#=============================
#	Main code
#=============================
user, password = recoverCredentials()
environment = recoverEnvironmentInformation()
hosts = recoverHosts(environment)

# Creating Temporary folder.
createFolder("./tmp");

createSSHKeys("./tmp/.ssh")

# Definind Connection with Virtual Machines
clients = ParallelSSHClient(hosts, user=user, password=password)

# Sending keys and authorized_keys to the clients
sendFiles(clients, "./tmp/.ssh/", "./.ssh")

# Changing permission of keys and authorized_keys in clients.
changeKeyPermissions(clients)

# Cross defining fingerprint for all Virtual Machines.
crossConnect(hosts, clients)

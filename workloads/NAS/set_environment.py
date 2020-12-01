import json
import os
from Crypto.PublicKey import RSA
from getpass import getpass
from pssh.clients import ParallelSSHClient
from gevent import joinall


# Creating folders
def createFolder(path):
  # Checking if the monitorinf folder exists.
  if(not os.path.isdir(path)):
    # Creating monitoring folder
    os.mkdir(path)

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
 with open("../../monitoring/environment.json", "r") as environment_file:
   return json.load(environment_file)

def createSSHKeys(path):

  # Create folder to store RSA keys.
  createFolder(path)

  key = RSA.generate(2048)
 
  private_key = key.exportKey('PEM')
  with open(path + "/id_rsa", "wb") as private:
    private.write(private_key)
 
  public_key = key.exportKey('OpenSSH')
  with open(path + "/id_rsa.pub", "wb") as public:
    public.write(public_key)
  
  with open(path + "/authorized_keys", "wb") as public:
    public.write(public_key)


# Sending keys to Virtual Machines
def sendFiles(clients, origin, destination):
  cmd = clients.scp_send(origin, destination, recurse=True)
  joinall(cmd, raise_error=True)

# Changing key permission inside the Virtual Machines.
def changeKeyPermissions(clients):
  cmd = clients.run_command('chmod 644 .ssh/id_rsa.pub .ssh/authorized_keys')
  clients.pool.join()

  cmd = clients.run_command('chmod 600 .ssh/id_rsa')
  clients.pool.join()

# Cross connecting all the Virtual Machines
def crossConnect(hosts, clients):
  
  # Joining all the hosts in the 'strHost ' string, separated by one space.
  strHosts = ' '.join(map(str, hosts))
  
  # Generating the 'known_hosts' file with fingerprint of all the VM.
  cmd = clients.run_command('ssh-keyscan ' + strHosts + '> ~/.ssh/known_hosts')
  clients.pool.join()    



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

crossConnect(hosts, clients)

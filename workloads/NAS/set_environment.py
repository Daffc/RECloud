import json
import os
from Crypto.PublicKey import RSA
from getpass import getpass


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
  
  location = path + "/.ssh";

  # Create folder to store RSA keys.
  createFolder(location)

  key = RSA.generate(2048)
 
  private_key = key.export_key()
  with open(location + "/id_rsa", "wb") as private:
    private.write(private_key)

  public_key = key.publickey().export_key()
  with open(location + "/id_rsa.pub", "wb") as public:
    public.write(public_key)

#Main code.
user, password = recoverCredentials()
environment = recoverEnvironmentInformation()
hosts = recoverHosts(environment)

# Creating Temporary folder.
createFolder("./tmp");

createSSHKeys("./tmp")

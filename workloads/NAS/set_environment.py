import json
from getpass import getpass



# Receiving credentials to access the virtual machines
def recoverCredentials():
  
  print("Inform the User and Password to access the Vitual Machines:")
  user = input("Inform the User:")
  password = getpass();

  return user, password;

#Recovering json environment information.
def recoverEnvironmentInformation():
 with open("../../monitoring/environment.json", "r") as environment_file:
   return json.load(environment_file)







#Main code.
a, b = recoverCredentials();
environment = recoverEnvironmentInformation()

print(a)
print(b)
print(environment)
for vm in environment["machines"]:
  print(f'Initiating process to machine {vm["name"]} ( {vm["ip"]} )')

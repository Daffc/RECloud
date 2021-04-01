#!/usr/bin/env python3.9

import os
import helper
from helper import RemoteCommand
from helper import FileType

#=============================
#   Some General Definitions
#=============================
PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))

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
user, password = helper.recoverCredentials()
hosts = helper.recoverHosts(f"{PROGRAM_PATH}/host_list", FileType.TEXT)

# Definind Connection with Virtual Machines
clients = helper.defineConnection(user, password, hosts)

# Run script 'set_environment.py' for all 'clients'
setAllDependences(clients, user, password)

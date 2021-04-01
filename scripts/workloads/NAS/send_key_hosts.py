#!/usr/bin/env python3.9

import os
import helper
from helper import FileType

#=============================
#   Some General Definitions
#=============================
PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))

#=============================
#	Main code
#=============================
user, password = helper.recoverCredentials()
hosts = helper.recoverHosts(f'{PROGRAM_PATH}/host_list', FileType.TEXT)

# Definind Connection with Virtual Machines
clients = helper.defineConnection(user, password, hosts)

# Sending keys among the hosts 
helper.sendFiles(clients, f'{PROGRAM_PATH}/keys', f'{os.getcwd()}/keys/')

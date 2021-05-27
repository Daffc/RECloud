#!/usr/bin/env python3.9

import os
import sys
import setproctitle
import argparse

#=============================
#   Some General Definitions
#=============================

PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))
setproctitle.setthreadtitle(os.path.basename(__file__))

#=============================
#   Including Project Libs
#=============================

# for the purpose of run this script, after that this SHOULD BE MODIFIED.
sys.path.append(f'{PROGRAM_PATH}/../../libs')

import helper
from helper import FileType

#=============================
#   Local Functions
#=============================
# Parsing program initialization arguments. 
def parsingArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("hostFile", default='', help="Path to file storing list of hosts.")
    args = parser.parse_args()

    return args.hostFile
#=============================
#	Main code
#=============================
if __name__ == "__main__": 
  host_list_path = parsingArguments()
  
  user, password = helper.recoverCredentials()

  host_list_path = os.path.normpath(host_list_path)
  hosts = helper.recoverHosts(host_list_path, FileType.TEXT)

  # Definind Connection with Virtual Machines
  clients = helper.defineConnection(user, password, hosts)

  # Generating public and private keys to share ammong Node and Virtual Machines.
  helper.createFolder(f'{PROGRAM_PATH}/keys')

  # Generating public and private keys to share ammong Node and Virtual Machines.
  helper.createSSHKeys(f'{PROGRAM_PATH}/keys')

  # Sending keys among the hosts 
  helper.sendFiles(clients, f'{PROGRAM_PATH}/keys', f'{os.getcwd()}/keys/')

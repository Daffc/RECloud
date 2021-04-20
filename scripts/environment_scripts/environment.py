#!/usr/bin/env python3.9

import subprocess
import json
import os
import sys
import socket
import collections


#=============================
#   Some General Definitions
#=============================

PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER_PATH = f'{PROGRAM_PATH}/../data'
OUTPUT_FILE = 'environment.json'


#=============================
#   Including Project Libs
#=============================
sys.path.append(f'{PROGRAM_PATH}/../libs')

import helper
import libvirt_helper as lh

#=============================
#   Local Functions
#=============================
def recoverHostData():
  data = {}

  #Recovering 'hostname' and outputing it in 'env_file'
  print(f'Recovering \'hostname\' of current machine.', flush=True)
  hostname = socket.gethostname() 
  data['hostname'] = hostname;
  print('OK!', flush=True)

  #Recovering IP from the host machine
  print(f'Recovering \'ip\' of current machine.', flush=True)
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.connect(("8.8.8.8", 80))
  data['ip'] = s.getsockname()[0];
  s.close()
  print('OK!', flush=True)

  return data

def recoverVMData():
  
  machines = []

  conn = lh.libvirtConnect()
  doms = lh.recoverActiveDomains(conn)

  #Recovering information about the subnet of host_machine (data['ip']).
  print(f'Recovering Network information from running Virtual Machines.', flush=True)
  p1 = subprocess.Popen(['nmap', '-sn', data['ip'][:data['ip'].rfind(".")] +'.0/24'], stdout = subprocess.PIPE)
  subnet = p1.communicate()[0].decode('utf-8')
  data['machines'] = []
  print('OK!', flush=True)

  #iterating over each VM process entry, recovering its informaion
  print(f'Structuring Virtual Machine data in JSON format.', flush=True)
  for dom in doms:

    #Recovering MAC address of virtual machine 'dom.name()'
    p1 = subprocess.Popen(['virsh domiflist ' + dom.name()], stdout = subprocess.PIPE, shell=True)
    output = p1.communicate()[0].decode('utf-8')
    mac_address = output.splitlines()[2].split()[4] 
    
    #Iterating over machines in subnet, retriving 'ip' by the 'mac_adress' of the current virtual machine.
    cache = collections.deque([], 2)
    for entry in subnet.split('\n'):
      if mac_address.upper() in entry: 
        ip = cache[1].split()[4]
      cache.appendleft(entry)

    _, maxmem, _, cpus, _ = dom.info()
    # Storing definind new VM entry in 'data'.
    machines.append({
      'name': dom.name(),
      'id': dom.ID(),
      'UUID': dom.UUIDString(),
      'mac': mac_address,
      'ip': ip,
      'max_memory': maxmem,
      'vcpus': cpus
    })	  
  print('OK!', flush=True)
  
  conn.close()

  return machines

def storeDataJson(data):
  # Storing all the 'data' information in 'envirionment.json'
  print(f'Storing environment information in {DATA_FOLDER_PATH}/{OUTPUT_FILE}', flush=True)
  with open(f'{DATA_FOLDER_PATH}/{OUTPUT_FILE}', 'w') as env_file:
    json.dump(data, env_file)
  print (json.dumps(data, indent=2))
  print('OK!', flush=True)

#=============================
#       Main code
#=============================

if __name__ == '__main__':
  # Cheking if this program is running under supdo provileges.
  if(os.getuid() != 0):
    print("Please run this script with sudo privileges.")
    exit(1)

  # Verifying and creating DATA_FOLDER.
  helper.createFolder(DATA_FOLDER_PATH)

  # Initiating json structure
  data = recoverHostData()

  data["machines"] = recoverVMData()
  
  storeDataJson(data)
  

#!/usr/bin/env python3.9

import subprocess
import json
import os.path
import socket
import collections


PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER_PATH = f'{PROGRAM_PATH}/../data'
OUTPUT_FILE = 'environment.json'

# Cheking if this program is running under supdo provileges.
if(os.getuid() != 0):
  print("Please run this script with sudo privileges.")
  exit(1)

#initiating json structure
data = {}

print(f'Checking existente of {DATA_FOLDER_PATH}', flush=True)
if(not os.path.isdir(DATA_FOLDER_PATH)):
  #creating monitoring folder
  subprocess.call(['mkdir', DATA_FOLDER_PATH])
print('OK!', flush=True)

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


#Recovering infotmation from all VM processes.
print(f'Recovering information of all running Virtual Machines.', flush=True)
p1 = subprocess.Popen(("ps", "awx"), stdout = subprocess.PIPE)
p2 = subprocess.Popen(('grep', 'qemu'), stdin = p1.stdout, stdout=subprocess.PIPE)
saida_procs = subprocess.check_output(("grep", "-v", "grep"), stdin=p2.stdout)
print('OK!', flush=True)


#Recovering information about the subnet of host_machine (data['ip']).
print(f'Recovering Network information from running Virtual Machines.', flush=True)
p1 = subprocess.Popen(['nmap', '-sn', data['ip'][:data['ip'].rfind(".")] +'.0/24'], stdout = subprocess.PIPE)
subnet = p1.communicate()[0].decode('utf-8')
data['machines'] = []
print('OK!', flush=True)

#iterating over each VM process entry, recovering its informaion
print(f'Structuring Virtual Machine data in JSON format.', flush=True)
for line in saida_procs.splitlines():
  # Spliting lines and recovering information separately.
  line_split = line.decode("utf-8").split()
  pid = line_split[0]  
  vm_name = line_split[7]
  uuid = line_split[20]

  #Recovering MAC address of virtual machine 'vm_name'
  p1 = subprocess.Popen(['virsh domiflist ' + vm_name], stdout = subprocess.PIPE, shell=True)
  output = p1.communicate()[0].decode('utf-8')
  mac_address = output.splitlines()[2].split()[4] 
  
  #Iterating over machines in subnet, retriving 'ip' by the 'mac_adress' of the current virtual machine.
  cache = collections.deque([], 2)
  for entry in subnet.split('\n'):
    if mac_address.upper() in entry: 
      ip = cache[1].split()[4]
    cache.appendleft(entry)

  # Storing definind new VM entry in 'data'.
  data['machines'].append({
    'name': vm_name,
    'PID': pid,
    'UUID': uuid,
    'mac': mac_address,
    'ip': ip  
  })	  
print('OK!', flush=True)

# Storing all the 'data' information in 'envirionment.json'
print(f'Storing environment information in {DATA_FOLDER_PATH}/{OUTPUT_FILE}', flush=True)
with open(f'{DATA_FOLDER_PATH}/{OUTPUT_FILE}', 'w') as env_file:
    json.dump(data, env_file)
print (json.dumps(data, indent=2))
print('OK!', flush=True)

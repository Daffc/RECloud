#!/usr/bin/env python3.9

import subprocess
import json
import os.path
import socket
import collections


PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))

#initiating json structure
data = {}

if(not os.path.isdir(f'{PROGRAM_PATH}/monitoring')):
  #creating monitoring folder
  print('OK!', flush=True)                                                                                          
  subprocess.call(['mkdir', f'{PROGRAM_PATH}/monitoring'])

#Recovering 'hostname' and outputing it in 'env_file'
hostname = socket.gethostname() 
data['hostname'] = hostname;


#Recovering IP from the host machine
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
data['ip'] = s.getsockname()[0];
s.close()

#Recovering infotmation from all VM processes.
p1 = subprocess.Popen(("ps", "awx"), stdout = subprocess.PIPE)
p2 = subprocess.Popen(('grep', 'qemu'), stdin = p1.stdout, stdout=subprocess.PIPE)
saida_procs = subprocess.check_output(("grep", "-v", "grep"), stdin=p2.stdout)


#Recovering information about the subnet of host_machine (data['ip']).
p1 = subprocess.Popen(['sudo', 'nmap', '-sn', data['ip'][:data['ip'].rfind(".")] +'.0/24'], stdout = subprocess.PIPE)
subnet = p1.communicate()[0].decode('utf-8')
data['machines'] = []

#iterating over each VM process entry, recovering its informaion
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

# Storing all the 'data' information in 'envirionment.json'
with open(f'{PROGRAM_PATH}/monitoring/environment.json', 'w') as env_file:
    json.dump(data, env_file)
#

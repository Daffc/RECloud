import subprocess
import json
import os.path
import socket


#initiating json structure
data = {}

if(not os.path.isdir('./monitoring')):
  #creating monitoring folder
  subprocess.call(['mkdir', 'monitoring'])

#Recovering 'hostname' and outputing it in 'env_file'
hostname = socket.gethostname() 
data['hostname'] = hostname;


#Recovering IP from the host machine [TODO]
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
data['ip'] = s.getsockname()[0];
s.close()

#Recovering infotmation from all VM processes.
p1 = subprocess.Popen(("ps", "awx"), stdout = subprocess.PIPE)
p2 = subprocess.Popen(('grep', 'qemu'), stdin = p1.stdout, stdout=subprocess.PIPE)
saida_procs = subprocess.check_output(("grep", "-v", "grep"), stdin=p2.stdout)


#Recovering information about all the NIC's in the system
p1 = subprocess.Popen(['arp -n'], stdout = subprocess.PIPE, shell=True)
nics = p1.communicate()[0].decode('utf-8')


data['machines'] = []

#iterating over each VM process entry, recovering its informaion
for line in saida_procs.splitlines():
  
  # Spliting lines and recovering information separately.
  line_split = line.decode("utf-8").split()
  pid = line_split[0]  
  vm_name = line_split[7]
  uuid = line_split[20]

  #Recovering virtual network of the system into 'saida_vir_net'
  p1 = subprocess.Popen(['virsh domiflist ' + vm_name], stdout = subprocess.PIPE, shell=True)
  output = p1.communicate()[0].decode('utf-8')
  mac_address = output.splitlines()[2].split()[4] 
  
  #Iterating over Network Interfaces, retriving 'ip' by the 'mac_adress' of the current virtual machine.
  for entry in nics.split('\n'):
    if mac_address in entry:
      ip = entry.split()[0]
  
  data['machines'].append({
    'name': vm_name,
    'PID': pid,
    'UUID': uuid,
    'mac': mac_address,
    'ip': ip  
  })	  


with open('./monitoring/environment.json', 'w') as env_file:
    json.dump(data, env_file)


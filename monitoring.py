import os
import signal
import subprocess

# Checking if the monitorinf folder exists.
if(not os.path.isdir('./monitoring')):
  # Creating monitoring folder
  subprocess.call(['mkdir', 'monitoring'])

# Defining output-file from top execution
top_output = open("./monitoring/top_output.txt", "w+")

# Calling 'top' and 'iptraf-ng' processes.
top = subprocess.Popen(["top","-u", "libvirt-qemu", "-d", "1", "-b"], stdout = top_output)
network = subprocess.Popen(["iptraf-ng", "-i", "all", "-B", "-L", "./monitoring/network_output.txt"])


# Waiting for users input to finish the monitoring process
input("Digita ai:")


# killing the 'top' and 'iptraf-ng' processes.
#(NOTE) for some unknow reason, it 'iptraf-ng' calls two pocesses when called by python, so its in needed to kill 'network.pid' as wall as 'network.pid + 1'
subprocess.call(["kill",  "-USR2", str(top.pid), str(network.pid), str(network.pid + 1)])

#!/usr/bin/env python3.9

import json
import os
import sys
from datetime import datetime
from datetime import timedelta
import argparse


#=============================
#   Some General Definitions
#=============================
PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))
PAJE_HEADER_FILE = f'{PROGRAM_PATH}/header.trace'
CPU_MEM_TIME_MASK = "%a %b %d %H:%M:%S.%f %Y"
NETWORK_TIME_MASK = "%a %b %d %H:%M:%S %Y"
CPU_MEM_START = " ********* Start Monitoring **********\n"
CPU_MEM_END = " ********* Stopping Monitoring **********\n"
NETWORK_START = " ******** IP traffic monitor started ********\n"
NETWORK_END = " ******** IP traffic monitor stopped ********\n"
UNKNOWN_HOST = "Unknown"

EXPERIMENT_ID = datetime.now().strftime('%d-%m-%Y_%H:%M')

PAJE_CODES = {
  'PajeDefineContainerType': 0,
  'PajeDefineVariableType': 1,
  'PajeDefineLinkType': 4,
  'PajeCreateContainer': 6,
  'PajeDestroyContainer': 7,
  'PajeSetVariable': 8,
  'PajeStartLink': 14,
  'PajeEndLink': 15,
}

#=============================
#   Including Project Libs
#=============================
sys.path.append(f'{PROGRAM_PATH}/../libs')

import helper

#=============================
#   Local Functions
#=============================

# Inserting into "env" entries input and output data paths for each element.
def agregatePaths(envs, input_folder, output_folder):
  envs['output_root_trace'] = f'{output_folder}/traces/{EXPERIMENT_ID}/root.trace'
  for host in envs['hosts']:
    host['trace_folder'] = f'{output_folder}/traces/{EXPERIMENT_ID}/{host["hostname"]}'
    host['cpu_mem_source'] = f'{input_folder}/{host["hostname"]}/cpu_mem_output.txt'
    host['network_source'] = f'{input_folder}/{host["hostname"]}/network_output.txt'
    for vm in host['virtualMachines']:
      vm['trace_path'] = f'{host["trace_folder"]}/{vm["name"]}.trace'

# Recovering environment data from json to dictionary.
def recoverEnvironments(path):
  if(not os.path.isfile(path)):
    sys.exit(f'File {path} does not exist.')
  with open(path, 'r') as envs_file:
    envs = json.load(envs_file)
    
  return envs

# Checking if folder exists.
def checkFoldersExistence(path_in, path_out):
  if(not os.path.isdir(path_in)):
    sys.exit(f"Folder '{path_in}' does not exists.")
  if(not os.path.isdir(path_out)):
    sys.exit(f"Folder '{path_out}' does not exists.")

# Recovering vm's from 'envs' into a list.
def generateVmList(envs):
  vm_list = []

  for host in envs['hosts']:
    vm_list.extend(host["virtualMachines"])

  return vm_list

# Recovering vm from 'vm list' if there is a 'key' 'value' match.
def searchVM(vm_list, key, value):
  vm = []
  for vm_entry in vm_list:  
    if(vm_entry[key] == value):
      vm = vm_entry
      break
  return vm

# Formatting and outputting 'PajeSetVariable' trace line.
def outputPAJEVariable(time, vm_name, var_name, var_value, file):
  print(PAJE_CODES['PajeSetVariable'], time, vm_name, var_name, var_value, file=file)

# Formating and outputing 'PajeStartLink' trace line.
def outputPAJEStartLink(time, vm_name, package_size, link_key, file):
  print(PAJE_CODES["PajeStartLink"], time, "LINK", "root", vm_name, package_size, link_key, file=file)

# Formating and outputing 'PajeEndLink' trace line.
def outputPAJEEndLink(time, vm_name, package_size, link_key, file):
  print(PAJE_CODES["PajeEndLink"], time, "LINK", "root", vm_name, package_size, link_key, file=file)

# Formating and outputing 'PajeCreateContainer' trace line.
def outputPAJECreateContainer(time, container_name, container_type, container_parent, file):
  print(PAJE_CODES["PajeCreateContainer"], time, container_name, container_type, container_parent, container_name, file=file)
  

# Generating CPU/MEM trace consumption from 'f_input' into 'f_output'
def tracingCPUMEM(vm, f_input, f_output):
  
  # Checking file first line.
  line = f_input.readline()
  line_cols = line.split(';')

  if(line_cols[1] != CPU_MEM_START):
    sys.exit(f"Wrong file format:'{f_input.name}'.")

  previous_time = datetime.strptime(line_cols[0], CPU_MEM_TIME_MASK)
  total_time = timedelta()
  
  for line in f_input.readlines():
    line_cols = line.split(';')

    # Checking file last line.
    if(line_cols[1] == CPU_MEM_END):
      break

    curr_time = datetime.strptime(line_cols[0], CPU_MEM_TIME_MASK)
    total_time += (curr_time - previous_time)
    tt_seconds = total_time.total_seconds()
    previous_time = curr_time
    
    # Loop through each vm entry in "line"
    for vm_entry in line_cols[1:]:
      vm_cols = vm_entry.split()

      # If entry corresponds to the current vm, register values.
      if(vm_cols[0] == vm["name"]):
        outputPAJEVariable(tt_seconds, vm["name"], 'MEM', vm_cols[1], f_output)
        outputPAJEVariable(tt_seconds, vm["name"], 'CPU', vm_cols[3], f_output)

# Generating NETWORK trace consumption from 'f_input' into 'f_output'
def tracingNetwork(vm, f_input, vm_list, f_output):

  # Checking file first line.
  line = f_input.readline()
  line_cols = line.split(';')
  if(line_cols[1] != NETWORK_START):
    sys.exit(f"Wrong file format:'{f_input.name}'.")

  previous_time = datetime.strptime(line_cols[0], NETWORK_TIME_MASK)
  total_time = timedelta()

  links_dict = {}
  
  for line in f_input.readlines():
    line_cols = line.split(';')

    # Checking file last line.
    if(line_cols[1] == NETWORK_END):
      break

    curr_time, _, nic, size, ori_dest, *_ = line_cols
    curr_time = datetime.strptime(curr_time, NETWORK_TIME_MASK) 
    size = size.split()[0]

    # Check if the entry maches the vm vnic.
    if(vm["vnic"] == nic.strip()):
      total_time += (curr_time - previous_time)
      tt_seconds = total_time.total_seconds()
      previous_time = curr_time

      ori_dest = ori_dest.split()
      sender = ori_dest[1].split(':')[0]
      receiver = ori_dest[3].split(':')[0]

      # Check if vm is the sender of the message.
      if(sender == vm["ip"]):
        vm_counterpart = searchVM(vm_list, "ip", receiver)
        # Check if the counterpar is another vm from experiment.
        if(vm_counterpart):
          link = f'{vm["name"]}:{vm_counterpart["name"]}'
          order = links_dict.setdefault(link, 0)
          outputPAJEStartLink(tt_seconds,vm["name"], size, f'{link}|{order}', f_output)
          links_dict[link] += 1
        # If the conterpart is unknown.
        else:
          link = f'{vm["name"]}:{UNKNOWN_HOST}'
          order = links_dict.setdefault(link, 0)
          outputPAJEStartLink(tt_seconds,vm["name"], size, f'{link}|{order}', f_output)
          outputPAJEEndLink((tt_seconds + 0.1),UNKNOWN_HOST, size, f'{link}|{order}', f_output)
          links_dict[link] += 1

      # Check if vm is the receiver of the message.
      elif(receiver == vm["ip"]):
        vm_counterpart = searchVM(vm_list, "ip", sender) 
        # Check if the counterpar is another vm from experiment.    
        if(vm_counterpart):
          link = f'{vm_counterpart["name"]}:{vm["name"]}'
          order = links_dict.setdefault(link, 0)
          outputPAJEEndLink(tt_seconds,vm["name"], size, f'{link}|{order}', f_output)
          links_dict[link] += 1
        # If the conterpart is unknown.
        else:
          link = f'{UNKNOWN_HOST}:{vm["name"]}'
          order = links_dict.setdefault(link, 0)
          outputPAJEStartLink((tt_seconds - 0.1),UNKNOWN_HOST, size, f'{link}|{order}', f_output)
          outputPAJEEndLink(tt_seconds,vm["name"], size, f'{link}|{order}', f_output)
          links_dict[link] += 1
      
      # Report if the vm does not act as sender or receiver.
      else:
        print(f"\t\tUncommon Network Communication: '{line.rstrip()}' for '{vm['name']}'.")

# Calling trace generators for each vm into 'host'.
def generateTraceFiles(host, vm_list):
    
  c_m_in = open(host['cpu_mem_source'], 'r')
  network_in = open(host['network_source'], 'r')
  
  # PARALELIZATION POINT.
  for vm in host['virtualMachines']:
    print(f'\tGenerating Traces for {vm["name"]}...')
    with open(vm['trace_path'], 'w') as f_output:
      c_m_in.seek(0)
      network_in.seek(0)

      print("# CPU / MEM TRACES", file=f_output)
      tracingCPUMEM(vm, c_m_in, f_output)
      print("\n# NETWORK TRACES", file=f_output)
      tracingNetwork(vm, network_in, vm_list, f_output)
    print('\tDone!')
  
  network_in.close()
  c_m_in.close()

def agrupateTraces(envs):
  with open(envs['output_root_trace'], 'w') as r_trace:
    with open(PAJE_HEADER_FILE, 'r') as h_trace:
      for line in h_trace:
        r_trace.write(line)

    print('\n# ----------------------------------------\n# -- Initializing Container & Variables --\n# ----------------------------------------\n', file=r_trace)
                                                          
    outputPAJECreateContainer(0.0, "root", 'ROOT', '0', r_trace)
    for host in envs['hosts']:
      outputPAJECreateContainer(0.0, host['hostname'], 'NODE', 'root', r_trace)
      for vm in host['virtualMachines']:
        outputPAJECreateContainer(0.0, vm['name'], 'VM', host['hostname'], r_trace)
        outputPAJEVariable(0.0, vm["name"], 'MEM', 0, r_trace)
        outputPAJEVariable(0.0, vm["name"], 'CPU', 0, r_trace)
                                                                          
# Parsing program initialization arguments. 
def parsingArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_folder", help="Path to source folder.")
    parser.add_argument("output_folder", help="Path to output folder.")
    parser.add_argument("-g", action='store_const', const=True, help="Indicates to agrupate the generated traces into a single trace 'root.trace' that will be stored in 'output_folder'.")
    args = parser.parse_args()

    return os.path.normpath(args.input_folder), os.path.normpath(args.output_folder), args.g

#=============================
#       Main code
#=============================

if __name__ == '__main__':

  input_folder, output_folder, root_trace = parsingArguments()
  checkFoldersExistence(input_folder, output_folder)

  # Generating output folders.
  helper.createFolder(f'{output_folder}/traces')
  helper.createFolder(f'{output_folder}/traces/{EXPERIMENT_ID}')

  # Recovering environments.
  envs = recoverEnvironments(f'{input_folder}/environments.json') 

  # Registering input an ouput file paths.
  agregatePaths(envs, input_folder, output_folder)
  
  # Recoverting list of vms.
  vm_list = generateVmList(envs)

  # PARALELIZATION POINT.
  for host in envs['hosts']:
    helper.createFolder(host['trace_folder'])
    print(f'Generating Traces for {host["hostname"]}...')
    generateTraceFiles(host, vm_list)
    print(f'Done!')

  if(root_trace): 
    agrupateTraces(envs)
#!/usr/bin/env python3.9

import re
import json
import os
import sys
from typing import Any
from io import IOBase
from scapy.all import PcapReader, IP
from datetime import datetime
from datetime import timedelta
import argparse

#=============================
#   Some General Definitions
#=============================
PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))
PAJE_HEADER_FILE = f'{PROGRAM_PATH}/header.trace'
CPU_MEM_TIME_MASK = "%a %Y-%m-%d %H:%M:%S.%f"                     
CPU_MEM_START = " ********* Start Monitoring **********\n"
CPU_MEM_END = " ********* Stopping Monitoring **********\n"
NETWORK_START = " ******** IP traffic monitor started ********\n"
NETWORK_END = " ******** IP traffic monitor stopped ********\n"
UNKNOWN_HOST = "Unknown"

EXPERIMENT_ID = datetime.now().strftime('%d-%m-%Y_%H:%M')

PAJE_CODES = {
  'PajeDefineContainerType': '0',
  'PajeDefineVariableType': '1',
  'PajeDefineLinkType': '4',
  'PajeCreateContainer': '6',
  'PajeDestroyContainer': '7',
  'PajeSetVariable': '8',
  'PajeStartLink': '14',
  'PajeEndLink': '15',
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
def agregatePaths(envs: dict, input_folder: str, output_folder: str):
  envs['output_root_trace'] = f'{output_folder}/traces/{EXPERIMENT_ID}/root.trace'
  envs['unknown_trace'] = f'{output_folder}/traces/{EXPERIMENT_ID}/unknown_host.trace'
  for host in envs['hosts']:
    host['trace_folder'] = f'{output_folder}/traces/{EXPERIMENT_ID}/{host["hostname"]}'
    host['cpu_mem_source'] = f'{input_folder}/{host["hostname"]}/cpu_mem_output.txt'
    host['pcap_source'] = f'{input_folder}/{host["hostname"]}/network_output.pcap'
    for vm in host['virtual_machines']:
      vm['trace_path'] = f'{host["trace_folder"]}/{vm["name"]}.trace'

# Recovering environment data from json to dictionary.
def recoverEnvironments(path: str):
  if(not os.path.isfile(path)):
    sys.exit(f'File {path} does not exist.')
  with open(path, 'r') as envs_file:
    envs = json.load(envs_file)
    
  return envs

# Checking if folder exists.
def checkFoldersExistence(f_paths: list):
  for path in f_paths:
    if(not os.path.isdir(path)):
      sys.exit(f"Folder '{path}' does not exists.")

# Recovering vm's from 'envs' into a list.
def generateVmList(envs: dict):
  vm_list = []

  for host in envs['hosts']:
    vm_list.extend(host["virtual_machines"])

  return vm_list

# Recovering vm from 'vm list' if there is a 'key' 'value' match.
def searchVM(vm_list: list, key: str, value: Any):
  vm = []
  for vm_entry in vm_list:  
    if(vm_entry[key] == value):
      vm = vm_entry
      break
  return vm

# Formatting and outputting 'PajeSetVariable' trace line.
def outputPAJEVariable(time: float, vm_name: str, var_name: str, var_value: Any, file: IOBase):
  print(PAJE_CODES['PajeSetVariable'], time, vm_name, var_name, var_value, file=file)

# Formating and outputing 'PajeStartLink' trace line.
def outputPAJEStartLink(time: float, vm_name: str, package_size: int, link_key: str, file: IOBase):
  print(PAJE_CODES["PajeStartLink"], time, "LINK", "root", vm_name, package_size, link_key, file=file)

# Formating and outputing 'PajeEndLink' trace line.
def outputPAJEEndLink(time: float, vm_name: str, package_size: int, link_key: str, file: IOBase):
  print(PAJE_CODES["PajeEndLink"], time, "LINK", "root", vm_name, package_size, link_key, file=file)

# Formating and outputing 'PajeCreateContainer' trace line.
def outputPAJECreateContainer(time: float, container_name: str, container_type: str, container_parent: str, file: IOBase):
  print(PAJE_CODES["PajeCreateContainer"], time, container_name, container_type, container_parent, container_name, file=file)
  

# Generating CPU, MEM and Network trace consumption from 'fcm_input' and 'fpcap_input' into 'f_output'.
# For each CPU/MEM trace timestamp interval, trace packets that has been sent by 'vm' in this interval.  
def tracing(vm: dict, fcm_input: IOBase, fpcap_input: IOBase, vm_list: list, f_output: IOBase, unk_output: IOBase):
  
  # Checking 'fcm_input' file first line.
  line = fcm_input.readline()
  line_cols = line.split(';')

  if(line_cols[1] != CPU_MEM_START):
    sys.exit(f"Wrong file format:'{fcm_input.name}'.")

  previous_time = datetime.strptime(line_cols[0][0:30], CPU_MEM_TIME_MASK)
  total_time = timedelta()
  prev_tt_seconds = 0.0
  
  for line in fcm_input.readlines():
    line_cols = line.split(';')

    # Checking if it's 'fcm_input' last line.
    if(line_cols[1] == CPU_MEM_END):
      break
    
    curr_time = datetime.strptime(line_cols[0][0:30], CPU_MEM_TIME_MASK)
    total_time += (curr_time - previous_time)
    tt_seconds = total_time.total_seconds()
    previous_time = curr_time
    
    # Loop through each vm entry in "line"
    for vm_entry in line_cols[1:]:
      vm_cols = vm_entry.split()

      # If entry corresponds to the current vm, register values.
      if(vm_cols[0] == vm["name"]):
        # Add CPU trace for 'tt_seconds' timestamp.
        outputPAJEVariable(tt_seconds, vm["name"], 'CPU', vm_cols[3], f_output)
        
        # Adding Network traces  that occurs in between 'prev_tt_seconds' and 'tt_seconds' interval.
        tracingPcap(vm, fpcap_input, vm_list, f_output, unk_output, prev_tt_seconds, tt_seconds)

        # Add MEM trace for 'tt_seconds' timestamp.
        outputPAJEVariable(tt_seconds, vm["name"], 'MEM', vm_cols[1], f_output)

    # Update 'prev_tt_seconds'
    prev_tt_seconds = tt_seconds

# Generating NETWORK trace traffict from 'fpcap_input' into 'f_output' if paket timestamp is between 'begin_interval' and 'end_interval'.
# If vm commuticates with unknow host, output is redirected to 'unk_dsc'.
def tracingPcap(vm: list, fpcap_input: IOBase, vm_list: list, f_output: IOBase, unk_output: IOBase, begin_interval, end_interval):

  pkt = PcapReader(fpcap_input).next()

  previous_time = datetime.fromtimestamp(float(pkt.time))
  total_time = timedelta()

  links_dict = {}
  
  # Looping through each packet (pkt) in pcap file.
  for pkt in PcapReader(fpcap_input):

    # Check if the current packet (pkt) has an IP protocol header.
    if(IP in pkt):

      # Recovering data from packt  
      curr_time = datetime.fromtimestamp(float(pkt.time))
      total_time += (curr_time - previous_time)
      tt_seconds = total_time.total_seconds()
      previous_time = curr_time

      sender = pkt[IP].src
      receiver = pkt[IP].dst

      size = pkt.wirelen 
      
      # If pkt timestamp is grater than 'end_interval', exit from function.
      if(tt_seconds > end_interval):
        return
      
      # If pkt timestamp is between 'begin_interval' and 'end_interval', write in file.  
      if(tt_seconds > begin_interval):
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
            outputPAJEStartLink(tt_seconds,vm["name"], size, f'{link}|{order}', unk_output)
            links_dict[link] += 1

        # Check if vm is the receiver of the message.
        if(receiver == vm["ip"]):
          vm_counterpart = searchVM(vm_list, "ip", sender) 
          # Check if the counterpar isnt't another vm from experiment (UNKNOWN_HOST).    
          if(not vm_counterpart):
            link = f'{UNKNOWN_HOST}:{vm["name"]}'
            order = links_dict.setdefault(link, 0)
            outputPAJEStartLink((tt_seconds), UNKNOWN_HOST, size, f'{link}|{order}', unk_output)
            links_dict[link] += 1

# Calling trace generators for each vm into 'host'.
def generateTraceFiles(host: dict, vm_list: list, unk_output):
    
  c_m_in = open(host['cpu_mem_source'], 'r')
  
  # PARALELIZATION POINT.
  for vm in host['virtual_machines']:
    print(f'\tGenerating Traces for {vm["name"]}...')
    with open(vm['trace_path'], 'w') as f_output:
      c_m_in.seek(0)

      tracing(vm, c_m_in, host['pcap_source'], vm_list, f_output, unk_output)

    print('\tDone!')
  
  c_m_in.close()

# Agrupates the traces into 'root.trace' file (readable by ViTE).
def agrupateTraces(envs: dict):
  print(f'Agrupating traces into "root.trace" file (readable by ViTE)...')

  with open(envs['output_root_trace'], 'w') as r_trace:
    with open(PAJE_HEADER_FILE, 'r') as h_trace:
      for line in h_trace:
        r_trace.write(line)

    r_trace.write('\n# ----------------------------------------\n# -- Initializing Container & Variables --\n# ----------------------------------------\n')                                                    
    outputPAJECreateContainer(0.0, "root", 'ROOT', '0', r_trace)
    outputPAJECreateContainer(0.0, UNKNOWN_HOST, 'NODE', 'root', r_trace)
    for host in envs['hosts']:
      outputPAJECreateContainer(0.0, host['hostname'], 'NODE', 'root', r_trace)
      for vm in host['virtual_machines']:
        outputPAJECreateContainer(0.0, vm['name'], 'VM', host['hostname'], r_trace)
        outputPAJEVariable(0.0, vm["name"], 'MEM', 0, r_trace)
        outputPAJEVariable(0.0, vm["name"], 'CPU', 0, r_trace)
                                                                          
    r_trace.write('\n# -----------------------------------------\n# --- Aggregating Virtual Machines Data ---\n# -----------------------------------------\n')
    for host in envs['hosts']:
      for vm in host['virtual_machines']:
        r_trace.write(f'# --- {vm["name"]} ---\n')
        with open(vm['trace_path'], 'r') as vm_trace:
          for line in vm_trace:
            
            r_trace.write(line)
            
            line_cols = re.split(' |:|\|', line)
            # If 'line' represents a packet send (PajeStartLink), write the complement (PajeEndLink) in 'root.trace' for proper visualization with ViTE. 
            if(line_cols[0] == PAJE_CODES['PajeStartLink']):
              outputPAJEEndLink(float(line_cols[1]), line_cols[7], int(line_cols[5]), f'{line_cols[6]}:{line_cols[7]}|{line_cols[8][:-1]}', r_trace)
              
        r_trace.write('\n\n')
    
    r_trace.write('\n# -----------------------------------------------\n# --- Aggregating Unknown Host Communications ---\n# -----------------------------------------------\n')
    with open(envs['unknown_trace'], 'r') as unknown_trace:
      for line in unknown_trace:
        r_trace.write(line)
        
        line_cols = re.split(' |:|\|', line)
        # If 'line' represents a packet send (PajeStartLink), write the complement (PajeEndLink) in 'root.trace' for proper visualization with ViTE. 
        if(line_cols[0] == PAJE_CODES['PajeStartLink']):
          outputPAJEEndLink(float(line_cols[1]), line_cols[7], int(line_cols[5]), f'{line_cols[6]}:{line_cols[7]}|{line_cols[8][:-1]}', r_trace)
          print(line)
          print(line_cols)

    print('Done!')
          
         
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
  checkFoldersExistence([input_folder, output_folder])

  # Generating output folders.
  helper.createFolder(f'{output_folder}/traces')
  helper.createFolder(f'{output_folder}/traces/{EXPERIMENT_ID}')

  # Recovering environments.
  envs = recoverEnvironments(f'{input_folder}/environments.json') 

  # Registering input an ouput file paths.
  agregatePaths(envs, input_folder, output_folder)

  # Recoverting list of vms.
  vm_list = generateVmList(envs)


  # Defining file output for unknown host communications.
  with open(envs['unknown_trace'], 'w') as unknown_host_dsc:

    # PARALELIZATION POINT.
    for host in envs['hosts']:
      helper.createFolder(host['trace_folder'])
      print(f'Generating Traces for {host["hostname"]}...')
      generateTraceFiles(host, vm_list, unknown_host_dsc)
      print(f'Done!')

  # If vizualition trace was selected ('-g' argument.)
  if(root_trace): 
    agrupateTraces(envs)
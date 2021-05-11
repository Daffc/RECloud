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
CPU_MEM_TIME_MASK = "%a %b %d %H:%M:%S.%f %Y"
NETWORK_TIME_MASK = "%a %b %d %H:%M:%S %Y"
CPU_MEM_START = " ********* Start Monitoring **********\n"
CPU_MEM_END = " ********* Stopping Monitoring **********\n"
NETWORK_START = " ******** IP traffic monitor started ********\n"
NETWORK_END = " ******** IP traffic monitor stopped ********\n"

EXPERIMENT_ID = datetime.now().strftime('%d-%m-%Y_%H:%M')

PAJE_CODES = {
  'PajeSetVariable' : 8,
  'PajeStartLink' : 14,
  'PajeEndLink': 15
}

#=============================
#   Including Project Libs
#=============================
sys.path.append(f'{PROGRAM_PATH}/../libs')

import helper

#=============================
#   Local Functions
#=============================

def agregatePaths(envs, input_folder, output_folder):
  for host in envs['hosts']:
    host['trace_folder'] = f'{output_folder}/traces/{EXPERIMENT_ID}/{host["hostname"]}'
    host['cpu_mem_source'] = f'{input_folder}/{host["hostname"]}/cpu_mem_output.txt'
    host['network_source'] = f'{input_folder}/{host["hostname"]}/network_output.txt'
    for vm in host['virtualMachines']:
      vm['trace_path'] = f'{host["trace_folder"]}/{vm["name"]}.trace'

def recoverEnvironments(path):
  if(not os.path.isfile(path)):
    sys.exit(f'File {path} does not exist.')

  with open(path, 'r') as envs_file:
    envs = json.load(envs_file)
    
  return envs

def outputPAJEVariable(time, vm_name, var_name, var_value, file):
  print(PAJE_CODES['PajeSetVariable'], time, vm_name, var_name, var_value, file=file)

def outputPAJEStartLink(time, vm_name, package_size, link_key, file):
  print(PAJE_CODES["PajeStartLink"], time, "LINK", "root", vm_name, package_size, link_key, file=file)
  
def outputPAJEEndLink(time, vm_name, package_size, link_key, file):
  print(PAJE_CODES["PajeEndLink"], time, "LINK", "root", vm_name, package_size, link_key, file=file)

def tracingCPUMEM(vm, f_input, output_path):
  
  line = f_input.readline()
  line_cols = line.split(';')

  if((not line) or (line_cols[1] != CPU_MEM_START)):
    sys.exit(f"Wrong file format:'{f_input.name}'.")

  previous_time = datetime.strptime(line_cols[0], CPU_MEM_TIME_MASK)
  total_time = timedelta()
  
  output_file = open(vm['trace_path'], 'w')
  line = f_input.readline()
  
  while(line):
    line_cols = line.split(';')

    if(line_cols[1] == CPU_MEM_END):
      break

    curr_time = datetime.strptime(line_cols[0], CPU_MEM_TIME_MASK)
    total_time += (curr_time - previous_time)
    previous_time = curr_time

    for vm_entry in line_cols[1:]:
      vm_cols = vm_entry.split()

      if(vm_cols[0] == vm["name"]):
        outputPAJEVariable(total_time.total_seconds(), vm["name"], 'MEM', vm_cols[2], output_file)
        outputPAJEVariable(total_time.total_seconds(), vm["name"], 'CPU', vm_cols[6], output_file)

    line = f_input.readline()
  
  output_file.close()

def searchVM(vm_list, key, value):
  vm = []
  for vm_entry in vm_list:  
    if(vm_entry[key] == value):
      vm = vm_entry
      break
  return vm

def tracingNetwork(vm, f_input, output_path, vm_list):

  line = f_input.readline()
  line_cols = line.split(';')
  if((not line) or (line_cols[1] != NETWORK_START)):
    sys.exit(f"Wrong file format:'{f_input.name}'.")

  previous_time = datetime.strptime(line_cols[0], NETWORK_TIME_MASK)
  total_time = timedelta()

  links_dict = {}
  output_file = open(vm['trace_path'], 'w')
  
  for line in f_input.readlines():
    line_cols = line.split(';')

    if(line_cols[1] == NETWORK_END):
      break

    curr_time, _, nic, size, ori_dest, *_ = line_cols
    
    curr_time = datetime.strptime(curr_time, NETWORK_TIME_MASK) 
    size = size.split()[0]

    if(vm["vnic"] == nic.strip()):
      total_time += (curr_time - previous_time)
      previous_time = curr_time

      ori_dest = ori_dest.split()
      sender = ori_dest[1].split(':')[0]
      receiver = ori_dest[3].split(':')[0]

      link = ''
      if(sender == vm["ip"]):
        vm_counterpar = searchVM(vm_list, "ip", receiver)
        if(vm_counterpar):
          link = f'{vm["name"]}:{vm_counterpar["name"]}'
        else:
          link = f'{vm["name"]}:Unknown'
        order = links_dict.setdefault(link, 0)
        outputPAJEStartLink(total_time.total_seconds(),vm["name"], size, f'{link}|{order}', output_file)
        links_dict[link] += 1

      elif(receiver == vm["ip"]):
        vm_counterpar = searchVM(vm_list, "ip", sender)     
        if(vm_counterpar):
          link = f'{vm_counterpar["name"]}:{vm["name"]}'
        else:
          link = f'Unknown:{vm["name"]}'
        order = links_dict.setdefault(link, 0)
        outputPAJEEndLink(total_time.total_seconds(),vm["name"], size, f'{link}|{order}', output_file)
        links_dict[link] += 1

      else:
        sys.exit(f"Uncomum Network Comunication: '{line}' for '{vm['name']}'.")

def generateTraceFiles(host, vm_list):
    
  c_m_in = open(host['cpu_mem_source'], 'r')
  network_in = open(host['network_source'], 'r')
  
  # PARALELIZATION POINT.
  for vm in host['virtualMachines']:
    tracingNetwork(vm, network_in, vm['trace_path'], vm_list)
    # tracingCPUMEM(vm, c_m_in, vm['trace_path'])
  
  network_in.close()
  c_m_in.close()

def parsingArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_folder", help="Path to source folder.")
    parser.add_argument("output_folder", help="Path to output folder.")
    args = parser.parse_args()

    return os.path.normpath(args.input_folder), os.path.normpath(args.output_folder)

def checkFoldersExistence(path_in, path_out):
  if(not os.path.isdir(path_in)):
    sys.exit(f"Folder '{path_in}' does not exists.")
  if(not os.path.isdir(path_out)):
    sys.exit(f"Folder '{path_out}' does not exists.")

def generateVmList(envs):
  vm_list = []

  for host in envs['hosts']:
    vm_list.extend(host["virtualMachines"])

  return vm_list
#=============================
#       Main code
#=============================

if __name__ == '__main__':
    
  input_folder, output_folder = parsingArguments()
  checkFoldersExistence(input_folder, output_folder)

  print(input_folder, output_folder)

  helper.createFolder(f'{output_folder}/traces')
  helper.createFolder(f'{output_folder}/traces/{EXPERIMENT_ID}')

  envs = recoverEnvironments(f'{input_folder}/environments.json') 

  agregatePaths(envs, input_folder, output_folder)
  
  vm_list = generateVmList(envs)

  # PARALELIZATION POINT.
  for host in envs['hosts']:
    helper.createFolder(host['trace_folder'])
    generateTraceFiles(host, vm_list)
  
#!/usr/bin/env python3.9

import json
import os
import sys
import datetime 
import argparse


#=============================
#   Some General Definitions
#=============================
PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))
TIME_MASK = "%a %b %d %H:%M:%S.%f %Y"
CPU_MEM_START = " ********* Start Monitoring **********"
CPU_MEM_END = " ********* Stopping Monitoring **********"

EXPERIMENT_ID = datetime.datetime.now().strftime('%d-%m-%Y_%H:%M')

PAJE_CODES = {
  'PajeSetVariable' : 8,
  'PajeNewEvent' : 16,
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
    for vm in host['machines']:
      vm['trace_path'] = f'{host["trace_folder"]}/{vm["name"]}.trace'

def recoverEnvironments(path):
  if(not os.path.isfile(path)):
    sys.exit(f'File {path} does not exist.')

  with open(path, 'r') as envs_file:
    envs = json.load(envs_file)
    
  return envs

def outputPAJEVariable(time, vm_name, vat_name, var_value, file):
  print(PAJE_CODES['PajeSetVariable'], time, vm_name, vat_name, var_value, file=file)

def tracingCPUMEM(vm, f_input, output_path):

  line = f_input.readline()
  line = line.rstrip()

  while (not line):
    line = f_input.readline()
    line = line.rstrip()

  line_cols = line.split(';')

  if ((not line) or (line_cols[1] != CPU_MEM_START)):
    sys.exit(f"Wrong file format:'{f_input.name}'.")

  previous_time = datetime.datetime.strptime(line_cols[0], TIME_MASK)
  total_time = datetime.timedelta()
  
  output_file = open(vm['trace_path'], 'w')
  line = f_input.readline()
  
  while (line):
    line_cols = line.split(';')
    if(line_cols[1] == CPU_MEM_END):
      break
    else:
      curr_time = datetime.datetime.strptime(line_cols[0], TIME_MASK)
      total_time += (curr_time - previous_time)
      previous_time = curr_time

      for vm_entry in line_cols[1:]:
        vm_cols = vm_entry.split()

        if(vm_cols[0] == vm["name"]):
          outputPAJEVariable(total_time.total_seconds(), vm["name"], 'MEM', vm_cols[2], output_file)
          outputPAJEVariable(total_time.total_seconds(), vm["name"], 'CPU', vm_cols[6], output_file)

    line = f_input.readline()
  
  output_file.close()

def tracingNetwork(vm, f_input, output_path):
  print()


def generateTraceFiles(host):
    
  c_m_in = open(host['cpu_mem_source'], 'r')
  network_in = open(host['network_source'], 'r')
  
  # PARALELIZATION POINT.
  for vm in host['machines']:
    # tracingNetwork(vm, network_in, vm['trace_path'])
    tracingCPUMEM(vm, c_m_in, vm['trace_path'])
  
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

  # PARALELIZATION POINT.
  for host in envs['hosts']:
    helper.createFolder(host['trace_folder'])
    generateTraceFiles(host)
  
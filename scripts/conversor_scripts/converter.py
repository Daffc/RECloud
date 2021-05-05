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

def transformListToDatetime(list):
  str_datetime = ' '.join(list)
  return datetime.datetime.strptime(str_datetime, TIME_MASK)

def outputPAJEVariable(time, vm_name, vat_name, var_value, file):
  print(PAJE_CODES['PajeSetVariable'], time, vm_name, vat_name, var_value, file=file)

def traceCPU_MEM(vm, f_input, output_path):

  line = f_input.readline()
  line = line.rstrip()

  while (not line):
    line = f_input.readline()
    line = line.rstrip()
  
  if (not line):
    sys.exit(f"File '{output_path}' is empt.")

  previous_time = transformListToDatetime(line.split()[4:9])
  total_time = datetime.timedelta()
  
  output_file = open(vm['trace_path'], 'w')
  line = f_input.readline()
  
  while (line):
    split_line = line.split()
    if(line[0] == '*'):
      break
    elif(line[0] != '\t'):
      curr_time = transformListToDatetime(split_line[0:5])
      total_time += (curr_time - previous_time)
      previous_time = curr_time
    elif(split_line[0] == vm["name"]):
      vm_cpu = split_line[6]
      vm_mem = split_line[2]

      outputPAJEVariable(total_time.total_seconds(), vm["name"], 'CPU', vm_cpu, output_file)
      outputPAJEVariable(total_time.total_seconds(), vm["name"], 'MEM', vm_mem, output_file)

    line = f_input.readline()
  
  output_file.close()

        
      
def traceFiles(host):
    
  c_m_in = open(host['cpu_mem_source'], 'r')
  
  # PARALELIZATION POINT.
  for vm in host['machines']:
    traceCPU_MEM(vm, c_m_in, vm['trace_path'])
  
  c_m_in.close()

def parsingArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_folder", help="Path to source folder.")
    parser.add_argument("output_folder", help="Path to output folder.")
    args = parser.parse_args()

    return args.input_folder, args.output_folder

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

  helper.createFolder(f'{output_folder}traces')
  helper.createFolder(f'{output_folder}traces/{EXPERIMENT_ID}')

  envs = recoverEnvironments(f'{input_folder}/environments.json') 

  agregatePaths(envs, input_folder, output_folder)

  # PARALELIZATION POINT.
  for host in envs['hosts']:
    helper.createFolder(host['trace_folder'])
    traceFiles(host)
  
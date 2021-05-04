#!/usr/bin/env python3.9

import json
import os
import sys
import time
import datetime 


#=============================
#   Some General Definitions
#=============================
PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))
SOURCE_PATH =  f'{PROGRAM_PATH}/../data/outputs'
TRACES_PATH = f'{PROGRAM_PATH}/../data/traces'
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

def agregatePaths(envs):
  for host in envs['hosts']:
    host['trace_folder'] = f'{TRACES_PATH}/{EXPERIMENT_ID}/{host["hostname"]}'
    host['cpu_mem_source'] = f'{SOURCE_PATH}/{host["hostname"]}/cpu_mem_output.txt'
    host['network_source'] = f'{SOURCE_PATH}/{host["hostname"]}/network_output.txt'
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

def traceCPU_MEM(vm, f_input, output_path):

  line = f_input.readline()
  line = line.rstrip()

  while (not line):
    line = f_input.readline()
    line = line.rstrip()
  
  if line:
    previous_time = transformListToDatetime(line.split()[4:9])
    total_time = datetime.timedelta()
    
    line = f_input.readline()
    while (line):
      if(line[0] == '*'):
        break
      if(line[0] != '\t'):
        curr_time = transformListToDatetime(line.split()[0:5])
        total_time += (curr_time - previous_time)
        # LOOP THROUGH TIME INTERVAL LOOKING FOR VM CPU CONSUMPTION.
        print(total_time.total_seconds())
        previous_time = curr_time

      line = f_input.readline()
      


  else:
    sys.exit(f"File '{output_path}' is empt.")


  # while line:

  # f_imput.readline()

  # for line in f_input:
  # 	line = line.rstrip()
  # 	if line:
  # 		print(f'-{line}-')
  # 		for word in line.split('\t'):
  # 			print(word)
      # print(line.split()[1])
        
      
def traceFiles(host):
    
  c_m_in = open(host['cpu_mem_source'], 'r')
  
  for vm in host['machines']:
    traceCPU_MEM(vm, c_m_in, vm['trace_path'])
  
  c_m_in.close()

#=============================
#       Main code
#=============================

if __name__ == '__main__':
  helper.createFolder(TRACES_PATH)
  helper.createFolder(f'{TRACES_PATH}/{EXPERIMENT_ID}')
    
  envs = recoverEnvironments(f'{SOURCE_PATH}/environments.json') 

  agregatePaths(envs)

  for host in envs['hosts']:
    helper.createFolder(host['trace_folder'])
    traceFiles(host)  
  
  # print(json.dumps(envs, indent=2))
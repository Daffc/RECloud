#!/usr/bin/env python3.9
import sys
import os
import socket
import time
import signal
import subprocess
import setproctitle
import argparse
from datetime import datetime


#=============================
#   Some General Definitions
#=============================
setproctitle.setthreadtitle(os.path.basename(__file__))

PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))
INTERVAL_SEC = 0.5
TIME_MASK = "%a %b %d %H:%M:%S.%f %Y"

#=============================
#   Including Project Libs
#=============================
# for the purpose of run this script, after that this SHOULD BE MODIFIED.
sys.path.append(f'{PROGRAM_PATH}/../libs')

from sig_helper import GracefulKiller
import libvirt_helper as lh

#=============================
#   Local Functions
#=============================
def startAllBalloonPeriods(doms):
  for dom in doms:
    try:
      subprocess.check_call(['virsh', 'dommemstat', '--domain', dom.name(), '--period', '1']) 
    except subprocess.CalledProcessError as e:
      sys.exit(f'Error while definning Balloon Period for {dom.name()}: {e}')

def stopAllBalloonPeriods(doms):
  for dom in doms:
    try:
      subprocess.check_call(['virsh', 'dommemstat', '--domain', dom.name(), '--period', '0'])
    except subprocess.CalledProcessError as e:
      sys.exit(f'Error while definning Balloon Period for {dom.name()}:{e}')

def getMemConsumption(dom):
  stats  = dom.memoryStats()
  totalMem = stats.get("actual", 1)
  curMem = max(0, totalMem - stats.get("unused", totalMem))

  curMemPercent = (curMem / float(totalMem)) * 100
  curMemPercent = max(0.0, min(curMemPercent, 100.0))
   
  return curMem, curMemPercent

def getCPUConsumption(dom):
  timestamp = time.time()

  _, _, _, _, cput = dom.info()

  percCPU = ((cput - dom.prevCput) / ((timestamp - dom.pTimeStamp) * 10_000_000))

  dom.prevCput = cput
  dom.pTimeStamp = timestamp
  
  return percCPU

# Returns output for program.
def defineOutputFile(path):
  if path != '':
    os.path.normpath(path)
    try:
      file = open(str(path), 'w')
    except Exception as e:
      sys.exit(f"Couldn't open file '{path}': {e}.")
    return file
  else:
    return sys.stdout

# Parsing program initialization arguments. 
def parsingArguments():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description="Program to collect CPU and Memory data from Virtual Machines.\nDisplayed data will follow the schema for each time interval:\n\tTIME; [VM0]; [VM1]; [VM2] ...\nEach [VMN] entry will have the following Information:\n\tVM-NAME VM-MEM-ABS VM-MEM-PERC VM-CPU-PERC.")
    parser.add_argument("-o", default='', required=False, help="Path to output file. If not informed, data will be displayed in stdout.")
    args = parser.parse_args()

    return args.o

#=============================
#       Main code
#=============================

if __name__ == '__main__':
  
  output_file_path = parsingArguments()

  f_output = defineOutputFile(output_file_path)  
  domName = socket.gethostname()

  conn = lh.libvirtConnect()
  doms = lh.recoverActiveDomains(conn) 
  
  for dom in doms:
    dom.pTimeStamp = time.time()
    dom.prevCput = 0

  startAllBalloonPeriods(doms)
  killer = GracefulKiller()

  # Setting initial Values for CPU registers. 
  for dom in doms:
    getCPUConsumption(dom)
  time.sleep(INTERVAL_SEC)

  print(f'********* Start Monitoring at {datetime.now().strftime(TIME_MASK)} **********', file=f_output)
  while not killer.kill_now:
  
    list_vm_data = []
    for dom in doms:
      curMem, curMemPerc = getMemConsumption(dom)
      percCPU = getCPUConsumption(dom)
      list_vm_data.append(f' {dom.name()} {curMem} {curMemPerc:.2f} {round(percCPU, 2)}')
    
    print(datetime.now().strftime(TIME_MASK), *list_vm_data, sep=';', file=f_output ) 
    time.sleep(INTERVAL_SEC)
    
  print(f'********* Stopping Monitoring at {datetime.now().strftime(TIME_MASK)} **********\n', file=f_output)

  stopAllBalloonPeriods(doms)
  conn.close()
  f_output.close()
  exit(0)


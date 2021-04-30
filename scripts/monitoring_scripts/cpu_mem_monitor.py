#!/usr/bin/env python3.9
import sys
import os
import socket
import time
import signal
import subprocess
import setproctitle
from datetime import datetime


#=============================
#   Some General Definitions
#=============================
setproctitle.setthreadtitle(os.path.basename(__file__))

PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))
INTERVAL_SEC = 0.5
TIME_MASK = "%d/%m/%Y %H:%M:%S.%f"

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
    except subprocess.CalledProcessError:
      print(f'Error while definning Balloon Period for {dom.name()}. Closing process.')
      exit(1)

def stopAllBalloonPeriods(doms):
  for dom in doms:
    try:
      subprocess.check_call(['virsh', 'dommemstat', '--domain', dom.name(), '--period', '0'])
    except subprocess.CalledProcessError:
      print(f'Error while definning Balloon Period for {dom.name()}. Closing process.')
      exit(1)

def getMemConsumption(dom):
  stats  = dom.memoryStats()
  totalMem = stats.get("actual", 1)
  curMem = max(0, totalMem - stats.get("unused", totalMem))

  curMemPercent = (curMem / float(totalMem)) * 100
  curMemPercent = max(0.0, min(curMemPercent, 100.0))
   
  return curMem, curMemPercent

def getCPUConsumption(dom):
  timestamp = time.time()

  state, maxmem, mem, cpus, cput = dom.info()

  percCPU = ((cput - dom.prevCput) / ((timestamp - dom.pTimeStamp) * 10_000_000))

  dom.prevCput = cput
  dom.pTimeStamp = timestamp
  
  return percCPU

# Redefine default output according to args[0] paramather.
def setOutput(args):
  if len(args):
    try:
      file = open(str(args[0]), 'a')
      try:
        sys.stdout = file
      except Exception as e:
        print(f"Coundn't redirect output: {e}.")
        exit(1)
    except Exception as e:
      print(f"Couldn't open file '{args[0]}': {e}.")
      exit(1)

#=============================
#       Main code
#=============================

if __name__ == '__main__':
  
  setOutput(sys.argv[1:])  
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

  print(f'********* Start Monitoring at {datetime.now().strftime(TIME_MASK)} **********', flush=True)
  while not killer.kill_now:
  
    print(datetime.now().strftime(TIME_MASK)) 
    for dom in doms:
      curMem, curMemPercent = getMemConsumption(dom)
      percCPU = getCPUConsumption(dom)
      print(f'\t{dom.name()}\tcurMem: {curMem}\tcurMemPercent:{curMemPercent:.2f}\tpercCPU: {percCPU}', flush=True)
    time.sleep(INTERVAL_SEC)

  print(f'********* Stopping Monitoring at {datetime.now().strftime(TIME_MASK)} **********\n', flush=True)

  stopAllBalloonPeriods(doms)
  conn.close()
  exit(0)


#!/usr/bin/env python3.9
# Example-35.py
from __future__ import print_function
import sys
import os
import socket
import libvirt
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

#=============================
#   Including Project Libs
#=============================
# for the purpose of run this script, after that this SHOULD BE MODIFIED.
sys.path.append(f'{PROGRAM_PATH}/../libs')

from sig_helper import GracefulKiller


def startAllBalloonPeriods(doms):
  for dom in doms:
    print(f'Definning Balloon Period for {dom.name()}') 
    try:
      subprocess.check_call(['virsh', 'dommemstat', '--domain', dom.name(), '--period', '1']) 
    except subprocess.CalledProcessError:
      print(f'Error while definning Balloon Period for {dom.name()}. Closing process.')
      exit(1)
    print('OK!')

def stopAllBalloonPeriods(doms):
  for dom in doms:
    print(f'Unfinning Balloon Period for {dom.name()}')
    try:
      subprocess.check_call(['virsh', 'dommemstat', '--domain', dom.name(), '--period', '0'])
    except subprocess.CalledProcessError:
      print(f'Error while definning Balloon Period for {dom.name()}. Closing process.')
      exit(1)
    print('OK!')

def getMemConsumption(dom):
  stats  = dom.memoryStats()
  totalMem = stats.get("actual", 1)
  curMem = max(0, totalMem - stats.get("unused", totalMem))

  curMemPercent = (curMem / float(totalMem)) * 100
  curMemPercent = max(0.0, min(curMemPercent, 100.0))
   
  return curMem, curMemPercent



#=============================
#       Main code
#=============================

if __name__ == '__main__':
  domName = socket.gethostname()

  conn = libvirt.open('qemu:///system')
  if conn == None:
    print('Failed to open connection to qemu:///system', file=sys.stderr)
    exit(1)

  domsID = conn.listDomainsID()

  if not domsID:
    print('Failed to find virtual domains in '+domName, file=sys.stderr)
    exit(1)

  doms = []
  for id in domsID:
    doms.append(conn.lookupByID(id))

  startAllBalloonPeriods(doms)

  killer = GracefulKiller()

  print(f'********* Start Memory Menitoring at {datetime.now().strftime("%d/%m/%Y %H:%M:%S")} **********')
  while not killer.kill_now:
  
    print(datetime.now().strftime("%d/%m/%Y %H:%M:%S")) 
    for dom in doms:
      curMem, curMemPercent = getMemConsumption(dom)
      print(f'\t{dom.name()}\t{curMem}\t{curMemPercent:.2f}')
    time.sleep(1)

  print(f'********* Stopping Memory Menitoring at {datetime.now().strftime("%d/%m/%Y %H:%M:%S")} **********')

  stopAllBalloonPeriods(doms)
  conn.close()
  exit(0)


#!/usr/bin/env python3.9
import libvirt

def libvirtConnect():
  try:
    conn = libvirt.open('qemu:///system')
  except Exception as e:
    print(f'Failed to open connection to qemu:///system: {Exception}', file=sys.stderr)
    exit(1)
  
  return conn

def recoverActiveDomains(conn):
  domIDs = []
  try:
    doms = conn.listAllDomains(libvirt.VIR_CONNECT_LIST_DOMAINS_ACTIVE)
  except Exception as e:
    print(f'Failed to recover domains {Exception}', file=sys.stderr)
    exit(1)

  return doms

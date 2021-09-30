#include <stdio.h>
#include <stdlib.h>
#include <libvirt/libvirt.h>

#include "cpuMemoryMonitor.h"

// Attempting to connect with virtual environment informed by 'connection'. 
virConnectPtr libvirtConnect(const char * connection){
    virConnectPtr conn;
    conn = virConnectOpen(connection);

    if (conn == NULL) {
        fprintf(stderr, "Failed to open connection to '%s'.\n", connection);
        exit(1);
    }

    return conn;
}

// Recovering all Active Domains from connection "conn".
TDomains getActiveDomains(virConnectPtr conn){
    TDomains domains;

    domains.number = virConnectListAllDomains(conn, &domains.pointer, VIR_CONNECT_LIST_DOMAINS_ACTIVE);

    if(domains.number < 0){
        fprintf(stderr, "Failed to recover Active Domains.\n");
        exit(1);
    }

    return domains;
}


int main(int argc, char *argv[])
{
    virConnectPtr conn;
    TDomains domains;

    // Establishing connection with qemu.
    conn = libvirtConnect("qemu:///system");
    
    // Recovering domains number and pointers to structure 'domains'.
    domains = getActiveDomains(conn);
        
    virConnectClose(conn);
}
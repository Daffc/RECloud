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

void getDomainInfo(virDomainPtr domain){
    virDomainInfo info;
    int ret;

    char * name;

    // unsigned char 	state the running state, one of virDomainState
    // unsigned long 	maxMem 	the maximum memory in KBytes allowed
    // unsigned long 	memory 	the memory in KBytes used by the domain
    // unsigned short 	nrVirtCpu 	the number of virtual CPUs for the domain
    // unsigned long long 	cpuTime 	the CPU time used in nanoseconds

    ret = virDomainGetInfo(domain, &info);

    if(ret < 0){
        fprintf(stderr, "Failed to recover domain Information.\n");
        exit(1);
    }

    name = (char *) virDomainGetName(domain);

    printf("%s\n", name);
    printf("\tstate: %u\n", info.state);
    printf("\tmaxMem: %lu\n", info.maxMem);
    printf("\tmemory: %lu\n", info.memory);
    printf("\trVirtCpu: %hu\n", info.nrVirtCpu);
    printf("\tcpuTime: %llu\n", info.cpuTime);
}


int main(int argc, char *argv[])
{
    virConnectPtr conn;
    TDomains domains;

    // Establishing connection with qemu.
    conn = libvirtConnect("qemu:///system");
    
    // Recovering domains number and pointers to structure 'domains'.
    domains = getActiveDomains(conn);
    
    // Recovering Domains Information.
    for(int i = 0; i < domains.number; i ++)
        getDomainInfo(domains.pointer[i]);

    virConnectClose(conn);
}
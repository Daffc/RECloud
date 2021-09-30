#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <libvirt/libvirt.h>

#include "cpuMemoryMonitor.h"
#include "timeLib.h"

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
TDomainsList getActiveDomains(virConnectPtr conn){
    TDomainsList domains;
    virDomainPtr *domains_pointers;
    int i;

    // Recovering the number of domains and their pointers.
    domains.number = virConnectListAllDomains(conn, &domains_pointers, VIR_CONNECT_LIST_DOMAINS_ACTIVE);

    if(domains.number < 0){
        fprintf(stderr, "Failed to recover Active Domains.\n");
        exit(1);
    }

    // Allocating domain structures and distributing domain pointer and name accordingly.
    domains.list = malloc(domains.number * sizeof(TDomain));
    for(i = 0; i< domains.number; i++){
        domains.list[i].pointer = domains_pointers[i];
        strcpy (domains.list[i].name, virDomainGetName(domains.list[i].pointer));
    } 

    return domains;
}

void getDomainInfo(TDomain domain){
    virDomainInfo info;
    struct timespec t_current;
    int ret;
    char * name;

    // unsigned char 	state the running state, one of virDomainState
    // unsigned long 	maxMem 	the maximum memory in KBytes allowed
    // unsigned long 	memory 	the memory in KBytes used by the domain
    // unsigned short 	nrVirtCpu 	the number of virtual CPUs for the domain
    // unsigned long long 	cpuTime 	the CPU time used in nanoseconds

    // Recovering time of sampling and sampling infomations from domain.
    clock_gettime(CLOCK_REALTIME, &t_current);
    ret = virDomainGetInfo(domain.pointer, &info);
    if(ret < 0){
        fprintf(stderr, "Failed to recover domain Information.\n");
        exit(1);
    }
    
    // Storing data to the domain structure.
    domain.info = info;
    domain.cpu_Timestamp = t_current;
    
    printf("%s\n", domain.name);
    printf("\tstate: %u\n", domain.info.state);
    printf("\tmaxMem: %lu\n", domain.info.maxMem);
    printf("\tmemory: %lu\n", domain.info.memory);
    printf("\trVirtCpu: %hu\n", domain.info.nrVirtCpu);
    printf("\tcpuTime: %llu\n", domain.info.cpuTime);
    printf("\t"); print_time(domain.cpu_Timestamp);

}


int main(int argc, char *argv[])
{
    virConnectPtr conn;
    TDomainsList domains;

    // Establishing connection with qemu.
    conn = libvirtConnect("qemu:///system");
    
    // Recovering domains number and pointers to structure 'domains'.
    domains = getActiveDomains(conn);
    
    // Recovering Domains Information.
    for(int i = 0; i < domains.number; i ++)
        getDomainInfo(domains.list[i]);

    virConnectClose(conn);
}
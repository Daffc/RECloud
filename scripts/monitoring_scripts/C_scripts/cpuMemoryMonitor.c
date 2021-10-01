#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <libvirt/libvirt.h>

#include <unistd.h>

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

// Recover domain CPU usage since the last measurement.
double getDomainCPUUsage(TDomain *domain){
    virDomainInfo info;

    struct timespec t_current;
    struct timespec t_diff;

    double percCPU;
    double d_diff;

    // unsigned char 	state the running state, one of virDomainState
    // unsigned long 	maxMem 	the maximum memory in KBytes allowed
    // unsigned long 	memory 	the memory in KBytes used by the domain
    // unsigned short 	nrVirtCpu 	the number of virtual CPUs for the domain
    // unsigned long long 	cpuTime 	the CPU time used in nanoseconds

    // Recovering time of sampling and sampling infomations from domain.
    clock_gettime(CLOCK_REALTIME, &t_current);
    if(virDomainGetInfo(domain->pointer, &info) < 0){
        fprintf(stderr, "Failed to recover domain Information.\n");
        exit(1);
    }    

    // Recovering the difference between the last and current sampling timestamp and converting the difference to double.
    timespec_enlapse(&t_diff, domain->cpu_Timestamp, t_current);
    d_diff = timespecToDouble(&t_diff);
    
    // Calculating new CPU usage percentage.
    percCPU = (((info.cpuTime - domain->cpuTime) * 1.0) / (d_diff * 10000000));

    // Storing data to the domain data.
    domain->cpuTime = info.cpuTime;
    domain->cpu_Timestamp = t_current;

    // Returning new CPU usage measurement.
    return percCPU;
}


int main(int argc, char *argv[])
{
    struct timespec t_sampling;
    virConnectPtr conn;
    TDomainsList domains;


    // Establishing connection with qemu.
    conn = libvirtConnect("qemu:///system");
    
    // Recovering domains number and pointers to structure 'domains'.
    domains = getActiveDomains(conn);
    

    // Recovering Domains Information.
    for(int i = 0; i < domains.number; i ++){
        clock_gettime(CLOCK_REALTIME, &(domains.list[i].cpu_Timestamp));
        domains.list[i].cpuTime = 0;
        getDomainCPUUsage(&(domains.list[i]));  

    }

    while(1){

        // Getting and printing samppling time.
        clock_gettime(CLOCK_REALTIME, &t_sampling);
        printf("%s\n", stringifyTimespec(t_sampling));
        
        // Recovering Domains Information.
        for(int i = 0; i < domains.number; i ++){
            printf("\t%s\n", domains.list[i].name);
            printf("\t\tpercCPU: %.2f\n", getDomainCPUUsage(&(domains.list[i])));
        }

        // Sleeping
        usleep(500000);
    }

    virConnectClose(conn);
}
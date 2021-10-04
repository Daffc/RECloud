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
void getDomainCPUUsage(TDomain *domain){
    virDomainInfo info;

    struct timespec t_current;
    struct timespec t_diff;

    double percCPU;
    double d_diff;

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
    
    // Returning new CPU usage measurement in domain structure.
    domain->cpu_perc = percCPU;
}

void getDomainMemUsage(TDomain *domain){
    virDomainMemoryStatStruct mem_stats[VIR_DOMAIN_MEMORY_STAT_NR];
    int n_mem_stats;
    unsigned long long unused, actual, used;

    // Recover All Memory Stats for domain.
    n_mem_stats = virDomainMemoryStats(domain->pointer, mem_stats, VIR_DOMAIN_MEMORY_STAT_NR, 0);
    if(n_mem_stats < 0){
        fprintf(stderr, "Failed to recover domain Memory Stats.\n");
        exit(1);
    }    

    // Iterating throught all returned memory status, looking for current 
    // unused memory (tag  = VIR_DOMAIN_MEMORY_STAT_UNUSED) and total 
    // available memory by the domain perspective (tag =VIR_DOMAIN_MEMORY_STAT_AVAILABLE). 
    for(int j = 0; j <  n_mem_stats; j++){
        if (mem_stats[j].tag == VIR_DOMAIN_MEMORY_STAT_UNUSED)
            unused = mem_stats[j].val;
        if (mem_stats[j].tag == VIR_DOMAIN_MEMORY_STAT_AVAILABLE)
            actual = mem_stats[j].val;
    }

    // Calculating Used Memory (Available - (Used + Cached)).
    used = actual - unused;

    // Updating domain structure valuer for memory in yse (used + cached)
    domain->used_mem = used;
    domain->used_mem_perc = (used * 1.0 / actual) * 100;
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

        // Sampling current time.
        clock_gettime(CLOCK_REALTIME, &t_sampling);
        
        // Recovering Domains Information.
        for(int i = 0; i < domains.number; i ++){
            getDomainCPUUsage(&(domains.list[i]));
            getDomainMemUsage(&(domains.list[i]));
        }

        // Printing sampling time.
        printf("%s", stringifyTimespec(t_sampling));
        
        // For all domains, dusplay statistics.
        for(int i = 0; i < domains.number; i ++){
            printf("; %s", domains.list[i].name);               // Domain name.
            printf(" %llu", domains.list[i].used_mem);          // Domain used memory (used + cached in KB).
            printf(" %3.2f", domains.list[i].used_mem_perc);    // Domain used memory percentage (used + cached).
            printf(" %3.2f", domains.list[i].cpu_perc);         // Domain used memory percentage.
        }
        printf("\n");


        // Sleeping
        usleep(500000);
    }

    virConnectClose(conn);
}

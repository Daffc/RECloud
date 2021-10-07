#include <libvirt/libvirt.h>
#include <time.h>

#ifndef __CPUMEMMONIOR__
#define __CPUMEMMONIOR__

    #define MAXNAME 100
    
    // Structure to store each domain of the virtual environment.
    typedef struct t_Domain{
        virDomainPtr pointer;
        unsigned long long  cpuTime;
        struct timespec cpu_Timestamp;
        double cpu_perc;
        unsigned long long used_mem;
        double used_mem_perc;
        char name[MAXNAME];
    }TDomain;

    // Structure to manage all domains of a connection. 
    typedef struct t_DomainsList{
        TDomain *list;
        int number;
    }TDomainsList;

#endif
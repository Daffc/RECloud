#include <libvirt/libvirt.h>

#ifndef __CPUMEMMONIOR__
#define __CPUMEMMONIOR__

    // Structure to manage all domains of a connection. 
    typedef struct t_Domains{
        virDomainPtr *pointer;
        int number;
    }TDomains;

#endif
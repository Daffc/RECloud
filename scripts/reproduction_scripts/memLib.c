#include <sys/time.h>
#include <sys/resource.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/sysinfo.h>
#include <unistd.h>

// Returns current processes (alongside childrens) resident memory usage in KB.
unsigned long getSelfMem(){
    struct rusage r_usage; 
    
    if (getrusage(RUSAGE_SELF,&r_usage) == -1){
        fprintf(stderr, "ERROR: Unable to sample memory usage of process.\n");
        exit(1);
    }

    // Returns proces memory usage in KB.
    return r_usage.ru_maxrss;
}

// Returns sysinfo structure, storing the following system's data:
// struct sysinfo {
//     long uptime;             /* Seconds since boot */
//     unsigned long loads[3];  /* 1, 5, and 15 minute load averages */
//     unsigned long totalram;  /* Total usable main memory size */
//     unsigned long freeram;   /* Available memory size */
//     unsigned long sharedram; /* Amount of shared memory */
//     unsigned long bufferram; /* Memory used by buffers */
//     unsigned long totalswap; /* Total swap space size */
//     unsigned long freeswap;  /* Swap space still available */
//     unsigned short procs;    /* Number of current processes */
//     unsigned long totalhigh; /* Total high memory size */
//     unsigned long freehigh;  /* Available high memory size */
//     unsigned int mem_unit;   /* Memory unit size in bytes */
//     char _f[20-2*sizeof(long)-sizeof(int)]; /* Padding to 64 bytes */
// };
void getSysMemInfo(struct sysinfo *sys_info){

    if(sysinfo(sys_info) != 0){
        fprintf(stderr, "ERROR: Unable to sample system's memory usage .\n");
        exit(1);
    }    
}

// Recover sysinfo structure from OS and calculates busy memory of the system ((total - free) AKA (used + buff/cache)) in kilobytes.
unsigned long long getSysBusyMem(){
    struct sysinfo sys_info;
    unsigned long long busy_sys_mem_kB;

    // Reecovering sysinfo structure.
    getSysMemInfo(&sys_info);

    // Calculating System Busy Memory ((total - free) AKA (used + buff/cache)). (kB)
    busy_sys_mem_kB = (sys_info.totalram - sys_info.freeram) * (unsigned long long) sys_info.mem_unit / 1024;

    return busy_sys_mem_kB;
}


// Given the 'mem' memory pointer, 'new_mem_load' and 'prev_mem_load' that informs new and previous 
// size of 'mem' allocation, this function calculates the address that hasn't been previously written 
// and access them, claiming physical memory pages.
void touchNewAddresses(char *mem, long long new_mem_load, long long prev_mem_load){
    char *p_begin_difference;
    long long difference;

    p_begin_difference = mem + prev_mem_load;
    difference =  new_mem_load - prev_mem_load;

    printf("\t\tdifference: %lld\n", difference);
    memset(p_begin_difference, 0, difference);
}
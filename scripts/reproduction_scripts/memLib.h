    #include <sys/time.h>
    #include <sys/resource.h>
    #include <stdio.h>
    #include <stdlib.h>
    #include <string.h>
    #include <sys/sysinfo.h>
    #include <unistd.h>

#ifndef __MEM_LIB__
    #define __MEM_LIB__

    // Structure to recover data from '/proc/self/statm', that contains memory data of 'conductor' process.
    typedef struct t_statm_entry{
        unsigned long size;         // (1) total program size (same as VmSize in /proc/[pid]/status)
        unsigned long resident;     // (2) resident set size (same as VmRSS in /proc/[pid]/status)
        unsigned long shared;       // (3) shared pages (i.e., backed by a file)
        unsigned long text;         // (4) text (code)
        char lib;                   // (5) library (unused in Linux 2.6)    
        unsigned long data;         // (6) data + stack
        char dt;                    // (7) dirty pages (unused in Linux 2.6) 
    } TstatmEntry;

    // Returns current processes (alongside children) resident memory usage in KB.
    unsigned long long getSelfMem();

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
    void getSysMemInfo(struct sysinfo *sys_info);

    // Recover sysinfo structure from OS and calculates busy memory of the system ((total - free) AKA (used + buff/cache)) in kilobytes.
    unsigned long long getSysBusyMem();

    // Given the 'mem' memory pointer, 'new_mem_load' and 'prev_mem_load' that informs new and previous 
    // size of 'mem' allocation, this function calculates the address that hasn't been previously written 
    // and access them, claiming physical memory pages.
    void touchNewAddresses(char *mem, long long new_mem_load, long long prev_mem_load);

#endif
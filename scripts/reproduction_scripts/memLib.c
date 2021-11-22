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
struct sysinfo getSysMemInfo(){
    struct sysinfo sys_info;

    if(sysinfo(&sys_info) != 0){
        fprintf(stderr, "ERROR: Unable to sample system's memory usage .\n");
        exit(1);
    }    

    return sys_info;
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

int main(int argc, char *argv[]){
 
    unsigned long long mem_sample;
    unsigned long long busy_sys_idel_mem;
    unsigned long long env_mem_load;
    char *mem;
    struct sysinfo sys_info;
    unsigned long proc_ram;
    long page_size;
    long long final_mem_load;
    long long prev_mem_load;

    if(argc < 2){
        fprintf(stderr, "ENTRADA: ./getSelfMeme [VALOR EM KB]\n");
        exit(1);
    }

    // Receive sample (KB)
    mem_sample = strtoull(argv[1], NULL, 0);
    printf("mem_sample: %lld\n", mem_sample);

    // Basic allocation to enable loop.
    mem = (char*) malloc(1);

    sys_info = getSysMemInfo();     // Recovering sysem info (Idle).
    proc_ram = getSelfMem();        // Recovering Program Memory usage (Idle)

    // Calculating System Busy Memory ((total - free) AKA (used + buff/cache)). (kB)
    busy_sys_idel_mem = (sys_info.totalram - sys_info.freeram) *(unsigned long long)sys_info.mem_unit / 1024;

    // Calculating Memory of Idle System + current process and childrens 
    // ( all functional structures properly and already allocated) in KB.
    env_mem_load = busy_sys_idel_mem;

    // Stores previous applyed memory load.
    prev_mem_load = 0;

    // --------------- DEBUG  ---------------
    printf("TOTAL RAM: %llu", sys_info.totalram *(unsigned long long)sys_info.mem_unit / 1024);
    printf("\tFree RAM: %llu", sys_info.freeram *(unsigned long long)sys_info.mem_unit / 1024);
    printf("\tBusy RAM: %llu", busy_sys_idel_mem);
    printf("\tenv_mem_load RAM: %llu", env_mem_load);
    printf("\tSELF MEM: %ld\n", proc_ram);
    // --------------- DEBUG  ---------------
    
    long variation = 0;

    while(1){
        
        // Calculating new memory workload (uptading mem_sample)
        final_mem_load = mem_sample - env_mem_load;
        printf("\tfinal_mem_load: %lld\n", final_mem_load);

        // Converting final_mem_load from Kbytes to bytes.
        final_mem_load = final_mem_load * 1024;

        // Checking if it is needed to memoy onerate the system (final_mem_load is positive).
        if(final_mem_load > 0){

            // Adjusting memory allocation.
            mem = (char*) realloc(mem, final_mem_load);

            // If the total needed memory has increased, occupy the allocated space.
            if(final_mem_load > prev_mem_load){
                touchNewAddresses(mem, final_mem_load, prev_mem_load);     
            }
        }
        // If system is alread to load compared to the mem sample (final_mem_load is negative, occupy minimum space as possible).
        else{
            // Adjusting memory allocation.
            mem = (char*) realloc(mem, 0);
        }

        // --------------- DEBUG  ---------------
        sys_info = getSysMemInfo();
        proc_ram = getSelfMem();
        printf("TOTAL RAM: %llu", sys_info.totalram *(unsigned long long)sys_info.mem_unit / 1024);
        printf("\tFree RAM: %llu", sys_info.freeram *(unsigned long long)sys_info.mem_unit / 1024);
        printf("\tSELF MEM: %ld\n", proc_ram);

        // mem_sample += variation;
        // --------------- DEBUG  ---------------


        prev_mem_load = final_mem_load;
        sleep(1);
    }

    getchar();
    free(mem);
}
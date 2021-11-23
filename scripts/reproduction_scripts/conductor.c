#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <ctype.h>
#include <pthread.h>
#include <unistd.h>

#include "timeLib.h"
#include "treaceReader.h"
#include "stressor.h"
#include "memLib.h"

#define NTHREADS 2

unsigned long long memLoadBytes;

// Reads Arguments received by the program, informing help messages, 
// defining input trace file.
void parseArguments(int argc, char *argv[], FILE **input){
    char c;
    *input = NULL;

    while ((c = getopt (argc, argv, "hi:")) != -1)
    switch (c){
        // Helper Argument.
        case 'h': 
            // Outputting help message.
            printf(
                "Program to reproduce  PAJE file trace that describes one virtual node of a cloud environment.\n\n"
                "Optional arguments:\n"
                "\t-h\tDisplay help Message.\n"
                "\t-i\tPath to input file (trace file).\n"
            );

            exit(0);
            break;
        
        // Defining input trace file. 
        case 'i':
            
            // Defining file descriptor to the output file. 
            *input = fopen(optarg,"r");

            // Checking if the operation was successful.
            if (*input == NULL) {
                fprintf(stderr, "ERROR: Error while oppening file '%s'.\n", optarg);
                exit(1);
            }
            break;

        // Unknow argument / not optinal argument not informed.  
        case '?':
            if (optopt == 'i')
                fprintf (stderr, "ERROR: Option '-i' requires an argument (path to PAJE trace file).\n");
            else if (isprint (optopt))
                fprintf (stderr, "ERROR: Unknown option '-%c'.\n", optopt);
            else
                fprintf (stderr, "ERROR: Unknown option character '\\x%x'.\n", optopt);
            exit(1);

        // Fallback.31229952
        default:
            abort();
    }

    if (*input == NULL){
        fprintf (stderr, "ERROR: Virtual machine trace file must be informed (option '-i [path_to_trace_file]')\n");
        exit(1);
    }
}

// Given Idle System load (env_mem_load_kB) and next expected system load (trace_mem_kB), 
// calculates the memory value in Bytes that each stressor will have to occupy.
unsigned long long calculateSharedMemLoadBytes(unsigned long long env_mem_load_kB, unsigned long long trace_mem_kB, unsigned char n_stressors){
    unsigned long long final_mem_load;

    // Calculating new memory workload
    final_mem_load = trace_mem_kB - env_mem_load_kB;

    // Converting final_mem_load from KB to B.
    final_mem_load = final_mem_load * 1024;

    printf("final_mem_load: %llu\n", final_mem_load);

    // Dividing load by the number of stressors.
    final_mem_load = final_mem_load / n_stressors;

    return final_mem_load;
}

int main(int argc, char *argv[]){
    struct timespec ts_sampling;        // Stores current time after calculus and before sleep.

    double db_delay;                    // Target delay between iterations (must be the same as the used to generate the reproduced trace).
    double db_acc;                      // Accumulates the time error between iterations in order to dissipate it along the reproduction.
    struct timespec ts_interval;        // Actial time interval that will be applied to sleep function.
    struct timespec ts_prev;            // Current time of previour time sampling (ts_sampling).

    pthread_t *stressors;               // Pointer to array of descriptors of stressor threads.

    // External mutex for stressors controll.
    extern pthread_cond_t cv;

    TTraceEntry t_entry;                // Structure that stores information for trace entry according to Timestamp.

    FILE *f_trace;                      // The file descriptor of trace that will be read.

    unsigned long long env_mem_load;    // Stores amount of memory used by the system in Idle state + allocated structures of 'conductor' processes and children in kB.

    parseArguments(argc, argv, &f_trace);

    // Adjusting 'f_traces' pointer to the first CPU/MEM trace entry.
    if(!preparePointerCPUMem(f_trace)){
        fprintf(stderr, "ERROR: CPU and/or Memory Trace was not found.\n");
        fclose(f_trace);
        exit(1);
    }

    // Allocating Stressors and getting them ready to reproduction.
    stressors = malloc (NTHREADS * sizeof(pthread_t));
    startStressors(stressors, NTHREADS);

    // Recovering environment memory load (Idle system + this process).
    env_mem_load = getSysBusyMem();
    printf("env_mem_load :%llu\n", env_mem_load);

    db_delay = 0.5;

    // Initiating time control variables.
    db_acc = 0;                                     // The variable that accumulates error between sampling rounds.
    ts_interval = doubleToTimespec(&db_delay);      // The Timespec representation of delay between sampling intervals.

    // Initializing variable to calculate elapsed time.
    clock_gettime(CLOCK_REALTIME, &ts_prev);

    nanosleep(&ts_interval , &ts_interval);
    
    // Sampling current time.
    clock_gettime(CLOCK_REALTIME, &ts_sampling);

    while(followCPUMem(f_trace, &t_entry)){

        printf("%s\n", stringifyTimespec(ts_sampling));
        printf("%lf, %llu, %f\n", t_entry.timestamp, t_entry.mem_kB, t_entry.cpu_perc);

        // Calculating new adusted interval.
        ts_interval = calculateNextInterval(ts_sampling, ts_prev, db_delay, &db_acc);

        // Updating value of previous time measured (ts_prev).
        ts_prev = ts_sampling;

        
        memLoadBytes = calculateSharedMemLoadBytes(env_mem_load, t_entry.mem_kB, NTHREADS);

        printf("memLoadBytes: %llu\n", memLoadBytes);

        pthread_cond_broadcast(&cv);

        // Sleeping
        nanosleep(&ts_interval , &ts_interval);

        // Sampling current time.
        clock_gettime(CLOCK_REALTIME, &ts_sampling);
    }

    // Killing stressors and freeinf their management memory.
    stopStressors(stressors, NTHREADS);
    free(stressors);
    fclose(f_trace);
}
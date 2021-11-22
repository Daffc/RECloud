#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <signal.h>
#include <ctype.h>
#include <pthread.h>
#include <unistd.h>

#include "timeLib.h"
#include "treaceReader.h"
#include "stressor.h"

#define NTHREADS 2

int *ids;

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

        // Fallback.
        default:
            abort();
    }

    if (*input == NULL){
        fprintf (stderr, "ERROR: Virtual machine trace file must be informed (option '-i [path_to_trace_file]')\n");
        exit(1);
    }
}

// int calculateSharedMemory

int main(int argc, char *argv[]){
    struct timespec ts_sampling;    // Stores current time after calculus and before sleep.

    double db_delay;                // Target delay between iterations (must be the same as the used to generate the reproduced trace).
    double db_acc;                  // Accumulates the time error between iterations in order to dissipate it along the reproduction.
    struct timespec ts_interval;    // Actial time interval that will be applied to sleep function.
    struct timespec ts_prev;        // Current time of previour time sampling (ts_sampling).

    pthread_t *stressors;           // Pointer to array of descriptors of stressor threads.

    TTraceEntry t_entry;            // Structure that stores information for trace entry according to Timestamp.

    FILE *f_trace;                  // The file descriptor of trace that will be read.

    parseArguments(argc, argv, &f_trace);

    if(!preparePointerCPUMem(f_trace)){
        fprintf(stderr, "ERROR: CPU and/ or Memory Trace was not found.\n");
        fclose(f_trace);
        exit(1);
    }

    stressors = malloc (NTHREADS * sizeof(pthread_t));
    ids = malloc(NTHREADS * sizeof(int));
    
    pthread_mutex_init( &lock_loop, NULL);
    pthread_mutex_init( &lock_sync, NULL);
    pthread_cond_init( &cv, NULL);

    pthread_mutex_lock(&lock_sync);

    // Creating threads
    for(int i = 0; i < NTHREADS; i++){
        ids[i] = i;
        pthread_create(&stressors[i], NULL, initializeStressor, (void *)(ids + i));
    }

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
        printf("%lf, %u, %f\n", t_entry.timestamp, t_entry.mem_kB, t_entry.cpu_perc);

        // Calculating new adusted interval.
        ts_interval = calculateNextInterval(ts_sampling, ts_prev, db_delay, &db_acc);

        // Updating value of previous time measured (ts_prev).
        ts_prev = ts_sampling;

        pthread_cond_broadcast(&cv);

        // Sleeping
        nanosleep(&ts_interval , &ts_interval);

        // Sampling current time.
        clock_gettime(CLOCK_REALTIME, &ts_sampling);
    }

    for(int i = 0; i < NTHREADS; i++){
        pthread_kill(stressors[i], SIGTERM);   
        pthread_join(stressors[i], NULL);
    }

    fclose(f_trace);
    free(ids);
    free(stressors);
}